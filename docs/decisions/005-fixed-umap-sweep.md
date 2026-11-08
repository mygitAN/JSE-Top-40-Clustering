# Fixed UMAP score sweep

The user's latest code fixes neighbors=3 and min_dist=0.01 and requests k=2–12,
printing both scores and a dual-axis plot. This is a distinct sensitivity from
the previous two-stage grid, whose selected min_dist was 0.1.

`configs/umap_fixed_001.json` records the supplied settings. The added
fixed-embedding mode fits one UMAP representation for June 2025 and computes
all eleven partitions without parameter-pair optimisation. The pre-existing
joint silhouette/DB rank rule identifies a compromise; the individual score
winners are printed separately. Company/ticker labels replace undefined
location-specific fields, and unused seaborn is not added as a dependency.

Run `fixed-umap-001-01` preserves all 41 instruments per date. Its selected k=5
is independently refitted with the same settings on the later dates, using the
unchanged June-fitted preprocessing. This single-seed exploration leaves the
paper baseline pointer and archived original runs unchanged. See
`reports/fixed_umap_001_results.md` for actual results and commands.
