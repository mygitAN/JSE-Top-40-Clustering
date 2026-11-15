# Method, data policy and limits

## Question and claim

The study describes peer groups among FTSE/JSE Top 40 instruments at three
decision dates and how membership changes between them. It is a descriptive
screening exercise. It does not predict returns, test a strategy or establish
causes.

## Population

| Date | Instruments | Company groups | Change since previous date |
| --- | ---: | ---: | --- |
| 2025-06-30 | 41 | 40 | |
| 2025-12-31 | 41 | 40 | Glencore (GLN) in, Aspen (APN) out |
| 2026-06-30 | 41 | 40 | Pan African Resources (PAN) in, Mondi (MNP) out |

Investec Limited (INL) and Investec plc (INP) are two securities of one
dual-listed company, so 41 instruments represent 40 groups. Both stay in the
analysis as separate rows.

Membership is checked against every published FTSE/JSE quarterly review in the
period, recorded with sources in `data/reference/index_changes.csv`.
`python -m top40.data` fails if any date's membership is not the previous date's
membership plus the reviews in between.

| Review | Effective | Top 40 change |
| --- | --- | --- |
| June 2025 | 23 Jun 2025 | Northam Platinum (NPH) in, Glencore (GLN) out; before the first date |
| September 2025 | 22 Sep 2025 | Glencore in, Aspen out |
| December 2025 | 22 Dec 2025 | none |
| March 2026 | 23 Mar 2026 | Pan African Resources in, Mondi out |
| June 2026 | 22 Jun 2026 | none |

So 39 instruments are members at all three dates and 43 at one or more. The
cluster-flow diagram shows the 39, because a three-date history needs all three
observations; Aspen, Glencore, Mondi and Pan African appear only at the dates
they were members.

There are 123 rows and 43 distinct tickers. 40 instruments continue between each
pair of adjacent dates and 39 are present at all three. The trailing one-year
windows of adjacent dates overlap by six months, and annual fundamentals are
often identical between dates, so the three cross-sections are not independent
samples.

## Inputs

`data/processed/Top40_Retrospective_Model_Inputs_v1.csv` holds one row per
instrument and date. `python -m top40.data` checks every value against
`data/source/Top40_PIT_Verification_v4.xlsx`, which records the source of each
field. `Top40_Retrospective_Model_Method_v1.json` records the imputation policy.

- **Market fields** (return, volume, beta, volatility, dividend yield) are
  rebuilt from vendor daily history. Return is a split-adjusted price return
  excluding dividends.
- **Fundamentals** (revenue, diluted EPS) come from dated issuer releases for
  120 of 123 rows, converted to rand at dated central-bank rates.
- **Shares and market capitalisation** are reconstructed and unverified. Market
  capitalisation equals close times shares.
- **Sector** is a legacy eight-category public-directory label, not a verified
  historical classification. It is never a model input and never selects a model.

Imputation and clipping constants are fitted on June 2025 only:

- Reinet (RNI) has no usable revenue or EPS at any date. Model columns take the
  June 2025 median; the raw columns stay blank.
- Anglo American (AGL) has no volume at the first two dates; the model column
  takes the June 2025 median.
- Earnings yield (EPS over close) replaces P/E and is clipped to the June 2025
  1st and 99th percentiles.

## Feature sets

Defined in `top40/features.py`.

`original10` is the archived reference used by all results before November 2026.
Two of its features depend on the share basis. A subdivision multiplies share
count and divides EPS without changing the business, and trailing volume in
shares changes with it. Its size variables are also heavily right-skewed.

`invariant8` replaces the basis-dependent and skewed inputs:

