"""What defines each cluster, and what changed for instruments that moved between clusters.

Everything here uses the Jaccard-aligned cluster ids, so "cluster 3" means the
same aligned group at every date and matches the cluster-flow diagram. Nothing
is refitted: the inputs are the saved partitions, seed fits and SHAP values.

Two kinds of evidence are kept apart:

- **Profiles** (median deviations, feature changes) describe the data directly.
- **SHAP** describes a gradient-boosted surrogate fitted separately at each date.
  It is comparable within a date, not across dates, and only as reliable as the
  surrogate's out-of-fold fidelity, which is reported next to it.

A move can happen because the instrument changed, or because the clusters
around it were redrawn. ``peer_retention`` and ``move_type`` separate the two.
"""
from textwrap import fill

import numpy as np
import pandas as pd

GUIDE = """# Cluster profiles and moves: column guide

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
"""


def _describe(deviations, labels, count=3):
    top = deviations.abs().sort_values(ascending=False).index[:count]
    return '; '.join(f'{"high" if deviations[f] > 0 else "low"} {labels[f]} ({deviations[f]:+.2f})' for f in top)


def _shap_lookup(folder, date):
    """SHAP array, ticker positions and class positions for one date's surrogate."""
    with np.load(folder / date / 'shap_values.npz', allow_pickle=False) as saved:
        values, tickers, classes = saved['values'], saved['tickers'].astype(str), saved['cluster_labels']
    return values, {t: i for i, t in enumerate(tickers)}, {int(c): i for i, c in enumerate(classes)}


def _seed_labels(folder, date, seeds):
    out = {}
    for seed in seeds:
        with np.load(folder / date / f'seed_{seed}.npz', allow_pickle=False) as saved:
            out[seed] = pd.Series(saved['clusters'], index=saved['tickers'].astype(str))
    return out


def _co_assignment(seed_fits, ticker, peers):
    if not peers:
        return None
    return float(np.mean([np.mean([fit[ticker] == fit[p] for p in peers]) for fit in seed_fits.values()]))


