# Research protocol: repeated cross-sectional screening of the JSE Top 40

**Status: FROZEN v1.1 (tag `protocol-v1.1`, 2026-11-08), amending frozen v1.0 (tag `protocol-v1`).** The amendments are marked **[v1.1]**, and the reasons are given in the change log (Section 12).
The v1.1 changes were made **before any v2 (point-in-time) data existed**, and were approved by the author on 2026-11-08.
Any later change is made in a new, dated version with the reason recorded. Results produced under an earlier version are never relabelled as confirmatory.

## 1. Purpose and claim

The study develops an interpretable, repeated cross-sectional decision-support framework. The framework:
- separates transient, emerging, persistent and resolving structural signals within an investable equity universe;
- attributes changes in peer relationships to changes in the firms' underlying financial characteristics.

**What the design supports:** the framework is **replicated across three market states** (decision dates).

**What it does not support:**
- The sample is not *n* = 120 (or 123) independent observations. Each date has about 40 firms. Most firms recur across dates, and the trailing 12-month market windows of adjacent dates overlap by six months.
- Results are descriptive screening signals, not predictions, investment recommendations or causal effects.

**[v1.1] Dimension reduction is tested, not assumed.** The model-selection experiment (Section 6) compares no reduction, PCA, t-SNE and UMAP, combined with several clustering methods, linkages and distances. Its result is reported whichever method wins. The SACJ t-SNE pipeline is kept as a replication baseline. If it does not win, that is itself a reported finding, and the framework does not depend on t-SNE.

## 2. Decision dates and information rule

| | Decision date |
|---|---|
| *t*₁ | 30 June 2025 |
| *t*₂ | 31 December 2025 |
| *t*₃ | 30 June 2026 |
| *t*₄ | 31 December 2026: **pre-registered blind confirmation date** (Section 11). Its data is pulled only after that date. |

These are decision dates, not six-month aggregation periods. At each date *t*:

1. **Market measures** use daily data in the trailing 12-month window ending on *t* (Section 4).
2. **[v1.1] Fundamentals** (revenue and EPS) come from the issuer's latest **audited annual results** whose results announcement (SENS) date is on or before *t*.
   - Interim results are not used. Firms have different year-ends, and a trailing-12-month figure would need two consistent interim periods for every firm.
   - Restated figures published after *t* are not used.
   - **Consequence:** a firm's fundamentals change only when it publishes a new annual result, so between adjacent dates some firms' fundamentals are unchanged. Any change for those firms comes from market data alone. Each record carries the announcement date and the financial year-end used.
3. **Index membership** is the FTSE/JSE Top 40 constituent list effective at the close on *t*.
4. **Sector** is the legacy Listcorp label (Section 4), checked against a dated source where possible.

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
| 1 | 1-year return | Split-adjusted **price return**, close(*t*) / close(*t* − 12 m) − 1, dividends excluded. Total return ≈ price return + dividend yield, and dividend yield is already feature 9. Total return would therefore count the dividend component twice and add correlation. | 12 m to *t* |
| 2 | Average volume | Mean daily traded shares | 12 m to *t* |
| 3 | Market cap | Close(*t*) in ZAR × shares in issue at *t* | at *t* |
| 4 | Beta | OLS slope of daily returns on J203 (All Share) daily returns | 12 m to *t* |
| 5 | Shares outstanding | **[v1.1]** Total shares in issue as published by the JSE/issuer in the latest monthly figure on or before *t* | at *t* |
| 6 | Revenue | **[v1.1]** From the annual results in rule 2.2, converted to ZAR at the spot exchange rate on *t* (the rate is recorded).<br>• **Non-financial firms:** IFRS revenue.<br>• **Banks:** total income = net interest income + non-interest revenue.<br>• **Insurers:** insurance revenue (IFRS 17) + net investment income.<br>• **Investment holding companies:** total income as presented; if no meaningful line exists, missing (Section 5).<br>The basis used is stored per firm in a `revenue_basis` column. | latest annual by *t* |
| 7 | EPS | **[v1.1]** Statutory **diluted EPS** (total operations) from the same annual results, converted to ZAR at the spot rate on *t*. Losses stay negative. Headline EPS is recorded but not used. | latest annual by *t* |
| 8 | Volatility | Sample SD of daily simple returns × √252 | 12 m to *t* |
| 9 | Dividend yield | **[v1.1]** Gross cash dividends per share with ex-date in the trailing 12 m (in ZAR) / close(*t*) | 12 m to *t* |
| 10 | Earnings yield | EPS / close(*t*). This **replaces P/E**, which is undefined or explodes for loss-makers. Clipped at the *t*₁ 1st/99th percentiles. | at *t* |
| — | ~~Analyst consensus rating~~ | **Dropped.** An as-of-date historical consensus cannot be reliably reconstructed, and a rating looked up today would introduce look-ahead. | — |

