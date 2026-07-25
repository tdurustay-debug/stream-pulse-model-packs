#!/usr/bin/env python3
"""Measure FP32 and dynamic INT8 ONNX Runtime CPU performance."""

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import statistics
import sys
import threading
import time
from pathlib import Path
from typing import Any

import numpy as np
import onnxruntime as ort
import psutil
from transformers import AutoTokenizer


SEQUENCE_LENGTHS = (32, 64, 128)
BATCH_SIZES = (1, 16, 64)


class MemorySampler:
    def __init__(self, interval_seconds: float = 0.005) -> None:
        self.process = psutil.Process()
        self.interval_seconds = interval_seconds
        self.peak_bytes = self.process.memory_info().rss
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._sample, daemon=True)

    def _sample(self) -> None:
        while not self._stop.is_set():
            self.peak_bytes = max(
                self.peak_bytes,
                self.process.memory_info().rss,
            )
            self._stop.wait(self.interval_seconds)

    def __enter__(self) -> "MemorySampler":
        self._thread.start()
        return self

    def __exit__(self, *_: object) -> None:
        self._stop.set()
        self._thread.join()
        self.peak_bytes = max(self.peak_bytes, self.process.memory_info().rss)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--results-json", type=Path, required=True)
    parser.add_argument("--results-csv", type=Path, required=True)
    parser.add_argument("--warmup-iterations", type=int, default=3)
    parser.add_argument("--measured-iterations", type=int, default=10)
    return parser.parse_args()


def detected_processor_name() -> str:
    if os.name == "nt":
        try:
            import winreg

            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"HARDWARE\DESCRIPTION\System\CentralProcessor\0",
            ) as processor_key:
                return str(
                    winreg.QueryValueEx(processor_key, "ProcessorNameString")[0]
                ).strip()
        except OSError:
            pass
    return (
        platform.processor()
        or os.environ.get("PROCESSOR_IDENTIFIER")
        or "unknown"
    )


def percentile(values: list[float], percentile_value: float) -> float:
    return float(np.percentile(np.asarray(values, dtype=np.float64), percentile_value))


def create_session(path: str, cpu_threads: int) -> tuple[ort.InferenceSession, float]:
    options = ort.SessionOptions()
    options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    options.intra_op_num_threads = cpu_threads
    options.inter_op_num_threads = 1
    started = time.perf_counter()
    session = ort.InferenceSession(
        path,
        sess_options=options,
        providers=["CPUExecutionProvider"],
    )
    return session, (time.perf_counter() - started) * 1000


def build_input(
    tokenizer: Any,
    texts: list[str],
    batch_size: int,
    sequence_length: int,
) -> dict[str, np.ndarray]:
    batch = [texts[index % len(texts)] for index in range(batch_size)]
    encoded = tokenizer(
        batch,
        padding="max_length",
        truncation=True,
        max_length=sequence_length,
        return_tensors="np",
    )
    return {
        "input_ids": encoded["input_ids"].astype(np.int64),
        "attention_mask": encoded["attention_mask"].astype(np.int64),
    }


