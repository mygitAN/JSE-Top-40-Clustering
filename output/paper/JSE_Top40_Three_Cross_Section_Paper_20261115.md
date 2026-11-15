# Interpretable Unsupervised Learning for JSE Top 40 Equities

A Repeated Cross Sectional Study of Financial Peer Groups

A. Nxitywa

15 November 2026

## Abstract

We investigate whether interpretable unsupervised learning can describe financial peer groups and their changing composition across three FTSE/JSE Top 40 cross-sections: 30 June 2025, 31 December 2025 and 30 June 2026. Each date contains 41 listed instruments representing 40 company groups. The union contains 43 securities, with 39 present throughout; the 123 instrument-date records are therefore dependent repeated observations. Eight pilot-informed financial characteristics are scaled against June 2025. At each date, a separately refitted two-dimensional UMAP representation is clustered using average linkage and Manhattan distance into eight groups, with parameters held fixed and five random seeds examined. Embedding silhouettes are 0.685, 0.638 and 0.721, whereas the same partitions score 0.151, 0.124 and 0.267 in the scaled financial features. Hungarian matching of continuing-member Jaccard overlaps identifies 15 and 11 aligned membership changes among 40 continuing securities in successive periods. Of 39 complete histories, 19 retain their aligned group and 20 shift at least once. Direct median profiles, company feature changes and qualified surrogate explanations describe these movements. Retrospective inputs, two December singleton groups, representation sensitivity and absent external validation constrain economic interpretation. The contribution is a reproducible screening and reporting procedure, rather than evidence of return predictability or confirmed structural anomalies.

Keywords: JSE Top 40; repeated cross-sections; UMAP; hierarchical clustering; peer groups; cluster alignment; interpretability.

## 1 Introduction

Financial markets generate multivariate data that are difficult to interpret using sector labels alone. Equity analysts commonly organise companies by sector classification, but firms within the same sector can differ in risk, liquidity, valuation, return behaviour and scale. Conversely, companies in different sectors may behave similarly because they share economic drivers, investor sentiment, balance-sheet structures or exposure to market cycles. These cross-sector relationships can be useful for portfolio screening, risk assessment and deeper analyst investigation. 

Much of the machine learning literature in stock-market analysis focuses on supervised prediction, especially forecasting prices, returns or buy-sell signals. Such tasks are difficult because stock prices are noisy, non-stationary and influenced by macroeconomic news, firm announcements, liquidity changes and behavioural factors. A complementary question is not whether a model can predict the next price, but whether it can reveal hidden structure in a market at a point in time. This question is well suited to unsupervised learning because no outcome labels are required during model fitting. 

This article studies the Johannesburg Stock Exchange (JSE) Top 40 as a South African emergingmarket case. The JSE, established in 1887, is a major African equity exchange. The JSE Top 40 contains large, liquid companies across multiple sectors but remains small enough for detailed post-clustering interpretation. The objective is not to produce an automated trading rule. It is to evaluate whether a transparent unsupervised learning pipeline can identify coherent financial peer groupings and describe how those relationships differ across decision dates. This is important because several JSE Top 40 firms have global revenue, commodity, banking, telecommunications or retail exposure, making sector groupings useful but incomplete descriptions of multivariate financial similarity. In this repeated study, sector labels serve as an external descriptive comparator, not as verified historical ground truth. 

The approach proposed by the paper is fourfold. First, we examine financial characteristics and index membership at three decision dates: 30 June 2025, 31 December 2025 and 30 June 2026. Second, we apply one pilot-informed UMAP–hierarchical pipeline, retaining the previous paper’s t-SNE–hierarchical configuration as a comparator and reporting clustering quality both in the original scaled financial-feature space and in the reduced map. Third, we match clusters across adjacent dates using continuing-member Jaccard overlap, report the results for all 41 instruments per date, and trace complete histories for the 39 instruments present throughout. Fourth, we examine directly observable cluster profiles and feature differences, with surrogate SHAP and a separate multivariate-distance screen treated as qualified descriptive evidence rather than causal explanations or confirmed anomalies. The research question is: How consistently can interpretable unsupervised learning identify financial peer groups within the JSE Top 40, and what descriptive changes in peer-group composition and measured financial characteristics occur across repeated cross-sections? 

The article is positioned as exploratory financial data mining rather than predictive modelling. It does not claim to forecast future returns, determine fair value or generate a trading strategy. Its purpose is to show how a reproducible unsupervised workflow can support analyst attention by highlighting financial similarity patterns and changes in peer-group relationships, while acknowledging the sensitivity of these patterns to feature design, model fitting and data provenance. 

Section 2 reviews related work, Section 3 describes the dated universe and inputs, Section 4 gives the method, Section 5 presents the empirical results, Section 6 discusses their implications, and Section 7 concludes.

## 2 Related Work

### 2.1 Unsupervised learning in financial markets

