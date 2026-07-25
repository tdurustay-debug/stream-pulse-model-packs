# Pack Formats

## Model-bearing packs

Every future context-analysis, rule-interpreter, or speech-recognition release
package must be self-contained and include:

```text
manifest.json
model file or files
LICENSE
NOTICE
ATTRIBUTION.md
SOURCE.json
SHA256SUMS
```

`manifest.json` describes the packaged model, runtime requirements, supported
tasks, and version. `LICENSE`, `NOTICE`, and `ATTRIBUTION.md` preserve all legal
material required by the source model. `SHA256SUMS` records a SHA-256 checksum
for every distributed file.

## Source provenance

`SOURCE.json` must record:

- original model name
- original model owner
- original source URL
- exact revision or commit
- original download date
- original file names
- conversion or quantization method
- converter version
- conversion parameters

If no conversion was performed, record that fact explicitly rather than
omitting provenance. All values must reflect archived evidence; never infer or
invent them.

The release archive name and its internal `manifest.json` version must match
the repository manifest entry. Before publication, verify the archive from a
clean directory and compare every checksum.

## Language prompt/profile packs

A language profile is a small text or JSON configuration package. It must not
contain model weights, tokenizer weights, ONNX graphs, or another executable
model artifact. Each profile will eventually contain:

- analysis instructions
- Twitch terminology
- common slang examples
- sarcasm examples
- playful-insult examples
- technical-complaint examples
- output labels
- confidence thresholds

The profile package must have its own manifest metadata, checksum, version, and
download location before becoming `ready`. It is selected by language and used
with either context-analysis mode. Updating a language profile must not require
shipping a separately trained copy of the context analyzer.

## Separation rule

Context analyzer packages and language prompt/profile packages are independent
release assets. A context analyzer contains the model artifact but no
language-specific profile bundle. A language profile contains configuration
only and declares `containsModelWeights: false` in the repository manifest.
