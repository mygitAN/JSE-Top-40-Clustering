# Full experiment: results and interpretation

[Open the executed review notebook](paper_experiments_executed.ipynb), [fresh execution record](paper_experiments_fresh_executed.ipynb), or [full protocol](../docs/paper_experiments_guide.md).

## Optimisation evidence

Run `paper-exhaustive-k8-01` completed all **3,268 configurations x five seeds = 16,340 selection fits**. It reused 430 fitted representations across clustering settings. All 86 reduction configurations were evaluated. Three invalid Ward/non-Euclidean linkage pairs were excluded before fitting. There were 10,083 valid-score trials and 6,257 unestimable-score trials; all are retained. The latter generally contain one/no non-noise clusters, rather than silently disappearing from the search.

The declared full-coverage/all-seed eligibility rule admitted 1,343 configurations. The overall paper rankings additionally require exactly eight clusters. Eighteen distinct family/criterion/reference selections were refitted at three dates and five seeds: **270 follow-up fits**. Sector labels did not select any parameter. These are finite-grid exploratory optima, and later dates were already examined previously; they are not untouched predictive validation.

## Exact overall optima

- **common_features_k8**: pca `{"n_components": 0.95, "svd_solver": "full"}`; hierarchical `{"linkage": "average", "metric": "euclidean", "n_clusters": 8}`.
- **embedding_k8**: umap `{"metric": "cosine", "min_dist": 0.01, "n_components": 2, "n_jobs": 1, "n_neighbors": 3}`; kmeans `{"n_clusters": 8, "n_init": 20}`.
- **baseline**: tsne `{"init": "random", "learning_rate": 10, "max_iter": 300, "metric": "euclidean", "n_components": 2, "n_jobs": 1, "perplexity": 5}`; hierarchical `{"linkage": "average", "metric": "manhattan", "n_clusters": 8}`.

PCA95 retained seven components in June 2025; each date's resolved dimension and variance ratios are saved. Its distance screen/maps use only the first two coordinates, whereas the hierarchy uses all retained components. The common-feature optimum and a within-family joint-rank winner can differ because ranks are recomputed within each ranking cohort. They are labelled separately. No single model is best under every geometry or interpretability criterion.

| Criterion/model | Date | Feature silhouette | Feature DB | Embedding silhouette | Embedding DB | Singleton clusters | Sector ARI |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| common_features_k8 | 2025-06-30 | 0.259 | 0.684 | 0.257 | 0.673 | 4 | 0.085 |
| common_features_k8 | 2025-12-31 | 0.368 | 0.703 | 0.403 | 0.585 | 2 | 0.220 |
| common_features_k8 | 2026-06-30 | 0.408 | 0.496 | 0.415 | 0.473 | 4 | 0.228 |
| embedding_k8 | 2025-06-30 | 0.129 | 1.278 | 0.829 | 0.218 | 0 | 0.236 |
| embedding_k8 | 2025-12-31 | 0.208 | 1.032 | 0.771 | 0.243 | 0 | 0.290 |
| embedding_k8 | 2026-06-30 | 0.228 | 1.128 | 0.748 | 0.309 | 0 | 0.292 |
| baseline | 2025-06-30 | 0.182 | 1.097 | 0.571 | 0.429 | 0 | 0.236 |
| baseline | 2025-12-31 | 0.177 | 1.014 | 0.598 | 0.447 | 1 | 0.248 |
| baseline | 2026-06-30 | 0.223 | 1.110 | 0.641 | 0.407 | 0 | 0.306 |

The PCA/hierarchical feature-space winner has 4/2/4 singleton clusters across the dates. Its stratified OOF classifier fidelity is consequently not estimable; report this rather than equating perfect in-sample fidelity with validation. The UMAP/K-Means embedding winner has no singletons, but weaker June common-feature scores. The trade-off is substantive, so the results pointer remains unpromoted.

## Primary model: named histories

**Stable at all three dates (29):** ABG, AGL, BHG, BID, BVT, CFR, CLS, CPI, DSY, FSR, GRT, INL, INP, MRP, NED, NRP, OMU, OUT, PPH, REM, RNI, SBK, SHP, SLM, SOL, SSW, VAL, VOD, WHL.

