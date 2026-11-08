# Fixed UMAP: 3 neighbors, min_dist=0.01

Completed run: `fixed-umap-001-01`. This uses the exact fixed settings supplied
in the latest snippet, rather than the previous grid winner's min_dist=0.1.

Run again:

```bash
python scripts/tune_umap.py --config configs/umap_fixed_001.json
```

Print all eleven saved scores and the selected parameters without refitting:

```bash
python scripts/tune_umap.py --print-run fixed-umap-001-01
```

UMAP uses n_neighbors=3, min_dist=0.01, n_components=2, Euclidean metric,
random_state=42 and n_jobs=1. Clustering uses average linkage and Manhattan
distance. Scores below are Euclidean embedding silhouette and centroid DB.
The embedding is fitted once for the June selection-date sweep.

| k | Silhouette (higher better) | Davies-Bouldin (lower better) |
| ---: | ---: | ---: |
| 2 | 0.736660 | 0.230306 |
| 3 | 0.625620 | 0.525421 |
| 4 | 0.702255 | 0.374575 |
| 5 | 0.801904 | 0.243014 |
| 6 | 0.774926 | 0.263568 |
| 7 | 0.735458 | 0.310729 |
| 8 | 0.746497 | 0.299780 |
| 9 | 0.719274 | 0.353403 |
| 10 | 0.649326 | 0.427369 |
| 11 | 0.616925 | 0.389870 |
| 12 | 0.630455 | 0.388706 |

The highest silhouette is at k=5; the lowest DB is at k=2. The previously
documented joint rank rule selects k=5. Neither metric's winner is hidden.

The requested dual-axis `cluster_count_scores.png` uses blue silhouette and
red DB, an integer k axis, combined legend and a marked joint choice.
`umap_embedding.csv` carries UMAP_1/UMAP_2, ticker, company, legacy sector,
imputation flags and selected cluster, replacing the snippet's undefined
`df_v1`/`location_name` dependency. Seaborn is not needed for this plot.

The corrected implementation is `scripts/tune_umap.py`; notebook callers may
use `sweep_fixed_umap(scaled_data, config)` and `print_results(result)` after
loading `configs/umap_fixed_001.json`. The saved run also contains all-date
assignments, frozen follow-up scores, a matching dendrogram, arrays, logs,
source/configuration snapshot and checksums. Saved-run printing was executed
successfully. All 42 unit tests pass locally.

These are single-seed exploratory scores. The common-feature scores for the
chosen k=5 in June are silhouette 0.220294 and DB 1.201766. Later dates refit
the frozen selected parameters descriptively; no baseline promotion, source
refresh or certification change is implied.
