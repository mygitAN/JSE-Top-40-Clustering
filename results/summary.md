# Three-cross-section study

Run `20261115T062631-0c09819ce3c0`. Feature set **invariant8** (pilot-informed candidate): No feature changes under a share subdivision: five scale-free measures, log market cap, log revenue-to-cap and log share turnover.

123 instrument-date rows over 3 dates; scaling fitted on 2025-06-30 only; k=8; seeds 42-46. Each date is clustered independently. These are overlapping cross-sections of mostly the same firms, not independent samples, and nothing here is a return prediction.

## Feature validity (`feature_audit/`)

Largest single-feature share of scaled variance. A share far above the even share means one feature drives the geometry at that date.

| feature_set | decision_date | top_feature_label | top_variance_share | even_share | max_scaled_value |
| --- | --- | --- | --- | --- | --- |
| original10 | 2025-06-30 | Dividend yield | 0.159 | 0.100 | 1.000 |
| original10 | 2025-12-31 | 1Y return | 0.327 | 0.100 | 3.631 |
| original10 | 2026-06-30 | Revenue | 0.347 | 0.100 | 3.852 |
| logsize10 | 2025-06-30 | Dividend yield | 0.159 | 0.100 | 1.000 |
| logsize10 | 2025-12-31 | 1Y return | 0.467 | 0.100 | 2.847 |
| logsize10 | 2026-06-30 | Volatility | 0.182 | 0.100 | 1.311 |
| invariant8 | 2025-06-30 | Dividend yield | 0.198 | 0.125 | 1.000 |
| invariant8 | 2025-12-31 | 1Y return | 0.525 | 0.125 | 2.847 |
| invariant8 | 2026-06-30 | Volatility | 0.221 | 0.125 | 1.244 |
| market5 | 2025-06-30 | Dividend yield | 0.304 | 0.200 | 1.000 |
| market5 | 2025-12-31 | 1Y return | 0.676 | 0.200 | 2.847 |
| market5 | 2026-06-30 | Volatility | 0.335 | 0.200 | 1.244 |

Instruments observed at all dates, by whether their aligned cluster ever changed:

| feature_set | recipe | stable | shifted | membership gap |
| --- | --- | --- | --- | --- |
| original10 | umap | 20 | 19 | 4 |
| original10 | ward_features | 26 | 13 | 4 |
| logsize10 | umap | 16 | 23 | 4 |
| logsize10 | ward_features | 23 | 16 | 4 |
| invariant8 | umap | 19 | 20 | 4 |
| invariant8 | ward_features | 20 | 19 | 4 |
| market5 | umap | 14 | 25 | 4 |
| market5 | ward_features | 6 | 33 | 4 |

Silhouette and Davies-Bouldin are computed in each feature set's own space and cannot be compared across feature sets. See `feature_audit/quality.csv`, `cross_set_agreement.csv` and `share_basis.csv`.

## Model specification (`model_specification.csv`)

