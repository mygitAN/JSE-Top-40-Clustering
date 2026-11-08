# Review of the paper-experiments notebook

The notebook provides a useful research workflow: EDA before modelling, an auditable finite tuning grid, both quality scores, frozen all-date comparisons, actual dendrograms, membership-aware tracking and separate SHAP targets. These parts should be retained.

## Why the primary clusters are unsatisfactory

The common-feature joint-score winner is PCA95 with average-linkage Euclidean hierarchy. Its representative June-2025 partition contains one group of 28 instruments and four singletons; June 2026 contains a group of 23 and four singletons. These partitions can isolate extremes while giving limited resolution within a broad residual group. A score optimum is therefore not sufficient evidence of a useful peer-group partition. Singleton status is not itself a confirmed outlier.

The selection rule required valid scores, full coverage and k=8, but did not require multiple instruments per group. This explains why the winning partition passed the implemented criteria. The loss of OOF classifier fidelity in singleton solutions is already reported honestly. Stability of a broad aligned group should not be equated with stable detailed peer relationships.

The feature geometry also matters. By June 2026 the first PCA component has large revenue and share-count loadings, and GLN lies far outside the June-2025 feature ranges in those fields. In June 2025 the leading component instead combines volatility, dividend yield and beta more strongly. The saved loadings and singleton deviations support these descriptions; they do not establish causes. Share/capitalisation and sector evidence remain unresolved, and some raw accounting measures are not uniform across industries. This is a reason to audit feature definitions, not silently change the data.

## A review shortlist, not a promoted replacement

The saved June search contains 488 valid full-coverage eight-cluster configurations with no singleton on any of five seeds. For this post hoc review, the top three are ranked using the same common-feature silhouette/DB rule within that cohort. No sector labels select them and equal cluster sizes are not forced. Their June settings are frozen for later refits; later singletons or weak results remain in the report.

| Review candidate | Reduction parameters | Clustering parameters |
| --- | --- | --- |
| c_68a10edff9ce364e | tsne: `{"init": "random", "learning_rate": "auto", "max_iter": 1000, "metric": "euclidean", "n_components": 2, "n_jobs": 1, "perplexity": 5}` | `{"linkage": "average", "metric": "manhattan", "n_clusters": 8}` |
| c_7c1fdd70546e22c7 | tsne: `{"init": "random", "learning_rate": 10, "max_iter": 1000, "metric": "euclidean", "n_components": 2, "n_jobs": 1, "perplexity": 10}` | `{"linkage": "ward", "metric": "euclidean", "n_clusters": 8}` |
| c_b0aaecdaf4f71ae6 | tsne: `{"init": "random", "learning_rate": 10, "max_iter": 1000, "metric": "euclidean", "n_components": 2, "n_jobs": 1, "perplexity": 5}` | `{"linkage": "average", "metric": "manhattan", "n_clusters": 8}` |

| Model | Date | Feature silhouette (mean) | Feature DB (mean) | Mean seed ARI | Smallest group, any seed | Largest group, any seed | Maximum singletons |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| c_68a10edff9ce364e | 2025-06-30 | 0.189 | 1.132 | 0.828 | 2 | 9 | 0 |
| c_68a10edff9ce364e | 2025-12-31 | 0.181 | 1.090 | 0.849 | 1 | 7 | 1 |
| c_68a10edff9ce364e | 2026-06-30 | 0.212 | 1.095 | 0.934 | 1 | 10 | 1 |
| c_7c1fdd70546e22c7 | 2025-06-30 | 0.189 | 1.142 | 0.828 | 2 | 8 | 0 |
| c_7c1fdd70546e22c7 | 2025-12-31 | 0.197 | 1.038 | 0.943 | 2 | 7 | 0 |
| c_7c1fdd70546e22c7 | 2026-06-30 | 0.208 | 1.092 | 0.810 | 2 | 9 | 0 |
| c_b0aaecdaf4f71ae6 | 2025-06-30 | 0.188 | 1.132 | 0.887 | 2 | 8 | 0 |
| c_b0aaecdaf4f71ae6 | 2025-12-31 | 0.205 | 1.057 | 0.878 | 2 | 7 | 0 |
| c_b0aaecdaf4f71ae6 | 2026-06-30 | 0.223 | 1.110 | 1.000 | 2 | 9 | 0 |

## What to keep and what to reconsider

Keep the EDA, trial-level parameter records, both score geometries, seed diagnostics, actual trees, membership rules and qualified reporting. Reconsider the rule for recommending a primary peer-group model: distinguish suitability for peer description from geometric extremeness. Show size distributions and fidelity beside scores, rather than treating a high score as sufficient. Any new no-singleton selection rule is a recorded post hoc sensitivity for these data, not a recovered historic specification.

Do not force every cluster to reproduce a sector, ban genuine isolated observations by definition, or choose a model because its later memberships tell a preferred story. Sector composition should help interpret financial peers, and the geometric screen should remain separate from the partition. The original baseline and both score optima remain available. No model is promoted by this review.

Source: `paper-exhaustive-k8-01`. See `cluster_sizes_all_seeds.csv`, `shortlist_scores.csv`, `shortlist_seed_stability.csv`, `primary_pca_loadings.csv`, `singleton_feature_deviations.csv` and the per-date membership maps/dendrograms.

## Review conclusion

The notebook does not need rebuilding. Its EDA, finite tuning grid, score transparency, actual trees and membership-aware reporting form a useful foundation. The main issue is how the score winner is recommended for the peer-screening purpose. The selected PCA partition has a large catch-all group plus isolated instruments.

A useful comparison candidate is `c_b0aaecdaf4f71ae6`: 2D t-SNE, perplexity=5, learning_rate=10, max_iter=1000, random initialization, then average-linkage Manhattan hierarchical clustering, k=8. This keeps the original baseline settings except for increasing t-SNE optimization from 300 to 1000 iterations. In this review it has no singleton on any of the five seeds at any date, with cluster sizes ranging from 2 to at most 8/7/9 across the three dates. Its mean seed ARI is 0.887/0.878/1.000, which should be considered alongside its weaker common-feature scores than PCA.

The Ward/Euclidean alternative with perplexity=10 and 1000 iterations also has no singleton over all tested seeds/dates. The June-ranked first no-singleton candidate (automatic learning rate) develops singletons at later dates; it is retained in the comparison rather than removed after seeing follow-up outcomes. These observations support a shortlist review, not a claim of universal optimality or automatic promotion. No new SHAP explanations are claimed for these alternate partitions.

## Both score geometries for the original-method comparison candidate

These are means over five seeds. Embedding separation does not by itself validate financial peer structure.

| Date | Feature silhouette | Feature DB | Embedding silhouette | Embedding DB |
| --- | ---: | ---: | ---: | ---: |
| 2025-06-30 | 0.188 | 1.132 | 0.532 | 0.499 |
| 2025-12-31 | 0.205 | 1.057 | 0.589 | 0.493 |
| 2026-06-30 | 0.223 | 1.110 | 0.607 | 0.449 |
