# Model Pack Staging

This directory is reserved for metadata-only staging and documentation of
future model packs. Model binaries and release archives must not be committed
to Git.

Completed production packages will follow
[`docs/MODEL_PACK_FORMAT.md`](../docs/MODEL_PACK_FORMAT.md), be verified, and
then be uploaded as GitHub Release assets. The application will discover those
assets only through the versioned manifest.
