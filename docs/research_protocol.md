# Research protocol: repeated cross-sectional screening of the JSE Top 40

**Status: FROZEN v1.2 (tag `protocol-v1.2`, 2026-11-08, approved by the author), amending v1.1 (tag `protocol-v1.1`) and v1.0 (tag `protocol-v1`).**
v1.1 was frozen on 2026-11-08 and is **superseded**: an independent review found that its T² error-rate and Bonferroni statements are wrong (Section 12).
Amendments are marked **[v1.2]** (new) or **[v1.1]** (kept from v1.1). No v2 (point-in-time) data exist yet.
Git tags are version labels, not external pre-registration. No external registration has been made (Section 11).
Any later change is made in a new, dated version with the reason recorded. Results produced under an earlier version are never relabelled.

## 1. Purpose and claim

The study develops an interpretable, repeated cross-sectional decision-support framework. The framework:
- separates transient, emerging, persistent and resolving structural signals within an investable equity universe;
- describes the financial characteristics *associated with* changes in peer relationships.

**[v1.2] What the design supports:** the framework is applied at **three decision-date cross-sections**. These are not defined market regimes.

**What it does not support:**
- The repeated cross-sections are not an independently enlarged sample (not *n* = 120 or 123). Each date has about 40 firms. Most firms recur across dates, many share the same annual accounts between adjacent dates, and the trailing 12-month market windows of adjacent dates overlap by six months.
- Results are descriptive screening signals. They are not predictions, investment recommendations or causal attributions.
- **[v1.2]** Fixed hyperparameters remove repeated model selection, not all variability. Refitted memberships depend on the data and on any fitting randomness. The perturbation runs (Section 6.1) assess how robust they are.

**[v1.1] Dimension reduction is tested, not assumed.** The model-selection experiment (Section 6) compares no reduction, PCA, t-SNE and UMAP, combined with several clustering methods, linkages and distances. Its result is reported whichever method wins. The SACJ t-SNE pipeline is kept as a replication baseline. If it does not win, that is itself a reported finding, and the framework does not depend on t-SNE.

## 2. Decision dates and information rule

| | Decision date |
|---|---|
| *t*₁ | 30 June 2025 |
| *t*₂ | 31 December 2025 |
| *t*₃ | 30 June 2026 |
| *t*₄ | 31 December 2026: **prospective follow-up date** (Section 11) |

These are decision dates, not six-month aggregation periods. At each date *t*:

1. **Market measures** use daily data in the trailing 12-month window ending on *t* (Section 4).
2. **[v1.1] Fundamentals** (revenue and EPS) come from the issuer's latest **audited annual results** available on or before *t*.
   - Interim results are not used. Firms have different year-ends, and a trailing-12-month figure would need two consistent interim periods for every firm.
   - Restated figures published after *t* are not used.
   - **[v1.2] Availability date** is the publication date of the source document actually used. If the figures are taken from an annual report published after the results announcement, the report's date applies, not the announcement's.
   - **[v1.2]** If a firm publishes no new annual results between dates, its **source accounting figures** are unchanged. Its model values can still change, through the exchange rate (rule 4.6) and through corporate actions (rule 2.5). Each record carries the availability date, the financial year-end, the native-currency amounts and the conversion details.
3. **Index membership** is the FTSE/JSE Top 40 constituent list effective at the close on *t*.
4. **[v1.2] Sector** is the legacy Listcorp label (Section 4), used as an **external comparator**. It is not a verified ground truth. Each label carries an evidence flag (*verified at t* / *unverified*).
5. **[v1.2] Instrument and per-share basis.** For every instrument at every *t*, record:
   - ISIN, share class, quote unit (ZAc or ZAR; ZAc is divided by 100) and, for depositary receipts, the receipt-to-ordinary-share ratio;
   - every split, consolidation and share-basis change with an effective date on or before *t*.

   All per-share and count measures are put on the **share basis in effect at *t***:
   - EPS and dividends per share are multiplied by the cumulative adjustment factor of events effective after the period they relate to and on or before *t*. The factor and its source are recorded. A firm may therefore need an EPS adjustment even when it publishes no new results.
   - Daily volumes and prices in the trailing window are adjusted to the same basis.
   - Events effective after *t* are never applied.

