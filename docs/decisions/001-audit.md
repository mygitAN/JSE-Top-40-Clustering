# Research decisions and implementation repairs

Date: 8 November 2026. Starting code: `59795b348a6ab447ca41219efb66ab4eddd93dce`.

## Fixed specification

The recovered historical settings remain MinMax, two-dimensional t-SNE,
perplexity 5, learning rate 10, 300 iterations, average/Manhattan hierarchical
clustering, k=8. The original executable notebook is unavailable. This is a
reconstruction, not an exact reproduction of historical results.

The existing implementation choices (random initialization, seed 42, UMAP,
DBSCAN standardization/parameters, K-Means n_init and XGBoost parameters) remain
unchanged. `configs/baseline.json` now drives the implementations. Seeds 42–46
and k=2–10 are descriptive sensitivity analyses. No settings were selected on
June 2026 or on sector agreement. No automatic promotion is permitted.

## Repairs, without a new model specification

- Re-derive medians from unflagged June 2025 rows. Derive clipping percentiles
  from the 40 resolved June earnings yields, before filling RNI. Using 41
  filled yields would change the bounds and does not match the supplied method.
- Reconcile the CSV's raw numeric fields, sector labels, missing volume and
  membership against all three workbook sheets and its Ticker Membership table.
  This verifies internal consistency, not the external truth of cited sources.
- Treat zero-overlap Hungarian pairs as unmatched, assigning fresh descriptive
  IDs. Align using continuing members only. Export mappings and raw labels.
- Flag both RNI fundamental imputations and the two AGL volume imputations in
  temporal interpretations. Entries and exits retain blank cluster-change flags.
- Use explicit class encoding for the surrogate, including nonconsecutive cluster
  labels. Export class mapping, original feature values and raw margins with SHAP.
- Label quality-score geometry explicitly: common Euclidean silhouette in each
  unstandardized embedding and June-scaled feature space; Euclidean centroid
  Davies–Bouldin in the embedding. Average linkage uses Manhattan distance.
  DBSCAN operates in standardized embedding coordinates. Quality scores are
  descriptive diagnostics, not the fitted linkage objective.
- Reserve immutable run directories before loading dependencies or validating
  input. Preserve failed status/logs; lock and atomically replace the registry.
  Never reuse a run ID. Check artifacts before writing a completion marker.

## Environment and execution

All eight top-level versions in requirements.txt were installed and executed on
Windows with CPython 3.11.14. The requested Python 3.12 download failed with a
gateway timeout. `configs/environment-windows-py311.txt` records the complete
installed dependency set. Linux/Python 3.12 and Windows/Python 3.11 CI jobs are
configured, but local success does not establish their remote success.

Windows sandbox ACLs blocked Python TemporaryDirectory fixtures, including
directories inside the workspace. Tests were run with normal temporary-file
access after preserving the failures during development. A genuine lock race
also occurred: Windows can return PermissionError during another owner's lock
close/unlink. Bounded retries and explicit closing of registry readers fixed it.
The tests exercise threads and independent processes.

## Open questions for the methodological reviewer

1. Are k=8 and the short 300-iteration t-SNE reconstruction adequate as the main
   descriptive specification? They remain fixed pending review.
2. Are the redundant size features (cap, shares, revenue) and native-unit skew
   defensible? Log transforms, alternative feature sets and imputation perturbations
   require separately specified sensitivity experiments before execution/promotion.
3. Is a surrogate OOF accuracy meaningful enough to report with very small groups?
   Singleton clusters make stratified OOF not estimable. Full-snapshot pseudo-label
   fidelity never validates unsupervised discovery or investment usefulness.
4. What external evidence can resolve RNI fundamentals, historical shares and
   sector classifications? No fresh-source certification was performed.
5. No documented Hotelling T² calibration was recovered. No anomaly threshold
   or classification rule has been invented.
6. Seed perturbations are not bootstrap uncertainty. A resampling unit, population
   treatment and uncertainty target would need a separate protocol.

No data, evidence flags, licence, repository visibility or historical source values
were changed. No analyst ratings were added. No economic usefulness or submission
readiness is claimed.
