# JSE Top 40 Clustering

An EDA-to-SHAP workflow extending the original single-window SACJ study to three
historical FTSE/JSE Top 40 cross-sections.

The paper's reporting direction is **structural-signal dynamics**: emerging,
persistent, resolving and related histories, with cluster shifts, geometric
screening and sector divergence kept separate. Read the
[working reporting example](reports/anomaly_dynamics_reporting_example.md) and
[reporting protocol](docs/reporting_direction.md). The primary design keeps k=8;
the separate varying-k sensitivity and revised taxonomy preserve all old outputs.

## Start here: EDA, experimentation and optimisation

Open **[notebooks/paper_experiments.ipynb](notebooks/paper_experiments.ipynb)**
with the project `.venv` kernel and choose **Run All**. It shows EDA first, all
3,268 declared parameter combinations over five seeds, joint silhouette/DB
selection, exact winning parameters, all-date dendrograms, named stable/shifted
instrument lists, Hotelling descriptive screens, sector divergence and SHAP
attribute reviews. See the [experiment guide](docs/paper_experiments_guide.md).

```bash
python scripts/paper_experiments.py
```

## Fixed-comparison walkthrough

Open **[notebooks/three_cross_section_study.ipynb](notebooks/three_cross_section_study.ipynb)**
in VS Code, select the project `.venv` kernel and choose **Run All**.

The notebook walks through:

1. Validate and load all 123 instrument-date observations.
2. **EDA:** population, missing cases, imputations, distributions, correlations and sector context.
3. **Modelling:** PCA/t-SNE/UMAP with hierarchical clustering, K-Means and DBSCAN at every date.
4. **Plots and scores:** silhouette **and** Davies-Bouldin in embedding/common-feature space, maps, profiles and dendrograms.
5. **SHAP:** gradient-boosted surrogate explanations, class mapping, additivity and in-sample/OOF fidelity.
6. **Temporal comparisons:** continuing members, index entries/exits and aligned transition tables.

The command-line equivalent runs the same stages:

```bash
python scripts/run_study.py
```

Each execution creates a new tracked `experiments/runs/<run_id>/` folder.
Start reading its **`study_summary.md`**. The original t-SNE baseline and the frozen
UMAP sensitivity are labelled separately; settings are not retuned on later dates.
The paper's hierarchical/K-Means models use **k=8**, matching the original
eight-sector design. Other k values remain diagnostics; DBSCAN reports its
natural cluster/noise count as a separate comparator.
See the [step-by-step study guide](docs/study_guide.md) for setup, file locations
and the meaning of the plots.

Each snapshot contains **40 company groups represented by 41 listed instruments**. Investec Limited (INL) and Investec plc (INP) are separate securities in one dual-listed company (DLC) group; both remain in the instrument-level analysis. Exited members are excluded at subsequent dates until an effective re-entry. See [the population audit](reports/population_count_audit.md) for sources and scope.

Study claim: a repeated, interpretable cross-sectional investment-screening
process. See the [ORiON methods-to-results checklist](docs/orion_methods_results_checklist.md)
for the evidence matrix, ten-feature variant, implemented results and pending
screening specifications. Reconstructed inputs do not become certified PIT
observations through modelling.

## Install dependencies

Use Python 3.11 or 3.12 in VS Code or a terminal. Windows Python 3.11.14
was executed locally with every pinned top-level dependency; see the
[full environment lock](configs/environment-windows-py311.txt). Windows/3.11 and
Ubuntu/3.12 CI passed for the earlier recorded commit; see
[recorded check evidence](reports/ci_status.json).

```bash
python -m venv .venv
# Activate .venv (Windows: .venv\Scripts\activate; macOS/Linux: source .venv/bin/activate)
python -m pip install -r requirements.txt
# For the interactive notebook, install the notebook support as well:
python -m pip install -r requirements-notebook.txt
python scripts/run_study.py
```

The notebook and command-line workflow use the same tested Python modules.
The supporting scripts below remain available for individual experiments.

<details>
<summary>Advanced: validation, individual experiments and saved-result printing</summary>

```bash
python scripts/validate_data.py
python -m unittest discover -s tests -v
python scripts/run_analysis.py --mode baseline --experiment baseline
# Full comparisons, five seeds (42–46), k=2–10, and SHAP on every date:
python scripts/run_analysis.py --mode full --experiment fixed-suite
# Explicitly requested finite-grid optimisation: both silhouette and DB:
python scripts/optimize_models.py
# Build the compact results/plots using the completed run ID:
python scripts/summarize_optimization.py silhouette-db-search-01
# Print the supplied UMAP grid's saved winners and parameters without refitting:
python scripts/tune_umap.py --print-run user-umap-grid-01
# Run that 36-combination grid and its selected-embedding k sweep again:
python scripts/tune_umap.py
# Fixed UMAP from the latest snippet: neighbors=3, min_dist=0.01, k=2..12:
python scripts/tune_umap.py --config configs/umap_fixed_001.json
python scripts/tune_umap.py --print-run fixed-umap-001-01
```

</details>