Every value records its source, its availability date and an evidence flag. A value that cannot be shown to have been available at *t* is treated as missing (Section 5).

> **Known gap.** The current dataset (`Top40_Retrospective_Model_Inputs_v1`) is a retrospective reconstruction:
> - later restatements are permitted;
> - shares and sector labels are unverified;
> - market data are not archived as-of extracts;
> - no per-instrument share-basis audit has been done (for example, the NPN share-count change is unexplained).
>
> It does **not** meet rules 2–5. A protocol-compliant data pull (v2) is required. See Section 11.

## 3. Universe

- All Top 40 constituents at each *t*, at instrument level. **[v1.2]** The two Investec lines (Ltd and plc) are separate instruments. Each uses the shares in issue of **its own listed entity**, never the combined DLC count. Their close economic link is disclosed, and results are reported with and without one of the two lines (Section 8).
- No firm is dropped for missing data. Section 5 sets out how gaps are handled.
- Entries and exits between dates are **membership events**. They are reported separately and never counted as cluster changes or anomalies.
- Taxonomy classification (Section 9) needs a firm to be present, **with a defined signal state**, at all three dates. Other firms are reported with their observed pattern and the label *partial history* or *undefined state*.

## 4. Features

The SACJ study used 11 features. This study uses **10**, with two departures:
- P/E is replaced by earnings yield (row 10);
- the analyst rating is dropped (last row).

The paper must state both departures, since they make the results not directly comparable with SACJ's 11-feature space.

| # | Feature | Definition | Window / source |
|---|---|---|---|
| 1 | 1-year return | Split-adjusted **price return**, close(*t*) / close(*t* − 12 m) − 1, dividends excluded. Total return ≈ price return + dividend yield, and dividend yield is already feature 9. Total return would therefore count the dividend component twice and add correlation. If *t* − 12 m is not a trading day, the last close before it is used. | 12 m to *t* |
| 2 | Average volume | Mean daily traded shares, on the basis in effect at *t*, over trading days with a recorded close. Non-trading days are excluded, not counted as zero, and their number is recorded. | 12 m to *t* |
| 3 | Market cap | Close(*t*) in ZAR × shares in issue at *t*. The price and the share count must refer to the same security and unit (rule 2.5). | at *t* |
| 4 | Beta | OLS slope of daily returns on J203 (All Share) daily returns, over days on which both have a close | 12 m to *t* |
| 5 | Shares outstanding | **[v1.2]** Total **shares in issue** of the listed entity (issued, not reduced for treasury shares), from the latest monthly JSE/issuer figure on or before *t*. If a treasury-adjusted count is available, it is recorded but not used. | at *t* |
| 6 | Revenue | **[v1.1]** From the annual results in rule 2.2, converted to ZAR (rule 4.6).<br>• **Non-financial firms:** IFRS revenue.<br>• **Banks:** total income = net interest income + non-interest revenue.<br>• **Insurers:** insurance revenue (IFRS 17) + net investment income.<br>• **Investment holding companies:** total income as presented; if no meaningful line exists, missing (Section 5).<br>The basis used is stored per firm in a `revenue_basis` column. | latest annual by *t* |
| 7 | EPS | **[v1.1]** Statutory **diluted EPS** (total operations) from the same annual results, converted to ZAR (rule 4.6) and to the share basis at *t* (rule 2.5). Losses stay negative. Headline EPS is recorded but not used. | latest annual by *t* |
| 8 | Volatility | Sample SD of daily simple returns × √252 | 12 m to *t* |
| 9 | Dividend yield | **[v1.2]** Gross cash dividends per share with an ex-date in the trailing 12 m, on the basis at *t*, in ZAR at the exchange rate on each ex-date, / close(*t*). **Special dividends are included and flagged.** A sensitivity excludes them. Distributions in kind are excluded and recorded. | 12 m to *t* |
| 10 | Earnings yield | EPS / close(*t*). This **replaces P/E**, which is undefined or explodes for loss-makers. Clipped at the *t*₁ 1st/99th percentiles. | at *t* |
| — | ~~Analyst consensus rating~~ | **Dropped.** An as-of-date historical consensus cannot be reliably reconstructed, and a rating looked up today would introduce look-ahead. | — |

