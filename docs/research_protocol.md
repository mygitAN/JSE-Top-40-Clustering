# Research protocol: repeated cross-sectional screening of the JSE Top 40

**Status: FROZEN v1.0 (2026-11-08).** The author has made all decisions; they are recorded in the change log (Section 12).
This version is committed and tagged `protocol-v1`. Any later change is made in a new, dated version with the reason recorded.
Results produced under an earlier version are never relabelled as confirmatory.

## 1. Purpose and claim

The study develops an interpretable, repeated cross-sectional decision-support framework. The framework:
- separates transient, emerging, persistent and resolving structural signals within an investable equity universe;
- attributes changes in peer relationships to changes in the firms' underlying financial characteristics.

**What the design supports:** the framework is **replicated across three market states** (decision dates).

**What it does not support:**
- The sample is not *n* = 120 (or 123) independent observations. Each date has about 40 firms. Most firms recur across dates, and the trailing 12-month market windows of adjacent dates overlap by six months.
- Results are descriptive screening signals, not predictions, investment recommendations or causal effects.

## 2. Decision dates and information rule

| | Decision date |
|---|---|
| *t*₁ | 30 June 2025 |
| *t*₂ | 31 December 2025 |
| *t*₃ | 30 June 2026 |
| *t*₄ | 31 December 2026: **pre-registered blind confirmation date** (Section 11). Its data is pulled only after that date. |

These are decision dates, not six-month aggregation periods. At each date *t*:

1. **Market measures** use daily data in the trailing window ending on *t* (Section 4).
2. **Fundamentals** are the latest figures *published* on or before *t*: the issuer's most recent annual results, or interim results where that rule says so. Restated figures published after *t* are not used.
3. **Index membership** is the FTSE/JSE Top 40 constituent list effective at the close on *t*.
4. **Sector** is the classification in force at *t*.

Every value records its source, its publication or observation date, and an evidence flag. A value that cannot be shown to have been available at *t* is treated as missing (Section 5).

> **Known gap.** The current dataset (`Top40_Retrospective_Model_Inputs_v1`) is a retrospective reconstruction:
> - later restatements are permitted;
> - shares and sector labels are unverified;
> - market data are not archived as-of extracts.
>
> It does **not** meet rules 2–4. A protocol-compliant data pull (v2) is required. See Section 11.

## 3. Universe

- All Top 40 constituents at each *t*, at instrument level. Dual-listed lines (Investec Ltd/plc) are kept as separate instruments, and this is disclosed.
- No firm is dropped for missing data. Section 5 sets out how gaps are handled.
- Entries and exits between dates are **membership events**. They are reported separately and never counted as cluster changes or anomalies.
- Taxonomy classification (Section 9) needs a firm to be present at all three dates. Other firms are reported with their observed pattern and the label *partial history*.

## 4. Features

The SACJ study used 11 features. This study uses **10**, with two departures:
- P/E is replaced by earnings yield (row 10);
- the analyst rating is dropped (last row).

The paper must state both departures, since they make the results not directly comparable with SACJ's 11-feature space.

| # | Feature | Definition | Window / source |
|---|---|---|---|
| 1 | 1-year return | Split-adjusted **price return**, close(*t*) / close(*t* − 12 m) − 1, dividends excluded (decided 2026-11-08). Total return ≈ price return + dividend yield, and dividend yield is already feature 9. Total return would therefore count the dividend component twice and add correlation. Price return keeps the two pieces of information separate and needs only price data, which is easier to verify as of each date. | 12 m to *t* |
| 2 | Average volume | Mean daily traded shares | 12 m to *t* |
| 3 | Market cap | Close(*t*) in ZAR × shares in issue at *t* | at *t* |
| 4 | Beta | OLS slope of daily returns on J203 (All Share) daily returns | 12 m to *t* |
| 5 | Shares outstanding | Shares in issue at *t* (JSE / issuer source) | at *t* |
| 6 | Revenue | Latest published annual revenue (bank/insurer equivalent defined per sector), in ZAR | latest published by *t* |
| 7 | EPS | Latest published diluted EPS, in ZAR. Losses stay negative. | latest published by *t* |
| 8 | Volatility | Sample SD of daily simple returns × √252 | 12 m to *t* |
| 9 | Dividend yield | Cash dividends with ex-date in the trailing 12 m / close(*t*) | 12 m to *t* |
| 10 | Earnings yield | EPS / close(*t*). This **replaces P/E**, which is undefined or explodes for loss-makers. Clipped at the *t*₁ 1st/99th percentiles. | at *t* |
| — | ~~Analyst consensus rating~~ | **Dropped (decided 2026-11-08).** An as-of-date historical consensus cannot be reliably reconstructed, and a rating looked up today would introduce look-ahead. The study uses **10 features**. | — |

Sector is **never** a model input. It is used only to interpret and validate the clusters.

**Sector scheme (decided):** the legacy **eight Listcorp sector labels**, kept the same at every date, for comparability with SACJ. ICB is not used.
- Each firm's label at each date is checked against a dated source where possible.
- Labels that can't be verified are flagged.

## 5. Missing data and preprocessing

