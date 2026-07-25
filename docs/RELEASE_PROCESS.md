# Release Process

Model packs are published as GitHub Release assets, not committed as repository
blobs. Release names use the pack ID and semantic version, for example:

- `context-qwen3-0.6b-v1.0.0`
- `context-qwen3-1.7b-v1.0.0`
- `prompt-en-US-v1.0.0`
- `prompt-tr-TR-v1.0.0`
- `prompt-ja-JP-v1.0.0`
- `rules-multilingual-v1.0.0`
- `speech-small-v1.0.0`
- `speech-balanced-v1.0.0`

## Procedure

1. Confirm licensing approval and a passed evaluation.
2. Build the package from the archived, exact source revision.
3. Verify package contents against `MODEL_PACK_FORMAT.md`.
4. Generate checksums and verify them from a clean extraction.
5. Confirm the local master and external backup copies.
6. Create the GitHub Release and upload the package.
7. Test the public asset download without credentials.
8. Update the manifest with the immutable release URL, size, checksum, and
   backup locations.
9. Run `npm run validate`.
10. Test application download and verification behavior before publishing the
    manifest change.

Never reuse a version for different bytes. If an asset changes, publish a new
semantic version. Release notes must identify the source revision, conversion
method, license, evaluation record, and checksum. Do not publish secrets,
private credentials, or expiring authenticated URLs.

This document defines a future process; it does not authorize or create a
release.

MiniLM and DistilBERT benchmark artifacts are archived research and must not be
packaged or released as production chat-analysis packs.