**4.6 [v1.2] Currency.** Native-currency revenue and EPS are stored. They are converted to ZAR at the spot rate on *t* (the rate and its source are recorded). For firms whose source figures did not change between dates, the change in the ZAR value caused by the exchange rate alone is reported separately.

Sector is **never** a model input. It is used only to interpret and compare the clusters.

**Sector comparator:** the legacy **eight Listcorp sector labels**, kept the same at every date, for comparability with SACJ. ICB is not used. **[v1.2]** Choosing k = 8 to match eight sector categories does not imply that a cluster *should* equal a sector.

## 5. Missing data and preprocessing

1. Raw values are never overwritten. Model-only fills go in separate columns, each with a flag.
2. **Imputation:** the *t*₁ cross-sectional median, applied at all dates, flagged. Results for imputed firms are labelled *imputation-sensitive*.
3. **Clipping:** earnings yield only, at the *t*₁ 1st/99th percentiles.
4. **Scaling:** MinMax, fitted on *t*₁ and frozen, so later values may leave [0, 1]. Freezing keeps one common clustering geometry across dates.
5. **[v1.2] Order:** clip → impute → (log, sensitivity only) → scale, with every constant fitted on *t*₁.
6. **[v1.2] Failure rule:** if a feature is entirely missing or constant at *t*₁, the analysis stops and the protocol is amended. No firm or feature is silently dropped, and no substitute transform is applied.

**Sensitivity analyses:**
- scaling refitted at each date;
- **[v1.2] log size:**
  - log₁₀ of market cap, shares, average volume and revenue, applied before imputation (the frozen *t*₁ median is then taken on the log scale) and before scaling;
  - a non-positive value has no log₁₀. It is set to missing for this sensitivity only, imputed by rule 2 and flagged. log1p is not used;
  - the selected method is reapplied unchanged, and the agreement of signal states and taxonomy classes with the primary analysis is reported.

## 6. Model selection

**Search space:**
- **Dimension reduction:** none (the scaled features directly); PCA (2 components, or 95% of variance); t-SNE (perplexity 5/10/20 × learning rate 10/auto × 300/1000 iterations × Euclidean/Manhattan input distance); UMAP (3/5/10/20 neighbours × min_dist 0/0.1/0.5 × Euclidean/Manhattan input distance).
- **Clustering:**
  - hierarchical: single, complete and average linkage, each with Euclidean, Manhattan or cosine distance, plus Ward with Euclidean;
  - K-Means with 20 random starts;
  - **[v1.2] DBSCAN** (eps 0.3/0.5/0.8/1.2 × min_samples 2/3/5, on standardised coordinates) is fitted and reported **as a comparator only**. It is **not eligible** as the primary method: it chooses its own number of clusters, so unchanged parameters cannot keep k = 8 at later dates, and retuning eps would break the unchanged-method rule. For DBSCAN, seed ARI is computed on firms that are non-noise in both seeds, and that coverage is reported.
- **k:** 2–10.
- **Seeds:** 42–46 for every stochastic step.

**Quality:**
- Silhouette and Davies–Bouldin, each computed **in the common scaled feature space** (the basis for selection) and in the embedding (reported only). Embedding scores are not comparable across reduction methods.
- Each score is averaged over the five seeds.

**[v1.2] Eligibility.** All five rules must hold **on every one of the five seeds** at *t*₁:
1. the fit succeeds and gives a valid partition (at least 2 clusters, fewer clusters than firms);
2. at least 95% of firms are assigned (non-noise);
3. the mean pairwise seed ARI is ≥ 0.80 (one number across seeds);
4. at most one singleton cluster;
5. no cluster holds more than 50% of **all firms at that date** (noise included in the denominator).

A failed fit on any seed makes the configuration ineligible.
Rules 4–5 exist because isolating outliers is the job of the S2 signal (Section 8). The clustering must form peer groups.