Sector is **never** a model input. It is used only to interpret and validate the clusters.

**Sector scheme:** the legacy **eight Listcorp sector labels**, kept the same at every date, for comparability with SACJ. ICB is not used.
- Each firm's label at each date is checked against a dated source where possible.
- Labels that can't be verified are flagged.

## 5. Missing data and preprocessing

1. Raw values are never overwritten. Model-only fills go in separate columns, each with a flag.
2. **Imputation:** the *t*₁ cross-sectional median, applied at all dates, flagged. Results for imputed firms are labelled *imputation-sensitive*.
3. **Clipping:** earnings yield only, at the *t*₁ 1st/99th percentiles.
4. **Scaling:** MinMax, fitted on *t*₁ and frozen, so later values may leave [0, 1]. Freezing keeps one common feature space, which is what makes the frozen-surrogate SHAP comparison in Section 10 valid.

**Sensitivity analyses:**
- scaling refitted at each date;
- **[v1.1] log size:** log₁₀ of market cap, shares, average volume and revenue before MinMax scaling. The four size features are heavily right-skewed, so a few mega-caps dominate the distances and T². The selected method is reapplied unchanged, and the agreement of signal states and taxonomy classes with the primary analysis is reported.

## 6. Model selection

**Search space:**
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

**Application:**
- The method is selected **once, at *t*₁** (30 June 2025), by the rule above, among k = 8 configurations. The method means the reduction and its settings, the clustering algorithm, the linkage and the distance.
- That method is then refitted **unchanged** at each later date, with **k = 8 fixed** at every date.
- The study measures shifts relative to the eight-sector ground truth. A fixed method and fixed k mean that differences between dates reflect the data, not changes in the model.

**[v1.1]** The eligibility rules apply at *t*₁ only. At later dates the number of singleton clusters is not constrained. Instead it is reported for each date as a **structural observation**; a rising count means firms are becoming isolated.

Fixing k could make the structure look more stable than it is. To address this, the **best-supported k at each date** is computed with the same ranking (k = 2–10) and reported **as a diagnostic only**. It never replaces k = 8.

**Sensitivity analyses, always reported:**
- the free-k diagnostic above;
- the SACJ baseline (t-SNE perplexity 5, learning rate 10, 300 iterations; average linkage, Manhattan distance; k = 8);
- the winner under alternative eligibility thresholds (singletons 0/1/2; largest cluster 40/50/60%; seed ARI 0.7/0.8/0.9).

### 6.1 [v1.1] Stability under data perturbation

Seed variation tests only the algorithm's randomness. If the selected method is deterministic, the "≥ 4 of 5 seeds" rules of v1.0 would pass automatically. Every firm-level robustness rule in Sections 7–8 therefore uses **perturbation runs**:

- At each date, draw **B = 100 subsamples of 37 of the 41 firms** (90%) without replacement.
  - The random generator is fixed: `numpy.random.default_rng(20251108)`. The draws are made in date order, and B draws per date.
- Refit the selected method on each subsample. Use the frozen *t*₁ scaler, k = 8, and seed 42 + (b mod 5) for any stochastic step. Each run therefore varies both the data and the seed.
- A firm-level property is **robust** if it holds in **≥ 80%** of the runs in which the firm is included. For properties that involve two dates, the run uses subsample b at both dates.
- The v1.0 five-seed full-sample results are also reported.

## 7. Cluster matching across dates (reproducible; sector plays no part)

