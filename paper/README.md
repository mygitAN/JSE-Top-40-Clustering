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
| `figures/python/*.png` | Seven original Python figures: maps, dendrograms and Jaccard overlap |
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

The manuscript includes the original Python-generated `cluster_map.png` and
`dendrogram.png` for each date, copied unchanged from the archived clean run.
They appear side by side at reduced size on standard portrait pages. No model is rerun and these images are not recreated in TikZ. `python_figure_sources.json` records their
archive paths and verified SHA-256 checksums.

The Jaccard overlap figure is also copied unchanged from
`results/longitudinal/umap/jaccard.png`, checked against its export and archive
checksums.

Cluster numbers in these original maps are local to each fit. The member lists
define the groups; asterisks flag imputed inputs. Dendrogram leaves carry ticker
and sector labels, and branch colours are independent of map colours. Use the
aligned identifiers in the longitudinal figures for comparisons between dates.

To refresh the copies from the archived run named by `results/manifest.json`:

```powershell
.venv/Scripts/python.exe paper/import_python_figures.py
.\paper\build.ps1 -Target Both
```

Overleaf compilation needs only the committed files in `paper/`, including the
seven PNGs. Python and the local run archive are needed only for refreshing them.
The older `make_figures.py` remains an optional separate plotting workflow; its
vector PDFs are not used for these cluster maps or dendrograms.

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