**Ranking:**
- Add the silhouette rank and the DB rank, both in feature space. The lowest sum wins.
- Ties go to the higher seed ARI, then the higher silhouette, then the configuration listed first in the grid order of Section 6.
- **[v1.2] If no configuration is eligible**, the selection is repeated with rules 4 and 5 dropped. The result is flagged and reported as a deviation.

**Application:**
- The method is selected **once, at *t*₁** (30 June 2025), by the rule above, among k = 8 configurations. The method means the reduction and its settings, the clustering algorithm, the linkage and the distance.
- That method is then refitted **unchanged** at each later date, with **k = 8 fixed** at every date.
- The study measures shifts relative to the eight-sector comparator. A fixed method and fixed k mean that no repeated parameter choice enters the differences between dates.

**[v1.1]** The eligibility rules apply at *t*₁ only. At later dates the number of singleton clusters is not constrained. **[v1.2]** It is reported for each date as a **structural observation, conditional on the fitted method**. A rising count does not by itself establish economic isolation: membership changes, data revisions, imputation and fitting variability can also produce it.

Fixing k could make the structure look more stable than it is. To address this, the **best-supported k at each date** is computed with the same ranking (k = 2–10) and reported **as a diagnostic only**. It never replaces k = 8.

**Sensitivity analyses, always reported:**
- the free-k diagnostic above;
- the SACJ baseline (t-SNE perplexity 5, learning rate 10, 300 iterations; average linkage, Manhattan distance; k = 8);
- the winner under alternative eligibility thresholds (singletons 0/1/2; largest cluster 40/50/60%; seed ARI 0.7/0.8/0.9).

### 6.1 [v1.1, made executable in v1.2] Stability under data perturbation

Seed variation tests only the algorithm's randomness. If the selected method is deterministic, seed-based rules would pass automatically. Every firm-level robustness rule in Sections 7–8 therefore uses **perturbation runs**.

**Draws:**
- At each date, instruments are sorted by ticker. Let *n* be that date's number of instruments, and *m* = ⌈0.9 *n*⌉ (37 when *n* = 41).
- One generator, `rng = numpy.random.default_rng(20251108)`, is used for all draws. For each date in order *t*₁, *t*₂, *t*₃ (and *t*₄ later, from a new generator `default_rng(20261231)`), and for b = 0, …, 99, the subsample is `sorted(rng.choice(n, size=m, replace=False))`.
- Run b refits the selected method on its subsample. It uses the frozen *t*₁ preprocessing, k = 8 and seed 42 + (b mod 5) for any stochastic step.
- Every draw is stored: date, b, included tickers, seed, success status, labels.

**Robustness and failure:**
- A failed fit (for example, fewer than k distinct clusters) is recorded and excluded from the denominator.
- A firm-level property is reported as a **stability proportion**: the number of successful runs in which it holds, divided by the number of successful runs in which it is evaluable. It is **robust** if that proportion is ≥ 0.80. This is a stability threshold, not a confidence level or error rate.
- If fewer than 20 runs are evaluable for a firm, the property is *not estimable*.

**Paired dates:**
- The subsamples are drawn independently at each date and **paired by b**.
- A two-date property is evaluated for a firm in run b only if the firm is included at both dates.
- This is not the same as sampling a common set of continuing firms. The choice is fixed here.

The five-seed full-sample results are also reported.

## 7. Cluster matching across dates (reproducible; sector plays no part)

Matching is between adjacent dates (*t*₁→*t*₂, *t*₂→*t*₃), plus *t*₁→*t*₃ for "base to current".

1. **[v1.2] Primary similarity:** the Jaccard overlap computed on **continuing firms only** (present at both dates), in both numerator and denominator: J(i, j) = |Cᵢ ∩ Dⱼ| / |Cᵢ ∪ Dⱼ|, where Cᵢ and Dⱼ are restricted to continuing firms.
2. **[v1.2] Assignment:**
   - Set every J < 0.30 to 0. A cluster can therefore only be matched through an accepted edge.
   - Solve the maximum-weight one-to-one assignment with `scipy.optimize.linear_sum_assignment` (maximise). Ties are resolved by its deterministic order, with clusters numbered by size and then by lowest member ticker.
   - Discard assigned pairs with J = 0. This equals the maximum-weight matching using accepted edges only.