Unsupervised learning is used when the goal is to discover structure rather than predict a known target. Clustering groups assets that are similar under a chosen feature representation and distance measure. In finance, this allows assets to be compared on returns, volatility, liquidity, valuation and fundamentals without assuming that industry labels fully describe behaviour Greene et al. (2008). Prior studies show that clustering can identify market regimes, volatility conditions and cross-asset relationships. Barradas et al. used PCA and K-Means to detect stock-market conditions associated with volatility Barradas et al. (2023). Chen et al. found that return-based commodity clusters aligned with market categories, while volatility-based clusters identified distress periods Chen et al. (2021). Leon et al. used agglomerative clustering to study how global equity-market structure changed after the global financial crisis León et al. (2017). 

Clustering also appears in portfolio-management and trading contexts. Lim and Ong used shapebased clustering for Singapore stocks and argued that price-pattern groupings can supplement industry-based diversification Lim and Ong (2021). Cuomo et al. proposed an unsupervised framework for market-neutral portfolios Cuomo et al. (2022). Unlu and Xanthopoulos combined ensemble clustering with modern portfolio theory to reduce clustering variance Ünlü and Xanthopoulos (2021). Han et al. used agglomerative clustering for pairs trading Han et al. (2023), and Nair et al. clustered stock price time series to produce trading recommendations Nair et al. (2017). These studies show that clustering can reveal economically meaningful groupings, but they also underline the need for interpretation and validation: useful clusters are not necessarily self-explanatory.

### 2.2 Anomaly detection, validation and interpretability

Anomaly detection in finance matters because outlying observations may reflect fraud, instability, unusual liquidity, structural change, hidden risk or unusual opportunity Ahmed et al. (2016). Ahmed et al. show that local and clustering-based outlier methods can be useful in financialmarket datasets Ahmed et al. (2017). However, an anomaly is not automatically a negative signal; in equity analysis it may reflect sector exposure, capital structure, global revenue exposure, growth expectations or recent operational stress. Interpretable anomaly-detection methods have therefore been proposed to help explain why a firm is flagged Cheong et al. (2021). 

Cluster validation is difficult because unsupervised learning does not learn from labelled outcomes. Internal metrics such as the Silhouette Score and Davies-Bouldin Index are widely used because they measure compactness and separation. A higher Silhouette Score implies that observations are closer to their assigned cluster than to alternative clusters Rousseeuw (1987); a lower DaviesBouldin Index implies that the clusters are well separated and compact Davies and Bouldin (1979). Comparative studies caution that no single validation index is sufficient across all settings, so multiple metrics should be used, as different indices capture distinct aspects of quality Arbelaitz et al. (2013); Vendramin et al. (2010). Desirable results show both within-cluster homogeneity and clear separation between clusters, reflected jointly in a high Silhouette Score and a low Davies-Bouldin Index. Where a credible external classification exists, it can also serve as a post-hoc ground-truth benchmark. In the present study, legacy sector labels provide descriptive context, but are not independently verified historical ground truth. 

Interpretability is particularly important in financial applications because decision-makers need to understand why assets are grouped together. SHAP (SHapley Additive exPlanations) values, derived from cooperative game theory, provide consistent feature-attribution scores and are widely used to explain complex machine-learning models. Merrick and Taly (2020); Rozemberczki et al. (2022). In this study, SHAP is applied after clustering by training a surrogate classifier to predict cluster membership from the original variables. The goal is not only to cluster equities but to explain whether groupings are driven by size, liquidity, valuation, volatility, recent return or combinations of these variables. 

The South African equity market remains underrepresented in this literature. Existing studies often focus on larger international markets, use a narrow PCA/K-Means pipeline or stop at visual cluster explanation Nourahmadi et al. (2022). The gap addressed here is the need for a compact, interpretable and measurable unsupervised learning workflow for a South African equity universe.

## 3 Study population and financial inputs

### 3.1 Three decision dates and effective index membership

The unit of analysis is a listed instrument at a decision date. We use 30 June 2025, 31 December 2025 and 30 June 2026 as three distinct cross-sections. Each contains 41 security lines because Investec Limited (INL) and Investec plc (INP) are separate listed instruments of one dual-listed economic group. Both are retained. Thus 41 instruments correspond to 40 company groups, rather than an accidental inclusion of a forty-first company.

Table 1. Date-specific population reconciliation.

| Decision date | Instruments | Groups | Change since preceding date |
|---|---|---|---|
| June 2025 | 41 | 40 | Initial observed population |
| December 2025 | 41 | 40 | GLN admitted; APN removed |
| June 2026 | 41 | 40 | PAN admitted; MNP removed |

The June 2025 review introduced Northam Platinum and removed Glencore before the first observation. The September review reversed Glencore's absence and removed Aspen. There was no recorded Top 40 change in December 2025. Pan African Resources replaced Mondi in March 2026, with no recorded change in June 2026. These events are stored with their effective dates and evidence in index_changes.csv. The validator checks both the first-date review and subsequent transitions rather than hard-coding a list of expected ticker changes.