**Shifted at least once (10):** ANG, ANH, BTI, GFI, HAR, IMP, MTN, NPH, NPN, PRX.

**Membership gaps (4):** APN, GLN, MNP, PAN. They receive no ordinary three-date stable/shifted or resolving classification.

MTN changes at the intermediate snapshot and returns to its aligned baseline cluster by June 2026; this differs from an endpoint-only shift. Raw numeric cluster IDs are not sector identities. Hungarian/Jaccard matches are descriptive; inspect overlap-objective and direct-versus-chained sensitivities.

## Hotelling-style candidates and attributes

The individual D^2 screen is compared with a descriptive F reference, with no n multiplier and no calibrated individual significance claim. An internal Beta reference is saved as a sensitivity. The primary model flags:

- **2025-06-30, ANH:** D^2=10.944; distance-surrogate leading attributes: market_cap_zar; shares_outstanding; return_1y.
- **2025-06-30, BHG:** D^2=7.434; distance-surrogate leading attributes: market_cap_zar; shares_outstanding; return_1y.
- **2025-12-31, GLN:** D^2=32.187; distance-surrogate leading attributes: shares_outstanding; revenue_zar_model; return_1y.
- **2025-12-31, SSW:** D^2=10.890; distance-surrogate leading attributes: return_1y; shares_outstanding; revenue_zar_model.
- **2026-06-30, GLN:** D^2=32.013; distance-surrogate leading attributes: shares_outstanding; revenue_zar_model; return_1y.

These are five instrument-date flags across four securities. ANH and BHG have resolving supported-screen histories; SSW is transient. GLN is flagged in both observed later snapshots, but was not a member in June 2025: do not call it a three-date persistent outlier or fabricate a 2025 feature-shift explanation. PCA/full-SVD hierarchical fits are deterministic, so identical results over five seeds are not five independent confirmations.

**Confirmed outliers: none established by this modelling exercise.** In particular, unverified shares/market-cap reconstruction could produce size extremes. The attributes below are surrogate associations and must be checked against source evidence before an economic explanation is asserted.

| Date | Distance surrogate train R^2 | OOF R^2 | OOF MAE |
| --- | ---: | ---: | ---: |
| 2025-06-30 | 0.982 | 0.461 | 1.187 |
| 2025-12-31 | 0.998 | 0.088 | 1.260 |
| 2026-06-30 | 0.998 | -0.019 | 1.298 |

The latest negative OOF R^2 means that distance-surrogate generalisation is poor despite excellent training fit. Its SHAP bars are therefore an exploratory description of that fitted surrogate, not a reliable confirmed explanation of outliers. The notebook retains these adverse results.

## Sector divergence and temporal SHAP

All instruments have a per-date case row. Leave-one-out majority-sector comparisons flag contextual divergence; singleton/tied cases remain unresolved. A separate one-to-one cluster/sector mapping is exported. Neither mapping establishes that an instrument is in the wrong true cluster. Sector labels themselves remain historically unverified legacy context.

For the actual shifted firms, the frozen-2025 classifier is evaluated at both feature vectors. Differences of destination-minus-source SHAP contrasts sum to the change in that same-model margin contrast. Raw feature changes, all ten contributions and imputation flags accompany the report. This does not causally explain a refitted partition changing as its peers and representation also change. Independently fitted per-date SHAP values are not subtracted as though they were the same function.

## Files to inspect

- Full trials, valid/invalid scores and exact JSON parameters: `experiments/runs/paper-exhaustive-k8-01/search/`.
- Primary dendrograms and case outputs: `experiments/runs/paper-exhaustive-k8-01/models/c_073540362ecaaa17/`.
- Main report in the immutable run: `paper_results.md`; per-model named explanation report: `case_review.md`.
- Integrity and domain checks: [paper_experiment_verification.json](paper_experiment_verification.json).

Historical shares/capitalisation, sector history and vendor-series evidence remain unresolved. Repeated cross-sections do not establish return prediction or economic usefulness.
