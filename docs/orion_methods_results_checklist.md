# ORiON methods-to-results checklist

The newer [full experiment workflow](paper_experiments_guide.md) adds an explicit
finite-grid search, actual-tree dendrograms, Jaccard histories, a specified
**descriptive** 2D distance/F-reference screen, supported-screen history taxonomy,
sector context and separate cluster/distance/frozen-2025 SHAP targets. Historical
?pending? statements below describe the earlier reporting package; the new
workflow is a separately versioned exploratory extension, not a retroactive
claim about old runs. No screen establishes a confirmed outlier.


Study claim: a repeated, interpretable, cross-sectional investment-screening
process. The outputs describe associations and candidate screening structure.
They do not demonstrate strategy-return prediction, a profitable strategy or
submission-grade historical point-in-time (PIT) observation.

This checklist supplements the saved review package. It does not promote or
silently replace the fixed baseline. A documented method, implemented output,
and externally verified observation are separate claims.

## 1. Population, dates and membership

| Snapshot | Instruments | Membership context |
| --- | ---: | --- |
| 2025-06-30 | 41 | NPH entered and GLN exited in the June 2025 review, before this snapshot |
| 2025-12-31 | 41 | GLN entered and APN exited in September 2025 |
| 2026-06-30 | 41 | PAN entered and MNP exited in March 2026 |

There are 123 instrument-date records, 43 distinct tickers in the union, 40
continuing instruments in each adjacent pair and 39 observed at all three dates.
These are overlapping historical index cross-sections selected by membership,
not independently sampled groups. Continuing instruments form a linked subset;
the entire data set is not a balanced independently sampled panel. The 41
instruments must not be silently reduced to 40 or described as 41 independent
economic firms. Index eligibility determines inclusion, including unresolved RNI.

Each snapshot contains **40 company groups represented by 41 listed instruments**. Investec Limited (INL) and Investec plc (INP) are separate securities in one dual-listed company (DLC) group; both remain in the instrument-level analysis. Exited members are excluded at subsequent dates until an effective re-entry. See [the population audit](../reports/population_count_audit.md) for sources and scope.

## 2. Evidence matrix and strict PIT claims

| Layer | Recorded evidence | Coverage | Permitted interpretation / remaining work |
| --- | --- | --- | --- |
| Membership | Workbook/CSV `VERIFIED` | 123 records | Internally reconciled to dated sheets and membership table; no fresh source certification in the coding audit |
| Revenue and statutory diluted EPS | `DATED_ISSUER_RELEASE`; workbook fundamental verification | 120 resolved records | Source-backed fundamental layer under the retrospective policy; do not imply the full feature vector was investor-observable at the date |
| RNI fundamentals | `UNRESOLVED_IMPUTED_FOR_MODEL` | 3 records | Raw revenue, EPS and E/P remain blank; separately flagged model-only June-median fills |
| Prices, return, volume, beta, volatility and cash yield | `RETROSPECTIVE_VENDOR_DAILY_HISTORY` | 123 records, with 2 flagged missing AGL volumes filled for modelling | Retrospective reconstruction, not archived as-of vendor history; validate daily source, repairs, corporate actions and field definitions |
| Shares and capitalization | `RETROSPECTIVE_LEGACY_YAHOO_RECONSTRUCTION`; cap = close × shares | 123 records | Legacy/unverified historical share bases; arithmetic reconciliation does not establish historical availability or correctness |
| Sector history | `PUBLIC_DIRECTORY_LEGACY_LABEL` | 123 records, eight legacy categories | Contextual external comparator; independently dated historical classification remains unresolved |
| Analyst recommendations / historic consensus | Unavailable; source workbook cells blank | All 123 records lack recommendations | Excluded; no current consensus substituted or historic ratings invented |

The counts above describe the supplied evidence flags, not new external
verification. Later restatements are permitted under the retrospective policy.
Strict PIT assertions are restricted to individually supported fields and their
actual timing evidence. No v4 clustering output is fully PIT certified.

Submission-grade empirical findings remain blocked by source-backed archived
PIT shares/capitalization, historical sector evidence and daily market-source
validation. A working model cannot convert reconstructed inputs into verified
historic observations.

## 3–4. Experiment identity, features and preprocessing

Name the implemented experiment a **10-feature historic-consensus-excluded
variant** of the original 11-feature design. Historical analyst consensus is
unavailable, P/E is replaced by clipped earnings yield, and sectors are held out
of the numeric matrix. These are substantive specification differences: do not
call the original and present experiments identical. The paper must enumerate
and cite the original 11 inputs rather than infer their identity from counts.
Close remains a derivation input, not an additional numeric baseline feature.

