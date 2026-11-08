# Joint silhouette and Davies-Bouldin optimisation

Completed run: `silhouette-db-search-01`. See `docs/decisions/003-silhouette-db-search.md` for the protocol.
Higher silhouette and lower DB are better. Values below average seeds 42–46.

## Selected configurations

- **baseline**: tsne {'n_components': 2, 'perplexity': 5, 'learning_rate': 10, 'max_iter': 300, 'init': 'random', 'n_jobs': 1}; hierarchical {'linkage': 'average', 'metric': 'manhattan', 'n_clusters': 8}.
- **paper_style_k8**: umap {'n_components': 2, 'n_neighbors': 5, 'min_dist': 0.0, 'n_jobs': 1}; hierarchical {'linkage': 'complete', 'metric': 'manhattan', 'n_clusters': 8}.
- **common_features_k8**: pca {'n_components': 0.95, 'svd_solver': 'full'}; hierarchical {'linkage': 'average', 'metric': 'euclidean', 'n_clusters': 8}.
- **common_features_free_k**: pca {'n_components': 0.95, 'svd_solver': 'full'}; hierarchical {'linkage': 'average', 'metric': 'euclidean', 'n_clusters': 2}.

## June 2025 joint selections and fixed baseline

| Scenario | Silhouette (embedding) | DB (embedding) | Silhouette (features) | DB (features) | Clusters |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.5501 | 0.5046 | 0.1664 | 1.1777 | 8 |
| paper_style_k8 | 0.6106 | 0.4772 | 0.1589 | 1.1988 | 8 |
| common_features_k8 | 0.2570 | 0.6726 | 0.2592 | 0.6840 | 8 |
| common_features_free_k | 0.3353 | 0.4890 | 0.3337 | 0.4921 | 2 |

## Frozen paper-style k=8 selection across dates

| Date | Silhouette (embedding) | DB (embedding) | Silhouette (features) | DB (features) |
| --- | ---: | ---: | ---: | ---: |
| 2025-06-30 | 0.6106 | 0.4772 | 0.1589 | 1.1988 |
| 2025-12-31 | 0.6732 | 0.4037 | 0.1815 | 1.0614 |
| 2026-06-30 | 0.6698 | 0.4265 | 0.2091 | 1.0902 |

## How to read this selection

The grid contains 1,426 configurations and 7,130 selection fits. Selection used June 2025 only. Later snapshots are descriptive refits of the chosen settings, not newly tuned configurations or untouched validation.

Both scores enter the declared equal-rank joint rule. Pareto frontiers and individual metric champions are retained, so a trade-off is visible rather than calling one score alone optimal.

The paper-style winner optimises scores in each representation. The common-feature winner checks whether the chosen labels separate in the same financial space. PCA95 may have more than two dimensions.

The source paper reports silhouette 0.5023 and DB 0.5296 on a different 2023–2024 sample and eleven features. The new scores cannot be called a controlled improvement on that old experiment.

Full coverage and valid scores on all five selection seeds are required for eligibility. DBSCAN noise and all rejected/degenerate configurations remain in the search tables. Sector agreement is report-only.

Raw `selection_seed_stability.csv` measures agreement of all assignment states, including the DBSCAN -1 sentinel. Use `optimization_dbscan_nonnoise_stability.csv` for ordinary DBSCAN cluster agreement conditional on firms non-noise in both seeds, with coverage explicitly shown. All eligible winners have full selection-date coverage, so noise cannot influence their ranking/tie-break.

The baseline pointer remains unpromoted. Source-evidence limitations remain; internal quality is not investment usefulness.
