# Multilingual Analysis Base-Model Benchmark

> **Research only — not selected for production chat analysis.**

This report is an archived research record. MiniLM and DistilBERT must not be
packaged or released as the production chat-analysis engine. The production
architecture has moved to planned Qwen3 context analyzers with separate
weight-free language prompt/profile packages.

Run completed on 2026-07-25 UTC (2026-07-26 Europe/Istanbul).

## Scope and interpretation

This report compares local CPU execution characteristics for two candidate
multilingual representation backbones. It is a technical smoke test and
performance benchmark, not a scientific classification-quality evaluation.
The test messages have no production ground-truth labels. Embedding similarity
or successful pooled-representation generation does not prove sentiment,
toxicity, conflict, spam, or question-detection quality.

Both candidates produced deterministic mean-pooled, L2-normalized
representations. Raw tensors were not compared between candidates because the
models have different architectures, dimensions, and intended uses.

## Immutable sources and licenses

| Candidate | Exact source revision | Repository license metadata | Archived license |
| --- | --- | --- | --- |
| `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | [`e8f8c211226b894fcb81acc59f3b34ba3efd5f42`](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2/tree/e8f8c211226b894fcb81acc59f3b34ba3efd5f42) | `apache-2.0`, confirmed in the [model card at the pinned revision](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2/blob/e8f8c211226b894fcb81acc59f3b34ba3efd5f42/README.md) | Official Apache 2.0 text |
| `distilbert/distilbert-base-multilingual-cased` | [`45c032ab32cc946ad88a166f7cb282f58c753c2e`](https://huggingface.co/distilbert/distilbert-base-multilingual-cased/tree/45c032ab32cc946ad88a166f7cb282f58c753c2e) | `apache-2.0`, confirmed in the [model card at the pinned revision](https://huggingface.co/distilbert/distilbert-base-multilingual-cased/blob/45c032ab32cc946ad88a166f7cb282f58c753c2e/README.md) | Official Apache 2.0 text |

The runner downloaded the official Apache 2.0 license text from
`https://www.apache.org/licenses/LICENSE-2.0.txt` into the gitignored local
archive `downloads/licenses/Apache-2.0.txt`. The archived file was 11,358 bytes
with SHA-256
`cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`.
The source model repositories do not include a standalone `LICENSE` file in
the pinned snapshots, so the repository model-card metadata and official
license text are recorded separately.

Neither candidate has been added to the production manifest.

## Architecture

| Candidate | Base architecture | Layers | Hidden size | Attention heads | Vocabulary | Output |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Multilingual MiniLM | `BertModel` | 12 | 384 | 12 | 250,037 | 384-dimensional pooled representation |
| Multilingual DistilBERT | `DistilBertForMaskedLM` configuration loaded through `AutoModel` | 6 | 768 | 12 | 119,547 | 768-dimensional pooled representation |

Both configurations support up to 512 positions. This benchmark tested only
sequence lengths 32, 64, and 128.

## Environment and method

- Processor: 12th Gen Intel Core i5-12400F (detected identifier:
  `Intel64 Family 6 Model 151 Stepping 5, GenuineIntel`)
- Physical cores / logical threads: 6 / 12
- ONNX Runtime intra-op threads: 6
- Operating system: Windows 11 Pro, reported as
  `Windows-11-10.0.26200-SP0`
- Python: 3.12.10
- ONNX Runtime: 1.22.0
- Execution provider: `CPUExecutionProvider`
- Warm-up iterations per cell: 3
- Measured iterations per cell: 10
- Matrix: sequence lengths 32, 64, 128 × batch sizes 1, 16, 64

Warm inference is the first measured call after three warm-ups. Average, p50,
and p95 are calculated from all ten measured calls after warm-up. Throughput is
batch size divided by average call duration. Peak RAM is peak process RSS
sampled during the relevant run and includes Python, ONNX Runtime, tokenizer
state, and allocator history.

## Execution and export checks

| Candidate | Original | FP32 ONNX | Dynamic INT8 ONNX | Output shape | Finite | Identical-input stability |
| --- | --- | --- | --- | --- | --- | --- |
| Multilingual MiniLM | Passed | Passed | Passed | `batch × 384` | Passed | Passed; max repeated-run difference `0.0` |
| Multilingual DistilBERT | Passed | Passed | Passed | `batch × 768` | Passed | Passed; max repeated-run difference `0.0` |

The maximum absolute difference from the original representation was
`1.23e-7` for MiniLM FP32 ONNX and `0.02633` for MiniLM INT8. It was
`1.19e-7` for DistilBERT FP32 ONNX and `0.04321` for DistilBERT INT8. These are
technical conversion checks, not semantic-quality scores.

## Artifact size, startup, and peak RAM

The original download size is the sum of the pinned inference snapshot used by
the scripts: weights, tokenizer/configuration files, pooling configuration
where applicable, and model card. It excludes unrelated upstream TensorFlow,
OpenVINO, and pre-existing ONNX variants.