3. **[v1.2] Events:**
   - A cluster whose members all left the index is *exited*.
   - Otherwise, an unmatched cluster at *t* is *dissolved*, and an unmatched cluster at *t*+1 is *new*.
4. **Split and merge** are a **separate relation**, not part of the one-to-one assignment:
   - A cluster at *t* with J ≥ 0.30 to two or more clusters at *t*+1 is a *split*.
   - The reverse case, two or more clusters at *t* with J ≥ 0.30 to one cluster at *t*+1, is a *merge*.
5. **Secondary matching (sensitivity):**
   - Use the Hungarian algorithm on the Euclidean distance between cluster median profiles in the frozen scaled feature space.
   - Report how often the two matchings agree.
6. **[v1.2] Perturbation support for cluster events:**
   - In each run, each perturbed cluster is first related to a full-sample cluster at the same date. Use the rule-2 matching on the firms included in that run.
   - A full-sample match, split or merge is then *supported* in run b if the same relation holds between the related perturbed clusters.
   - Its stability proportion is reported.
7. **Firm transition:** a firm *moves* if its cluster at *t*+1 is not the accepted match of its cluster at *t* (including when that cluster dissolved).
   - **[v1.1]** It is a **robust move** if this holds in ≥ 80% of the evaluable perturbation runs (Section 6.1).
   - **[v1.2] Label-free check (descriptive only):** for each continuing firm, report the Jaccard overlap between its full-sample peer sets (continuing firms only) at *t* and *t*+1. Alongside it, report the median of the same statistic between the full-sample fit and each perturbation run at the same date. No threshold or classification is applied to this check.

A move in peer group is a **structural change, not an anomaly**.

## 8. Firm-level signals (at each date; each takes the value 1, 0 or NA)

Three separate signals.

**S1. Sector divergence.**
- A cluster has a *dominant sector* if one sector has strictly more members than any other, and at least 2 members.
- A firm in such a cluster whose sector differs is *divergent* in that run.
- **S1 = 1** if the firm is divergent in ≥ 80% of the evaluable perturbation runs.
- **[v1.2] S1 = 0** means *no detected dominance-based divergence*. It does not mean the cluster is sector-coherent. The reason is recorded: *aligned*, *no dominant sector*, or *not robust*.
- **[v1.2] S1 = NA** when it does not apply. The reason is recorded separately:
  - *structural*: the firm is isolated (S3 = 1);
  - *data*: the firm's sector label is unavailable at *t*.

**[v1.1] S3. Isolation.**
- **S3 = 1** if the firm is alone in its cluster in the full-sample fit **and** in ≥ 80% of the evaluable perturbation runs. Otherwise S3 = 0.
- **[v1.2]** Isolation is a structural signal, conditional on the fitted method. It is not, by itself, sector divergence.

**[v1.2] S2. Multivariate outlier (individual squared Mahalanobis distance).**
- Dᵢ² = (xᵢ − x̄)ᵀ S⁻¹ (xᵢ − x̄), in the p = 10 scaled features. Here x̄ is that date's sample mean and S is its unbiased sample covariance (ddof = 1, `numpy.cov`).
- **Conditioning check.** S is inverted with `numpy.linalg.inv`, not a pseudoinverse. If rank(S) < p or its condition number exceeds 10⁸, S2 is **NA for every firm at that date**, and this is reported. No substitute estimator is used for the primary signal.
- **Primary reference.** Each firm is measured against its own sample, so the correct reference is the scaled Beta distribution: under iid multivariate normality, Dᵢ² · n / (n − 1)² ~ Beta(p/2, (n − p − 1)/2).
  - **S2 = 1** if Dᵢ² > ((n − 1)² / n) · Beta⁻¹(0.95; p/2, (n − p − 1)/2). That is 16.36 for n = 41, p = 10.
  - The reference is only a benchmark. Equity data are skewed, heterogeneous and partly imputed or clipped, so the 5% rate is **not** assumed to hold. Expected chance flags (≈ nα ≈ 2 per date) are quoted only as "under the iid-normal reference".
  - **Identity.** Σᵢ Dᵢ² = (n − 1) p for any sample. S2 is therefore a *relative* screen within each date, and is reported as such.