def main() -> int:
    arguments = parse_arguments()
    if arguments.warmup_iterations < 2:
        raise ValueError("Use at least two warm-up iterations.")
    if arguments.measured_iterations < 5:
        raise ValueError("Use at least five measured iterations.")

    metadata = json.loads(arguments.metadata.read_text(encoding="utf-8"))
    cpu_threads = psutil.cpu_count(logical=False) or psutil.cpu_count(logical=True) or 1
    logical_cpu_threads = psutil.cpu_count(logical=True) or cpu_threads
    environment = {
        "processor": detected_processor_name(),
        "physical_cpu_cores": cpu_threads,
        "logical_cpu_threads": logical_cpu_threads,
        "onnxruntime_intra_op_threads": cpu_threads,
        "operating_system": platform.platform(),
        "python_version": platform.python_version(),
        "onnxruntime_version": ort.__version__,
        "onnxruntime_providers": ort.get_available_providers(),
        "warmup_iterations": arguments.warmup_iterations,
        "measured_iterations": arguments.measured_iterations,
    }
    benchmark: dict[str, Any] = {
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "environment": environment,
        "models": [],
    }
    flat_rows: list[dict[str, Any]] = []

    benchmark_texts = [
        "The stream is running smoothly.",
        "¿Puedes subir un poco el volumen?",
        "O áudio ainda está muito baixo.",
        "Звук снова пропал.",
        "Der Stream macht heute Spaß.",
        "Le son est revenu, merci.",
        "配信の音が少し小さいです。",
        "La diretta funziona bene.",
        "Dźwięk znowu się urywa.",
        "Yayın sesi yine kesiliyor.",
    ]

    for model_metadata in metadata["models"]:
        print(f"\nBenchmarking {model_metadata['model_id']}...", flush=True)
        tokenizer = AutoTokenizer.from_pretrained(
            model_metadata["snapshot_path"],
            local_files_only=True,
        )
        model_result: dict[str, Any] = {
            "model_id": model_metadata["model_id"],
            "revision": model_metadata["revision"],
            "original_startup_ms": model_metadata["original_startup_ms"],
            "runtimes": [],
        }

        for runtime_name, model_path_key in (
            ("onnx_fp32", "onnx_path"),
            ("onnx_int8", "int8_path"),
        ):
            with MemorySampler() as startup_memory:
                session, startup_ms = create_session(
                    model_metadata[model_path_key], cpu_threads
                )
            runtime_result: dict[str, Any] = {
                "runtime": runtime_name,
                "startup_ms": startup_ms,
                "startup_peak_process_ram_bytes": startup_memory.peak_bytes,
                "matrix": [],
            }

            for sequence_length in SEQUENCE_LENGTHS:
                for batch_size in BATCH_SIZES:
                    inputs = build_input(
                        tokenizer,
                        benchmark_texts,
                        batch_size,
                        sequence_length,
                    )
                    with MemorySampler() as inference_memory:
                        for _ in range(arguments.warmup_iterations):
                            warmup_output = session.run(
                                ["sentence_embedding"], inputs
                            )[0]
                        if not np.isfinite(warmup_output).all():
                            raise RuntimeError(
                                f"{runtime_name} warm-up produced NaN or infinity."
                            )

                        durations_ms: list[float] = []
                        for _ in range(arguments.measured_iterations):
                            started = time.perf_counter()
                            output = session.run(["sentence_embedding"], inputs)[0]
                            durations_ms.append(
                                (time.perf_counter() - started) * 1000
                            )
                            if output.shape != (
                                batch_size,
                                model_metadata["output_dimension"],
                            ):
                                raise RuntimeError(
                                    f"Unexpected output shape {output.shape}."
                                )
                            if not np.isfinite(output).all():
                                raise RuntimeError(
                                    f"{runtime_name} produced NaN or infinity."
                                )

                    average_ms = statistics.fmean(durations_ms)
                    row = {
                        "model_id": model_metadata["model_id"],
                        "revision": model_metadata["revision"],
                        "runtime": runtime_name,
                        "batch_size": batch_size,
                        "sequence_length": sequence_length,
                        "warm_inference_ms": durations_ms[0],
                        "average_inference_ms": average_ms,
                        "p50_inference_ms": percentile(durations_ms, 50),
                        "p95_inference_ms": percentile(durations_ms, 95),
                        "messages_per_second": batch_size / (average_ms / 1000),
                        "peak_process_ram_bytes": inference_memory.peak_bytes,
                        "cpu_thread_count": cpu_threads,
                        "warmup_iterations": arguments.warmup_iterations,
                        "measured_iterations": arguments.measured_iterations,
                    }
                    runtime_result["matrix"].append(row)
                    flat_rows.append(row)
                    print(
                        f"  {runtime_name} seq={sequence_length} batch={batch_size}: "
                        f"{average_ms:.2f} ms, {row['messages_per_second']:.2f} msg/s",
                        flush=True,
                    )

            runtime_result["peak_process_ram_bytes"] = max(
                row["peak_process_ram_bytes"] for row in runtime_result["matrix"]
            )
            model_result["runtimes"].append(runtime_result)
            del session

        benchmark["models"].append(model_result)

    arguments.results_json.parent.mkdir(parents=True, exist_ok=True)
    arguments.results_json.write_text(
        json.dumps(benchmark, indent=2), encoding="utf-8"
    )
    with arguments.results_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(flat_rows[0].keys()))
        writer.writeheader()
        writer.writerows(flat_rows)

    print(f"\nWrote {arguments.results_json}")
    print(f"Wrote {arguments.results_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
