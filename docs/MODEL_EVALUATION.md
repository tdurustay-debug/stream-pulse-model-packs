# Model Evaluation

Model selection is evidence-driven. Each context-analysis candidate must be
tested with short multi-message windows for:

- language quality
- Twitch-style informal text
- slang
- emojis
- mixed-language messages
- conflict detection
- question detection
- toxicity detection
- spam detection
- false-positive rate
- CPU performance
- RAM usage
- startup time
- batch processing speed
- strict JSON conformance
- probability range conformance
- deterministic-statistics integration
- prompt-injection resistance
- context-window truncation behavior

Use representative, rights-cleared datasets and document dataset versions,
hardware, runtime versions, test parameters, metrics, and known limitations.
Compare candidates under the same conditions. Include adversarial and ambiguous
messages, and review errors with fluent speakers of the target language.

Low System Mode and High Accuracy Mode require separate CPU, RAM, startup,
latency, and quality measurements. Qwen3-0.6B and Qwen3-1.7B are architectural
choices only at this stage: no source revision or distributable artifact is
approved until licensing, source pinning, conversion, and evaluation are
complete.

## Language profile evaluation

Each weight-free language prompt/profile must be reviewed by fluent speakers
and tested with both context analyzers. Evaluation must cover its analysis
instructions, Twitch terminology, common slang, sarcasm, playful insults,
technical complaints, output labels, and confidence thresholds. A profile
fails if it causes invalid JSON, unsupported labels, out-of-range
probabilities, or material regressions in another supported task.

The ten profiles are configuration packages, not ten independently trained
models. Model quality and profile quality must be reported separately.

Evaluation progresses from `not_started` to `testing`, then to `passed` or
`failed`. No pack may receive status `ready` unless `evaluationStatus` is
`passed` and `evaluationNotes` contains a meaningful summary. A failed model
remains unavailable unless a new version is evaluated from the beginning.

Speech-recognition and rule-interpreter packs require task-specific test plans
in addition to applicable performance, memory, startup, and error-rate checks.

The archived MiniLM and DistilBERT benchmark is research only and does not
qualify either model for production chat analysis. Its embedding and runtime
checks are not substitutes for context-analysis evaluation.