| Feature | Definition |
| --- | --- |
| Return, beta, volatility, dividend yield, earnings yield | As in `original10` |
| Log market cap | log10 of market capitalisation (each Investec line's own) |
| Log revenue / cap | log10 of revenue over market capitalisation (group figures for Investec) |
| Log turnover | log10 of average daily volume over shares outstanding, on one share basis |

Derived features that depend on an imputed input are imputed with the June 2025
median of the derived feature itself.

`logsize10` and `market5` are diagnostics that isolate, respectively, the effect
of skew and the effect of dropping size and liquidity altogether.

## Corrections

The source CSV and workbook are never edited. Corrections live in
`data/reference/`, each with its source. The derived feature columns use them;
the raw columns, and therefore `original10`, do not.

**Share subdivisions** (`corporate_actions.csv`). Naspers subdivided five for one:
trading on the new basis began 1 October 2025, and the register was updated on
6 October. The feature audit restates shares and EPS to a common basis.

**Volume on one share basis** (`volume_corrections.csv`). The workbook's trailing
average volume for Naspers at December 2025 and June 2026 mixes pre- and
post-subdivision units. Both values are restated to post-subdivision units from
the daily series behind the workbook (Yahoo Finance NPN.JO, split-adjusted).
Dividing the pre-1 October volumes by five reproduces both workbook values
exactly, which confirms it is the same series. June 2025 is entirely before the
subdivision and already matches the June 2025 share count.

| Date | Workbook (mixed units) | Corrected (post-split) |
| --- | ---: | ---: |
| 2025-12-31 | 800,935 | 2,140,029 |
| 2026-06-30 | 1,502,524 | 1,847,639 |

**Investec line share counts** (`dual_listed_shares.csv`). Both Investec rows
carry the combined dual-listed count (about 900 million), so each showed the
whole group's market capitalisation. Investec's AGM notices disclose each
issuer's outstanding shares (issued, less shares held within the group):

| Disclosure | Investec plc | Investec Limited | Combined | plc fraction |
| --- | ---: | ---: | ---: | ---: |
| 19 June 2024 | 645,162,307 | 257,612,296 | 902,774,603 | 0.7146 |
| 10 June 2026 | 630,541,464 | 256,396,598 | 886,938,062 | 0.7109 |

These combined totals match the inputs' combined counts to within 0.2%, so the
inputs are on the same outstanding-share basis. Each line's count is the
combined count in the inputs times its fraction. June 2025 uses the 2024 notice
(Investec plc's count was unchanged at the 7 August 2025 AGM), June 2026 the 2026
notice, and December 2025 the midpoint of the two fractions, since no notice is
near that date.

Each line then has its own market cap and turnover. For revenue relative to
market value, both lines use group revenue (the two issuers' revenues summed)
over group market cap: a share in either line is a claim on the whole group,
which is also why both lines report the same group EPS and dividends.

## Pipeline

1. **Scaling.** MinMax, fitted on June 2025 and applied unchanged to later
   dates, so later values can fall outside [0, 1].
2. **Representation.** PCA (2 components), t-SNE (perplexity 5, learning rate
   10, 300 iterations, random initialisation) and UMAP (10 neighbours).
3. **Clustering.** Average-linkage Manhattan hierarchy and K-Means at k=8;
   DBSCAN on standardised coordinates with its own cluster count.
4. **Study model.** UMAP (2 components, 3 neighbours, min_dist 0.01,
   Euclidean), then `AgglomerativeClustering` on the UMAP coordinates with
   k=8, average linkage and Manhattan distance, refitted over seeds 42 to 46.
   The settings came from exploring June 2025: an author-specified sweep fixed
   3 neighbours and min_dist 0.01, while an earlier 36-combination grid had
   preferred min_dist 0.1. k=8, average linkage and Manhattan distance follow the
   original paper. The paper's own recipe (t-SNE, perplexity 5, the same
   clustering) remains in the comparison table as `tsne_hierarchical`.
5. **Scores.** Silhouette and Davies-Bouldin in both the representation and the
   scaled feature space, with cluster sizes and singleton counts. DBSCAN noise is
   excluded from scores and reported as coverage.

Every date is fitted independently. No setting is tuned on a later date.

## Reading the results

- **Feature-space scores before embedding scores.** t-SNE and UMAP compress
  neighbours, so embedding scores are high even for unstructured data. With
  min_dist 0.01 UMAP packs points especially tightly: its clusters look
  sharper on the map than they are in the financial features.
- **Seed agreement is the noise reference.** Pairwise adjusted Rand index
  between seeds shows how much a partition moves when only the random seed
  changes. Date-to-date change should be read against it.
- **Scores are not comparable across feature sets.** Each is computed in its own
  space. Compare cluster sizes, seed agreement and cross-set agreement instead.
- **Alignment.** Cluster numbers are matched date to date by a Hungarian
  assignment on Jaccard overlap among continuing instruments. A cluster with no
  overlap gets a new number, and a retired number is never reused. Entries and
  exits are separate events, never cluster changes.
- **Distance screen.** Squared Mahalanobis distance from the same-date mean in
  the scaled feature space, compared with the Beta reference for an individual
  same-sample distance under multivariate normality. The data are not normal, so
  it ranks unusual profiles; it is not a significance test.
- **SHAP.** Explains a gradient-boosted surrogate of the cluster labels. Rely on
  it only as far as out-of-fold fidelity allows, and prefer the cluster median
  profiles, which need no surrogate.

## Known limits

- Inputs are reconstructed, not verified point-in-time.
- The combined Investec count itself is reconstructed. Only the split between
  the two lines comes from disclosures, and December 2025 is interpolated.
- Volume is JSE trading only. For companies whose main listing is abroad (for
  example Investec plc, Anglo American, British American Tobacco, Glencore,
  Prosus, Richemont) turnover understates total liquidity.
- Revenue is not defined uniformly across sectors (banks report total income).
- With 41 instruments and eight clusters, several clusters have two to four
  members; small changes in inputs move them.
- No external validation and no resampling-based noise floor have been run.
