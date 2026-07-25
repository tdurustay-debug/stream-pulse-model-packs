# Stream Pulse AI Model Packs

This repository is the official archive and manifest source for Stream Pulse AI
model packs. It contains metadata, validation rules, licenses, attribution, and
release documentation. Production model files will be distributed as GitHub
Release assets after their legal and technical review is complete.

## Distribution principles

- The desktop application must never depend directly on an original model
  owner's download URL.
- A model owner removing, renaming, or changing a repository must not break the
  application.
- The application downloads only the selected context analyzer, language
  prompt/profile, rule-interpreter, and optional speech-recognition packs.
- The versioned manifest controls pack versions and official download
  locations.
- Every redistributed model must include its original license, notices, and
  attribution.
- Models must not be added until commercial-use and redistribution rights have
  been confirmed. Commercial use permission alone does not necessarily grant
  redistribution permission.
- Public release files and repository content must never contain private
  credentials or secrets.

No model binaries are stored in the repository. See
[`docs/ADDING_A_MODEL.md`](docs/ADDING_A_MODEL.md) for the review workflow and
[`docs/RELEASE_PROCESS.md`](docs/RELEASE_PROCESS.md) for the future release
process.

## Pack strategy

- Low System Mode will use a planned Qwen3-0.6B context analyzer.
- High Accuracy Mode will use a planned Qwen3-1.7B context analyzer.
- Each analyzer processes a short recent-message window and returns a strict
  JSON result.
- The ten supported languages use small text or JSON prompt/profile packages.
  They do not use ten separately trained full models, and language profiles
  must never contain model weights.
- One small shared multilingual rule-interpreter pack will translate
  natural-language rules into a strict machine-readable format. For example:
  “When at least five viewers complain about game audio within one minute, show
  an OBS alert.”
- Speech-recognition packs are optional downloads with small and balanced
  profiles.

The runtime flow is documented in
[`docs/ANALYSIS_ARCHITECTURE.md`](docs/ANALYSIS_ARCHITECTURE.md). Historical
MiniLM and DistilBERT performance work remains under `benchmarks/` as archived
research only; neither model was selected for production chat analysis and
neither may be packaged or released as the production analyzer.

## Manifest

The current machine-readable manifest is
[`manifest/v1/model-manifest.json`](manifest/v1/model-manifest.json), validated
against [`schemas/model-manifest.schema.json`](schemas/model-manifest.schema.json).
All entries are placeholders until a candidate model passes licensing,
evaluation, packaging, and backup requirements.

```bash
npm install
npm run validate
```

## Repository layout

- `manifest/` — versioned pack metadata used by the application
- `schemas/` — strict JSON Schema definitions
- `docs/` — packaging, licensing, evaluation, backup, and release procedures
- `licenses/` — archived third-party license material, organized by pack
- `packs/` — metadata-only pack staging guidance
- `scripts/` — manifest validation tooling
