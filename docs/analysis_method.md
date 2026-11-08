# Three-cross-section analysis

The later supplied SACJ manuscript specifies PCA(95% variance) and automatic
t-SNE learning rate, while the frozen recovered baseline below uses PCA(2) and
learning rate 10. Both alternatives are evaluated in the separately documented
[joint silhouette/DB search](decisions/003-silhouette-db-search.md), with
[saved results](../reports/optimization_results.md). No existing baseline is
silently relabelled as an exact reproduction of the manuscript.

The [ORiON checklist](orion_methods_results_checklist.md) defines the paper's
claim boundary and evidence layers. The current ten-feature historic-consensus-
excluded variant differs from the original 11-feature experiment. Supplementary
Jaccard alignment and SHAP/univariate checks do not replace saved baseline results.

## Recovered baseline and explicit implementation choices

The historical conversation of 8 October 2024 records MinMax scaling, t-SNE
with perplexity 5, learning rate 10 and 300 iterations, followed by average
linkage/Manhattan agglomerative clustering with eight clusters. The manuscript
describes PCA/t-SNE/UMAP comparisons, K-Means/DBSCAN/hierarchical clustering,
and gradient-boosted-tree surrogate SHAP. The original executable notebook was
not recovered; this implementation reconstructs those documented methods,
not a byte-for-byte reproduction. Historical scores are not expected to repeat.

The initialization (`random`), seed (42), UMAP parameters (10 neighbours,
min_dist 0.1), DBSCAN parameters (eps 0.5, min_samples 3 on standardized
embedding coordinates), K-Means n_init (20), and XGBoost surrogate are explicit
new implementation choices, not claimed historical approvals. All settings and
package versions are saved in each run manifest. Eight clusters is the legacy
baseline, not an optimum or a requirement imposed by sector labels; a k=2–10
sensitivity table accompanies it. Do not select settings using June 2026 scores
then describe June 2026 as an untouched test.

The machine-readable implementation contract is `configs/baseline.json`.
Audit repairs, environment differences and open decisions are recorded in
`docs/decisions/001-audit.md`. Results are review candidates until explicitly
promoted through `experiments/baseline.json`; execution never changes that pointer.

## Inputs and preprocessing

Each snapshot contains **40 company groups represented by 41 listed instruments**. Investec Limited (INL) and Investec plc (INP) are separate securities in one dual-listed company (DLC) group; both remain in the instrument-level analysis. Exited members are excluded at subsequent dates until an effective re-entry. See [the population audit](../reports/population_count_audit.md) for sources and scope.

All 123 rows (41/date, 43 unique tickers) remain, including RNI. The ten numeric
inputs are return, average volume, market cap, beta, shares, revenue, EPS,
annualised volatility, dividend yield and clipped earnings yield. Unavailable
analyst ratings are not fabricated. Close is not counted as an extra feature.
Sector labels are retained as external descriptive labels, not ordinal codes
or model inputs. Sector ARI/NMI are agreement statistics, not ground-truth
accuracy. This keeps the clustering unsupervised with respect to sectors.

Units are preserved from the supplied workbook: return, beta, volatility and
dividend/earnings yields are numeric ratios; volume is average daily shares;
shares outstanding is a count; capitalization and revenue are ZAR; EPS and close
are ZAR per share. The workbook describes return as split-adjusted price return,
excluding cash dividends. These labels do not remove differing revenue/EPS
accounting definitions across sectors or certify historical share bases.

The audited CSV already holds separate model-only imputation columns and flags,
with constants and E/P clipping fitted on June 2025 only. It is not overwritten.
MinMax scaling is fitted once on June 2025 and reused without clipping; later
values can exceed [0,1]. No pooled future fit, log transforms or silent row drops
are performed. Imputation flags remain metadata, not extra numeric dimensions.

## Cross-sections and comparisons

Each representation and clustering is independently refitted at each date.
This is a descriptive temporal extension, NOT train/predict validation:
ordinary t-SNE and agglomerative clustering have no native predictive transform.
The source CSV's train/validation/test labels do not change that fact.
The nine representation/algorithm combinations are reported, not automatically
selected using sector agreement. Silhouette is reported both in embedding space
and in the common ten-feature scaled space. Davies–Bouldin uses Euclidean
embedding geometry; it is distinct from average/Manhattan linkage. DBSCAN noise
is excluded from quality/agreement calculations and its count and coverage are
always shown. Do not compare an almost-all-noise score to full-population models
without considering coverage.

The primary pipeline is rerun over five distinct seeds (42–46); all ten pairwise
ARI/NMI comparisons per date are exported. These are seed sensitivity, not
bootstrap confidence intervals or stability guarantees.

Continuing members alone enter temporal ARI/NMI and maximum-overlap Hungarian
label alignment. Entries/exits receive separate events and no cluster-change
flag. RNI is marked imputation-sensitive. Alignment is descriptive, estimated
after observing both cross-sections; matched numbers do not establish stable
economic identities. Never compare coordinates across independently fitted
t-SNE maps as if they share an axis system. No investment returns, Sharpe ratios,
or portfolio backtest are inferred from these cross-sectional data.

## SHAP interpretation

For each primary partition, an XGBoost multiclass surrogate learns labels from
the original ten-feature matrix. Tree SHAP explains surrogate raw class margins,
not the unsupervised algorithm, causal effects, or investment returns. Values,
base values, tickers, feature names, class mapping, global importance, and
within-cluster importance are exported; raw-margin additivity is checked.
Surrogate in-sample fidelity is labelled in-sample. Stratified out-of-fold
fidelity is reported only if every cluster has at least two members, otherwise
explicitly not estimable. Even OOF fidelity uses full-snapshot pseudo-labels and
does not validate the cluster discovery. Singleton SHAP is labelled descriptive
only; no claim of reliable subgroup inference is made.

## Remaining evidence limits

Public-source retrospective reconstruction and restatements are allowed by the
data policy. Historical shares/sectors remain unverified. Imputed fundamentals
and correlated size features may influence partitions. These limitations are
not resolved by a successful execution or high silhouette. No new Hotelling
T² decision rule is introduced here: the original implementation and approved
calibration details were not recovered.

API references: [scikit-learn TSNE](https://scikit-learn.org/stable/modules/generated/sklearn.manifold.TSNE.html),
[silhouette](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.silhouette_score.html),
[TreeExplainer](https://shap.readthedocs.io/en/stable/generated/shap.TreeExplainer.html).
