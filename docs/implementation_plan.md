# Implementation plan

Starting commit: `59795b348a6ab447ca41219efb66ab4eddd93dce` (clean `main`).
Working branch: `research/reproducible-review`.
No AGENTS.md was found in the repository or checked parent directories.

1. Audit supplied code, CSV, method constants and workbook evidence without refreshing data.
2. Strengthen input derivation checks, temporal alignment, score geometry and surrogate exports.
3. Add local immutable run tracking, locked registry, checksums and explicit promotion pointer.
4. Test edge cases and run the complete fixed suite twice with numerical reproduction checks.
5. Store compact results and complete bundles in Git when small enough; prepare a reviewer guide,
   commit the work and open a draft PR if remote access permits. Never merge automatically.

The ten baseline features and recovered historical settings remain fixed. Implementation
repairs are recorded separately from open methodological extensions. No broad tuning search.
