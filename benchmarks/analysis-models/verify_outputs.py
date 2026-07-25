#!/usr/bin/env python3
"""Verify original, FP32 ONNX, and INT8 outputs across supported languages."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import onnxruntime as ort
import torch
import torch.nn.functional as functional
from transformers import AutoModel, AutoTokenizer


REQUIRED_NON_UNKNOWN_LANGUAGES = {"ja-JP", "tr-TR", "pl-PL", "ru-RU"}


class MeanPoolingModel(torch.nn.Module):
    def __init__(self, model: torch.nn.Module) -> None:
        super().__init__()
        self.model = model

    def forward(
        self, input_ids: torch.Tensor, attention_mask: torch.Tensor
    ) -> torch.Tensor:
        token_embeddings = self.model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            return_dict=True,
        ).last_hidden_state
        expanded_mask = attention_mask.unsqueeze(-1).to(token_embeddings.dtype)
        pooled = (token_embeddings * expanded_mask).sum(dim=1)
        pooled = pooled / expanded_mask.sum(dim=1).clamp(min=1e-9)
        return functional.normalize(pooled, p=2, dim=1)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--messages", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    return parser.parse_args()


def ort_session(path: str) -> ort.InferenceSession:
    return ort.InferenceSession(path, providers=["CPUExecutionProvider"])


def run_session(
    session: ort.InferenceSession, encoded: dict[str, torch.Tensor]
) -> np.ndarray:
    return session.run(
        ["sentence_embedding"],
        {
            "input_ids": encoded["input_ids"].cpu().numpy().astype(np.int64),
            "attention_mask": encoded["attention_mask"].cpu().numpy().astype(np.int64),
        },
    )[0]


def assert_valid_output(
    output: np.ndarray,
    expected_rows: int,
    expected_dimension: int,
    label: str,
) -> None:
    if output.shape != (expected_rows, expected_dimension):
        raise ValueError(
            f"{label} returned shape {output.shape}; expected "
            f"({expected_rows}, {expected_dimension})."
        )
    if not np.isfinite(output).all():
        raise ValueError(f"{label} returned NaN or infinity.")


def tokenization_result(
    tokenizer: Any, language: str, texts: list[str]
) -> dict[str, Any]:
    counts: list[int] = []
    unknown_counts: list[int] = []
    content_counts: list[int] = []
    special_ids = set(tokenizer.all_special_ids)
    unknown_id = tokenizer.unk_token_id

    for text in texts:
        token_ids = tokenizer(text, add_special_tokens=True)["input_ids"]
        content_ids = [token for token in token_ids if token not in special_ids]
        counts.append(len(token_ids))
        content_counts.append(len(content_ids))
        unknown_counts.append(
            sum(token == unknown_id for token in content_ids)
            if unknown_id is not None
            else 0
        )

    all_content_unknown = bool(
        sum(content_counts) > 0 and sum(unknown_counts) == sum(content_counts)
    )
    if language in REQUIRED_NON_UNKNOWN_LANGUAGES and all_content_unknown:
        raise ValueError(f"{language} tokenization was entirely unknown tokens.")
    if any(count == 0 for count in content_counts):
        raise ValueError(f"{language} produced an empty content token sequence.")

    return {
        "message_count": len(texts),
        "total_tokens_including_special": sum(counts),
        "minimum_tokens_including_special": min(counts),
        "maximum_tokens_including_special": max(counts),
        "total_content_tokens": sum(content_counts),
        "unknown_content_tokens": sum(unknown_counts),
        "all_content_unknown": all_content_unknown,
        "passed": True,
    }


def main() -> int:
    arguments = parse_arguments()
    metadata = json.loads(arguments.metadata.read_text(encoding="utf-8"))
    dataset = json.loads(arguments.messages.read_text(encoding="utf-8"))
    languages = dataset["languages"]

    results: dict[str, Any] = {
        "dataset_kind": dataset["dataset_kind"],
        "dataset_warning": dataset["warning"],
        "models": [],
    }
    failures: list[str] = []

    torch.manual_seed(20260725)
    torch.set_num_threads(max(1, torch.get_num_threads()))

    for model_metadata in metadata["models"]:
        model_result: dict[str, Any] = {
            "model_id": model_metadata["model_id"],
            "revision": model_metadata["revision"],
            "output_dimension": model_metadata["output_dimension"],
            "tokenization": {},
            "runtime_checks": {},
            "passed": False,
            "warnings": [],
        }
        try:
            snapshot_path = Path(model_metadata["snapshot_path"])
            tokenizer = AutoTokenizer.from_pretrained(
                snapshot_path, local_files_only=True
            )
            original = MeanPoolingModel(
                AutoModel.from_pretrained(
                    snapshot_path,
                    local_files_only=True,
                    use_safetensors=True,
                )
            ).eval()
            fp32_session = ort_session(model_metadata["onnx_path"])
            int8_session = ort_session(model_metadata["int8_path"])

            representative_texts: list[str] = []
            for language_entry in languages:
                language = language_entry["language"]
                texts = [message["text"] for message in language_entry["messages"]]
                model_result["tokenization"][language] = tokenization_result(
                    tokenizer, language, texts
                )
                representative_texts.append(texts[0])

            encoded = tokenizer(
                representative_texts,
                padding=True,
                truncation=True,
                max_length=128,
                return_tensors="pt",
            )
            model_inputs = {
                "input_ids": encoded["input_ids"],
                "attention_mask": encoded["attention_mask"],
            }
            expected_rows = len(representative_texts)
            expected_dimension = model_metadata["output_dimension"]

            with torch.inference_mode():
                original_first = original(**model_inputs).cpu().numpy()
                original_second = original(**model_inputs).cpu().numpy()
            fp32_first = run_session(fp32_session, model_inputs)
            fp32_second = run_session(fp32_session, model_inputs)
            int8_first = run_session(int8_session, model_inputs)
            int8_second = run_session(int8_session, model_inputs)

            runtime_outputs = {
                "original": (original_first, original_second),
                "onnx_fp32": (fp32_first, fp32_second),
                "onnx_int8": (int8_first, int8_second),
            }
            for runtime, (first, second) in runtime_outputs.items():
                assert_valid_output(
                    first, expected_rows, expected_dimension, runtime
                )
                assert_valid_output(
                    second, expected_rows, expected_dimension, runtime
                )
                stability_difference = float(np.max(np.abs(first - second)))
                stable = stability_difference <= 1e-6
                if not stable:
                    raise ValueError(
                        f"{runtime} repeated-input difference "
                        f"{stability_difference} exceeded tolerance."
                    )
                model_result["runtime_checks"][runtime] = {
                    "finite": True,
                    "shape": list(first.shape),
                    "stable_for_identical_input": stable,
                    "repeat_max_absolute_difference": stability_difference,
                }

            model_result["runtime_checks"]["onnx_fp32"][
                "original_max_absolute_difference"
            ] = float(np.max(np.abs(original_first - fp32_first)))
            model_result["runtime_checks"]["onnx_int8"][
                "original_max_absolute_difference"
            ] = float(np.max(np.abs(original_first - int8_first)))
            model_result["passed"] = True
        except Exception as error:
            failures.append(f"{model_metadata['model_id']}: {error}")
            model_result["warnings"].append(str(error))
        results["models"].append(model_result)

    arguments.results.parent.mkdir(parents=True, exist_ok=True)
    arguments.results.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Wrote {arguments.results}")

    if failures:
        print("Output verification failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Output verification passed for both candidates and all ten languages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