![Figure 1. The complete date-specific populations and the restricted longitudinal population. Entries and exits are counted independently from cluster movement.](figures/figure_01.pdf)

Across dates there are 123 rows and 43 distinct tickers. Each adjacent pair shares 40 instruments, while 39 appear at all three dates. Aspen has only the first observation, Mondi the first two, Glencore the last two and Pan African only the last. A complete-history figure therefore contains 39 instruments; this is not the index size. Adjacent trailing annual market windows overlap by six months, many fundamentals recur, and the instruments themselves repeat. Neither rows nor dates are treated as independent replications.

### 3.2 Financial representation and measurement

The eight-feature representation is a pilot-informed revision intended to reduce the sensitivity of share-count and EPS inputs to share subdivisions and to reduce skew in size measures. It is not the eleven-variable representation in the original SACJ manuscript, nor a direct replication of its 2023-2024 sample. The archived ten-variable representation is an intermediate reference; it also differs from that original experiment.

Table 2. Variables used by the current study model. Sector, company and ticker identify or describe observations and are excluded from fitting.

| Feature | Construction and interpretation |
|---|---|
| One-year return | Trailing split-adjusted price change; cash dividends excluded. |
| Beta | Slope relative to daily J203 market returns over the trailing year. |
| Annualised volatility | Daily-return sample standard deviation multiplied by the square root of 252. |
| Dividend yield | Trailing dividends relative to the security close, under the recorded currency convention. |
| Earnings yield | EPS / close; clipped at June 2025 first and ninety-ninth percentiles. |
| Log market capitalisation | Base-10 logarithm of rand line-specific market capitalisation. |
| Log revenue / capitalisation | Base-10 logarithm of revenue divided by market value; group totals for Investec. |
| Log share turnover | Base-10 logarithm of corrected average daily JSE volume / line-specific shares. |

For a subdivision factor q, price and EPS divide by q and shares and consistently measured share volume multiply by q. Earnings yield, market capitalisation, revenue/capitalisation and turnover are consequently unchanged under a consistent restatement. This algebraic property motivates the representation; it does not certify historical source consistency. In particular, trailing volume that mixes pre- and post-subdivision units requires a correction before taking the ratio.

### 3.3 Corrections and missing observations

Original source values remain unchanged in the input CSV and provenance workbook. The feature pipeline applies documented corrections from separate reference tables. Naspers began trading on the five-for-one share basis on 1 October 2025; its register date was 6 October. Its December 2025 average daily volume is restated from 800,935 mixed-basis units to 2,140,029 post-subdivision shares, and the June 2026 figure from 1,502,524 to 1,847,639. These are corrections to the trailing-volume units, not additional trading observations.

Both Investec rows originally carry a combined share count. Issuer disclosures from June 2024 and June 2026 allocate that reconstructed total between the two lines. December 2025 uses the midpoint of the disclosed line fractions. Each line has its own market capitalisation and turnover, while revenue relative to market value uses combined issuer revenue and combined market value because each line represents a claim on the group. The December interpolation and the reconstructed combined total remain limitations.

Reinet has no usable raw revenue or EPS at any date, and Anglo American lacks usable volume at the first two dates. Missing model values use June 2025 medians. A derived feature depending on an imputed source is imputed using the June 2025 median of that derived feature, rather than treating the imputed raw value as observed. No instrument is removed because of these missing inputs. The earnings-yield clipping limits are likewise fitted on June 2025 and then held fixed.

Market measures are rebuilt from retrospective vendor histories. Dated issuer releases support revenue and diluted EPS for 120 of 123 rows, with dated currency conversions, but shares and market capitalisation are reconstructed. Sector is a legacy eight-category directory label. JSE-only volume understates total liquidity for issuers whose principal market is overseas; revenue is also not defined uniformly across sectors. The data are not certified strict point-in-time observations.

## 4 Repeated cross sectional methods

![Figure 2. Study workflow. A common preprocessing reference is carried forward, while the embedding and clusters are refitted independently at each date. The alignment stage compares sets of continuing members, rather than arbitrary numeric labels.](figures/figure_02.pdf)

### 4.1 Scaling and independent fitting

For feature j, let a(j) and b(j) be its June 2025 minimum and maximum after the declared imputation and transformations. The scaled value at any date is the difference between the observed value and a(j), divided by b(j) minus a(j). Scaling is not clipped. A later observation can therefore exceed one or fall below zero. This preserves a reference scale and avoids using later observations to estimate preprocessing constants, but does not prevent later variance being dominated by one feature.

