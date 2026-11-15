# Editable LaTeX paper

This folder is the working source for future manuscript updates. Open `main.tex`
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
| `sections/07_conclusion.tex` | Conclusion |
| `sections/appendix_reproducibility.tex` | Provenance and reproducibility |
| `references.tex` | References and citation keys |
| `preamble.tex` | Packages, typography and shared diagram styles |
| `figures/*.tex` | Fourteen editable TikZ and PGFPlots diagrams |
| `diagrams.tex` | Separate atlas containing all diagrams |

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

For Overleaf, upload this folder and select `main.tex` as the main document.
The project has no external image dependency: the diagrams are drawn in LaTeX.

## Updating diagrams and numbers

For example, edit `figures/alignment.tex` to change diagram text or positions.
Its caption and placement are in `sections/04_methods.tex`. Shared node and
arrow styles are in `preamble.tex`.

Numerical diagrams currently contain coordinates generated from the archived
study tables. Editing a CSV in `data/` alone does not regenerate those coordinates.
For a new analysis run, refresh the source tables, diagram coordinates, manuscript
numbers and provenance together. `figure_sources.json` records the current sources.

The existing `make_figures.py` and vector PDFs in `figures/` are retained as a
separate figure-generation workflow. The current LaTeX manuscript inputs the
native `.tex` diagrams.