1. Raw values are never overwritten. Model-only fills go in separate columns, each with a flag.
2. **Imputation:** the *t*₁ cross-sectional median, applied at all dates, flagged. Results for imputed firms are labelled *imputation-sensitive*.
3. **Clipping:** earnings yield only, at the *t*₁ 1st/99th percentiles.
4. **Scaling:** MinMax, fitted on *t*₁ and frozen, so later values may leave [0, 1]. Freezing keeps one common feature space, which is what makes the frozen-surrogate SHAP comparison in Section 10 valid.
   - Sensitivity check: scaling refitted at each date.

## 6. Model selection (the same procedure at every date)

**Search space** (the same at each date):
- **Dimension reduction:** none (the scaled features directly); PCA (2 components, or 95% of variance); t-SNE (perplexity 5/10/20 × learning rate 10/auto × 300/1000 iterations × Euclidean/Manhattan input distance); UMAP (3/5/10/20 neighbours × min_dist 0/0.1/0.5 × Euclidean/Manhattan input distance).
- **Clustering:**
  - hierarchical: single, complete and average linkage, each with Euclidean, Manhattan or cosine distance, plus Ward with Euclidean;
  - K-Means with 20 random starts;
  - DBSCAN: eps 0.3/0.5/0.8/1.2 × min_samples 2/3/5.
- **k:** 2–10.
- **Seeds:** 42–46 for every stochastic step.

**Quality:**
- Silhouette and Davies–Bouldin, each computed **in the common scaled feature space** (the basis for selection) and in the embedding (reported only). Embedding scores are not comparable across reduction methods.
- Each score is averaged over the five seeds.

**Eligibility** (all must hold):
1. a valid partition on all 5 seeds;
2. at least 95% of firms assigned (non-noise);
3. mean pairwise seed ARI ≥ 0.80;
4. at most one singleton cluster;
5. no cluster holding more than 50% of firms.

Rules 4–5 exist because isolating outliers is the job of T² (Section 8). The clustering must form peer groups.

**Ranking:** silhouette rank plus DB rank, both in feature space; the lowest sum wins. Ties go to the higher seed ARI, then the higher silhouette.

**Application (decided).**
- The method is selected **once, at *t*₁** (30 June 2025), by the rule above, among k = 8 configurations. The method means the reduction and its settings, the clustering algorithm, the linkage and the distance.
- That method is then refitted **unchanged** at each later date, with **k = 8 fixed** at every date.
- Rationale: the study measures shifts relative to the eight-sector ground truth. A fixed method and fixed k mean that differences between dates reflect the data, not changes in the model.

Fixing k could make the structure look more stable than it is. To address this, the **best-supported k at each date** is computed with the same ranking (k = 2–10) and reported **as a diagnostic only**. It never replaces k = 8.

**Sensitivity analyses, always reported:**
- the free-k diagnostic above;
- the SACJ baseline (t-SNE perplexity 5, learning rate 10, 300 iterations; average linkage, Manhattan distance; k = 8);
- the winner under alternative eligibility thresholds (singletons 0/1/2; largest cluster 40/50/60%; seed ARI 0.7/0.8/0.9).

## 7. Cluster matching across dates (reproducible; sector plays no part)

Matching is between adjacent dates (*t*₁→*t*₂, *t*₂→*t*₃), plus *t*₁→*t*₃ for "base to current". Only firms present at both dates are used.

1. **Primary similarity:** the Jaccard overlap of membership, J(i, j) = |Cᵢ ∩ Dⱼ| / |Cᵢ ∪ Dⱼ|, for every cluster i at *t* and every cluster j at *t*+1.
2. **Assignment:** the Hungarian algorithm maximises total J.
3. **Acceptance:** a matched pair counts as "the same cluster" only if J ≥ **0.30** (decided). Clusters left unmatched are *dissolved* (at *t*) or *new* (at *t*+1).
4. **Split and merge:**
   - A cluster at *t* with J ≥ 0.30 to two or more clusters at *t*+1 is a *split*.
   - The reverse case, two or more clusters at *t* with J ≥ 0.30 to one cluster at *t*+1, is a *merge*.
5. **Secondary matching (sensitivity):**
   - Use the Hungarian algorithm on the Euclidean distance between cluster median profiles in the frozen scaled feature space.
   - Report how often the two matchings agree.
6. Matching is repeated for each seed. A match is **robust** if it holds in at least 4 of 5 seeds.
7. **Firm transition:** a firm *moves* if its cluster at *t*+1 is not the accepted match of its cluster at *t*. It is a **robust move** if this holds in at least 4 of 5 seeds.
   - A label-free check (peer-set Jaccard compared with same-date seed noise) is reported as a sensitivity.

A move in peer group is a **structural change, not an anomaly**.

## 8. Firm-level signals (binary, at each date)

Two separate signals:

**S1. Sector divergence.**
- A cluster has a *dominant sector* if one sector has strictly more members than any other, and at least 2 members.
- A firm in such a cluster whose sector differs is *divergent* in that run.
- **S1 = 1** if the firm is divergent in at least 4 of 5 seeds.
- Firms in singleton clusters, or in clusters with no dominant sector, get S1 = 0, and this is recorded.