| Candidate | Original download | FP32 ONNX | Dynamic INT8 ONNX | INT8 reduction from FP32 |
| --- | ---: | ---: | ---: | ---: |
| Multilingual MiniLM | 476.42 MiB | 448.50 MiB | 112.68 MiB | 74.9% |
| Multilingual DistilBERT | 519.52 MiB | 514.07 MiB | 128.85 MiB | 74.9% |

| Candidate | Runtime | Startup | Peak process RAM |
| --- | --- | ---: | ---: |
| Multilingual MiniLM | Original PyTorch model initialization | 903.77 ms | Not isolated |
| Multilingual MiniLM | FP32 ONNX session | 687.69 ms | 1,296.2 MiB |
| Multilingual MiniLM | INT8 ONNX session | 288.42 ms | 1,361.5 MiB |
| Multilingual DistilBERT | Original PyTorch model initialization | 92.54 ms | Not isolated |
| Multilingual DistilBERT | FP32 ONNX session | 597.26 ms | 1,438.2 MiB |
| Multilingual DistilBERT | INT8 ONNX session | 227.37 ms | 1,448.9 MiB |

Startup was measured as in-process model/session construction from local disk,
not a machine reboot or cleared operating-system filesystem cache. The
original-model timings are order-sensitive because MiniLM was initialized
first. Peak RSS is conservative and sequential-session allocator retention
means small differences should not be treated as isolated model memory.

## Throughput results

Times are milliseconds per inference call; RAM is peak process MiB.

### Multilingual MiniLM — FP32 ONNX

| Seq | Batch | Warm | Average | p50 | p95 | Messages/s | Peak RAM |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 32 | 1 | 7.88 | 8.36 | 8.39 | 8.91 | 119.58 | 1,107.8 |
| 32 | 16 | 83.46 | 76.54 | 77.73 | 81.65 | 209.04 | 1,110.1 |
| 32 | 64 | 303.77 | 304.74 | 306.03 | 324.29 | 210.02 | 1,146.2 |
| 64 | 1 | 12.78 | 12.21 | 12.52 | 12.82 | 81.93 | 1,146.2 |
| 64 | 16 | 205.87 | 172.28 | 168.37 | 199.76 | 92.87 | 1,146.2 |
| 64 | 64 | 693.29 | 684.35 | 682.49 | 717.72 | 93.52 | 1,182.2 |
| 128 | 1 | 18.83 | 21.39 | 21.09 | 23.86 | 46.75 | 1,182.2 |
| 128 | 16 | 336.33 | 337.24 | 338.98 | 345.36 | 47.44 | 1,182.2 |
| 128 | 64 | 1,773.16 | 1,724.89 | 1,708.60 | 1,819.05 | 37.10 | 1,296.2 |

### Multilingual MiniLM — dynamic INT8 ONNX

| Seq | Batch | Warm | Average | p50 | p95 | Messages/s | Peak RAM |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 32 | 1 | 38.89 | 8.26 | 4.64 | 24.46 | 121.03 | 1,361.5 |
| 32 | 16 | 34.58 | 33.20 | 33.53 | 36.62 | 481.87 | 718.8 |
| 32 | 64 | 188.75 | 167.97 | 165.98 | 184.47 | 381.02 | 753.5 |
| 64 | 1 | 9.00 | 9.43 | 8.74 | 12.22 | 106.02 | 753.5 |
| 64 | 16 | 79.20 | 76.02 | 75.15 | 81.63 | 210.46 | 753.5 |
| 64 | 64 | 363.47 | 369.87 | 369.85 | 379.23 | 173.03 | 806.0 |
| 128 | 1 | 12.24 | 12.10 | 12.08 | 12.91 | 82.65 | 806.0 |
| 128 | 16 | 187.02 | 188.41 | 188.43 | 192.33 | 84.92 | 806.0 |
| 128 | 64 | 923.64 | 928.89 | 929.59 | 937.93 | 68.90 | 927.5 |

### Multilingual DistilBERT — FP32 ONNX

| Seq | Batch | Warm | Average | p50 | p95 | Messages/s | Peak RAM |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 32 | 1 | 28.84 | 14.14 | 12.36 | 23.21 | 70.72 | 1,371.6 |
| 32 | 16 | 138.85 | 135.94 | 133.65 | 143.98 | 117.70 | 1,031.7 |
| 32 | 64 | 546.35 | 569.62 | 550.69 | 646.06 | 112.36 | 1,102.2 |
| 64 | 1 | 21.18 | 20.89 | 21.05 | 22.87 | 47.86 | 1,102.2 |
| 64 | 16 | 296.62 | 287.14 | 285.51 | 297.22 | 55.72 | 1,109.0 |
| 64 | 64 | 1,228.00 | 1,212.61 | 1,204.37 | 1,280.18 | 52.78 | 1,197.1 |
| 128 | 1 | 39.16 | 37.46 | 38.29 | 42.56 | 26.70 | 1,197.1 |
| 128 | 16 | 581.37 | 566.69 | 564.99 | 580.27 | 28.23 | 1,197.1 |
| 128 | 64 | 2,548.25 | 2,687.18 | 2,691.97 | 2,904.90 | 23.82 | 1,438.2 |