Matching is between adjacent dates (*t*₁→*t*₂, *t*₂→*t*₃), plus *t*₁→*t*₃ for "base to current". Only firms present at both dates are used.

1. **Primary similarity:** the Jaccard overlap of membership, J(i, j) = |Cᵢ ∩ Dⱼ| / |Cᵢ ∪ Dⱼ|, for every cluster i at *t* and every cluster j at *t*+1.
2. **Assignment:** the Hungarian algorithm maximises total J.
3. **Acceptance:** a matched pair counts as "the same cluster" only if J ≥ **0.30**. Clusters left unmatched are *dissolved* (at *t*) or *new* (at *t*+1).
4. **Split and merge:**
   - A cluster at *t* with J ≥ 0.30 to two or more clusters at *t*+1 is a *split*.
   - The reverse case, two or more clusters at *t* with J ≥ 0.30 to one cluster at *t*+1, is a *merge*.
5. **Secondary matching (sensitivity):**
   - Use the Hungarian algorithm on the Euclidean distance between cluster median profiles in the frozen scaled feature space.
   - Report how often the two matchings agree.
6. **[v1.1]** Cluster-level matches and events are reported for the full-sample fit. Their frequency across the perturbation runs (Section 6.1) is also given.
7. **Firm transition:** a firm *moves* if its cluster at *t*+1 is not the accepted match of its cluster at *t*.
   - **[v1.1]** It is a **robust move** if this holds in ≥ 80% of the perturbation runs in which it is present at both dates.
   - A label-free check (peer-set Jaccard compared with same-date noise) is reported as a sensitivity.

A move in peer group is a **structural change, not an anomaly**.

## 8. Firm-level signals (binary, at each date)

Three separate signals:

**S1. Sector divergence.**
- A cluster has a *dominant sector* if one sector has strictly more members than any other, and at least 2 members.
- A firm in such a cluster whose sector differs is *divergent* in that run.
- **[v1.1] S1 = 1** if the firm is divergent in ≥ 80% of the perturbation runs.
- Firms in clusters with no dominant sector get S1 = 0, and this is recorded.

**[v1.1] S3. Isolation.**
- **S3 = 1** if the firm is alone in its cluster in the full-sample fit **and** in ≥ 80% of the perturbation runs.
- Isolation is the most extreme form of not grouping with one's sector (GLN in the SACJ study). It is a signal in its own right, not "no divergence".
- For an isolated firm, S1 is undefined and recorded as such.

