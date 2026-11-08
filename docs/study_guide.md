# Three-cross-section study: step-by-step guide

The aim is to extend the original single-window SACJ study to three historical
cross-sections for a revised paper. This guide explains the complete EDA-to-SHAP
workflow. It does not assume that repeating the analysis alone resolves the
remaining evidence limitations or guarantees acceptance by another journal.

## Open the notebook

1. Open `notebooks/three_cross_section_study.ipynb` in VS Code.
2. Select the project's `.venv` Python kernel in the top-right kernel picker.
3. Install `requirements-notebook.txt` in that environment if needed.
4. Choose **Run All**, or run the cells in their numbered order.

For a new checkout, create the environment first:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements-notebook.txt
```

If you prefer a terminal, the complete equivalent is:

```bash
python scripts/run_study.py
```

Both entry points call the same `StudySession` methods. Every run has its own
immutable output folder and registry record. No tracking server or paid service
is needed. Never reuse a run ID to overwrite previous results.

## Follow the analysis in order

| Stage | What to inspect | What it answers |
| --- | --- | --- |
| 1. Inputs | 41 instruments at each date; 123 records; 43 distinct tickers; evidence flags | Which observations and fields are actually available? |
| 2. EDA | Missing-case table, model-only imputations, raw descriptive statistics, distributions, correlations and sector context | What does the data look like before clustering? |
| 3. Modelling | All nine representation/algorithm combinations at each snapshot, plus the fixed UMAP sensitivity | Do different methods produce different descriptive partitions? |
| 4. Cluster plots | Both silhouette/DB geometries, membership maps, median profiles and dendrograms | How separated are groups, who belongs to them, and which financial features differ? |
| 5. SHAP | Global/per-cluster bars, class distribution plot, feature deviations, class mapping and additivity | Which original variables influence the surrogate's cluster-membership margins? |
| 6. Fidelity and time | In-sample versus OOF fidelity, pairwise seed ARI/NMI, continuing-member transitions and entry/exit events | Are descriptions sensitive to seeds, surrogate fitting or changing index membership? |

The dates are 2025-06-30, 2025-12-31 and 2026-06-30. Each adjacent pair has 40
continuing instruments. Only 39 are observed at all three dates. These are
overlapping historical populations, not 123 independent firms.

## EDA comes before models

The notebook first validates the supplied workbook/CSV and preserves unresolved
cases. RNI's raw fundamentals stay blank, with model-only June-median fills and
flags. AGL's two volume imputations remain flagged. No rows disappear because
raw data are unresolved. Analyst recommendations are unavailable and excluded.

Raw descriptive statistics retain the financial units. Distribution plots use
the common MinMax transformation fitted on June 2025 only. Values in later dates
can exceed [0,1]. Correlations include the flagged model values; high correlations
are reported for interpretation rather than silently removing baseline features.
Sector labels remain context and do not enter the ten-feature model matrix.

## Keep the two model roles clear

**Recovered baseline:** 2D t-SNE, perplexity 5, learning rate 10, 300 iterations,
random initialisation, then average-linkage Manhattan clustering with k=8.
The comparison also retains PCA/UMAP and K-Means/DBSCAN. Configuration lives in
`configs/baseline.json`.

**Fixed UMAP sensitivity:** neighbours=3, min_dist=0.01, average-linkage Manhattan,
k=8, fixed by the user's original eight-sector design. Other k values are
sensitivity diagnostics only. This is a review candidate, not an
automatically promoted main specification. Configuration lives in `configs/study.json`.
Both model roles are refitted independently at each date with fixed parameters.
The default workflow compares five seeds per date for each role.

The notebook reports both silhouette (higher is better) and Davies-Bouldin (lower
is better). They use Euclidean score geometry; fitting the hierarchy uses the
declared Manhattan linkage. DBSCAN noise is excluded from quality scores, and
coverage remains visible. A high score after excluding many instruments is not
equivalent to full-population separation.

## Read SHAP correctly

SHAP explains an XGBoost surrogate trained on the discovered cluster labels.
It does not directly explain the clustering algorithm, establish causality or
forecast investment returns. Global bars, class-specific distributions and
within-cluster tables have different aggregations, explained in the notebook.

For every model/date the workflow checks dimensions, feature order, class mapping
and raw-margin additivity, and saves feature values, tickers, SHAP/base values and
margins. In-sample accuracy and stratified OOF accuracy are separate. Singleton
clusters make stratified OOF not estimable and do not support reliable subgroup
inference. OOF fidelity to full-snapshot pseudo-labels does not validate discovery.

## Find the saved outputs

The notebook prints its unique run ID and output path. Each complete bundle has:

```text
study_summary.md                 Read this first
eda/                            EDA tables and figures
model_comparison.csv            All models, both silhouette/DB geometries and coverage
primary_model_summary.csv       Baseline and UMAP sensitivity by date, with fidelity/stability
models/<date>/                  Baseline plots, arrays, profiles, surrogate and SHAP
umap_sensitivity/<date>/         Fixed UMAP candidate plots, arrays, profiles, surrogate and SHAP
seed_stability.csv              All pairwise seed ARI/NMI comparisons
temporal_agreement.csv          Continuing-member ARI/NMI
temporal_observation_eligibility.csv
study_manifest.json             Resolved study choices and population checks
status.json, run.log             Provenance, status and diagnostics
source_snapshot.zip             Matching code, notebook, configuration and inputs
artifact_checksums.json         Exact-byte artifact hashes
COMPLETED                       Present only after all stages/checks succeed
```

The original source notebook is kept without generated outputs so the code stays
easy to read. A separately saved executed copy under `reports/` demonstrates the
actual Run All outputs. Images/tables are also ordinary files in the run bundle;
you can use them without opening the notebook.

To verify a saved bundle:

```bash
python scripts/verify_run.py experiments/runs/<run_id>
```

If a kernel is stopped before finishing, do not call that run completed. A phase
error is recorded as failed; a killed kernel may leave running status. Start a
new session/run ID instead of writing over its files. Later notebook figures can
be inspected by changing `VIEW_DATE`; this does not refit or tune models.

## Implementation map

- `scripts/study_workflow.py`: the readable stage order and tracking lifecycle.
- `scripts/study_eda.py`: population/missingness/evidence tables and EDA figures.
- `scripts/study_plots.py`: cluster maps, profiles, SHAP distribution and transitions.
- `scripts/study_reporting.py`: final report and required artifact validations.
- `scripts/analysis.py`: shared baseline modelling, scores, surrogate SHAP and alignment.
- `scripts/run_study.py`: one command that runs the same stages as the notebook.

The three-snapshot extension adds empirical contexts and descriptive temporal
checks. It does not certify historic share counts/capitalisation, sector history
or vendor series. The original eleven-feature SACJ experiment and current
ten-feature historic-consensus-excluded variant remain distinct. No Hotelling
cutoff or emerging/persistent/resolving anomaly taxonomy is invented here.
