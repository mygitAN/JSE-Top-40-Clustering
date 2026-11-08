# Tracking structural signals across repeated equity screenings

Working reporting example, not a submission-ready manuscript. This reporting amendment was written after the existing results were examined.

## Contribution and study design

This study develops an interpretable repeated cross-sectional equity-screening framework for tracking changes in peer relationships and distinguishing emerging, persistent and resolving structural signals. It examines the financial characteristics associated with those changes, while distinguishing geometric outlier flags from sector divergence.

The framework is applied at three decision dates: 30 June 2025, 31 December 2025 and 30 June 2026. Each cross-section contains 41 listed instruments representing 40 company groups because Investec Limited and Investec plc form one dual-listed group. Membership is determined separately at each date. The 123 instrument-date records do not constitute 123 independent firms, and the trailing market windows overlap.

The historic-consensus-excluded implementation has ten features, with earnings yield replacing P/E; it is not identical to the original eleven-feature design. Strict point-in-time information availability remains the target. Current reconstructed share counts, market capitalisations, sector history and vendor series do not establish a fully verified historical information set.

## Experimentation supports the interpretation

The primary analysis retains k=8 and the settings selected from June 2025. The earlier exhaustive finite grid contains 3,268 configurations over five seeds, with silhouette and Davies-Bouldin reported jointly in both embedding and common financial-feature spaces. Exact distance, linkage, reduction and algorithm parameters remain in the original experiment archive. These are criterion-dependent finite-grid optima, not a universal best model.

A separate sensitivity varies k from 2 to 12 independently at each decision date for the three existing main models. It holds representation settings and other clustering parameters fixed, reuses the saved five-seed representations, and performs 495 clustering fits. This isolates the effect of cluster count; it is not a new full retuning of every algorithm and reduction at each date. The primary k=8 classifications and SHAP results are unchanged.

| Model role | Scoring criterion | June 2025 k | December 2025 k | June 2026 k |
| --- | --- | ---: | ---: | ---: |
| baseline | embedding | 12 | 9 | 9 |
| baseline | features | 6 | 2 | 2 |
| common_features_k8 | embedding | 2 | 2 | 2 |
| common_features_k8 | features | 2 | 2 | 2 |
| embedding_k8 | embedding | 8 | 7 | 4 |
| embedding_k8 | features | 12 | 9 | 9 |

## From cluster changes to signal histories

A changed cluster is not automatically an anomaly. Three signals are reported separately: a geometric screen flag, contextual sector divergence, and agreement between those two signals. Cluster shifts and stability are a separate membership history. Unknown sector comparisons, singletons, ties and missing membership are not treated as normal observations.

| Pattern: first, second, third decision date | Reporting classification |
| --- | --- |
| not flagged -> not flagged -> not flagged | never flagged |
| not flagged -> not flagged -> flagged | emerging |
| not flagged -> flagged -> flagged | emerging and sustained |
| flagged -> flagged -> flagged | persistent |
| flagged -> flagged -> not flagged | resolving |
| flagged -> not flagged -> not flagged | resolved |
| not flagged -> flagged -> not flagged | transient |
| flagged -> not flagged -> flagged | recurring |

These labels refine the earlier reporting taxonomy: 100 is now resolved, 110 remains resolving, and 011 is emerging and sustained. The amendment is explicitly post hoc for these already analysed data; the old immutable results are not relabelled or described as prospectively prespecified.

The primary PCA/hierarchy k sensitivity selects k=2 at every date, with one singleton under either score criterion. Its higher scores do not by themselves establish a useful peer-group partition. Selected values at k=2 or k=12 lie on the tested range boundary; report the range and singleton counts explicitly. K=8 remains primary.

## What the current primary results show

**geometric screen**

- never flagged (36): ABG, AGL, ANG, BID, BTI, BVT, CFR, CLS, CPI, DSY, FSR, GFI, GRT, HAR, IMP, INL, INP, MRP, MTN, NED, NPH, NPN, NRP, OMU, OUT, PPH, PRX, REM, RNI, SBK, SHP, SLM, SOL, VAL, VOD, WHL.
- not eligible: missing observation or unestimable signal (4): APN, GLN, MNP, PAN.
- resolved (2): ANH, BHG.
- transient (1): SSW.

