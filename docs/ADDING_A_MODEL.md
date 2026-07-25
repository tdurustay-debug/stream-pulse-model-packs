# Adding a Model

Use this workflow for every model candidate:

1. Research the candidate model and its ownership.
2. Confirm license terms, commercial-use permission, and redistribution rights.
3. Archive the applicable license and exact source revision.
4. Benchmark language quality, task quality, and runtime performance.
5. Convert or quantize only when the license permits it.
6. Create the model pack in the documented package format.
7. Generate and independently verify SHA-256 checksums.
8. Store a local master copy and a separate external backup.
9. Upload the verified package to GitHub Releases.
10. Update the repository manifest with evidence-backed values.
11. Run `npm run validate`.
12. Test the official download and checksum verification path.
13. Commit and publish the manifest update.

Do not combine legal approval and technical evaluation into a single implicit
decision. Preserve the evidence for each review. Never add credentials,
temporary download tokens, or private storage URLs to this public repository.
