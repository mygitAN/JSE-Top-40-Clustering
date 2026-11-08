The latest review preserves the notebook's EDA, explicit tuning trail and
results reporting while examining the suitability of the recommended clusters.
The PCA score winner has one large residual group plus multiple singletons.
An explicitly post hoc, June-only shortlist ranks eight-cluster candidates with
no singleton on any June seed, then freezes the top three for 45 follow-up fits.
Two alternatives avoid singletons across all tested dates/seeds, including the
original average-Manhattan t-SNE method with 1000 rather than 300 iterations.
Scores, group sizes, feature profiles, memberships and actual trees are reported;
later failures remain visible. No primary model or old notebook is replaced.
All 66 tests pass; the review's 112 artifacts are checksum verified. See
[the review](https://github.com/mygitAN/JSE-Top-40-Clustering/blob/research/reproducible-review/reports/notebook_cluster_review.md).

The single-cross-section study could describe unusual peer relationships but
could not distinguish their temporal histories. This revision adds a repeated,
interpretable screening workflow at three decision dates, with 40 company groups
represented by 41 securities per date. Cluster shifts, geometric screen flags,
sector divergence and agreement between signals remain separate descriptions.

The reporting example now follows structural-signal dynamics: emerging,
emerging and sustained, persistent, resolving, resolved, transient and recurring
histories. The taxonomy refinement is recorded as a reporting amendment after
the initial results were examined. Missing membership or an unestimable sector
comparison is not treated as a normal observation. K=8 stays primary; a separate
495-fit sensitivity selects k=2..12 at each date while freezing other settings.
For the primary PCA/hierarchy it selects k=2 at all dates, with a singleton:
higher scores alone do not establish useful peer structure.

The underlying experiment evaluates 3,268 configurations over five seeds (16,340
selection fits), then 270 frozen follow-up fits across 18 models. It retains both
silhouette/DB geometries, all parameters and trial outcomes, seed variability,
actual dendrograms, Hungarian/Jaccard memberships, named stable/shifted lists,
and separate cluster, distance and frozen-2025 contrast SHAP targets. The working
report asks what financial-profile changes accompany changing peer relationships,
without presenting surrogate associations as causes or confirming outliers.

Validation: 64 passing tests; 1,186 verified original experiment artifacts plus
53 verified reporting-amendment artifacts; original and saved-review notebooks
executed successfully; exact k=8 source partitions reproduced in the sensitivity.
The primary outputs and baseline pointer remain unchanged. Remote CI is assessed
separately. Read [the reporting example](https://github.com/mygitAN/JSE-Top-40-Clustering/blob/research/reproducible-review/reports/anomaly_dynamics_reporting_example.md)
and [the protocol](https://github.com/mygitAN/JSE-Top-40-Clustering/blob/research/reproducible-review/docs/reporting_direction.md).

These are overlapping cross-sections, not an independently enlarged sample.
The ten-feature variant differs from the original eleven-feature experiment.
Historical source certification and substantive outlier corroboration remain
unresolved. Singleton groups and weak surrogate OOF fidelity are reported.
This is a working reporting example, not an updated submission-ready manuscript.
No baseline promotion or automatic merge.