**sector divergence**

- never flagged (15): ABG, CPI, DSY, FSR, GRT, INL, INP, NED, NRP, OMU, OUT, REM, RNI, SBK, SLM.
- not eligible: missing observation or unestimable signal (11): ANH, APN, BHG, BTI, GLN, MNP, NPN, PAN, SOL, SSW, VAL.
- persistent (11): AGL, BID, BVT, CLS, MRP, MTN, PPH, PRX, SHP, VOD, WHL.
- resolved (5): ANG, GFI, HAR, IMP, NPH.
- resolving (1): CFR.

**joint agreement**

- never flagged (32): ABG, AGL, ANG, BID, BVT, CFR, CLS, CPI, DSY, FSR, GFI, GRT, HAR, IMP, INL, INP, MRP, MTN, NED, NPH, NRP, OMU, OUT, PPH, PRX, REM, RNI, SBK, SHP, SLM, VOD, WHL.
- not eligible: missing observation or unestimable signal (11): ANH, APN, BHG, BTI, GLN, MNP, NPN, PAN, SOL, SSW, VAL.

For example, ANH and BHG are flagged geometrically at the first decision date but not at the subsequent two dates. Under this reporting taxonomy their geometric signals are **resolved**. SSW is flagged only at the middle date and is therefore **transient**. GLN is flagged at the two later dates, but is absent from the first cross-section: it is not assigned a three-date persistent classification.

These are histories of descriptive screen flags, not confirmed economic anomalies. The Hotelling-style F threshold is a descriptive reference for individual squared distances in learned coordinates, not a calibrated significance test. Repeating deterministic PCA/hierarchical fits over seeds does not provide independent confirmations. Sector divergence refers to the legacy sector comparator and does not prove that a firm is in a wrong true cluster.

The taxonomy defines possible histories; the data need not populate every category. In this primary model the eligible geometric histories show resolved and transient flags, with no emerging or persistent geometric history. There is no positive three-date joint-agreement history among instruments with fully estimable channels. The report should state these absences rather than manufacture examples for every category.

## Financial-profile interpretation

The case question is: what changed in a firm's financial profile when its peer relationship changed? Report the observed feature changes, cluster profiles and their SHAP associations together. The frozen 2025 classifier provides an additive comparison within the same function; independently refitted per-date SHAP values must not be subtracted as if they came from one model. A separate regression surrogate describes associations with the distance screen itself.

An illustrative case is Naspers (NPN), which moves from aligned cluster 7 at the first date to cluster 0 at the second and remains there at the third. In the frozen 2025 classifier, changes in the destination-versus-source margin are associated most strongly with market capitalisation, share count and earnings yield. The reconstructed inputs show market capitalisation changing from approximately ZAR895.4 billion to ZAR818.6 billion, shares from 162.3 million to 741.1 million, and earnings yield from 9.60% to 8.92% between the first two dates. These are reconstructed inputs, not newly verified issuer observations. The share-count and capitalisation basis must be checked before interpreting this as an economic change; corporate-action or reconstruction effects could contribute. This is an attribute-association example, not a confirmed causal explanation of the peer-group shift.

The original primary model has 29 instruments stable at all three dates and 10 that shift at least once. The individual lists and case reports remain in the source archive. These counts describe reproducibly aligned memberships rather than an increase in independent sample size. Weak surrogate fidelity and imputed values constrain interpretation; in particular, the latest distance-surrogate OOF R-squared is negative. SHAP does not establish a causal explanation or confirm an outlier.

## Reporting boundary

The defensible contribution is repeated interpretable screening and the description of signal histories across three decision dates. It is not return prediction, confirmed anomaly detection, proof of distinct market regimes, or fully certified point-in-time empirical evidence. Source-backed historical validation and substantive case corroboration remain necessary.

Source experiment: `paper-exhaustive-k8-01`. This derived report contains no primary model refits and no baseline promotion.
