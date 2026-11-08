The study now exposes the complete EDA-to-experimentation workflow for three
historical cross-sections: 40 company groups / 41 securities per date, including
both Investec DLC lines. The new guided notebook evaluates every valid combination
in a declared finite grid of reductions, metrics, linkages and clustering settings:
3,268 configurations over five seeds (16,340 fits). Both silhouette and
Davies-Bouldin, exact parameters, all trial outcomes, coverage, seed stability,
Pareto fronts and nine-family comparisons are retained. Hierarchical/K-Means fix
k=8; sector labels never tune the models.

June-selected settings are frozen for 270 follow-up fits across 18 distinct
models and three dates. Results include actual fitted-tree dendrograms,
Hungarian/Jaccard stable/shifted instrument lists, entry/exit events, alignment
sensitivity, descriptive 2D distance/F-reference screens, sector context,
cluster/distance surrogate SHAP and additive frozen-2025 attribute contrasts.
The common-feature optimum is PCA95 + average/Euclidean hierarchy; the embedding
optimum is UMAP(3, 0.01, cosine) + K-Means. These are criterion-dependent finite-grid
optima, not a universal best model. The PCA choice creates singletons and cannot
provide stratified OOF classifier fidelity; its latest distance-surrogate OOF R^2
is negative. These adverse results are displayed rather than omitted.

Validation: 60 passing tests; 1,186 checksum-verified run artifacts; complete
candidate/seed coverage and selection reproduction; all SHAP additivity checks;
fresh and read-only review notebooks each executed 14 code cells without errors.
The read-only review mode verifies the completed archive and changes no run or
registry files. The full experiment is an optional workflow_dispatch CI job;
normal CI retains the shorter end-to-end study. Check current remote CI separately.

Read [the full results and limitations](https://github.com/mygitAN/JSE-Top-40-Clustering/blob/research/reproducible-review/reports/paper_experiment_results.md)
and [the protocol](https://github.com/mygitAN/JSE-Top-40-Clustering/blob/research/reproducible-review/docs/paper_experiments_guide.md).
Geometric screens, seed agreement, sector divergence and SHAP do not confirm
outliers or establish causes. Historical shares/market cap, sector history and
vendor-series evidence remain unresolved. Later dates were previously examined
and are descriptive follow-ups. No baseline promotion or automatic merge.