| Numeric column | Definition / scale convention |
| --- | --- |
| `return_1y` | Reconstructed split-adjusted one-year price return as a fraction; cash dividends excluded |
| `average_daily_volume_1y_model` | Average daily traded shares over the reconstructed window; no currency conversion |
| `market_cap_zar` | Close in ZAR per share × reconstructed shares; ZAR, not ZAc or millions |
| `beta_1y` | Reconstructed OLS slope against J203 daily price returns; dimensionless |
| `shares_outstanding` | Reconstructed count of shares, not monetary capitalization |
| `revenue_zar_model` | Selected issuer annual revenue/income definition converted to ZAR; sector accounting definitions differ |
| `eps_zar_model` | Selected statutory diluted annual EPS on the workbook share basis, converted to ZAR per share; losses remain negative |
| `annualised_volatility_1y` | Sample standard deviation of simple daily price returns × sqrt(252), expressed as a fraction |
| `dividend_yield` | Reconstructed trailing cash-dividend events / close, expressed as a fraction; gross/net basis not independently certified |
| `earnings_yield_model_clipped` | Raw EPS(ZAR/share) / close(ZAR/share), with separately flagged RNI fill and June-fitted clipping |

ZAc denotes South African cents. A ZAc price is divided by 100 to obtain ZAR;
issuer EPS in cents/pence also requires the documented unit/currency conversion.
The modelling CSV already contains ZAR values: do not divide it again. Close,
EPS and share bases must be compatible before computing E/P or capitalization.
Preserve source FX and split-basis notes; MinMax cannot repair a unit error.

For feature j, let a_j and b_j be its minimum and maximum among the 41 June
2025 model observations. Transform each snapshot with
`z_ij = (x_ij - a_j) / d_j`, where `d_j = b_j - a_j` if positive and 1 for a
constant training feature. The same scaler is reused with `clip=False`.
Future transformed values may leave [0,1]. No pooled refit or sector coding.

Missing-case accounting: retain all 123 rows; fill AGL volume only at the first
two dates with 1,534,909.228915663 shares/day. Fill RNI's three model-only
fundamentals at every date with June medians: revenue ZAR 98,244,535,964.16383,
EPS ZAR 12.7715/share, and E/P 0.051361404520658835. These independent fills do
not obey an accounting identity with each other. Clip raw resolved E/P at
−0.5889019129867248 and 0.14636747615529913, the 1st/99th linear-interpolated
percentiles of the 40 resolved June values. Evidence flags remain metadata.

`earnings_yield_and_pe_diagnostic.csv` and `pe_case_counts.csv` in the separate
ORiON reporting run account for positive, nonpositive and unresolved raw EPS.
P/E is shown only for positive EPS. Loss/zero-EPS and unresolved cases are not
dropped. This is missing/loss accounting, **not a completed alternative P/E
clustering sensitivity**. A fair comparator still needs a prespecified treatment
of nonmeaningful P/E, retained observations and preprocessing before execution.

## 5–6. Representations, clustering and quality

The reconstructed fixed baseline is 2D t-SNE, perplexity 5, learning rate 10,
300 iterations, random initialization and seed 42, followed by k=8 average-linkage
Manhattan hierarchical clustering. Recovered historical settings and newer
implementation choices remain distinguished in `analysis_method.md`. Each date
is independently refitted; it is not inductive train/predict validation.

Saved results cover PCA/t-SNE/UMAP × hierarchical/K-Means/DBSCAN, five t-SNE
seeds per date and k=2–10 sensitivity. No scores automatically select/promote
a model, and sector agreement is not a fitting or tuning target.

Report both embedding and common June-scaled feature-space silhouettes with
their Euclidean geometry. Davies–Bouldin uses Euclidean embedding centroids,
distinct from Manhattan linkage. DBSCAN operates in standardized embedding
coordinates; exclude noise from score calculations and display noise/coverage.
External sector ARI/NMI are contextual agreement, not historical classification
accuracy. Report all seed comparisons without interpreting t-SNE separation
alone as inference. Repeated seeds are not bootstrap uncertainty.

## 7. Surrogate associations and univariate checks

Tree SHAP explains the XGBoost surrogate's raw class margins, not the clustering
algorithm, causal mechanisms or investment returns. Preserve label/class mapping,
feature order and additivity checks. In-sample fidelity is 1.0 at each date;
stratified OOF fidelity is 0.537, not estimable (December singleton), and 0.732.
These OOF scores use full-snapshot pseudo-labels and do not validate discovery.

The separately tracked reporting script compares own-class mean absolute SHAP
importance with `cluster median − same-date population median` for each of the
ten saved June-scaled features. It exports signed deviations and within-cluster
magnitude ranks, SHAP ranks and their descriptive rank correlations. No p-values,
univariate significance claims or causal direction are inferred. This is a
post hoc association check, not an approved historic method or refitted model.
Singleton and imputation-sensitive profiles are labelled explicitly. Differences
between multivariate surrogate importance and univariate deviations are expected
and should be discussed rather than treated as proof that either is correct.

## 8. Proposed 2D Hotelling T² descriptive screen: pending specification

Update after receiving the SACJ manuscript: page 11 supplies n=40, p=2, 5% and
an approximate cutoff 6.66 for its original sample. Those historical details are
now available. The individual-distance statistic/reference calibration and its
use with the new 41-instrument learned embeddings still need to be explicit.
See `decisions/003-silhouette-db-search.md`; no Hotelling run is implied here.