### Multilingual DistilBERT — dynamic INT8 ONNX

| Seq | Batch | Warm | Average | p50 | p95 | Messages/s | Peak RAM |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 32 | 1 | 57.53 | 10.91 | 5.01 | 35.83 | 91.67 | 1,448.9 |
| 32 | 16 | 64.05 | 63.00 | 63.85 | 69.92 | 253.98 | 527.8 |
| 32 | 64 | 239.29 | 245.41 | 245.26 | 256.98 | 260.79 | 601.3 |
| 64 | 1 | 8.50 | 11.34 | 10.38 | 16.60 | 88.19 | 601.3 |
| 64 | 16 | 175.98 | 120.40 | 114.61 | 151.60 | 132.89 | 601.3 |
| 64 | 64 | 509.69 | 517.47 | 516.94 | 524.86 | 123.68 | 705.4 |
| 128 | 1 | 28.28 | 20.37 | 19.27 | 25.68 | 49.10 | 705.4 |
| 128 | 16 | 250.18 | 244.56 | 246.24 | 251.62 | 65.42 | 705.4 |
| 128 | 64 | 1,193.55 | 1,175.69 | 1,173.25 | 1,191.14 | 54.44 | 914.6 |

## Per-language tokenization smoke test

Each language contains eight mild, safe examples covering neutral chat,
positive chat, a viewer question, disagreement, aggressive conflict, repeated
complaint, spam-like repetition, and a streamer mention. Counts below include
special tokens and are aggregated across those eight messages.

| Language | MiniLM total (min–max) | MiniLM unknown content | DistilBERT total (min–max) | DistilBERT unknown content | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| en-US | 100 (10–16) | 0 / 84 | 99 (9–16) | 0 / 83 | Passed |
| es-ES | 115 (10–17) | 0 / 99 | 117 (9–18) | 0 / 101 | Passed |
| pt-BR | 106 (9–19) | 0 / 90 | 113 (9–19) | 0 / 97 | Passed |
| ru-RU | 109 (11–18) | 0 / 93 | 138 (13–21) | 0 / 122 | Passed |
| de-DE | 117 (10–20) | 0 / 101 | 120 (9–19) | 0 / 104 | Passed |
| fr-FR | 127 (10–20) | 0 / 111 | 128 (9–20) | 0 / 112 | Passed |
| ja-JP | 111 (11–17) | 0 / 95 | 159 (13–26) | 0 / 143 | Passed |
| it-IT | 114 (10–20) | 0 / 98 | 117 (9–19) | 0 / 101 | Passed |
| pl-PL | 116 (11–20) | 0 / 100 | 152 (16–23) | 0 / 136 | Passed |
| tr-TR | 100 (8–15) | 0 / 84 | 135 (13–23) | 0 / 119 | Passed |

Both tokenizers produced nonempty valid sequences for every language. Japanese,
Turkish, Polish, and Russian were not reduced entirely to unknown tokens; in
this dataset neither tokenizer emitted any unknown content token.

## Export warnings and Windows-specific issues

- The initial Hugging Face large-file fallback established connections but did
  not progress reliably. Adding pinned `hf-xet==1.5.2` resolved the local
  download and remains part of the reproducible requirements.
- ONNX Runtime 1.22.0 failed to create its temporary `*-inferred.onnx` file
  while quantizing under the workspace path containing the non-ASCII character
  `ü`. The exporter now copies FP32 ONNX into an ASCII-only system temporary
  directory, quantizes there, verifies the result, and copies the INT8 file
  back to the gitignored output directory.
- PyTorch emitted a tracing warning for a constant created by attention-mask
  arithmetic during MiniLM export. Dynamic execution was subsequently verified
  at sequence lengths 32, 64, and 128 and all batch sizes in the matrix.
- ONNX Runtime recommended optional preprocessing before dynamic quantization.
  Both quantized graphs nevertheless passed ONNX checking, execution, output
  dimension, finite-value, and stability checks. Future packaging work should
  evaluate ONNX Runtime preprocessing as a separate controlled variant.
- The repository resides in OneDrive. Filesystem synchronization and caching
  may influence startup timing; repeat on target deployment hardware before a
  production decision.

## Historical performance conclusion

For this machine and implementation, Multilingual MiniLM is the
performance-oriented lead: its downloaded snapshot and ONNX artifacts are
smaller, and it was faster than Multilingual DistilBERT in every tested
FP32 and INT8 batch/sequence cell. Both candidates passed every supported
language smoke check, so neither is excluded on technical language coverage.
Peak-RSS differences are mixed and affected by sequential allocator retention,
so they do not justify a strong memory conclusion without isolated-process
reruns.

This performance result is superseded by the architecture decision. Neither
MiniLM nor DistilBERT is a production candidate, and neither belongs in the
production manifest. Future evaluation will instead test short-window
contextual JSON analysis with the selected Qwen modes and separately labeled,
representative evaluation data.
