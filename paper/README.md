# Editable LaTeX paper

This folder is the working source for future manuscript updates. The original
`SACJ_JSE_Top40.pdf` is the designated writing-style reference. Open `main.tex`
in your editor. It assembles the separate sections below; the paper's wording
lives in those section files.

| File | What to edit |
| --- | --- |
| `main.tex` | Title, author, date and section order |
| `sections/00_abstract.tex` | Abstract and keywords |
| `sections/01_introduction.tex` | Introduction and research question |
| `sections/02_related_work.tex` | Literature review |
| `sections/03_population_and_inputs.tex` | Population, inputs and corrections |
| `sections/04_methods.tex` | Methods, equations and matching procedure |
| `sections/05_results.tex` | Results, tables, figure captions and figure placement |
| `sections/06_discussion.tex` | Discussion |
| `sections/06_limitations_and_future_work.tex` | Limitations and future research |
| `sections/07_conclusion.tex` | Conclusion |
| `references.tex` | References and citation keys |
| `preamble.tex` | Packages, typography and shared diagram styles |
| `figures/*.tex` | Thirteen editable TikZ and PGFPlots diagrams |
| `figures/cluster_map_*.pdf` | Cluster maps with aligned cluster numbers, from `make_figures.py` |
| `figures/python/*.png` | Four original Python figures: dendrograms and Jaccard overlap |
| `tables/*.tex` | Data-driven tables written by `make_tables.py` |
| `diagrams.tex` | Complete atlas retaining all seventeen figures |

## Build and preview

From the repository root, run:

```powershell
.\paper\build.ps1
```

Open `paper/build/main.pdf` beside the source. Edit, save, and run the same
command to refresh the PDF. To compile both the paper and the diagram atlas:

```powershell
.\paper\build.ps1 -Target Both
```

The build script uses the project's portable Tectonic compiler when available,
then checks for Tectonic, latexmk or pdfLaTeX on PATH. Generated PDFs and logs
stay in the ignored `build/` directory.

For the linked GitHub repository in Overleaf, select `paper/main.tex` as the main document.
If uploading just this folder, select `main.tex`. All required images are included.
There is one manuscript source under `paper/`; the obsolete `output/paper/` export
has been removed. Build previews stay in the ignored `paper/build/` folder.

## Updating diagrams and numbers

For example, edit `figures/alignment.tex` to change diagram text or positions.
Its caption and placement are in `sections/04_methods.tex`. Shared node and
arrow styles are in `preamble.tex`.

Numerical diagrams currently contain coordinates generated from the archived
study tables. Editing a CSV in `data/` alone does not regenerate those coordinates.
For a new analysis run, refresh the source tables, diagram coordinates, manuscript
numbers and provenance together. `figure_sources.json` records the current sources.

## Cluster maps beside dendrograms

Each date's figure pairs a cluster map with the original Python dendrogram.

The maps are drawn by `make_figures.py` from the archived clean run. They show
the same UMAP coordinates and partition as the run's own `cluster_map.png`,
but numbered and coloured with the Jaccard-aligned cluster ids used in the rest
of the paper, so a cluster keeps its number and colour across dates. Each map
reports silhouette and Davies-Bouldin in both the financial features and the
map; asterisks flag imputed inputs.

The dendrograms and the Jaccard overlap figure are unchanged copies of the
run's PNGs. `import_python_figures.py` copies them after checking their
SHA-256 checksums against the run, and records them in
`python_figure_sources.json`. Dendrogram leaves carry ticker and sector labels;
branch colours are independent of cluster colours.

To refresh both from the run named by `results/manifest.json`:

```powershell
.venv/Scripts/python.exe paper/make_figures.py
.venv/Scripts/python.exe paper/import_python_figures.py
.\paperuild.ps1 -Target Both
```

`make_figures.py` also writes other vector figures that the paper does not use.
Overleaf compilation needs only the committed files in `paper/`.

## Data-driven tables

`make_tables.py` writes the complete model comparison (`tables/model_comparison.tex`)
and the sector-agreement table (`tables/sector_agreement.tex`) from `results/`
and the source run, and saves `data/sector_context.csv`. It also writes the
forward co-movement tables (`tables/comovement.tex`, `tables/comovement_pairs.tex`)
from the frozen outputs in `research/comovement/output/`. Rerun it after a new run
is exported:

```powershell
.venv/Scripts/python.exe paper/make_tables.py
```

## UMAP and t-SNE comparison

Section 4.6 and Tables 8 and 9 come from `compare_methods.py`, which fits the
UMAP model and the t-SNE comparator through the same pipeline (features,
scaling, clustering, five seeds and cross-date matching) and writes
`data/method_quality.csv`, `data/method_groups.csv`,
`data/method_histories.csv` and `data/method_switches.csv`. Regenerate with:

```powershell
.venv/Scripts/python.exe paper/compare_methods.py
```

## Selected movement attributions

Table source `data/selected_move_attributions.csv` is a subset of
`results/longitudinal/umap/moves/move_features.csv`. The export checksum and
all 16 selected values were checked against the archived destination-class
SHAP tensors, using each date's raw-to-aligned membership mapping. Table values
are rounded raw-margin contributions from the fitted surrogate, not financial
changes or probabilities.

## One manuscript with all diagrams

All seventeen figures are included in `main.tex` through the section files,
near the methods and results they explain. There is no separate supplement.
The concise limitations text, UMAP rationale and clarified SHAP attributions
remain in the paper. Grouped SHAP rows contain identical individual values
before rounding, not averages.

Compile `paper/main.tex` in the linked Overleaf repository. The optional
`diagrams.tex` atlas is only a development preview of the same figures;
it is not a separate part of the manuscript.
