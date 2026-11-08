# Supplied UMAP grid and best-parameter printing

The user supplied a concrete grid and asks to print its best scores and parameters,
along with a cluster-count curve and dendrogram. This follow-up implements that
grid rather than substituting the previous search's chosen configuration.

Configuration: `configs/user_umap_grid.json`. The supplied malformed cluster list
is repaired as `[7, 10, 11, 12]`. UMAP neighbors are `[3,5,10]` and minimum
distances `[0.01,0.04,0.1]`; average linkage/Manhattan and seed 42 are preserved.
Stage one evaluates all 36 combinations and caches its nine embeddings. Stage two
evaluates k=2–15 on the selected stage-one embedding, not the last loop embedding.
Selection reuses the already documented joint rank of silhouette and DB; each
individual metric champion is printed as well.

The completed run `user-umap-grid-01` prints and exports the selected parameters.
It fits the final frozen parameters independently on the two later dates as
descriptive follow-ups. The four-cluster result is an exploratory sensitivity,
not a replacement of the eight-cluster baseline. Seed-42 scores are not described
as means across seeds, and this two-stage grid is not a full Cartesian 9×14 search.

Saved scores, plots, printing commands and limitations are documented in
`reports/user_umap_grid_results.md`. No raw source values, promotion pointer or
historical memberships were changed.
