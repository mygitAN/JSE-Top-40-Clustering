# Full experimentation and longitudinal review

Date: 8 November 2026. User requested an EDA-first experiment trail showing
distance/linkage/reduction/algorithm tuning, exact chosen parameters, both
silhouette and Davies–Bouldin, dendrograms across dates, stable/shifted instrument
lists, geometric statistics, sector disagreement and attribute explanations.

The new entry point is `notebooks/paper_experiments.ipynb`, backed by
`scripts/paper_experiments.py`, `paper_search.py` and `paper_longitudinal.py`.
The existing fixed-comparison walkthrough and all old results are preserved.
The finite grid is declared in `configs/paper_experiments.json`: 86
representations, 3,268 configurations and 16,340 selection fits over five seeds.
All valid combinations of the listed settings are tested; incompatible Ward
metrics are recorded as exclusions. Hierarchical and K-Means use fixed k=8.
No unbounded or globally optimal search claim is made.

Common-feature joint silhouette/DB ranking is the primary exploratory selection
criterion, with embedding ranking reported as a sensitivity. Five-seed full
coverage, eligibility and deterministic tie-breaks are explicit. The full trials
table retains density outcomes with noise or unavailable scores; the shared
eligibility aggregation restricts density-family winners to 2–10 clusters.
Sector statistics do not select parameters. Later dates have already been
examined, so the subsequent frozen-parameter refits are descriptive follow-ups.

Hungarian Jaccard histories separate common members from entry/exit and compare
alignment objectives. The two Investec securities remain distinct observations
within one group. Each selected hierarchical model gets the actual fitted tree.

The Hotelling-style extension explicitly uses individual D², p=2, same-date
unbiased covariance and the paper-style mean-T² F expression only as a
descriptive reference. An internal Beta reference and multi-seed support are
additional sensitivities. No screen/consensus/SHAP result confirms an outlier.
The exact history taxonomy and observation eligibility are specified in the
[experiment guide](../paper_experiments_guide.md).

Cluster classifiers, distance regressors and frozen-2025 class-contrast changes
have separate SHAP targets and fidelity checks. Frozen contrasts use the same
model at both feature vectors and are checked for additive margin changes.
They do not establish the causal reason for a partition changing after an
independent refit. Source certification, substantive outlier confirmation and
the separate P/E sensitivity remain unresolved. No baseline promotion occurs.
