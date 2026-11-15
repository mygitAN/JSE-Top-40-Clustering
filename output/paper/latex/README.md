# LaTeX manuscript and native diagrams

Compile `main.tex` twice with pdfLaTeX (or use `latexmk -pdf main.tex`).
Compile `diagrams.tex` for the separate diagram atlas. Tectonic is also supported:

```
tectonic main.tex
tectonic diagrams.tex
```

All 14 diagrams are native TikZ or PGFPlots. No PNG or externally drawn PDF is needed.
`figures/` contains the reusable LaTeX inputs; `data/` contains the saved numerical source tables.
`figure_sources.json` records the provenance and the checksum-verified cluster-count source.
The manuscript retains the supplied literature and uses native equations and author-year citations.
Upload this complete folder (or its ZIP) to Overleaf and choose `main.tex` as the main document.

Five additions: overlapping annual windows; observed Jaccard matching example;
seed-pair variability; feature-representation sensitivity; separate evidence streams.
The original nine diagrams have also been redrawn natively.
