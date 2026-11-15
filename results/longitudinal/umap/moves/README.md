# Cluster profiles and moves: column guide

Cluster ids are Jaccard-aligned, so an id names the same group across dates and
matches `cluster_flows.png`. Scaled values use the June 2025 MinMax scaling, so
a scaled difference of 0.1 is a tenth of that feature's June 2025 range.

## cluster_profiles.csv (one row per date, cluster and feature)

- `cluster_median`, `date_median`: medians in the feature's own units.
- `deviation_scaled`: cluster median minus the date median, scaled. Positive
  means the cluster is high on that feature.
- `deviation_rank`: 1 = the feature on which the cluster differs most.
- `mean_abs_shap`, `mean_signed_shap`, `shap_rank`: how much the date's
  surrogate relies on the feature to place members in this cluster. Read
  together with `surrogate_oof_accuracy`.

## cluster_summary.csv (one row per date and cluster)

`members`, `n`, `defining_features` (top three deviations, high or low),
`shap_top_features`, and `surrogate_oof_accuracy`.

## moves.csv (one row per instrument that changed aligned cluster)

- `from_cluster` at `before`, `to_cluster` at `after`.
- `old_peers`: the instrument's cluster-mates at `before` that are still in the
  index. `peers_kept`: those still in its cluster at `after`.
- `peer_retention`: share of old peers kept. `move_type` is "group redrawn" when
  most peers moved with it (the cluster changed around it), "instrument moved"
  when it left most of its peers, "no continuing peers" when it was a singleton
  or all its old peers left the index.
- `new_peers`: its cluster-mates at `after`.
- `largest_changes`: the three features whose scaled value changed most.
- `fits_destination_on`: features where, at `after`, the instrument is closer to
  the destination cluster median than to its former peers' median.
- `destination_defining_features`: what characterises the destination cluster.
- `shap_toward_destination`: features the `after` surrogate credits most for
  placing it in the destination cluster.
- `support_new_peers`, `support_old_peers`: across all seeds at `after`, the
  average share of new (old) peers that share its cluster. A move is robust when
  the first is high and the second low; if both are similar, the move is within
  fitting noise.
- `data_caveat`: imputed or corrected inputs for this instrument.

## move_features.csv (one row per move and feature)

Raw and scaled values before and after, the change, the source cluster median at
`before`, the destination median and the old peers' median at `after`, the gaps
to each, and the instrument's SHAP for the destination class at `after` and for
the source class at `before`.
