# Three-cross-section study: results and reading order

Run ID: `three-cross-section-cli-check-01`. Each date retains 41 instruments; 123 records, 43 distinct tickers, 39 observed at all three dates. These are overlapping historical cross-sections.

## 1. Start with EDA

- `eda/population.csv`: population counts and flagged imputations.
- `eda/evidence.csv` and `eda/missingness.csv`: evidence/missing-case accounting.
- `eda/feature_distributions.png`: all ten model features, all three dates, June-scaled units.
- `eda/correlation_<date>.png`: correlations for each date, including model-only imputations.
- `eda/membership_presence.png`: observed membership rather than a balanced independent panel.

## 2. Compare models using both scores

Scores below use the representative seed fit. All nine baseline model families are in `model_comparison.csv`. DBSCAN noise/coverage remain explicit. DB and silhouette use Euclidean score geometry; the hierarchical fits use average/Manhattan linkage.

| Model | Date | Embedding silhouette | Embedding DB | Feature silhouette | Feature DB | Mean seed ARI |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 2025-06-30 | 0.571 | 0.429 | 0.182 | 1.097 | 0.806 |
| baseline | 2025-12-31 | 0.598 | 0.447 | 0.177 | 1.014 | 0.909 |
| baseline | 2026-06-30 | 0.641 | 0.407 | 0.223 | 1.110 | 1.000 |

The UMAP case is the frozen neighbors=3/min_dist=0.01/k=5 sensitivity from the earlier June exploration. Its settings are reused across dates and seeds. It is not silently promoted over the historical t-SNE k=8 baseline. No new search occurs on later dates.

## 3. Read cluster plots, profiles and SHAP together

`models/<date>/` contains the recovered baseline. `umap_sensitivity/<date>/` contains the additional candidate when enabled. Each has a cluster map/membership panel, dendrogram, median-deviation heatmap, global and per-cluster SHAP bars, and a SHAP distribution plot for the largest local class.

| Model | Date | In-sample fidelity | OOF fidelity | OOF status |
| --- | --- | ---: | ---: | --- |
| baseline | 2025-06-30 | 1.000 | 0.537 | estimated |
| baseline | 2025-12-31 | 1.000 | not estimable | not estimable: singleton cluster |
| baseline | 2026-06-30 | 1.000 | 0.732 | estimated |

SHAP describes a supervised surrogate of cluster membership, not the clustering algorithm, causality or investment returns. Dimensions, class mapping and raw-margin additivity are checked. Singleton explanations are descriptive only. OOF fidelity to full-snapshot pseudo-labels does not validate discovery.

## 4. Compare dates with membership-aware joins

`temporal_agreement.csv` contains continuing-member ARI/NMI. Each model folder contains aligned transition tables, entry/exit events and `transition_heatmaps.png`. Each adjacent pair has 40 continuing instruments, one entry and one exit. Entry/exit events have no ordinary cluster-change flag. RNI/AGL imputation sensitivity remains flagged. Cluster numbers and independently fitted map axes are not persistent economic identities/shared coordinates.

## Research boundary

Three cross-sections extend the single-window SACJ study, but repetition alone does not certify historical inputs or guarantee publication readiness. Archived shares/capitalisation, sector history and daily vendor-series evidence remain unresolved. Analyst recommendations are not invented. The ten-feature variant and historical baseline remain distinct from the original eleven-feature experiment. No Hotelling cutoff or temporal outlier taxonomy is invented in this workflow.