For each date and each seed in 42-46, UMAP (McInnes et al., 2018) learns a new two-dimensional representation using three neighbours, minimum distance 0.01, Euclidean input distance and one computational job. Agglomerative clustering then joins groups bottom-up with average linkage under Manhattan distance on the two coordinates, stopping at eight groups. Seed 42 supplies the representative partition and figures. The five fits quantify stochastic sensitivity; their outputs are not pooled into an enlarged sample or a consensus partition.

Table 3. The study model is distinct from the generic UMAP comparator, which uses ten neighbours and minimum distance 0.1 in the broader comparison grid.

| Stage | Fixed specification |
|---|---|
| Scaling | MinMax; fitted 30 June 2025; clip=False |
| UMAP | 2 components; n_neighbors=3; min_dist=0.01; Euclidean; n_jobs=1 |
| Agglomerative clustering | 8 groups; average linkage; Manhattan metric on UMAP coordinates |
| Seeds | 42, 43, 44, 45, 46; representative partition 42 |
| Software | umap-learn 0.5.12; scikit-learn 1.6.1 |
| Sensitivity | Cluster counts 2-12; alternative feature representations |
| Historical comparator | t-SNE: perplexity 5; learning rate 10; 300 iterations; random initialisation; average-Manhattan hierarchy, k=8 |

Three neighbours and minimum distance 0.01 were author-specified after exploratory June 2025 analysis. An earlier 36-combination grid preferred minimum distance 0.1. Eight groups, average linkage and Manhattan distance follow the original paper. These settings are pilot-informed, not prospectively registered. Later-date fitting holds the recipe fixed but refits the representation and labels, so the results do not measure out-of-sample predictive performance.

### 4.2 Quality in two geometries and seed agreement

Each representative partition is evaluated in both the two-dimensional representation and the eight-dimensional scaled financial space. Silhouette uses within-cluster and nearest-other-cluster Euclidean distances; larger values indicate greater separation. Davies-Bouldin compares within-group dispersion with distances between group centres; smaller values indicate more compact separation. The evaluation distance is Euclidean even though the hierarchy uses Manhattan distance. The two geometries answer different questions and are reported together. DBSCAN comparator scores exclude noise and must be read with coverage.

Within each date, five seeds give ten pairwise adjusted Rand indices (ARI). ARI is label-invariant and adjusted for chance agreement; it is not an accuracy against a known financial truth. Its mean summarises variability induced by the embedding seed, conditional on the fixed inputs. The five-seed mean is not a confidence interval, bootstrap, or independent null distribution for temporal changes. Cluster size ranges and singleton counts accompany the quality scores.

### 4.3 Matching clusters between dates

Let C be the instruments observed at both adjacent dates. For each earlier group A and later group B, restrict both to C and calculate their Jaccard similarity as the size of their intersection divided by the size of their union. A Hungarian assignment chooses a one-to-one matching that maximises the sum of these similarities. An assigned pair with zero intersection is not retained as a match; that later cluster receives a fresh identifier. Retired identifiers are never reused for unrelated groups.

Table 4. Reproducible cross-date matching procedure implemented in top40/temporal.py.

| Step | Operation |
|---|---|
| 1 | Partition each date independently; retain ticker as the stable security key. |
| 2 | Identify continuing members, entries and exits from date-specific populations. |
| 3 | Build the cluster-by-cluster Jaccard matrix using continuing members only. |
| 4 | Maximise total Jaccard overlap with a one-to-one Hungarian assignment. |
| 5 | Transfer earlier labels only for positive-overlap matches; issue new labels otherwise. |
| 6 | Count a switch only when a continuing instrument has different aligned labels. |
| 7 | Chain the matches for complete three-date histories; leave membership gaps missing. |

Temporal ARI is computed directly on the two partitions of continuing members and does not depend on the label matching. Switch counts do depend on matching. A global one-to-one assignment cannot fully represent a split or merger, so the overlap matrix and named member histories remain essential. A label that survives a match is a descriptive continuity identifier, not an invariant economic factor. We use "stable" only for a complete history whose aligned label never changes, and "shifted" when it changes at least once. These terms do not imply unchanged or changed business fundamentals.

### 4.4 Direct profiles and surrogate interpretation

For each cluster, we subtract the same-date cross-sectional median from the cluster median for each of the eight scaled features. Positive and negative deviations describe the group relative to its contemporaries in June 2025 reference units. For an instrument that changes group, the reporting tables retain its feature changes, old and new peers, peer retention and destination profile. These directly calculated descriptions form the primary interpretation.

An XGBoost classifier is fitted to the unscaled engineered features to reproduce the cluster labels: 150 trees, maximum depth two, learning rate 0.05, full row and column sampling, one job and a multiclass probability objective. Tree SHAP explains the surrogate raw class margins using tree-path-dependent perturbation. Saved attributions are checked for additivity with a maximum tolerance of 0.0001. These attributions explain the surrogate, rather than the UMAP or hierarchy directly, and do not establish causes of group membership.