- **Continuous evidence.**
  - For every firm and date, report the ratio Dᵢ² / reference value.
  - A state is **borderline** if the ratio lies in [0.9, 1.1). Taxonomy classes that rest on a borderline state are marked.
- **Multiplicity sensitivity.**
  - The family is all instruments at one date.
  - Bonferroni uses the same Beta reference at α = 0.05 / n (22.59 for n = 41). This is attainable, since the maximum possible Dᵢ² is (n − 1)² / n = 39.02.
- **SACJ replication reference (descriptive only).** The SACJ expression p(n − 1)/(n − p) · F₀.₉₅(p, n − p) (27.78 for n = 41) is applied as a replication sensitivity. It is a test for a *mean vector*, not for an individual firm, so it is assigned **no error rate**. Under the iid-normal reference it would flag about 0.0004 firms per date.
- **Masking sensitivity (MCD).**
  - Compute robust distances with `sklearn.covariance.MinCovDet(random_state=42)` (default support fraction), and flag above χ²₀.₉₅(p).
  - Report the support size, the condition number of the robust covariance, and any convergence warnings.
  - This is a sensitivity, not a confirmation. MCD assumes one elliptical population, which a cross-sector universe need not be.
- **Other sensitivities:**
  - α = 0.01 and 0.10 (same Beta reference);
  - the log-size space (Section 5);
  - the SACJ 2-D-map version (flagged in ≥ 4 of 5 seeds; descriptive);
  - S2 recomputed without INP (one Investec line).
- **Implementation check.** Dᵢ² is invariant to any non-singular affine rescaling of the features. Frozen and refitted MinMax scaling must give identical Dᵢ², and the code asserts this. The log transform does change it.
- **Decomposition.** Dᵢ² = Σₖ cₖ(S⁻¹c)ₖ is reported for every flagged firm. Terms are signed and conditional on the correlations, so they are not independent feature importances.

**[v1.2] Combining signals.**
- **S∨ = 1** if any applicable signal is 1.
- **S∨ = 0** if all applicable signals are 0.
- **S∨ = NA** if no signal applies.
- **Multi-signal**: two or more of S1, S2 and S3 equal 1 at the same date. The number of signals that applied is reported alongside.
- Two signals agreeing is treated as stronger screening evidence, not as independent confirmation.

## 9. Anomaly-dynamics taxonomy (applied to S1, S2, S3 and S∨ separately)

For a firm with a **defined** state (0 = N, 1 = A) at *t*₁, *t*₂ and *t*₃:

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

- **[v1.2]** Firms absent at any date are *partial history*. Firms present but with an NA state at any date are *undefined state*, and the date and reason are given. Neither group is classified. Their observed states are reported.
- Results for imputation-sensitive firms are marked. Classes resting on a borderline S2 state are marked.
- **Peer-group moves are reported alongside the class but never define it.**
- **[v1.2] Overlap between dates:**
  - Adjacent dates share six months of the market window, and often the same annual accounts. Persistence between adjacent dates is therefore partly mechanical.
  - The return windows of *t*₁ and *t*₃ do not overlap, but the firms, some accounts, the metadata and the frozen preprocessing do.
  - Firms in state A at both *t*₁ and *t*₃ (Persistent, Recurrent) are reported separately as **less mechanically overlapping market evidence** of persistence. This is not an independent test.

## 10. Explaining transitions (SHAP)

1. **Surrogate:** an XGBoost classifier at each date (fixed settings), trained on the raw features to predict that date's cluster labels.
   - Fidelity is reported as in-sample accuracy and stratified out-of-fold accuracy.
   - Out-of-fold accuracy is also reported with singleton clusters excluded, or marked "not estimable".
   - **[v1.2]** If out-of-fold accuracy without singletons is below 0.60, the attributions at that date carry a *weak fidelity* warning.
   - SHAP additivity is checked for every explanation.
