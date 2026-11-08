# Requested execution: 8 November 2026

Full run: `user-full-20261108`. Reporting run: `user-orion-20261108`.
Both completed with checked manifests. Full-run runtime was approximately 21 seconds.

Executed commands:

```bash
python scripts/run_analysis.py --mode full --seed 42 --stability-runs 5 --experiment fixed-suite --purpose "User-requested full rerun with saved ORiON reporting" --run-id user-full-20261108
python scripts/checks.py
python scripts/orion_review.py --source-run user-full-20261108 --run-id user-orion-20261108
python scripts/compare_runs.py experiments/runs/final-full-42 experiments/runs/user-full-20261108 --report reports/user_rerun_reproducibility.json
python scripts/verify_run.py experiments/runs/user-orion-20261108
```

The active interpreter was the existing Windows Python 3.11.14 environment.
All 31 tests passed. All 89 deterministic full-suite artifacts matched the saved
baseline with the stated tolerances. The full suite includes 27 model comparisons,
30 pairwise seed comparisons, 27 k-sensitivity rows and three surrogate/SHAP analyses.
All 123 observations remain, with 41 instruments per date and 43 distinct tickers.

| Date | Embedding silhouette | Feature silhouette | Mean seed ARI | Surrogate OOF accuracy |
| --- | ---: | ---: | ---: | ---: |
| 2025-06-30 | 0.571 | 0.182 | 0.727 | 0.537 |
| 2025-12-31 | 0.598 | 0.177 | 0.920 | Not estimable: singleton |
| 2026-06-30 | 0.641 | 0.223 | 0.934 | 0.732 |

In-sample surrogate accuracy is 1.0 on all dates. Sector ARI is 0.236, 0.248 and
0.306. Complete precision, Davies–Bouldin, sector NMI and comparison-model scores
are in the saved `model_comparison.csv` and `reports/user_rerun_summary.csv`.
Feature-space separation is much weaker than embedding separation, and in-sample
surrogate fidelity exceeds the estimable OOF scores.

Continuing-member temporal ARI/NMI are 0.450/0.714 and 0.604/0.788, with 40
continuing instruments, one entry and one exit in each pair. Only 39 instruments
are observed at all three dates. The ORiON reporting run contains 240 cluster-feature
deviation/SHAP comparisons and both overlap/Jaccard alignment objectives.

For June 2026 the leading global surrogate SHAP features are shares outstanding,
beta, revenue, dividend yield and average trading volume. These explain surrogate
cluster membership associations, not investment returns or causal effects.

Plots: each date's `clusters.png`, `shap_global.png`, and eight cluster-level SHAP
plots are in the full run. Imputed observations carry an asterisk in cluster maps.
Maps are independently fitted and their coordinates do not share an axis system.

The baseline pointer is unchanged. No Hotelling cutoff or temporal outlier taxonomy
was invented; those specifications remain pending. Source-data PIT limitations
are unchanged. These results do not establish investment usefulness.
