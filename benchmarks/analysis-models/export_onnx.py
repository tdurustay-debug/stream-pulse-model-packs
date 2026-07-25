#!/usr/bin/env python3
"""Download pinned candidates, execute them, export ONNX, and quantize INT8."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import shutil
import sys
import tempfile
import time
import urllib.request
from pathlib import Path
from typing import Any

import numpy as np
import onnx
import onnxruntime as ort
import torch
import torch.nn.functional as functional
from huggingface_hub import snapshot_download
from onnxruntime.quantization import QuantType, quantize_dynamic
from transformers import AutoConfig, AutoModel, AutoTokenizer


MODEL_SPECS = (
    {
        "key": "multilingual-minilm",
        "model_id": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        "revision": "e8f8c211226b894fcb81acc59f3b34ba3efd5f42",
        "license": "apache-2.0",
    },
    {
        "key": "multilingual-distilbert",
        "model_id": "distilbert/distilbert-base-multilingual-cased",
        "revision": "45c032ab32cc946ad88a166f7cb282f58c753c2e",
        "license": "apache-2.0",
    },
)

SNAPSHOT_PATTERNS = (
    "README.md",
    "config.json",
    "config_sentence_transformers.json",
    "model.safetensors",
    "modules.json",
    "sentence_bert_config.json",
    "sentencepiece.bpe.model",
    "special_tokens_map.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "unigram.json",
    "vocab.txt",
    "1_Pooling/config.json",
)

LICENSE_URL = "https://www.apache.org/licenses/LICENSE-2.0.txt"


class MeanPoolingModel(torch.nn.Module):
    """Return deterministic, L2-normalized mean-pooled representations."""

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
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--downloads-dir", type=Path, required=True)
    parser.add_argument("--generated-dir", type=Path, required=True)
    parser.add_argument("--results-dir", type=Path, required=True)
    return parser.parse_args()


def directory_size(directory: Path) -> int:
    return sum(
        file.stat().st_size
        for file in directory.rglob("*")
        if file.is_file() and ".cache" not in file.parts
    )


def sha256_file(file: Path) -> str:
    digest = hashlib.sha256()
    with file.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def architecture_metadata(config: Any) -> dict[str, Any]:
    return {
        "model_type": getattr(config, "model_type", None),
        "architectures": getattr(config, "architectures", None),
        "hidden_size": getattr(config, "hidden_size", getattr(config, "dim", None)),
        "num_hidden_layers": getattr(
            config, "num_hidden_layers", getattr(config, "n_layers", None)
        ),
        "num_attention_heads": getattr(
            config, "num_attention_heads", getattr(config, "n_heads", None)
        ),
        "vocab_size": getattr(config, "vocab_size", None),
        "max_position_embeddings": getattr(config, "max_position_embeddings", None),
    }


def run_onnx(path: Path, encoded: dict[str, torch.Tensor]) -> np.ndarray:
    session = ort.InferenceSession(
        str(path),
        providers=["CPUExecutionProvider"],
    )
    inputs = {
        "input_ids": encoded["input_ids"].cpu().numpy().astype(np.int64),
        "attention_mask": encoded["attention_mask"].cpu().numpy().astype(np.int64),
    }
    return session.run(["sentence_embedding"], inputs)[0]


def main() -> int:
    arguments = parse_arguments()
    for directory in (
        arguments.cache_dir,
        arguments.downloads_dir,
        arguments.generated_dir,
        arguments.results_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    random.seed(20260725)
    np.random.seed(20260725)
    torch.manual_seed(20260725)
    torch.set_num_threads(max(1, os.cpu_count() or 1))

    license_directory = arguments.downloads_dir / "licenses"
    license_directory.mkdir(parents=True, exist_ok=True)
    license_path = license_directory / "Apache-2.0.txt"
    if not license_path.exists():
        urllib.request.urlretrieve(LICENSE_URL, license_path)

    results: dict[str, Any] = {
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "license_archive": {
            "identifier": "apache-2.0",
            "source_url": LICENSE_URL,
            "local_path": str(license_path.resolve()),
            "size_bytes": license_path.stat().st_size,
            "sha256": sha256_file(license_path),
        },
        "tool_versions": {
            "python": sys.version.split()[0],
            "torch": torch.__version__,
            "onnx": onnx.__version__,
            "onnxruntime": ort.__version__,
        },
        "models": [],
    }

    for spec in MODEL_SPECS:
        print(f"\nPreparing {spec['model_id']} at {spec['revision']}...", flush=True)
        model_result: dict[str, Any] = {
            **spec,
            "source_url": (
                f"https://huggingface.co/{spec['model_id']}/tree/{spec['revision']}"
            ),
            "license_metadata_source": (
                f"https://huggingface.co/api/models/{spec['model_id']}"
            ),
            "download_succeeded": False,
            "original_execution_succeeded": False,
            "onnx_export_succeeded": False,
            "onnx_execution_succeeded": False,
            "int8_quantization_succeeded": False,
            "int8_execution_succeeded": False,
            "warnings": [],
        }
        model_directory = arguments.downloads_dir / "models" / spec["key"]
        onnx_path = arguments.generated_dir / f"{spec['key']}.onnx"
        int8_path = arguments.generated_dir / f"{spec['key']}-int8.onnx"

        try:
            snapshot_path = Path(
                snapshot_download(
                    repo_id=spec["model_id"],
                    revision=spec["revision"],
                    local_dir=model_directory,
                    allow_patterns=list(SNAPSHOT_PATTERNS),
                    cache_dir=arguments.cache_dir / "huggingface",
                )
            )
            model_result["download_succeeded"] = True
            model_result["snapshot_path"] = str(snapshot_path.resolve())
            model_result["original_download_size_bytes"] = directory_size(snapshot_path)

            tokenizer = AutoTokenizer.from_pretrained(
                snapshot_path,
                local_files_only=True,
            )
            config = AutoConfig.from_pretrained(snapshot_path, local_files_only=True)
            model_result["architecture"] = architecture_metadata(config)

            load_started = time.perf_counter()
            base_model = AutoModel.from_pretrained(
                snapshot_path,
                local_files_only=True,
                use_safetensors=True,
            )
            base_model.eval()
            wrapped_model = MeanPoolingModel(base_model).eval()
            model_result["original_startup_ms"] = (
                time.perf_counter() - load_started
            ) * 1000

            example_texts = [
                "The stream audio sounds clear.",
                "Yayın sesi net duyuluyor.",
            ]
            encoded = tokenizer(
                example_texts,
                padding="max_length",
                truncation=True,
                max_length=32,
                return_tensors="pt",
            )
            inputs = {
                "input_ids": encoded["input_ids"],
                "attention_mask": encoded["attention_mask"],
            }
            with torch.inference_mode():
                original_output = wrapped_model(**inputs).cpu().numpy()
            if not np.isfinite(original_output).all():
                raise RuntimeError("Original model produced NaN or infinity.")
            model_result["original_execution_succeeded"] = True
            model_result["output_dimension"] = int(original_output.shape[-1])

            with torch.inference_mode():
                torch.onnx.export(
                    wrapped_model,
                    (inputs["input_ids"], inputs["attention_mask"]),
                    onnx_path,
                    export_params=True,
                    opset_version=17,
                    do_constant_folding=True,
                    input_names=["input_ids", "attention_mask"],
                    output_names=["sentence_embedding"],
                    dynamic_axes={
                        "input_ids": {0: "batch", 1: "sequence"},
                        "attention_mask": {0: "batch", 1: "sequence"},
                        "sentence_embedding": {0: "batch"},
                    },
                    dynamo=False,
                )
            onnx.checker.check_model(onnx.load(onnx_path))
            model_result["onnx_export_succeeded"] = True
            model_result["onnx_path"] = str(onnx_path.resolve())
            model_result["onnx_size_bytes"] = onnx_path.stat().st_size
            model_result["onnx_sha256"] = sha256_file(onnx_path)

            onnx_output = run_onnx(onnx_path, inputs)
            if onnx_output.shape != original_output.shape:
                raise RuntimeError(
                    f"ONNX shape {onnx_output.shape} differs from original "
                    f"{original_output.shape}."
                )
            if not np.isfinite(onnx_output).all():
                raise RuntimeError("ONNX model produced NaN or infinity.")
            model_result["onnx_execution_succeeded"] = True
            model_result["onnx_max_absolute_difference"] = float(
                np.max(np.abs(original_output - onnx_output))
            )

            try:
                # ONNX Runtime shape inference does not reliably create its
                # temporary "-inferred.onnx" file when a Windows path contains
                # non-ASCII characters. Quantize in the ASCII system temp path.
                with tempfile.TemporaryDirectory(
                    prefix=f"stream-pulse-{spec['key']}-"
                ) as temporary_directory:
                    temporary_root = Path(temporary_directory)
                    temporary_fp32 = temporary_root / "model.onnx"
                    temporary_int8 = temporary_root / "model-int8.onnx"
                    shutil.copy2(onnx_path, temporary_fp32)
                    quantize_dynamic(
                        model_input=str(temporary_fp32),
                        model_output=str(temporary_int8),
                        weight_type=QuantType.QInt8,
                        per_channel=False,
                        reduce_range=False,
                    )
                    shutil.copy2(temporary_int8, int8_path)
                onnx.checker.check_model(onnx.load(int8_path))
                model_result["int8_quantization_succeeded"] = True
                model_result["int8_path"] = str(int8_path.resolve())
                model_result["int8_size_bytes"] = int8_path.stat().st_size
                model_result["int8_sha256"] = sha256_file(int8_path)

                int8_output = run_onnx(int8_path, inputs)
                if int8_output.shape != original_output.shape:
                    raise RuntimeError(
                        f"INT8 shape {int8_output.shape} differs from original "
                        f"{original_output.shape}."
                    )
                if not np.isfinite(int8_output).all():
                    raise RuntimeError("INT8 model produced NaN or infinity.")
                model_result["int8_execution_succeeded"] = True
                model_result["int8_max_absolute_difference"] = float(
                    np.max(np.abs(original_output - int8_output))
                )
            except Exception as error:  # Continue so the other model is tested.
                model_result["warnings"].append(f"INT8 quantization: {error}")

        except Exception as error:  # Continue so failures are preserved as evidence.
            model_result["warnings"].append(f"Export pipeline: {error}")
            print(f"ERROR: {error}", file=sys.stderr, flush=True)
        finally:
            results["models"].append(model_result)
            del model_result

    output_path = arguments.results_dir / "export-results.json"
    output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nWrote {output_path}", flush=True)

    required_flags = (
        "original_execution_succeeded",
        "onnx_export_succeeded",
        "onnx_execution_succeeded",
        "int8_quantization_succeeded",
        "int8_execution_succeeded",
    )
    failed = [
        f"{model['model_id']}: {flag}"
        for model in results["models"]
        for flag in required_flags
        if not model.get(flag)
    ]
    if failed:
        print("One or more required export checks failed:", file=sys.stderr)
        for failure in failed:
            print(f"- {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
