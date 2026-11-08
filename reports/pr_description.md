The previous pipeline lacked durable run provenance and had gaps in preprocessing
derivation checks, temporal alignment and surrogate exports. This preserves the
documented baseline, reconciles all 123 observations to the supplied workbook,
adds immutable local tracking, and expands verification to 25 passing tests.

Complete suites `final-full-42` and `repeat-full-42` include all three dates,
nine model combinations per date, five seeds, k=2–10 and SHAP. All 89 deterministic
artifacts compared successfully. Complete bundles and checksums are stored in Git.
The results pointer remains unpromoted.
An additional all-date baseline/SHAP run verifies final completion-marker I/O
failure recovery. Both configured CI platforms passed for the results commit.

Common-feature silhouettes are 0.182/0.177/0.223; mean seed ARI is 0.727/0.920/0.934.
Surrogate OOF accuracy is 0.537/not estimable (singleton)/0.732 despite perfect
in-sample accuracy. These results do not establish economic usefulness.

See [the reviewer guide](https://github.com/mygitAN/JSE-Top-40-Clustering/blob/research/reproducible-review/reports/reviewer_guide.md).
Validation: `python scripts/checks.py`, complete end-to-end suites, artifact
verification and repeated numerical comparison. Executed on Windows CPython
3.11.14 with all pinned top-level dependencies. Check remote CI separately.
Review questions include k=8, short t-SNE optimization, correlated size inputs,
imputation sensitivity and unverified historical shares/sectors. No data values,
licence or visibility changed. Do not merge automatically.