**S2. Multivariate outlier (Hotelling's T²).**
- T² = (x − x̄)ᵀ S⁻¹ (x − x̄), using that date's mean and covariance.
- The critical value is p(n−1)/(n−p) · F₀.₉₅(p, n−p), at α = 0.05. This is the SACJ rule: n = 40 and p = 2 give 6.66.
- **Primary space:** the p = 10 scaled features (critical value 27.78 for n = 41) (decided).
  - Rationale for the feature space: distances in a t-SNE map have no distributional meaning, and the feature-space version does not depend on the model or the seed.
- **Sensitivity:** the SACJ 2-D-map version, flagged if it exceeds the threshold in at least 4 of 5 seeds; α = 0.01 and 0.10.
- The T² feature decomposition, Σₖ cₖ(S⁻¹c)ₖ, is reported for every flagged firm.

**Combined:** S∨ = S1 or S2. **Multi-signal** = S1 and S2 at the same date. The most compelling cases are those where several signals agree.

## 9. Anomaly-dynamics taxonomy (fixed now, applied to S1, S2 and S∨ separately)

For a firm present at all three dates, with signal state N (0) or A (1) at *t*₁, *t*₂ and *t*₃:

| Pattern | Class |
|---|---|
| N N N | No signal |
| N N A | **Emerging** |
| N A A | **Emerging and sustained** |
| A A A | **Persistent** |
| A A N | **Resolving** |
| A N N | **Resolved** |
| N A N | **Transient** |
| A N A | **Recurrent** (not in the original list; added so that every pattern is covered) |

- Firms absent at any date are labelled *partial history*. Their observed states are reported, but they are not classified.
- Results for imputation-sensitive firms are marked.
- **Peer-group moves are reported alongside the class but never define it.**

## 10. Explaining transitions (SHAP)

1. **Surrogate:** an XGBoost classifier at each date (fixed settings), trained on the raw features to predict that date's cluster labels.
   - Fidelity is reported as in-sample accuracy and stratified out-of-fold accuracy.
   - Out-of-fold accuracy is also reported with singleton clusters excluded, or marked "not estimable".
2. **Cluster profile:** global and per-cluster mean |SHAP|, and beeswarm plots.
3. **Transition attribution:** for each robust move, and for every firm with an S1 or S2 signal at any date:
   - Apply the *t*₁ surrogate (valid because scaling is frozen) to the firm's *t*₁ and later feature vectors.
   - Compute ΔSHAP = SHAP(later) − SHAP(*t*₁), towards the firm's *t*₁ cluster and towards its destination. The destination is the *t*₁ cluster that holds most of its current peers.
   - Report the change in each raw feature alongside.
4. **Sector divergence:** SHAP(assigned cluster) − SHAP(the cluster holding most of the firm's sector peers).
5. **Language:** "is associated with" or "accompanies", never "caused" or "drove".

## 11. Data provenance and what has already been seen (disclosure)

The following were produced on the **v1 reconstructed data** before this protocol was written:
- the archived runs in `experiments/runs/`;
- the bounded optimisation search (`silhouette-db-search-01`, June 2025 only);
- a full exploratory grid search on all three dates.

The authors have therefore seen results on v1, including:
- seed ARI;
- sector ARI;
- which firms were sector-divergent;
- that t-SNE-map T² flags no firms;
- that, in the feature space, unreduced Ward clustering ranks first among the k = 8 models.

The eligibility rules in Section 6 were written after the v1 June 2025 grid showed that unconstrained ranking picks degenerate partitions.

Consequences:
- **All v1 analyses are exploratory (pilot)** and will be reported as such.
- **Confirmatory results** are only those produced by this frozen protocol on the **v2 point-in-time dataset**. That dataset is built after freezing, to the rules in Sections 2–5.
- **Blind confirmation (decided).** *t*₄ = 31 December 2026 is pre-registered. At the time of freezing it is in the future, so nobody can have seen its data. After that date, its data is pulled under Sections 2–5, and the frozen *t*₁ method with k = 8 is applied unchanged. These are reported as a separate confirmation:
  - signal states at *t*₄;
  - taxonomy classes extended to four dates, where *t*₂–*t*₄ is classified with the same table;
  - cluster matching from *t*₃ to *t*₄.

## 12. Change log

| Version | Date | Change | Reason |
|---|---|---|---|
| 0.1 | 2026-11-08 | Draft | — |
| 0.2 | 2026-11-08 | Analyst rating dropped; 10 features | It cannot be reconstructed as of each decision date without look-ahead |
| 0.3 | 2026-11-08 | Return = price return | Avoids double-counting dividend yield (feature 9); chosen on that principle, not on model scores |
| 1.0 | 2026-11-08 | Frozen. Method selected at *t*₁ and fixed; k = 8 at all dates (free k as a diagnostic only); Listcorp 8 sectors, no ICB; matching threshold J ≥ 0.30; T² primary space = 10 features; *t*₄ = 31 Dec 2026 blind confirmation | Author decisions: shifts are measured relative to the eight-sector ground truth |