Where the smallest cluster contains at least two members, stratified cross-validation uses the smaller of five folds and the minimum cluster size, with shuffling and the representative seed. Singleton clusters make this out-of-fold fidelity estimate unavailable under the implemented procedure. The measured fidelity is agreement with algorithm-generated labels, not accuracy in forecasting a financial outcome. A model that reproduces every training label can still have inadequate fidelity on held-out instruments.

### 4.5 Separate financial distance screen

The screen computes squared Mahalanobis distance from the same-date mean in the eight scaled features using the sample covariance matrix. It is not the predictive Hotelling statistic for a new observation. Under independent multivariate normal sampling, an individual internal distance D squared, multiplied by n divided by (n minus one) squared, has a Beta reference with shape parameters p/2 and (n minus p minus one)/2. Here n=41, p=8 and the nominal upper-tail level is 0.05. A singular or excessively ill-conditioned covariance produces an unestimable result rather than a flag.

Those assumptions are doubtful for heterogeneous, overlapping equity cross-sections with clipped and imputed financial variables. The threshold therefore provides a descriptive ranking screen, not calibrated significance or a multiple-testing-controlled anomaly discovery procedure. Cluster isolation, sector divergence, aligned membership movement and financial distance are separate observations. No combined score converts them into a confirmed economic anomaly.

## 5 Empirical results

### 5.1 Cluster quality and the historical comparator

Table 5. Representative UMAP partition quality, mean pairwise five-seed ARI and cluster size ranges. S is silhouette; DB is Davies-Bouldin. All 41 instruments are included.

| Date | Feature S | Feature DB | Map S | Map DB | Seed ARI | Size range |
|---|---|---|---|---|---|---|
| June 2025 | 0.151 | 1.153 | 0.685 | 0.385 | 0.846 | 2-9 |
| December 2025 | 0.124 | 1.049 | 0.638 | 0.268 | 0.892 | 1-8 |
| June 2026 | 0.267 | 1.059 | 0.721 | 0.355 | 0.738 | 2-8 |

The largest quality distinction is between geometries: financial-feature silhouettes range from 0.124 to 0.267, whereas map silhouettes range from 0.638 to 0.721. In December, the representative partition contains two singletons; neither June partition has a singleton. High map compactness is therefore compatible with weak financial separation and small or isolated groups. The mean seed ARI is highest in December (0.892), despite those singletons, and lowest in June 2026 (0.738).

The historical t-SNE recipe has map silhouettes 0.532, 0.589 and 0.656. Its financial silhouettes are 0.195, 0.240 and 0.255. Thus UMAP produces the higher map silhouette at every date, while t-SNE scores higher in financial space at the first two dates. UMAP is only slightly higher in financial space in June 2026. This does not support a general claim of superior financial grouping or a direct comparison with the original manuscript's different sample and features.

![Figure 3. Silhouettes for the UMAP study model and the historical t-SNE/hierarchical recipe applied to the same current eight-feature inputs. Darker bars evaluate the financial features; lighter bars evaluate the embedding. Both recipes use eight clusters.](figures/figure_03.pdf)

### 5.2 Continuing members and complete histories

Table 6. Temporal comparison among the 40 continuing instruments in each adjacent pair. Entries and exits are excluded from changed and unchanged counts.

| Period | Continue | Entry / exit | Changed | Unchanged | ARI | NMI |
|---|---|---|---|---|---|---|
| Jun-Dec 2025 | 40 | 1 / 1 | 15 (37.5%) | 25 (62.5%) | 0.377 | 0.646 |
| Dec 2025-Jun 2026 | 40 | 1 / 1 | 11 (27.5%) | 29 (72.5%) | 0.590 | 0.751 |

The second pair is more similar by temporal ARI and has fewer aligned switches, but two transitions are insufficient to establish a trend or a statistically significant reduction in change. Across the 39 complete histories, 19 (48.7%) keep an aligned label and 20 (51.3%) change at least once. There are 26 adjacent switch events, rather than 26 distinct changing securities. Five complete-history instruments switch in both periods; 15 switch once. Those histories account for 25 switch events; Mondi contributes the remaining first-period event before its subsequent exit. Membership gaps are neither stability nor change.

The 19 stable histories are ANH, BHG, BID, BVT, CFR, FSR, GRT, IMP, INL, INP, MRP, NED, NPH, NRP, OUT, SBK, SHP, SSW, WHL. The 20 shifted histories are ABG, AGL, ANG, BTI, CLS, CPI, DSY, GFI, HAR, MTN, NPN, OMU, PPH, PRX, REM, RNI, SLM, SOL, VAL, VOD. The five instruments changing in both adjacent periods are ABG, DSY, OMU, REM, RNI. These named outcomes allow the counts to be checked against the saved memberships and prevent a single aggregate statistic from concealing different histories.

