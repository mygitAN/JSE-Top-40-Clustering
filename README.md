# JSE Top 40 clustering

Do FTSE/JSE Top 40 companies fall into stable peer groups on their financial
characteristics, and do those groups change in ways worth tracking?

This repository extends an earlier single-date clustering study to three dates:
30 June 2025, 31 December 2025 and 30 June 2026. Each date has 41 listed
instruments (40 company groups; Investec has two lines), giving 123 rows and 43
distinct tickers.

## Manuscript

Edit [paper/main.tex](paper/main.tex) and its section files. In the GitHub-linked
Overleaf project, select `paper/main.tex` as the main document. The original
Python cluster maps and dendrograms are included in `paper/figures/python/`.
See [paper/README.md](paper/README.md) for building and updating figures.
The duplicate `output/paper/` manuscript export has been retired.

## Status

The work is exploratory. The pipeline is reproducible, but the evidence that the
clusters are economically meaningful is still weak:

- **Feature definitions change the answer.** Partitions from the original ten
  features and from the share-basis-invariant set agree only moderately
  (adjusted Rand index about 0.43 to 0.62).
- **Scaling fitted on June 2025 lets one feature dominate later dates.** In
  December 2025 the one-year return carries a third to two thirds of the total
  scaled variance, whichever feature set is used.
- **There is no external validation yet**, and the only noise reference is
  agreement between random seeds.

Next steps are listed at the end.

## Run it

Python 3.11 or 3.12.

```bash
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements-notebook.txt   # exact Windows versions: requirements-lock-windows-py311.txt

python -m top40.data              # validate the inputs (standard library only)
python -m unittest discover -s tests -t .
python -m top40                   # full study, about two minutes
```

Or open [notebooks/three_cross_section_study.ipynb](notebooks/three_cross_section_study.ipynb),
select the `.venv` kernel and choose **Run All**. The notebook calls the same
code and shows every table and figure in order.

Each run writes a new folder under `experiments/runs/<run id>/`; start with its
`summary.md`. Run folders stay local and are not committed.

## Results

[results/](results/) is the committed copy of the tables and figures the paper
cites, all from one run. [results/manifest.json](results/manifest.json) names
that run, its code commit and the checksum of every file. To refresh it from a
new run, and to check it has not been edited by hand:

```bash
python -m top40.export experiments/runs/<run id>
python -m top40.export --check
```

Export replaces the whole folder, so it never mixes runs. Only cite results whose
manifest shows `"git_dirty": false`. The manifest identifies the exact implementation commit used to generate the export.
An [executed review notebook](reports/three_cross_section_review.ipynb) retains the
plots and tables for viewing without rerunning the study.

## Feature sets

Choose one with `--feature-set` or `FEATURE_SET` in the notebook. The default is
set in [configs/study.json](configs/study.json).

| Name | Status | Features |
| --- | --- | --- |
| `original10` | Archived reference | Return, volume, market cap, beta, shares, revenue, EPS, volatility, dividend yield, earnings yield |
| `logsize10` | Diagnostic | The same ten with log volume, market cap, shares and revenue |
| `invariant8` (default) | Candidate | Return, beta, volatility, dividend yield, earnings yield, log market cap, log revenue/cap, log turnover |
| `market5` | Diagnostic | Return, beta, volatility, dividend yield, earnings yield |

`original10` reproduces the earlier results exactly. It includes raw share count
and EPS, which change mechanically when a company subdivides its shares: Naspers'
five-for-one subdivision on 6 October 2025 multiplies its recorded share count by
4.57 while the count on a common basis falls to 0.91. Nothing in `invariant8`
changes under a subdivision.

All sets except `original10` were defined after the earlier results had been
examined. They are pilot-informed, not pre-registered.

## What a run does