**S2. Multivariate outlier (Hotelling's T²).**
- T² = (x − x̄)ᵀ S⁻¹ (x − x̄), using that date's full-sample mean and covariance.
- The critical value is p(n−1)/(n−p) · F₀.₉₅(p, n−p), at α = 0.05. This is the SACJ rule: n = 40 and p = 2 give 6.66.
- **Primary space:** the p = 10 scaled features (critical value 27.78 for n = 41). Distances in a t-SNE map have no distributional meaning, and the feature-space version does not depend on the model or the seed.
- **[v1.1] Continuous evidence:** for every firm and date, the ratio T² / critical value is reported. A state is **borderline** if the ratio lies in [0.9, 1.1); taxonomy classes that rest on a borderline state are marked.
- **[v1.1] Chance flags:** with n = 41 and α = 0.05, about 2 firms per date are expected to cross the threshold by chance alone. This is stated next to every count of flags. A Bonferroni sensitivity (α = 0.05 / 41) is reported.
- **[v1.1] Masking:** large outliers inflate S and can hide one another. As a robust sensitivity:
  - compute robust squared distances from the minimum covariance determinant (`sklearn.covariance.MinCovDet`, `random_state = 42`);
  - flag a firm if its distance exceeds χ²₀.₉₅(p).
- **Other sensitivities:** the SACJ 2-D-map version (flagged in ≥ 4 of 5 seeds); α = 0.01 and 0.10; the log-size space (Section 5).
- The T² feature decomposition, Σₖ cₖ(S⁻¹c)ₖ, is reported for every flagged firm.

**Combined:** S∨ = S1 or S2 or S3. **Multi-signal** = two or more of S1, S2 and S3 at the same date. The most compelling cases are those where several signals agree.

## 9. Anomaly-dynamics taxonomy (applied to S1, S2, S3 and S∨ separately)

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
| A N A | **Recurrent** (added so that every pattern is covered) |

- Firms absent at any date are labelled *partial history*. Their observed states are reported, but they are not classified.
- Results for imputation-sensitive firms are marked. Classes resting on a borderline T² state are marked.
- **Peer-group moves are reported alongside the class but never define it.**
- **[v1.1] Overlapping windows:**
  - Adjacent dates share six months of the market window, and may share the same annual fundamentals. Persistence between adjacent dates is therefore partly mechanical.
  - *t*₁ and *t*₃ have **non-overlapping** 12-month windows. Firms in state A at both *t*₁ and *t*₃ (classes Persistent and Recurrent) are reported separately as the **cleanest evidence of persistence**.

## 10. Explaining transitions (SHAP)

1. **Surrogate:** an XGBoost classifier at each date (fixed settings), trained on the raw features to predict that date's cluster labels.
   - Fidelity is reported as in-sample accuracy and stratified out-of-fold accuracy.
   - Out-of-fold accuracy is also reported with singleton clusters excluded, or marked "not estimable".
2. **Cluster profile:** global and per-cluster mean |SHAP|, and beeswarm plots.
3. **Transition attribution:** for each robust move, and for every firm with an S1, S2 or S3 signal at any date:
   - Apply the *t*₁ surrogate (valid because scaling is frozen) to the firm's *t*₁ and later feature vectors.
   - Compute ΔSHAP = SHAP(later) − SHAP(*t*₁), towards the firm's *t*₁ cluster and towards its destination. The destination is the *t*₁ cluster that holds most of its current peers.
   - Report the change in each raw feature alongside.
   - **[v1.1] Range flag:** a tree surrogate treats any value outside its training range as if it were at the edge of that range. If a later value lies outside the *t*₁ minimum–maximum of that feature, its attribution is flagged *outside training range* and may be understated.
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
- that, in the feature space, unreduced Ward clustering ranks first among the k = 8 models, and that its number of singleton clusters rises across dates.

Two rules were influenced by these results:
- the eligibility rules in Section 6, which were written after the v1 June 2025 grid showed that unconstrained ranking picks degenerate partitions;
- the v1.1 isolation signal S3, which was prompted partly by the rising singleton count, and partly by SACJ's GLN finding.

All other v1.1 changes follow from design reasoning (Section 12).

Consequences:
- **All v1 analyses are exploratory (pilot)** and will be reported as such.
- **Confirmatory results** are only those produced by this frozen protocol on the **v2 point-in-time dataset**. That dataset is built after freezing, to the rules in Sections 2–5.
- **Blind confirmation.** *t*₄ = 31 December 2026 is pre-registered. At the time of freezing it is in the future, so nobody can have seen its data. After that date, its data is pulled under Sections 2–5, and the frozen *t*₁ method with k = 8 is applied unchanged. These are reported as a separate confirmation:
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
| 1.1 | 2026-11-08 | (a) Perturbation stability (Section 6.1) replaces seed-only robustness | Seed rules pass automatically for a deterministic method |
| | | (b) Isolation signal S3; singletons unconstrained after *t*₁ and reported | A singleton is the strongest non-sector grouping and was miscounted as S1 = 0 (partly prompted by the pilot; see Section 11) |
| | | (c) Fundamentals, shares, revenue basis, currency conversion and dividend definitions pinned down | v1.0 left "annual or interim" and the bank/insurer revenue basis open |
| | | (d) Log-size sensitivity | Skewed size features let mega-caps dominate distances and T² |
| | | (e) T² ratio and borderline marking; expected chance flags; Bonferroni and MCD sensitivities | Threshold flips, multiple testing and masking with n = 41, p = 10 |
| | | (f) Overlapping-window caveat; *t*₁–*t*₃ persistence as the cleanest test | Adjacent dates share six months of market data |
| | | (g) SHAP outside-training-range flag | Tree surrogates treat values beyond the training range as if at its edge, so attributions saturate |
| | | (h) Dimension reduction stated as tested, not assumed | Author: the finding may change, and the framework need not rely on t-SNE |