Outputs go to unique immutable `experiments/runs/<run_id>/` directories. Each run
has a status, diagnostic log, exact configuration, code snapshot, input hashes,
environment, artifacts and checksums. `experiments/registry.csv` has one record
per run. A `COMPLETED` marker is written only after required outputs, checksums
and registry updates succeed. Failed runs are retained. Never reuse a run ID.
`--output` changes the registry root, not a reusable run directory.
`--skip-shap` explicitly requests an incomplete smoke test and is recorded in
configuration. `--mode baseline` still exports k/seed sensitivity diagnostics.

The [review package](reports/reviewer_guide.md) links saved results. Full bundles,
including plots, models and SHAP arrays, are small enough to commit in Git.
No expiring Actions artifact is the sole archive. `experiments/baseline.json`
holds the specification pointer and an intentionally unpromoted results pointer.

The [joint silhouette/DB optimisation results](reports/optimization_results.md)
report both scores, the full nine-family comparison, seed variability and
Pareto trade-offs. The [paper review](reports/paper_review.md) records differences
between the supplied SACJ manuscript and the reconstructed baseline. The bounded
[search protocol](docs/decisions/003-silhouette-db-search.md) uses June 2025 alone
for selection and preserves the baseline. Expensive optimisation is optional in
CI through the `optimize_models` workflow-dispatch input.

Verify and reproduce a saved run (replace the IDs with those in the registry):

```bash
python scripts/verify_run.py experiments/runs/final-full-42
python scripts/run_analysis.py --mode full --seed 42 --stability-runs 5 --experiment fixed-suite --purpose "All three dates; nine combinations; seeds 42-46; k=2-10; SHAP" --run-id my-reproduction
python scripts/compare_runs.py experiments/runs/final-full-42 experiments/runs/my-reproduction --report reports/my-reproduction.json
```

Use the matching code commit recorded in `status.json`, or extract its
`source_snapshot.zip` into a separate clean directory for dirty-worktree runs.
Install the archived environment lock there for the closest local reproduction.
`resolved_config.json` records overrides. Comparison checks CSVs, numerical NPZ
contents and deterministic model/manifest JSON with rtol=1e-7, atol=1e-6 for
tables/arrays. Images and archive timestamps need not have identical bytes.
Run IDs, purposes and timestamps differ and are excluded from numerical checks.

Registry updates use an exclusive lock and atomic replacement. After a killed
process, inspect the owner in `.registry.lock` before removing an abandoned lock.
A stale `running` record or a directory without `COMPLETED` is not a successful run.
See [analysis method](docs/analysis_method.md)
for recovered historical settings, explicit new implementation choices, and
interpretation limits. The primary baseline is t-SNE + hierarchical clustering,
with sector held out for external comparison.

## Data

- 30 June 2025, 31 December 2025 and 30 June 2026.
- 41 instruments at each date: 123 rows and 43 distinct tickers.
- Every historical index member is retained, including unresolved observations.
- Market cap, shares outstanding, sector, return, volume, beta, volatility, dividend yield, revenue, EPS and earnings yield are included.

| File | Purpose |
| --- | --- |
| `data/processed/Top40_Retrospective_Model_Inputs_v1.csv` | Modelling inputs with raw and model-only imputed values |
| `data/source/Top40_PIT_Verification_v4.xlsx` | Audit workbook, underlying inputs, source URLs and field-level evidence |
| `docs/Top40_Retrospective_Model_Method_v1.json` | Selection, imputation, clipping and evidence policy |
| `scripts/validate_data.py` | Dataset checks using the Python standard library |

## Research policy

This is a retrospective public-source reconstruction, not a certified investor-observable point-in-time backtest. Later restatements are permitted, although this version retains the issuer values already in the v4 workbook. Prices and other market features come from reconstructed vendor daily history. Historical shares and sector labels remain unverified; market cap reconciles to close times shares. Sector uses the existing eight legacy Listcorp labels, not a newly verified historical 11-industry ICB mapping.

Membership changes are index entries/exits, not ordinary cluster transitions: NPH replaced GLN in June 2025, GLN replaced APN in September 2025, and PAN replaced MNP in March 2026.

Reinet remains in all snapshots. Its unresolved raw fundamentals stay blank. Training medians populate separate model columns and are flagged with `fundamentals_imputed`. The two missing AGL volume observations are imputed and marked `volume_imputed`. Imputed earnings yield is not an accounting identity with separately imputed EPS; do not interpret either as reported company data.

Earnings yield replaces P/E for modelling. Imputation and 1st/99th percentile clipping were fitted on June 2025 only. The supplied train/validation/test labels do not make independently refitted cross-sections an out-of-sample prediction test. The baseline holds sector out for external interpretation; it is not an ordinal numeric input. Scaling is fitted on June 2025 only. Keep identifiers, evidence fields, dates and raw alternatives out of the numeric feature matrix. Examine sensitivity to imputation, correlated size features and extreme observations before interpreting clusters.

## Validate

Python 3.10 or later; no packages required:

```bash
python scripts/validate_data.py
```

Validation checks membership, unique keys, retained unresolved rows, model-feature completeness, missingness flags, imputation constants, clipping, and cap arithmetic. It does not independently certify the source data. Analyst ratings are not inferred or included.

## Data reuse

Source attribution is retained in the workbook. Public availability does not imply unrestricted redistribution rights. No blanket open-data licence is asserted for third-party data.