The checklist now requests this extension, but no recovered implementation or
calibration has been established. Do not describe it as already reported in v4
or attach an invented F cutoff. Before execution record the 2D coordinate system,
reference population, centre, covariance estimator/regularization, statistic,
finite-sample F-reference mapping and cutoff level. A same-sample individual
distance is not automatically the sample-mean Hotelling statistic. NIST treats
[mean-vector T²](https://www.itl.nist.gov/div898/handbook/pmc/section5/pmc543.htm)
and [individual-observation control charts](https://itl.nist.gov/div898/software/dataplot/refman1/auxillar/hotell.htm)
separately, with calibration depending on the setup.

If an F-reference cutoff is chosen for data-adaptive t-SNE coordinates, label it
an explicitly specified **descriptive reference threshold**, not a confirmed
significance test, false-positive guarantee or calibrated investment-risk test.
An extreme geometric distance, sector divergence and a one-instrument cluster
are distinct flags. A singleton does not establish that the firm is an outlier,
and disagreement with a legacy sector label does not prove misclassification.
No Hotelling values, exceedance counts or confirmed outlier claims are exported yet.

## 9. Alignment and observation eligibility

The baseline's saved temporal tables use maximum-overlap Hungarian alignment.
That objective is **not Jaccard**. The ORiON reporting extension separately
exports both objectives for adjacent dates using saved labels. For continuing
sets A_i and B_j, J_ij = |A_i ∩ B_j| / |A_i ∪ B_j|, with zero for an empty
union. Sorted labels and Hungarian optimization maximize total Jaccard; reject
zero-intersection matches and assign fresh descriptive IDs. Entries/exits do
not contribute to these sets and receive no ordinary cluster-change flag.
The supplemental pairs start from each date's raw labels, rather than claiming
to replace the chained baseline numbering. ARI/NMI remain label invariant.

`temporal_observation_eligibility.csv` lists every union ticker and its observed
dates. Three-date histories are eligible for 39 instruments, adjacent-pair
histories for 40 each. Any later emerging/persistent/transient/resolving label
must identify its underlying binary screen and relevant observation window.
Absent membership is missing observation, not a negative flag or a resolution.
No taxonomy is assigned until those flag definitions and windows are specified.
Display Top 40 entry/exit separately, and carry imputation sensitivity into any
interpretation. Never interpret raw cluster IDs or independently fitted t-SNE
coordinates as persistent economic identities/shared axes.

## 10. Claim boundary and remaining deliverables

Completed: baseline and comparison experiments; seed/k diagnostics; evidence
accounting; membership-aware descriptive transitions; surrogate fidelity and
SHAP exports; supplementary Jaccard and univariate association reporting.

Pending: the alternative P/E sensitivity protocol, an explicit Hotelling
statistic/F-reference/cutoff, and definitions/windows for temporal screening
flags. Source-backed archived shares/capitalization, sector history and market
series validation remain the blocker for submission-grade empirical findings.
No full v4 output is certified PIT, and no paper-readiness claim is made.

Reproduce supplementary reports with:

```bash
python scripts/orion_review.py --source-run final-full-42 --run-id my-orion-review
python scripts/verify_run.py experiments/runs/my-orion-review
```

The reporting run records its source bundle checksum, exact code/configuration,
artifacts and diagnostics in the existing experiment registry. It does not
change the baseline pointer or overwrite the original runs.

## Saved supplementary results

Run `orion-report-01` derives its outputs from `final-full-42`; no model was
refitted. Its artifact manifest and completion marker verify the saved report.
It contains 240 cluster-feature comparisons (3 dates × 8 clusters × 10 features).
Median within-cluster SHAP/univariate rank correlations are 0.650, 0.677 and
0.572 across the dates. These descriptive rank associations do not establish
surrogate validity or imply causal attribution.

The separately computed overlap and Jaccard procedures produce the same aggregate
change counts: 14/40 then 10/40 continuing instruments. Their instrument-level
flags agree in the first pair but differ for four instruments in the second:
AGL and SOL change only under Jaccard, while MTN and NPN change only under
maximum overlap. Equal totals therefore conceal different interpretations.
Keep both outputs available and settle the alignment objective explicitly before
using individual flags in the paper. Synthetic and saved-data regression fixtures
demonstrate the distinction. These are aligned cluster-change flags, not Hotelling
outlier or emerging/persistent/transient/resolving flags.

| Date | Positive raw EPS | Nonpositive raw EPS | Unresolved raw EPS |
| --- | ---: | ---: | ---: |
| 2025-06-30 | 35 | 5 | 1 |
| 2025-12-31 | 36 | 4 | 1 |
| 2026-06-30 | 38 | 2 | 1 |

The one unresolved case at each date is RNI. These counts identify the problem
an alternative P/E specification must handle; they are not its sensitivity result.
