# Full experiment notebook

Open `notebooks/paper_experiments.ipynb`, select the project `.venv` kernel and
run the cells in order. Install `requirements-notebook.txt` for notebook support.
The equivalent command is:

```bash
python scripts/paper_experiments.py
```

For read-only review, set `REUSE_COMPLETED_RUN` in the notebook setup cell to
`"paper-exhaustive-k8-01"`. The archive is verified before display; no models,
registry or artifacts are changed. Leave it `None` for a fresh experiment.

Each fresh execution reserves a fresh immutable run ID. The complete result starts at
`experiments/runs/<id>/paper_results.md`. The older
`three_cross_section_study.ipynb` remains the fixed-comparison walkthrough; it
does not replace this explicit optimisation workflow.

## What is optimised

The grid has 86 representations and 38 valid clustering specifications per
representation: 3,268 configurations, each evaluated at five seeds. All 16,340
selection-score rows, including invalid-score and noise cases, are retained.
`configs/paper_experiments.json` records the exact choices. This is exhaustive
within those lists, rather than every possible real-valued parameter or every
clustering algorithm in existence.

PCA, t-SNE and UMAP are compared with hierarchical clustering, K-Means and
DBSCAN. The hierarchy tests single, complete, average and Ward linkages;
Euclidean, Manhattan, Chebyshev and cosine distances are used where valid.
Ward/non-Euclidean combinations are explicitly excluded. The reduction input
distance is varied separately from the hierarchy's fitting distance. K-Means
uses its Euclidean squared-distance objective. DBSCAN works on axis-standardised
representations, with its own distance, epsilon and minimum-sample choices.
Its score calculations exclude noise and display coverage; embedding scores
use the unstandardised representation consistently across algorithms.

Hierarchical and K-Means paper candidates fix k=8. Overall winners must have
eight clusters, full coverage and valid scores on all seeds. The shared
aggregation additionally restricts eligible density-family comparisons to 2–10
clusters; all other DBSCAN outcomes still appear in the complete trials table.
An empty eligible family is reported, not hidden or assigned a fabricated winner.
Later k=2–12 curves are diagnostics for selected hierarchical settings.

The primary selection minimises the sum of ranks of mean silhouette (descending)
and mean Davies–Bouldin (ascending), measured in the same original June-scaled
financial-feature space. Tie-breaks use mean seed ARI, feature silhouette and
candidate ID. An alternative ranks embedding-space scores. Individual metric
champions, Pareto fronts, nine-family winners and full parameter JSON are exported.
No sector statistic participates in selection. A finite-grid optimum under one
objective need not win under the other objective, and score selection itself
creates optimism in the June results.

Preprocessing is fitted on June 2025. Selected settings are frozen and each
representation/partition is independently refitted at each date. Later dates
have already been examined in the project; they are descriptive follow-ups,
not untouched test sets or predictions. Report every date, not only favourable
ones, and report variability across seeds rather than calling it bootstrap
uncertainty. PCA with full SVD and hierarchical clustering is deterministic on the same inputs, so repeated seeds for those fits are identical rather than independent replications.

## Trees and longitudinal membership

Every selected hierarchical model has three dendrograms from the actual fitted
AgglomerativeClustering tree, including all dimensions used for fitting.
Non-hierarchical models are not presented as dendrogram models. Maps show the
first two coordinates; PCA95 clustering may use more dimensions.

Hungarian maximum-Jaccard alignment uses only continuing instruments. Sorted
labels and the deterministic solver resolve the same input reproducibly; zero
overlap is unmatched, and fresh IDs are never reused. The files also compare
maximum overlap and direct 2025-to-current alignment. Label matching does not
establish persistent economic cluster identities. List individual instruments
as stable all three dates or shifted at least once only when all three
observations exist. Separate baseline-to-current changes, intermediate changes,
index entries/exits and alignment-objective sensitivity.

## Descriptive outlier and sector flags

For each selected main model/date/seed, use the first two representation
coordinates, same-date mean and unbiased covariance. The statistic is the
individual squared Mahalanobis distance D², without an n multiplier. The
paper-style reference is p(n−1)/(n−p) times the 95th F(p,n−p) quantile, with
p=2 and the actual n. This is a **descriptive reference**, not the individual
distance's null distribution or a confirmed significance test. The report also
saves a one-sided internal Beta reference
((n−1)²/n) Beta⁻¹(0.95; p/2,(n−p−1)/2) as a sensitivity. Both normal-theory
calibrations have unverified assumptions on learned manifold coordinates.
Singular/ill-conditioned covariance produces no flag, rather than a pseudoinverse
that makes degenerate data look ordinary.

The distinction between mean T² and individual distance calibration follows
[NIST's Hotelling discussion](https://www.itl.nist.gov/div898/handbook/pmc/section5/pmc543.htm)
and its [individual versus subgroup control-chart cases](https://www.itl.nist.gov/div898/software/dataplot/refman1/auxillar/hotell.htm).
The F reference is retained for continuity with the paper, with the limitation
made explicit rather than presented as formal confirmation.

A multi-seed-supported candidate exceeds the F reference at seed 42 and in at
least three of five estimable seeds. This is still not a confirmed outlier.
The three-date supported-flag patterns are: 000 never flagged; 001/011 emerging;
111 persistent; 010 transient; 100/110 resolving; 101 recurring. Missing membership
or an unestimable screen means no three-date history classification.

Sector divergence uses the other members' majority sector within a firm's
cluster. A tie or singleton is unresolved. A separate maximum-overlap one-to-one
sector mapping is descriptive, and not a tuning target or verified historical
ground-truth accuracy measure. A geometric candidate, sector divergence and
singleton are distinct flags. Both Investec securities remain in the model:
41 instrument observations represent 40 economic groups at each date.

## Three SHAP targets

1. Each date's gradient-boosted classifier explains associations with cluster
   membership. In-sample fidelity, OOF fidelity, class mapping and raw-margin
   additivity remain explicit. OOF pseudo-label fidelity does not validate
   unsupervised discovery.
2. A separate regression surrogate explains associations with the geometric
   distance itself. Train/OOF R² and OOF MAE accompany its SHAP output. Weak OOF
   fidelity limits any attribute interpretation; a cluster surrogate's importance
   alone is not an explanation of the distance screen.
3. Temporal attribution holds the June-2025 classifier fixed. For a continuing
   instrument, calculate destination-minus-source class SHAP contrasts at the
   baseline and later input vectors, then difference them. The feature sum must
   equal the change in the same-model raw-margin contrast. These describe input
   associations in a fixed function, not a causal explanation of independently
   refitted clusters. Unmatched destinations have no 2025 class and are marked
   not estimable. Identical source/destination classes give zero contrasts by
   construction, which does not mean unchanged finances.

SHAP's model-output and feature-dependence assumptions are documented in the
[TreeExplainer reference](https://shap.readthedocs.io/en/latest/generated/shap.TreeExplainer.html).
Independent per-date SHAP values are not subtracted and relabelled as temporal
causal effects. Case reports retain all ten feature contributions, raw changes,
population deviations, imputation flags and surrogate fidelity. Substantive
issuer evidence is still needed to validate an economic explanation or confirm
an outlier. Historical source-certification blockers remain unresolved.
