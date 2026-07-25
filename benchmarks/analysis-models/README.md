# Analysis Base-Model CPU Benchmark

> **Research only — not selected for production chat analysis.**

MiniLM and DistilBERT are retained here only to preserve the completed research
record. Do not package or release either candidate as the production
chat-analysis engine. The production architecture now uses planned Qwen3
context analyzers with separate weight-free language prompt/profile packages.

This local benchmark compares two candidate multilingual representation models:

- `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- `distilbert/distilbert-base-multilingual-cased`

The benchmark pins immutable Hugging Face revisions, exports deterministic
mean-pooled representations to ONNX, attempts dynamic INT8 quantization, checks
all ten supported writing systems, and measures ONNX Runtime CPU performance.

This is a technical smoke test and performance benchmark. It does not measure
sentiment, toxicity, conflict, spam, or other production classification
quality. Those claims require task-specific fine-tuning and a separately
labeled evaluation dataset.

## Local-only artifacts

Model snapshots, license downloads, ONNX files, and raw JSON/CSV results are
stored in gitignored directories:

- `.cache/`
- `downloads/`
- `generated/`
- `results/*.json`
- `results/*.csv`
- `results/*.onnx`

Only the scripts, transparent smoke-test dataset, final Markdown report, and
empty results-directory marker belong in Git.

## Run

From the repository root:

```powershell
pwsh -File scripts/run-analysis-benchmark.ps1
```

The runner creates `.venv` when needed, installs pinned dependencies, downloads
the two pinned model snapshots, archives the Apache 2.0 license text locally,
exports and quantizes both candidates, verifies outputs, and runs the full
matrix:

- sequence lengths: 32, 64, 128
- batch sizes: 1, 16, 64
- runtimes: FP32 ONNX and dynamic INT8 ONNX

The default uses three warm-up iterations and ten measured iterations for each
matrix cell. Override these only for troubleshooting:

```powershell
pwsh -File scripts/run-analysis-benchmark.ps1 -WarmupIterations 3 -MeasuredIterations 10
```

Raw results are local evidence. The checked-in
[`BENCHMARK_REPORT.md`](BENCHMARK_REPORT.md) summarizes the completed run and
records its environment and limitations.
