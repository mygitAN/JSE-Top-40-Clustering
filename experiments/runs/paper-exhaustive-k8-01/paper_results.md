# EDA, experimentation, optimisation and longitudinal results

Run: `paper-exhaustive-k8-01`. 40 groups / 41 instruments per date; k=8 for hierarchical/K-Means.

The declared grid exhaustively tested **3,268 configurations × 5 seeds = 16,340 selection fits** on June 2025. These are finite-grid exploratory optima; later dates are descriptive refits with frozen settings.

## Read in order

1. `eda/`: populations, missingness, evidence, distributions and correlations.
2. `search/grid_manifest.json` and `candidate_configurations.csv`: exact parameter combinations and invalid Ward exclusions.
3. `search/selection_scores_all_seeds.csv`, `selection_seed_stability.csv`, `candidate_summary.csv`: every trial, invalid/noise result and seed variability.
4. `search/ranking_*.csv`, `pareto_*.csv`, `family_best_models.csv`, `best_parameters.csv`: both silhouette/DB objectives and nine family comparisons.
5. `selected_model_scores.csv`: frozen settings across dates; sector ARI/NMI are contextual only.
6. `models/<candidate>/<date>/`: actual hierarchical dendrograms, membership maps, feature profiles and available SHAP.
7. `models/<candidate>/`: stable/shifted instrument lists, entry/exit events, Jaccard/overlap sensitivity, screens, case reports and frozen-2025 shift attribution.

## Main model parameters

- **common_features_k8** (`c_073540362ecaaa17`): pca `{"n_components": 0.95, "svd_solver": "full"}` + hierarchical `{"linkage": "average", "metric": "euclidean", "n_clusters": 8}`.
- **embedding_k8** (`c_152cbd6e85993337`): umap `{"metric": "cosine", "min_dist": 0.01, "n_components": 2, "n_jobs": 1, "n_neighbors": 3}` + kmeans `{"n_clusters": 8, "n_init": 20}`.
- **baseline** (`c_4f80a40f7dda0468`): tsne `{"init": "random", "learning_rate": 10, "max_iter": 300, "metric": "euclidean", "n_components": 2, "n_jobs": 1, "perplexity": 5}` + hierarchical `{"linkage": "average", "metric": "manhattan", "n_clusters": 8}`.

## Representative scores (seed 42)

| Role | Date | Feature silhouette | Feature DB | Embedding silhouette | Embedding DB | Sector ARI |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| common_features_k8 | 2025-06-30 | 0.259 | 0.684 | 0.257 | 0.673 | 0.085 |
| common_features_k8 | 2025-12-31 | 0.368 | 0.703 | 0.403 | 0.585 | 0.220 |
| common_features_k8 | 2026-06-30 | 0.408 | 0.496 | 0.415 | 0.473 | 0.228 |
| embedding_k8 | 2025-06-30 | 0.129 | 1.278 | 0.829 | 0.218 | 0.236 |
| embedding_k8 | 2025-12-31 | 0.208 | 1.032 | 0.771 | 0.243 | 0.290 |
| embedding_k8 | 2026-06-30 | 0.228 | 1.128 | 0.748 | 0.309 | 0.292 |
| baseline | 2025-06-30 | 0.182 | 1.097 | 0.571 | 0.429 | 0.236 |
| baseline | 2025-12-31 | 0.177 | 1.014 | 0.598 | 0.447 | 0.248 |
| baseline | 2026-06-30 | 0.223 | 1.110 | 0.641 | 0.407 | 0.306 |

## Stability and candidate counts

- {"role": "baseline", "candidate_id": "c_4f80a40f7dda0468", "status": "completed descriptive review", "stable_all_three": 21, "shifted_all_three": 18, "membership_gaps": 4, "screen_candidates": 0, "multi_seed_supported_candidates": 0, "confirmed_outliers": 0, "sector_divergences": 40}.
- {"role": "common_features_k8", "candidate_id": "c_073540362ecaaa17", "status": "completed descriptive review", "stable_all_three": 29, "shifted_all_three": 10, "membership_gaps": 4, "screen_candidates": 5, "multi_seed_supported_candidates": 5, "confirmed_outliers": 0, "sector_divergences": 48}.
- {"role": "embedding_k8", "candidate_id": "c_152cbd6e85993337", "status": "completed descriptive review", "stable_all_three": 19, "shifted_all_three": 20, "membership_gaps": 4, "screen_candidates": 0, "multi_seed_supported_candidates": 0, "confirmed_outliers": 0, "sector_divergences": 37}.

## Interpretation boundaries

Primary selection jointly ranks silhouette and DB in the common June-scaled original financial features. The embedding criterion is reported separately because nonlinear layouts can exaggerate separation. The sum of ranks is an explicit trade-off rule, not evidence of a universal best model. Both metric champions and Pareto sets remain inspectable in the ranking files.

Individual D² uses the first two representation coordinates and same-date sample covariance. The p(n−1)/(n−p) F(0.95;p,n−p) cutoff is an illustrative paper-style reference, not an individual-distance significance test. An internal Beta reference and seed support are sensitivity descriptions. No confirmed outlier is claimed without substantive validation. Sector divergence and singletons are distinct flags.

Cluster SHAP explains each date’s surrogate. A separate regression surrogate describes attributes associated with the geometric distance. Its fidelity is reported separately. For temporal explanations, the same frozen 2025 classifier is evaluated at both feature vectors: contrast-SHAP differences sum to the margin-contrast change. They describe associations within that fixed function, not the causal mechanism of an independent refit.

All source-certification limitations remain; no baseline pointer is promoted.
