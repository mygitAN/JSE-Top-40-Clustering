# Three-cross-section study: results and reading order

Run ID: `three-cross-section-population-clarified-01`. Each date retains 41 instruments representing 40 company groups; 123 records, 43 distinct tickers, 39 observed at all three dates. These are overlapping historical cross-sections.

Investec Limited (INL) and Investec plc (INP) are distinct securities in one dual-listed company (DLC) group. Both remain separate rows in this instrument-level analysis. Membership is determined independently at each date; an exited instrument is absent until its re-entry takes effect. Group counts do not imply independent observations.

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
| baseline | 2025-06-30 | 0.571 | 0.429 | 0.182 | 1.097 | 0.727 |
| baseline | 2025-12-31 | 0.598 | 0.447 | 0.177 | 1.014 | 0.920 |
| baseline | 2026-06-30 | 0.641 | 0.407 | 0.223 | 1.110 | 0.934 |
| umap_sensitivity | 2025-06-30 | 0.746 | 0.300 | 0.209 | 1.110 | 0.814 |
| umap_sensitivity | 2025-12-31 | 0.733 | 0.346 | 0.202 | 1.033 | 0.911 |
| umap_sensitivity | 2026-06-30 | 0.700 | 0.371 | 0.201 | 1.228 | 0.764 |

The UMAP case uses frozen neighbors=3/min_dist=0.01 and k=8 fixed by the original sector-count design. Other k values are diagnostics only. Its settings are reused across dates and seeds. It is not silently promoted over the historical t-SNE k=8 baseline. No new search occurs on later dates.

## 3. Read cluster plots, profiles and SHAP together

`models/<date>/` contains the recovered baseline. `umap_sensitivity/<date>/` contains the additional candidate when enabled. Each has a cluster map/membership panel, dendrogram, median-deviation heatmap, global and per-cluster SHAP bars, and a SHAP distribution plot for the largest local class.

| Model | Date | In-sample fidelity | OOF fidelity | OOF status |
| --- | --- | ---: | ---: | --- |
| baseline | 2025-06-30 | 1.000 | 0.537 | estimated |
| baseline | 2025-12-31 | 1.000 | not estimable | not estimable: singleton cluster |
| baseline | 2026-06-30 | 1.000 | 0.732 | estimated |
| umap_sensitivity | 2025-06-30 | 1.000 | 0.610 | estimated |
| umap_sensitivity | 2025-12-31 | 1.000 | 0.634 | estimated |
| umap_sensitivity | 2026-06-30 | 1.000 | 0.707 | estimated |

SHAP describes a supervised surrogate of cluster membership, not the clustering algorithm, causality or investment returns. Dimensions, class mapping and raw-margin additivity are checked. Singleton explanations are descriptive only. OOF fidelity to full-snapshot pseudo-labels does not validate discovery.

## 4. Compare dates with membership-aware joins

`temporal_agreement.csv` contains continuing-member ARI/NMI. Each model folder contains aligned transition tables, entry/exit events and `transition_heatmaps.png`. Each adjacent pair has 40 continuing instruments, one entry and one exit. Entry/exit events have no ordinary cluster-change flag. RNI/AGL imputation sensitivity remains flagged. Cluster numbers and independently fitted map axes are not persistent economic identities/shared coordinates.

## Research boundary

Three cross-sections extend the single-window SACJ study, but repetition alone does not certify historical inputs or guarantee publication readiness. Archived shares/capitalisation, sector history and daily vendor-series evidence remain unresolved. Analyst recommendations are not invented. The ten-feature variant and historical baseline remain distinct from the original eleven-feature experiment. No Hotelling cutoff or temporal outlier taxonomy is invented in this workflow.