![Figure 4. Aligned group membership for the 39 instruments observed at all three dates. Bold tickers change aligned group at least once. The per-date quality annotations refer to the full 41-instrument partition. APN, MNP, GLN and PAN are omitted only from this complete-history view. Vertical position is layout; colours identify aligned groups, not sectors.](figures/figure_04.png)

### 5.3 Overlap structure and interpretation of switches

![Figure 5. Continuing-member Jaccard similarities underlying cross-date matching. Similarity is computed on 40 continuing securities in each period; index entrants and exits do not create artificial peer-group switches. Positive-overlap assignments transfer labels, while zero-overlap groups receive new identifiers.](figures/figure_05.png)

The flow diagram is a compact history summary, whereas the overlap matrices expose continuity strength. For example, a larger first-period matched group has Jaccard overlap about 0.62, while some other matches are substantially weaker. The matching maximises the total across all pairs, so it should not be interpreted as proving that each matched group has strong continuity. Entry, exit, splitting and regrouping are visible in the accompanying member tables.

Absa and Old Mutual move from aligned group 1 to group 5 and then return to group 1. Their paths illustrate why two adjacent switch events do not imply persistent movement away from an original peer set. Reinet follows 6 to 7 to 2, with fundamentals imputed at every date. Naspers follows 7 to 7 to 9 after the documented share-basis corrections; its observed path remains conditional on those corrections and the embedding. These cases require different substantive follow-up despite sharing the generic label "shifted".

### 5.4 Financial profiles at each decision date

Figures 6-8 use the aligned labels from the longitudinal outputs, rather than the raw local cluster numbers in independent fits. They report cluster median minus same-date median for all eight inputs. A positive cell identifies a relatively high feature on the frozen scale; it is not a coefficient, effect size in returns or SHAP attribution. The row counts refer to the full date-specific population, including partial histories.

![Figure 6. June 2025 aligned-cluster median deviations. Values are in June 2025 MinMax units. Row labels give aligned cluster identifiers and instrument counts; missing identifiers reflect retired groups, not missing observations.](figures/figure_06.pdf)

![Figure 7. December 2025 aligned-cluster median deviations. Values are in June 2025 MinMax units. Row labels give aligned cluster identifiers and instrument counts; missing identifiers reflect retired groups, not missing observations.](figures/figure_07.pdf)

![Figure 8. June 2026 aligned-cluster median deviations. Values are in June 2025 MinMax units. Row labels give aligned cluster identifiers and instrument counts; missing identifiers reflect retired groups, not missing observations.](figures/figure_08.pdf)

A precious-metals grouping illustrates changing composition rather than a fixed sector partition. AngloGold Ashanti, Gold Fields and Harmony join the group containing Impala Platinum, Northam and Sibanye-Stillwater by December 2025, together with Valterra. That December group has relatively high trailing return, beta and volatility. Its main membership persists in June 2026, when newly admitted Pan African Resources is included. This is a description of saved features and memberships, not evidence that commodity prices caused a structural break.

ANH, BHG and CFR remain together throughout. BTI joins their aligned group in December 2025, and PRX leaves by June 2026. Their June 2026 profile combines high log market capitalisation with low JSE share turnover. That contrast is consistent with the recorded feature geometry but requires caution for internationally traded firms: low JSE turnover need not mean low total market liquidity. The financial profiles supply hypotheses for analyst investigation without declaring inherited sectors incorrect.

### 5.5 Representation sensitivity and cluster count

Table 7. Scale drift in invariant8 and UMAP agreement with the archived original10 representation. An even variance allocation would be 12.5%. Cross-set ARI compares partitions, not the magnitude of silhouette values across feature spaces.

| Date | Dominant feature | Variance share | Max scaled | Cross-set ARI |
|---|---|---|---|---|
| June 2025 | Dividend yield | 19.8% | 1.000 | 0.668 |
| December 2025 | 1Y return | 52.5% | 2.847 | 0.607 |
| June 2026 | Volatility | 22.1% | 1.244 | 0.590 |

Return accounts for 52.5% of scaled variance in December 2025, compared with an even eight-variable share of 12.5%. The maximum scaled value reaches 2.847. The frozen reference preserves temporal comparability of units but does not preserve feature influence. Consequently, the weaker December financial silhouette and changing peer groups can reflect shifts in the relative geometry induced by preprocessing, as well as changes in firms' measured financial attributes.

Feature alternatives also affect histories. UMAP yields 20 stable and 19 shifted complete histories under original10, 16 and 23 under logsize10, 19 and 20 under invariant8, and 14 and 25 under market5. Each uses the same 39 complete-history instruments. These are diagnostic alternatives rather than independently validated models. Their silhouette and Davies-Bouldin values are computed in different feature spaces and cannot be ranked as though they shared identical units or inputs.

![Figure 9. Sensitivity to cluster count from two to twelve under the study representation. Eight clusters remain the historical reference choice. Inspect financial-space quality together with minimum group size and seed agreement; the plot does not establish a uniquely correct number of economic groups.](figures/figure_09.png)

