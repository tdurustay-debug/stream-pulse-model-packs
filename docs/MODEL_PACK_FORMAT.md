# Model Pack Format

Every future release package must be self-contained and include:

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
