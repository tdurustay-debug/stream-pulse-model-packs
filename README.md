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
- The application downloads only the language, rule-interpreter, and optional
  speech-recognition packs selected or enabled by the user.
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

- Each supported language has a separate lightweight real-time analysis pack.
- One small shared multilingual rule-interpreter pack will translate
  natural-language rules into a strict machine-readable format. For example:
  “When at least five viewers complain about game audio within one minute, show
  an OBS alert.”
- Speech-recognition packs are optional downloads with small and balanced
  profiles.

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
