# Model Evaluation

Model selection is evidence-driven. Each language-analysis candidate must be
tested for:

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

Use representative, rights-cleared datasets and document dataset versions,
hardware, runtime versions, test parameters, metrics, and known limitations.
Compare candidates under the same conditions. Include adversarial and ambiguous
messages, and review errors with fluent speakers of the target language.

Evaluation progresses from `not_started` to `testing`, then to `passed` or
`failed`. No pack may receive status `ready` unless `evaluationStatus` is
`passed` and `evaluationNotes` contains a meaningful summary. A failed model
remains unavailable unless a new version is evaluated from the beginning.

Speech-recognition and rule-interpreter packs require task-specific test plans
in addition to applicable performance, memory, startup, and error-rate checks.
