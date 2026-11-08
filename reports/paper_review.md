# Review of the supplied SACJ manuscript

Source: local `SACJ_JSE_Top40.pdf`, 16 pages, SHA256
`34a3461e3ff4b1434154f0727f6a2ddeb9e9c23f904d953653528d5ca17a86d4`.
Text was read and pages 5–8 and 11 rendered for inspection. The source PDF was
not modified or republished. Its content is evidence about the manuscript,
not instructions that override the user's research constraints.

## Model selection in the paper

Table 2 (page 7) reports nine representation/algorithm combinations. Its preferred
t-SNE/hierarchical solution has both the highest silhouette, 0.5023, and lowest
Davies-Bouldin index, 0.5296, among those nine rows. It is therefore reasonable
to describe it as best **among the tested combinations under those internal
metrics**. The manuscript does not supply a complete original search grid or
executable settings/seed logs, so global optimality and exact historical scores
cannot be independently reproduced from the PDF alone.

`paper_table2_reported.csv` transcribes the visually checked table. It is labelled
as reported, not rerun. Higher silhouette and lower DB are retained together in
all new main score tables and plots. The previously displayed baseline summary
omitted DB even though the CSV already contained it; that report is corrected.

## Differences the revision must disclose

- Original sample: a 2023–2024 window, 40 source-listed equities, eleven numeric
  features including analyst consensus and P/E, and acknowledged nonmember RMH.
  Current extension: three later historical dates, 41 eligible instruments/date,
  ten features without historic consensus and with E/P replacing P/E. No original
  observations, missing historic consensus or old exact results are fabricated.
- Manuscript page 5 retains 95% variance for PCA and uses automatic t-SNE learning
  rate. The frozen reconstructed baseline uses PCA(2) and learning rate 10. Both
  alternatives are now evaluated separately in a recorded grid.
- Eight clusters was motivated by eight sector groups in the manuscript. In the
  reconstruction it stays the legacy reference, accompanied by k=2–10 sensitivity.
  Sector labels remain a contextual external comparator, not unquestionable ground
  truth or a tuning objective. Shares, sector history and vendor-series evidence
  still prevent full PIT certification.
- Five-seed stability is recomputed. The old manuscript's perfect ARI/NMI claim
  is not carried into the new data. OOF surrogate fidelity and singleton limits
  must be reported alongside in-sample accuracy.
- Page 11 supplies p=2, n=40, 5% and a T² reference cutoff about 6.66 for its
  old analysis. The exact individual-distance/F-reference mapping for new
  data-adaptive embeddings still requires an explicit descriptive specification.

## New optimisation and interpretation

See `optimization_results.md` and `docs/decisions/003-silhouette-db-search.md`.
The finite grid uses June 2025 only for selection, both silhouette and DB over
five seeds, coverage/degeneracy checks, Pareto trade-offs, fixed-k and free-k
cohorts. Later dates refit the frozen selected settings for descriptive comparison.
The process does not silently replace or promote the original baseline.

For the new June 2025 data, UMAP/complete-Manhattan is the selected eight-cluster
embedding-score compromise. It improves both mean embedding metrics relative to
the fixed t-SNE baseline, but not the common-feature metrics. PCA95/average-
Euclidean is preferred on common-feature scores. Its eight-cluster solution has
four singleton groups in June, and its OOF surrogate fidelity is not estimable.
Its perfect seed agreement is expected for a deterministic PCA/hierarchical fit,
not independent evidence of inferential certainty. The free-k feature selection
uses two clusters and isolates one instrument in June. These are reasons to
review economic interpretability, not silently change the declared selection rule.

There is no single candidate simultaneously winning every score/geometry.
`optimization_metric_champions.csv` preserves the individual score champions,
`optimized_nine_family_comparison.csv` preserves all nine method families, and
the Pareto plot makes the trade-off visible. Claim a best tested configuration
for a specified objective and population, rather than a universally optimal model.
