# Backup Policy

Every production model pack requires:

1. A GitHub Release copy.
2. A local master copy.
3. A separate external-drive or cloud backup.
4. The archived original license.
5. Archived attribution and notice files.
6. The archived exact source revision.
7. A recorded SHA-256 checksum.
8. A periodic restoration test.

At least two backup locations must be recorded before a pack can be marked
`ready`. Backup records must identify stable locations without exposing
credentials. The GitHub Release alone is not a sufficient backup.

Restoration tests must fetch or restore each stored copy, verify SHA-256
checksums, inspect required legal files, and record the result and date.
Failures require replacement of the affected copy and another restoration
test.