2. **Cluster profile:** global and per-cluster mean |SHAP|, and beeswarm plots.
3. **Transition attribution:** for each robust move, and for every firm with an S1, S2 or S3 signal at any date:
   - **[v1.2]** Apply the *t*₁ surrogate to the firm's *t*₁ and later raw feature vectors. This is valid because both inputs use the same feature definitions and per-share basis (rules 2.5 and 4.6).
   - Compute ΔSHAP = SHAP(later) − SHAP(*t*₁) towards the firm's *t*₁ cluster and towards its **reference destination**.
   - **[v1.2] Reference destination** (in order):
     1. the *t*₁ cluster that is the accepted match (Section 7) of the firm's current cluster;
     2. if there is none, the *t*₁ cluster holding most of its current continuing peers, with ties going to the lowest *t*₁ cluster number;
     3. if the firm is isolated, the cluster the *t*₁ surrogate assigns its current profile to.

     The reference used is recorded for every firm.
   - Firms absent at *t*₁ are not attributed.
   - Report the change in each raw feature alongside, split into source change and exchange-rate change where rule 4.6 applies.
   - **[v1.2] Range flag:** if a later value lies outside the *t*₁ minimum–maximum of that feature, the attribution is flagged *outside training range*. It is an extrapolation the surrogate cannot support, and the direction of any bias is unknown.
