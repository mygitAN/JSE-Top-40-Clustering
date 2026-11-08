The revised study now has a guided notebook and equivalent one-command workflow:
validation and EDA, modelling, plots, SHAP, seed stability and temporal comparisons
for three cross-sections of 41 instruments each. Hierarchical and K-Means models
fix k=8 as requested; sector labels are contextual comparators. Both silhouette
and Davies?Bouldin are reported in embedding and original scaled feature spaces.
DBSCAN retains its naturally found cluster/noise count.

The executed notebook completed all 11 code cells without errors in run
`three-cross-section-k8-01`. Its 289 artifacts pass checksum verification, and
baseline saved arrays reproduce `final-full-42` at every date. All 49 tests pass.
The notebook extras have a separate requirements file and Windows environment
snapshot. Both entry points share the same staged implementation.

Three overlapping populations do not constitute 123 independent firms. SHAP
explains surrogate associations with cluster membership; perfect in-sample
fidelity does not imply out-of-sample fidelity. Historical shares, market cap,
sector history and daily-source evidence still block submission-grade empirical
claims. No baseline promotion or automatic merge. New remote CI must be assessed
separately from earlier recorded CI evidence.

Earlier work and exploratory searches remain archived below.

The previous pipeline lacked durable run provenance and had gaps in preprocessing
derivation checks, temporal alignment and surrogate exports. This preserves the
documented baseline, reconciles all 123 observations to the supplied workbook,
adds immutable local tracking, and originally expanded verification to 42 passing tests.

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

The ORiON follow-up adds an evidence matrix, ten-feature variant/units/missingness
definitions and explicit claim boundaries. Separately tracked `orion-report-01`
compares univariate median deviations with SHAP and maximum-Jaccard with
maximum-overlap alignment. Aggregate transition counts agree, but the objectives
disagree for AGL, MTN, NPN and SOL in the second date pair. Only 39 instruments
are observed at all three dates. The Hotelling F-reference screen, temporal flag
taxonomy and alternative P/E sensitivity remain pending explicit specifications.
Archived share/capitalization, sector-history and market-source evidence remains
the submission-grade empirical blocker.

The supplied SACJ paper has now been reviewed, including its nine-combination
silhouette/DB table. A separately archived bounded search evaluates 1,426
configurations over five June-2025 seeds (7,130 fits) and freezes the joint-score
choices for later descriptive refits. UMAP/complete-Manhattan wins the declared
eight-cluster embedding-score compromise; PCA95/average-Euclidean wins the
common-feature criterion but creates singleton groups. Both silhouette and DB,
individual metric champions, Pareto trade-offs, coverage and seed stability are
reported. These are new-data exploratory optima within the declared grid, not
an exact reproduction or automatic replacement of the original paper results.

The user's UMAP snippet is also repaired and executed as `user-umap-grid-01`:
36 supplied combinations, followed by k=2–15 on the winning embedding. It prints
separate silhouette/DB champions, the joint winner and exact parameters, and
offers a verified print-only command for saved runs. Score curves and a matching
average/Manhattan dendrogram are archived. The seed-42 four-cluster result is
explicitly an exploratory sensitivity and does not replace the baseline.

The subsequent fixed UMAP request (neighbors=3, min_dist=0.01, k=2–12) is archived
as `fixed-umap-001-01`, with every k printed and a dual-axis silhouette/DB plot.
The silhouette winner is k=5 and DB winner k=2; the declared joint rule selects
k=5. The implementation no longer depends on undefined location-specific globals.
