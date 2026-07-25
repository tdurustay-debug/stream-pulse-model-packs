# Model Pack Staging

This directory is reserved for metadata-only staging and documentation of
future model packs. Model binaries and release archives must not be committed
to Git.

Completed production packages will follow
[`docs/MODEL_PACK_FORMAT.md`](../docs/MODEL_PACK_FORMAT.md), be verified, and
then be uploaded as GitHub Release assets. The application will discover those
assets only through the versioned manifest.

Language prompt/profile packages are small text or JSON configuration assets.
They are staged and released separately from context analyzers and must never
contain model weights. MiniLM and DistilBERT benchmark artifacts are research
only and are not eligible production packages.