4. **Sector divergence:** SHAP(assigned cluster) − SHAP(the cluster holding most of the firm's sector peers). Ties go to the lowest cluster number.
5. **Language:** "is associated with" or "accompanies", never "caused" or "drove".

## 11. Data provenance, what has already been seen, and the status of results

The following were produced on the **v1 reconstructed data** before this protocol was written:
- the archived runs in `experiments/runs/`;
- the bounded optimisation search (`silhouette-db-search-01`, June 2025 only);
- **[v1.2]** an exploratory three-date grid search **that included unreduced features**. It was run from an unarchived scratch script (`search_proto.py`, author's session, 2026-11-08) and is not one of the archived runs. Its claims will be cited only after it is rerun inside the paper notebook and archived with its run ID, configuration and data hash;
- **[v1.2]** a check of S2 counts under both references on v1 (2026-11-08, during this revision). Above the SACJ F reference: 3, 1 and 2 firms at *t*₁–*t*₃. Above the Beta reference: 9, 6 and 7 firms.

The authors have therefore seen results on v1, including:
- seed ARI;
- sector ARI;
- which firms were sector-divergent;
- that t-SNE-map T² flags no firms;
- that, in the feature space, unreduced Ward clustering ranks first among the k = 8 models, and that its number of singleton clusters rises across dates;
- the S2 counts above.

Rules influenced by these results:
- the eligibility rules in Section 6, written after the v1 June 2025 grid showed that unconstrained ranking picks degenerate partitions;
- the isolation signal S3, prompted partly by the rising singleton count and partly by SACJ's GLN finding;
- **[v1.2]** the change of primary S2 reference. It was made because the v1.1 reference is statistically wrong for individual distances. The Beta counts were computed before this decision was written down, so the change is disclosed as pilot-informed.

**[v1.2] Status of results:**
- **All v1 analyses are exploratory (pilot)** and will be reported as such.
- **v2** (same firms and dates, rebuilt to Sections 2–5 after this protocol is frozen) is a **protocol-frozen point-in-time reanalysis of pilot-informed historical cross-sections**. It improves measurement and source validity. It is not an independent confirmatory sample.
- ***t*₄ = 31 December 2026 is a prospective follow-up.**
  - On 8 November 2026, its full 12-month window and its decision-date values are not yet observable. Most of the window and some annual results it will use are already public, and the window overlaps *t*₃.
  - So it is not an unseen, independent sample. It is a later cross-section, analysed by a method locked before its decision-date data exist.
  - Before *t*₄ data are pulled, the method, k, all thresholds and the analysis code are fixed by the `protocol-v1.2` commit (or its successor) and a tagged code commit. Every pull of *t*₄ data is logged with its date in `docs/data_access_log.md`.
  - The frozen *t*₁ method with k = 8 is applied unchanged. These are reported:
    - signal states at *t*₄;
    - taxonomy classes extended to four dates, where *t*₂–*t*₄ is classified with the same table;
    - cluster matching from *t*₃ to *t*₄.
  - The dependence from repeated firms, shared accounts and overlapping windows remains.
- **Timestamp.** A Git tag is a version label. If an independent timestamp is wanted, the frozen protocol can be deposited with a registry (for example OSF) before the v2 pull. The paper will say which was done, and will not claim pre-registration otherwise.

## 12. Change log

| Version | Date | Change | Reason |
|---|---|---|---|
| 0.1 | 2026-11-08 | Draft | — |
| 0.2 | 2026-11-08 | Analyst rating dropped; 10 features | It cannot be reconstructed as of each decision date without look-ahead |
| 0.3 | 2026-11-08 | Return = price return | Avoids double-counting dividend yield (feature 9); chosen on that principle, not on model scores |
| 1.0 | 2026-11-08 | Frozen. Method selected at *t*₁ and fixed; k = 8 at all dates (free k as a diagnostic only); Listcorp 8 sectors, no ICB; matching threshold J ≥ 0.30; T² primary space = 10 features; *t*₄ = 31 Dec 2026 follow-up | Author decisions: shifts are measured relative to the eight-sector comparator |
| 1.1 | 2026-11-08 | Frozen, then superseded. (a) perturbation stability; (b) isolation signal S3; (c) pinned fundamentals, shares, revenue basis, FX and dividends; (d) log-size sensitivity; (e) T² ratio, borderline marking, chance flags, Bonferroni and MCD; (f) overlapping-window caveat; (g) SHAP range flag; (h) dimension reduction tested, not assumed | See v1.1 text (tag `protocol-v1.1`) |
| 1.2 | 2026-11-08 | (a) S2 primary reference changed to the scaled-Beta individual-distance reference; SACJ F kept as a descriptive replication with no error rate; Bonferroni and chance flags recomputed on the Beta reference; covariance, inversion and conditioning rules added; the Σ D² identity and affine-invariance check stated | Independent review: v1.1 applied a mean-vector F test to individual distances. Its Bonferroni cutoff (52.62) exceeded the maximum attainable D² (39.02), and its "≈ 2 chance flags" was wrong (≈ 0.0004). Verified numerically |
| | | (b) Results status: v2 = protocol-frozen PIT reanalysis of pilot-informed dates; *t*₄ = prospective follow-up with a data-access log; no implied pre-registration | v2 reuses the seen firms and dates; *t*₄'s window is partly public and overlaps *t*₃ |
| | | (c) Instrument and per-share basis (ISIN, quote unit, share class, corporate-action factors, per-entity Investec shares, shares in issue); native amounts and FX effects; source-document availability date; special dividends | Model values can change without new accounts; receipt prices and DLC counts are incompatible |
| | | (d) Wording: decision-date cross-sections, external sector comparator, singleton counts conditional on method, S3 not called sector divergence, *t*₁–*t*₃ as less mechanically overlapping evidence | Claims stronger than the design supports |
| | | (e) Executable eligibility (every seed, denominator, ties, no-eligible rule, failed fits); DBSCAN as comparator only; perturbation draws, storage, failure handling, minimum runs, *n*-general *m*, paired-by-b design | DBSCAN cannot hold k = 8 unchanged; v1.1 left the procedures under-specified |
| | | (f) Matching: thresholded maximum-weight assignment, Jaccard on continuing firms, exited vs dissolved, split/merge as a separate relation, perturbation support defined; label-free check made descriptive | v1.1 matching objective and noise comparison were ambiguous |
| | | (g) Signals take the values 1/0/NA with recorded reasons; union and multi-signal logic; taxonomy needs defined states | Undefined states were treated as 0 |
| | | (h) Preprocessing order, log rules for non-positive values, failure rule for constant features; SHAP reference destination, ties, absent firms, fidelity warning; range flag direction unknown | Review items 7 |
| | | (i) Provenance of the unreduced-Ward pilot claim and of the S2 counts seen during this revision | Disclosure |