### 5.6 Surrogate fidelity and descriptive distance flags

Table 8. Surrogate agreement with representative cluster labels. Where estimated, the minimum group size of two limits stratified cross-validation to two folds.

| Date | Training fidelity | Out-of-fold fidelity | Singleton groups |
|---|---|---|---|
| June 2025 | 1.000 | 0.439 | 0 |
| December 2025 | 1.000 | Not estimable | 2 |
| June 2026 | 1.000 | 0.707 | 0 |

Perfect reproduction of training labels does not imply reliable explanation. The June 2025 held-out fidelity is only 43.9%, compared with 70.7% in June 2026; December cannot be estimated with the implemented stratified scheme because of two singletons. These values justify using the direct median profiles and feature histories as the principal interpretation. SHAP may describe the fitted surrogate but cannot establish why an instrument moved or validate the economic relevance of that movement.

Table 9. Separate same-date Mahalanobis distance screen at nominal alpha 0.05. These are descriptive flags, not significant economic anomalies.

| Date | Flagged instruments | Count |
|---|---|---|
| June 2025 | APN, BHG, BTI, SOL, VAL | 5 |
| December 2025 | AGL, BHG, BTI, SOL, SSW | 5 |
| June 2026 | GLN, PAN, SOL, SSW | 4 |

Fourteen instrument-date observations are flagged, spanning nine distinct tickers. Sasol is flagged at all three dates; BHG and BTI at the first two; SSW at the last two. APN and PAN have incomplete eligibility histories, so their unobserved dates cannot be recorded as an absence of a flag. AGL also carries imputed volume. These differences prevent a simple count of repeated flags from establishing persistence of an economic anomaly. No forecast-return test, external event corroboration or calibrated transition null is available for this run.

## 6 Discussion

The central finding is that high visual separation is not equivalent to strong financial peer structure. A small UMAP neighbourhood and low minimum distance make compact local islands possible, yet the financial-space silhouettes are modest. The historical t-SNE comparator confirms that the model with a stronger map silhouette can have a weaker silhouette on the financial characteristics themselves. Model evaluation must therefore name the geometry and report group sizes, rather than rely on the appearance of a coloured plot.

The repeated design adds a dated universe, a reproducible alignment rule and company-level histories to the original single-window study. It separates index reconstitution from movement among continuing members, and prevents arbitrary cluster numbering from producing spurious transitions. However, a continuing aligned label is only a convenient description. A one-to-one matching compresses cluster splits and mergers, and a switch can be induced by movements in other firms, local embedding variability or preprocessing influence without a large change in the focal firm.

The 19 stable and 20 shifted histories are consequently conditional results. The seed sensitivity measures one part of uncertainty, not a probability that a switch is real. Shared observations, overlapping annual windows, repeated issuer accounts, common market shocks and the two Investec lines also limit independence. No inferential procedure in this study treats the 123 rows as 123 independently sampled companies, or the five seeds as five new datasets.

Feature corrections are part of the empirical specification. Correcting subdivisions and separating dual-listed share counts improves interpretability of the chosen ratios, but reconstructed shares, interpolated line fractions, JSE-only liquidity and sector-dependent accounting definitions remain consequential. Alternate feature results show that the history labels change when the geometry changes. "Share-basis invariant" describes the algebra of consistently measured variables; it is not a certificate that historical sources are free of error.

The present contribution is a transparent process for repeated financial screening. A future confirmatory design should freeze inputs and settings before a new decision date, certify as-of data availability, calibrate transitions with suitable input perturbations and compare subsequent within-cluster return co-movement against sector-defined and matched random groups. It should also examine sensitivity to the alignment objective, cluster count, sampling unit and preprocessing policy. These are proposed validation steps; no results from them are claimed here.

## 7 Conclusion

We extend an interpretable equity-clustering study to three repeated FTSE/JSE Top 40 cross-sections, each containing 41 listed instruments and 40 company groups. The union has 43 instruments and 39 complete histories. A fixed, pilot-informed UMAP and agglomerative recipe yields high map silhouettes but weaker financial-feature separation. Continuing-member Jaccard alignment identifies 15 and 11 adjacent switches, with 19 complete histories retaining their group and 20 shifting at least once. Profile tables, named histories, sensitivity diagnostics and fidelity-qualified surrogate outputs make these findings inspectable. The evidence supports descriptive screening and prioritisation of further investigation. It does not establish causal structural change, return predictability, or validated economic anomalies.

## References

Mohiuddin Ahmed, Abdun Naser Mahmood, and Md Rafiqul Islam. A survey of anomaly detection techniques in financial domain. Future Generation Computer Systems, 55:278–288, 2016. doi: 10.1016/j.future.2015.01.001.