def explain_moves(name, assigned, aligned, snapshots, scaled, feature_set, model_folder, fidelity, seeds, out,
                  quality=None):
    """Write cluster profiles, move tables and figures for one primary model.

    ``assigned`` holds the representative-seed raw labels; ``aligned`` maps each
    date to aligned ids by ticker; ``snapshots`` and ``scaled`` give each date's
    inputs and scaled matrix in ticker order. ``quality`` maps each date to the
    representative fit's silhouette and Davies-Bouldin scores, shown on every figure.
    """
    from . import plots

    out.mkdir(parents=True, exist_ok=True)
    columns, labels = list(feature_set.columns), dict(zip(feature_set.columns, feature_set.labels))
    dates = list(snapshots)
    oof = fidelity.set_index('decision_date').oof_accuracy.to_dict()
    raw_label = {d: assigned[assigned.decision_date == d].set_index('ticker').cluster for d in dates}

    # Per-date frames indexed by ticker: raw values, scaled values, aligned cluster, own-class SHAP.
    tables, shap_of = {}, {}
    for date in dates:
        frame = snapshots[date].set_index('ticker')
        values, row, column = _shap_lookup(model_folder, date)
        table = frame[columns].copy()
        table[[f'scaled::{c}' for c in columns]] = scaled[date]
        table['cluster'] = aligned[date].reindex(frame.index).astype(int)
        tables[date] = table
        # SHAP of instrument t for the class of raw cluster r, as a feature Series.
        shap_of[date] = lambda t, r, v=values, row=row, column=column: pd.Series(v[row[t], :, column[int(r)]], columns)

    # --- cluster profiles -------------------------------------------------------------------
    profile_rows, summary_rows, medians = [], [], {}
    for date in dates:
        table = tables[date]
        scaled_cols = [f'scaled::{c}' for c in columns]
        date_median, date_median_scaled = table[columns].median(), table[scaled_cols].median()
        medians[date] = table.groupby('cluster')[scaled_cols].median().set_axis(columns, axis=1)
        for cluster, members in table.groupby('cluster'):
            deviation = members[scaled_cols].median().set_axis(columns) - date_median_scaled.set_axis(columns)
            raw = int(raw_label[date][members.index[0]])
            shap = np.array([shap_of[date](t, raw) for t in members.index])
            mean_abs, mean_signed = pd.Series(np.abs(shap).mean(0), columns), pd.Series(shap.mean(0), columns)
            for feature in columns:
                profile_rows.append(dict(
                    study_model=name, decision_date=date, cluster=int(cluster), n=len(members), feature=feature,
                    feature_label=labels[feature], cluster_median=float(members[feature].median()),
                    date_median=float(date_median[feature]), deviation_scaled=float(deviation[feature]),
                    deviation_rank=int(deviation.abs().rank(ascending=False)[feature]),
                    mean_abs_shap=float(mean_abs[feature]), mean_signed_shap=float(mean_signed[feature]),
                    shap_rank=int(mean_abs.rank(ascending=False)[feature]), surrogate_oof_accuracy=oof.get(date)))
            summary_rows.append(dict(
                study_model=name, decision_date=date, cluster=int(cluster), n=len(members),
                members=', '.join(sorted(members.index)), defining_features=_describe(deviation, labels),
                shap_top_features=', '.join(labels[f] for f in mean_abs.sort_values(ascending=False).index[:3]),
                surrogate_oof_accuracy=oof.get(date)))
    profiles, summary = pd.DataFrame(profile_rows), pd.DataFrame(summary_rows)
    profiles.to_csv(out / 'cluster_profiles.csv', index=False)
    summary.to_csv(out / 'cluster_summary.csv', index=False)

    histories = pd.DataFrame({d: aligned[d] for d in dates})
    colours = plots.cluster_colours(histories, dates)
    for date in dates:
        plots.cluster_profile_panels(profiles[profiles.decision_date == date], summary[summary.decision_date == date],
                                     feature_set, colours, out / f'cluster_profiles_{date}.png',
                                     f'{name}, {date}: what defines each cluster',
                                     quality[date] if quality else None)

    # --- moves -----------------------------------------------------------------------------
    move_rows, feature_rows = [], []
    for before, after in zip(dates, dates[1:]):
        old, new = tables[before], tables[after]
        common = old.index.intersection(new.index)
        seed_fits = _seed_labels(model_folder, after, seeds)
        for ticker in sorted(common):
            source, destination = int(old.cluster[ticker]), int(new.cluster[ticker])
            if source == destination:
                continue
            old_peers = sorted(t for t in common if t != ticker and old.cluster[t] == source)
            kept = [t for t in old_peers if new.cluster[t] == destination]
            new_peers = sorted(t for t in new.index if t != ticker and new.cluster[t] == destination)
            retention = len(kept) / len(old_peers) if old_peers else None
            move_type = ('no continuing peers' if retention is None else
                         'group redrawn' if retention >= .5 else 'instrument moved')
            x0 = old.loc[ticker, [f'scaled::{c}' for c in columns]].set_axis(columns)
            x1 = new.loc[ticker, [f'scaled::{c}' for c in columns]].set_axis(columns)
            change = x1 - x0
            source_before = medians[before].loc[source]
            destination_after = medians[after].loc[destination]
            peers_after = (new.loc[old_peers, [f'scaled::{c}' for c in columns]].median().set_axis(columns)
                           if old_peers else pd.Series(np.nan, columns))
            gap_destination, gap_old_peers = (x1 - destination_after).abs(), (x1 - peers_after).abs()
            fits = (gap_old_peers - gap_destination).dropna().sort_values(ascending=False)
            shap_destination = shap_of[after](ticker, raw_label[after][ticker])
            shap_source = shap_of[before](ticker, raw_label[before][ticker])
            destination_summary = summary[(summary.decision_date == after) & (summary.cluster == destination)].iloc[0]
            frame = snapshots[after].set_index('ticker').loc[ticker]
            caveats = [flag for flag in ['fundamentals_imputed', 'volume_imputed', 'volume_corrected']
                       if flag in frame and (bool(frame[flag]) or bool(snapshots[before].set_index('ticker').loc[ticker].get(flag, False)))]
            move_rows.append(dict(
                study_model=name, ticker=ticker, company=frame.company, sector_label=frame.sector_label,
                before=before, after=after, from_cluster=source, to_cluster=destination, move_type=move_type,
                peer_retention=retention, old_peers=', '.join(old_peers), peers_kept=', '.join(kept),
                new_peers=', '.join(new_peers),
                largest_changes='; '.join(f'{labels[f]} {change[f]:+.2f}'
                                          for f in change.abs().sort_values(ascending=False).index[:3]),
                fits_destination_on='; '.join(labels[f] for f in fits.index[:3] if fits[f] > 0),
                destination_defining_features=destination_summary.defining_features,
                shap_toward_destination='; '.join(f'{labels[f]} {shap_destination[f]:+.2f}'
                                                  for f in shap_destination.sort_values(ascending=False).index[:3]),
                support_new_peers=_co_assignment(seed_fits, ticker, new_peers),
                support_old_peers=_co_assignment(seed_fits, ticker, old_peers),
                surrogate_oof_accuracy_after=oof.get(after), data_caveat=', '.join(caveats)))
            for feature in columns:
                feature_rows.append(dict(
                    study_model=name, ticker=ticker, before=before, after=after, from_cluster=source,
                    to_cluster=destination, feature=feature, feature_label=labels[feature],
                    value_before=float(old.loc[ticker, feature]), value_after=float(new.loc[ticker, feature]),
                    scaled_before=float(x0[feature]), scaled_after=float(x1[feature]),
                    scaled_change=float(change[feature]), source_median_before=float(source_before[feature]),
                    destination_median_after=float(destination_after[feature]),
                    old_peers_median_after=float(peers_after[feature]),
                    gap_to_destination=float(gap_destination[feature]), gap_to_old_peers=float(gap_old_peers[feature]),
                    shap_destination_after=float(shap_destination[feature]),
                    shap_source_before=float(shap_source[feature])))
    moves = pd.DataFrame(move_rows) if move_rows else pd.DataFrame(columns=[
        'study_model', 'ticker', 'before', 'after', 'from_cluster', 'to_cluster', 'move_type',
        'peer_retention', 'largest_changes', 'support_new_peers', 'support_old_peers',
        'surrogate_oof_accuracy_after', 'data_caveat'])
    features = pd.DataFrame(feature_rows) if feature_rows else pd.DataFrame(columns=[
        'study_model', 'ticker', 'before', 'after', 'feature', 'scaled_change'])
    moves.to_csv(out / 'moves.csv', index=False)
    features.to_csv(out / 'move_features.csv', index=False)
    for move in moves.itertuples():
        detail = features[(features.ticker == move.ticker) & (features.before == move.before)]
        plots.move_panels(move, detail, feature_set, colours,
                          out / f'move_{move.before}_{move.after}_{move.ticker}.png', name, quality)
    (out / 'README.md').write_text(GUIDE, encoding='utf-8')
    return moves