| step | setting | value | note |
| --- | --- | --- | --- |
| Model | description | UMAP to two dimensions, then agglomerative (hierarchical) clustering with average linkage and Manhattan distance into k=8 clusters |  |
| Inputs | feature set | invariant8 | pilot-informed candidate |
| Inputs | features | 1Y return, Beta, Volatility, Dividend yield, Earnings yield, Log market cap, Log revenue / cap, Log turnover |  |
| Inputs | instruments | 41 per date, 123 rows | all index members retained |
| Scaling | method | MinMaxScaler(clip=False) | fitted on 2025-06-30 only and applied unchanged to later dates |
| Dimensionality reduction | algorithm | umap.UMAP (umap-learn 0.5.12) |  |
| Dimensionality reduction | n_components | 2 |  |
| Dimensionality reduction | n_neighbors | 3 |  |
| Dimensionality reduction | min_dist | 0.01 |  |
| Dimensionality reduction | metric | euclidean |  |
| Dimensionality reduction | n_jobs | 1 |  |
| Dimensionality reduction | random_state | 42-46 | 5 seeds; 42 is the representative fit |
| Clustering | algorithm | sklearn.cluster.AgglomerativeClustering (scikit-learn 1.6.1) | hierarchical, bottom-up; fitted on the 2-D reduced coordinates |
| Clustering | n_clusters | 8 | reference specification from the original paper |
| Clustering | linkage | average |  |
| Clustering | metric | manhattan |  |
| Fitting | dates | 2025-06-30, 2025-12-31, 2026-06-30 | each date fitted independently with identical settings; nothing re-tuned on later dates |
| Evaluation | silhouette, Davies-Bouldin | Euclidean, in the 2-D embedding and in the scaled feature space |  |
| Evaluation | stability | pairwise adjusted Rand index between seeds |  |
| Evaluation | cluster count sensitivity | 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 |  |
| Explanation | surrogate | xgboost.XGBClassifier (xgboost 2.1.4) | n_estimators=150, max_depth=2, learning_rate=0.05, subsample=1, colsample_bytree=1, n_jobs=1, objective=multi:softprob, eval_metric=mlogloss |
| Explanation | SHAP | shap.TreeExplainer (shap 0.49.1) | explains the surrogate, not the clustering |
| Provenance | how the settings were chosen | n_neighbors=3 and min_dist=0.01 were set by the author in an exploratory June 2025 sweep (archived run fixed-umap-001-01). The earlier 36-combination June 2025 grid (user-umap-grid-01) preferred n_neighbors=3 with min_dist=0.1. Average linkage, Manhattan distance and k=8 follow the original paper. All were chosen after the data had been examined; none is pre-registered. |  |

## Primary model (`models/`)

| study_model | decision_date | smallest_cluster | largest_cluster | singleton_clusters | silhouette_features | davies_bouldin_features | silhouette_embedding | davies_bouldin_embedding | mean_seed_ari | in_sample_accuracy | oof_accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| umap | 2025-06-30 | 2 | 9 | 0 | 0.151 | 1.153 | 0.685 | 0.385 | 0.846 | 1.000 | 0.439 |
| umap | 2025-12-31 | 1 | 8 | 2 | 0.124 | 1.049 | 0.638 | 0.268 | 0.892 | 1.000 | n/a |
| umap | 2026-06-30 | 2 | 8 | 0 | 0.267 | 1.059 | 0.721 | 0.355 | 0.738 | 1.000 | 0.707 |

Surrogate fidelity is agreement with the cluster labels, not predictive validity. Out-of-fold fidelity is not estimable when a cluster has one member.

## Across dates (`longitudinal/`)

| study_model | before | after | continuing | entries | exits | ari | changed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| umap | 2025-06-30 | 2025-12-31 | 40 | 1 | 1 | 0.377 | 15 |
| umap | 2025-12-31 | 2026-06-30 | 40 | 1 | 1 | 0.590 | 11 |

A changed label is not yet evidence of a changed firm: compare `changed` with the seed agreement above, which is the only noise reference this run computes.

Feature-space distance screen (descriptive, alpha=0.05): APN 2025-06-30, BHG 2025-06-30, BTI 2025-06-30, SOL 2025-06-30, VAL 2025-06-30, AGL 2025-12-31, BHG 2025-12-31, BTI 2025-12-31, SOL 2025-12-31, SSW 2025-12-31, GLN 2026-06-30, PAN 2026-06-30, SOL 2026-06-30, SSW 2026-06-30.

## Known data limits

- Historical share counts, market capitalisation and sector labels are reconstructed, not verified point-in-time.
- Reinet fundamentals and two Anglo American volume observations are imputed with June 2025 medians.
- Investec line share counts split the combined count by fractions disclosed in June 2024 and June 2026; December 2025 uses their midpoint.
- Volume is JSE trading only, so turnover understates liquidity for companies whose main listing is abroad.