Mohiuddin Ahmed, Nazim Choudhury, and Shahadat Uddin. Anomaly detection on big data in financial markets. In 2017 IEEE/ACM International Conference on Advances in Social Networks Analysis and Mining, pages 998–1005, 2017. doi: 10.1145/3110025.3119402.

Olatz Arbelaitz, Ibai Gurrutxaga, Javier Muguerza, Jesús M. Pérez, and Iñigo Perona. An extensive comparative study of cluster validity indices. Pattern Recognition, 46(1):243–256, 2013. doi: 10.1016/j.patcog.2012.07.021.

Ana Barradas, Rosa-Maria Canton-Croda, and David-Eduardo Gibaja-Romero. Identification of patterns in the stock market through unsupervised algorithms. Analytics, 2(3):592–603, 2023. doi: 10.3390/analytics2030033.

James Ming Chen, Mobeen Ur Rehman, and Xuan Vinh Vo. Clustering commodity markets in space and time: Clarifying returns volatility and trading regimes through unsupervised machine learning. Resources Policy, 73:102162, 2021. doi: 10.1016/j.resourpol.2021.102162.

Min-Soo Cheong, Ming-Chang Wu, and Shih-Han Huang. Interpretable stock anomaly detection based on spatio-temporal relation networks with genetic algorithm. IEEE Access, 9:68302– 68319, 2021. doi: 10.1109/ACCESS.2021.3077067.

Salvatore Cuomo, Francesco Gatta, Fabio Giampaolo, Ciro Iorio, and Francesco Piccialli. An unsupervised learning framework for market-neutral portfolio. Expert Systems with Applications, 192:116308, 2022. doi: 10.1016/j.eswa.2021.116308.

David L. Davies and Donald W. Bouldin. A cluster separation measure. IEEE Transactions on Pattern Analysis and Machine Intelligence, PAMI-1(2):224–227, 1979. doi: 10.1109/TPAMI.1979.4766909.

Derek Greene, Pádraig Cunningham, and Rudolf Mayer. Unsupervised learning and clustering. In Machine Learning Techniques for Multimedia, pages 25–71. Springer, 2008. doi: 10.1007/ 978-3-540-75171-7_3.

Chao Han, Zhaoyang He, and A. J. W. Toh. Pairs trading via unsupervised learning. European Journal of Operational Research, 307(2):929–947, 2023. doi: 10.1016/j.ejor.2022.09.041.

Carlos León, Gwang-Young Kim, Constanza Martínez, and Dowe Lee. Equity markets clustering and the global financial crisis. Quantitative Finance, 17(12):1905–1922, 2017. doi: 10.1080/14697688.2017.1357970.

T. Lim and C. S. Ong. Portfolio management: A financial application of unsupervised shapebased clustering-driven machine learning method. International Journal of Computing and Digital Systems, 10(1):257–269, 2021. doi: 10.12785/ijcds/100124.

Leland McInnes, John Healy, and James Melville. UMAP: Uniform manifold approximation and projection for dimension reduction, 2018.

Luke Merrick and Ankur Taly. The explanation game: Explaining machine learning models using shapley values. In Machine Learning and Knowledge Extraction, volume 12279 of Lecture Notes in Computer Science, pages 17–38. Springer, 2020. doi: 10.1007/978-3-030-57321-8_2.

B. B. Nair, P. K. S. Kumar, N. R. Sakthivel, and U. Vipin. Clustering stock price time series data to generate stock trading recommendations: An empirical study. Expert Systems with Applications, 70:20–36, 2017. doi: 10.1016/j.eswa.2016.11.002.

Mohsen Nourahmadi, Fatemeh Rasti, and Hassan Sadeqi. A comparative approach to financial clustering models: A study of the companies listed on tehran stock exchange. Iranian Journal of Finance, 6(4):31–55, 2022. doi: 10.30699/IJF.2022.303980.1267.

Peter J. Rousseeuw. Silhouettes: A graphical aid to the interpretation and validation of cluster analysis. Journal of Computational and Applied Mathematics, 20(1):53–65, 1987. doi: 10.1016/0377-0427(87)90125-7.

Benedek Rozemberczki, Lauren Watson, Peter Bayer, Hao-Ting Yang, Oliver Kiss, Sebastian Nilsson, and Rik Sarkar. The shapley value in machine learning. arXiv:2202.05594, 2022. doi: 10.48550/arXiv.2202.05594.

R. Ünlü and P. Xanthopoulos. A reduced variance unsupervised ensemble learning algorithm based on modern portfolio theory. Expert Systems with Applications, 180:115085, 2021. doi: 10.1016/j.eswa.2021.115085.

Lucas Vendramin, Ricardo J. G. B. Campello, and Eduardo R. Hruschka. Relative clustering validity criteria: A comparative overview. Statistical Analysis and Data Mining, 3(4):209–235, 2010. doi: 10.1002/sam.10080.