| Stage | Output folder | Content |
| --- | --- | --- |
| 1. Load | | Validate the inputs against the source workbook; fit scaling on June 2025 only |
| 2. Explore | `eda/` | Population, imputed cases, distributions, rank correlations |
| 3. Audit features | `feature_audit/` | Share-basis changes, feature dominance, the same recipe on every feature set |
| 4. Fit models | `comparison/`, `models/` | PCA, t-SNE and UMAP with hierarchical, K-Means and DBSCAN at one seed; the study model over five seeds |
| 5. Explain | `models/` | Cluster profiles, and a gradient-boosted surrogate explained with SHAP |
| 6. Compare dates | `longitudinal/` | Jaccard-aligned cluster histories, entries and exits kept separate, a feature-space distance screen |
| 7. Finish | | Check every expected output, write `summary.md`, mark the run completed |

## The study model

UMAP followed by agglomerative clustering, fitted separately at each date with
the same settings:

| Step | Setting |
| --- | --- |
| Scaling | MinMax, fitted on 30 June 2025 only |
| Dimensionality reduction | `umap.UMAP`: 2 components, 3 neighbours, min_dist 0.01, Euclidean |
| Clustering | `sklearn.cluster.AgglomerativeClustering` on the UMAP coordinates: 8 clusters, average linkage, Manhattan distance |
| Seeds | 42 to 46; seed 42 is the representative fit |

Each run writes the full specification, with package versions, to
`model_specification.csv` and `summary.md`. The settings were chosen after
exploring the June 2025 data, and k=8 is the original paper's choice (it matched
eight sector labels); neither is pre-registered or evidence of eight natural
groups.

The original paper's recipe (t-SNE, perplexity 5, then the same clustering) stays
in the model comparison as the `tsne_hierarchical` row, for reference.

## Layout

```
configs/study.json        dates, seeds, model settings, default feature set
data/source/              audit workbook with field-level sources
data/processed/           the 123-row model inputs and their imputation policy
data/reference/           sourced corrections: subdivisions, volume basis, Investec shares
top40/                    the package
  data.py                   load and validate inputs
  features.py               feature sets and derived columns
  models.py                 scaling, representations, clustering, scores, distance screen
  ablation.py               feature-validity comparison
  explain.py                surrogate and SHAP
  temporal.py               alignment and histories across dates
  eda.py, plots.py          tables and figures
  study.py, report.py       the staged run and its summary
  tracking.py               run folders, checksums, registry
  export.py                 copy one run's cited outputs into results/
results/                  committed tables and figures from one named run
notebooks/                the walkthrough
tests/
docs/method.md            method, data policy and limits
```

## Data limits

The inputs are a retrospective reconstruction from public sources, not a
verified point-in-time dataset. See [docs/method.md](docs/method.md). In short:

- Share counts, market capitalisation and sector labels are unverified.
- Reinet's fundamentals are imputed at all three dates, and Anglo American's
  volume at two.
- Volume is JSE trading only, which understates liquidity for companies whose
  main listing is abroad.

Three corrections are applied to the derived features, with sources in
[data/reference/](data/reference/); the raw inputs are unchanged:

- **Naspers subdivision:** recorded, so shares and EPS can be compared on one
  basis.
- **Naspers volume:** restated to post-subdivision units at December 2025 and
  June 2026. It previously mixed both bases.
- **Investec:** each line gets its own share count, from Investec's disclosed
  per-issuer counts. Both lines previously carried the combined dual-listed
  count, and so the whole group's market cap.

Source attribution is in the workbook. Third-party data is not relicensed here.

## Next steps

1. **Scaling.** Decide between scaling fitted on June 2025 and per-date robust
   scaling, and report how many shifts survive the choice.
2. **Noise floor.** Resample instruments within each date and compare
   date-to-date change against within-date variability.
3. **External validation.** Test whether clusters at one date explain return
   co-movement over the following six months better than sector labels and
   random partitions. This needs daily prices, which are not in the repository.
   Fix the evaluation rules before the 31 December 2026 window closes.
4. **Data.** Verified point-in-time share counts for all instruments, and total
   (not JSE-only) volume for foreign-listed companies.

## History

Everything before the November 2026 clean-up, including the 3,268-configuration
grid search, 32 archived runs and the earlier reports, is preserved at the git
tag `archive/pre-slim-2026-11-14`.
