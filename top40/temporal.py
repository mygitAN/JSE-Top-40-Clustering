"""Compare partitions across dates without confusing index changes with cluster changes.

Cluster numbers from independent fits are arbitrary, so each date's labels are
aligned to the previous date by a Hungarian match on Jaccard overlap among
instruments present at both dates. Entries and exits are separate events and
never count as a cluster change.
"""
import numpy as np
import pandas as pd


def align_members(old, new, objective='jaccard'):
    """Relabel ``new`` to match ``old``. Unmatched clusters get fresh ids.

    Both arguments are label Series indexed by ticker. Returns the relabelled
    Series and one detail record per new cluster.
    """
    from scipy.optimize import linear_sum_assignment

    if objective not in {'jaccard', 'overlap'}:
        raise ValueError('Unknown alignment objective')
    if not old.index.is_unique or not new.index.is_unique:
        raise ValueError('Unique ticker keys required')
    common = old.index.intersection(new.index)
    a, b = sorted(old.unique()), sorted(new.unique())
    left = {c: set(common[(old.loc[common] == c).to_numpy()]) for c in a}
    right = {c: set(common[(new.loc[common] == c).to_numpy()]) for c in b}
    counts = np.array([[len(left[i] & right[j]) for j in b] for i in a], dtype=float).reshape(len(a), len(b))
    unions = np.array([[len(left[i] | right[j]) for j in b] for i in a], dtype=float).reshape(len(a), len(b))
    similarity = np.divide(counts, unions, out=np.zeros_like(counts), where=unions > 0)
    rows, cols = linear_sum_assignment(-(similarity if objective == 'jaccard' else counts))
    mapping = {b[c]: a[r] for r, c in zip(rows, cols) if counts[r, c] > 0}
    next_id = max(a, default=-1) + 1
    details = []
    for j in b:
        matched = j in mapping
        if not matched:
            mapping[j] = next_id
            next_id += 1
        i = mapping[j]
        intersection = len(left.get(i, set()) & right[j])
        union = len(left.get(i, set()) | right[j])
        details.append(dict(raw_cluster=int(j), aligned_cluster=int(i), continuing_intersection=intersection,
                            continuing_union=union, jaccard=intersection / union if union else 0.,
                            matched=matched))
    return new.map(mapping), details


def aligned_histories(snapshots, dates):
    """Chain Jaccard alignment through ``dates``.

    ``snapshots`` maps each date to a frame with ``ticker`` and ``cluster``.
    Returns aligned label Series per date, the alignment map, per-pair events,
    per-instrument histories and a comparison with the overlap objective.
    """
    from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

    aligned = {dates[0]: snapshots[dates[0]].set_index('ticker').cluster}
    maps, events, objective_checks, agreement = [], [], [], []
    next_id = int(aligned[dates[0]].max()) + 1
    for before, after in zip(dates, dates[1:]):
        old, raw = aligned[before], snapshots[after].set_index('ticker').cluster
        _, details = align_members(old, raw, 'jaccard')
        for detail in details:
            # An id that disappeared is never reused for a later, unrelated cluster.
            if not detail['matched']:
                detail['aligned_cluster'] = next_id
                next_id += 1
        new = raw.map({d['raw_cluster']: d['aligned_cluster'] for d in details})
        aligned[after] = new
        by_overlap, _ = align_members(old, raw, 'overlap')
        maps.extend(dict(before=before, after=after, **d) for d in details)
        common = old.index.intersection(raw.index)
        agreement.append(dict(before=before, after=after, continuing=len(common),
                              entries=len(raw.index.difference(old.index)),
                              exits=len(old.index.difference(raw.index)),
                              ari=float(adjusted_rand_score(old.loc[common], raw.loc[common])),
                              nmi=float(normalized_mutual_info_score(old.loc[common], raw.loc[common])),
                              changed=int((old.loc[common] != new.loc[common]).sum())))
        for ticker in sorted(old.index.union(raw.index)):
            both = ticker in old.index and ticker in raw.index
            events.append(dict(before=before, after=after, ticker=ticker,
                               membership_event='continuing' if both else 'entry' if ticker in raw.index else 'exit',
                               cluster_before=int(old[ticker]) if ticker in old.index else None,
                               cluster_after=int(new[ticker]) if ticker in raw.index else None,
                               cluster_changed=bool(old[ticker] != new[ticker]) if both else None))
            if both:
                objective_checks.append(dict(before=before, after=after, ticker=ticker,
                                             jaccard_changed=bool(old[ticker] != new[ticker]),
                                             overlap_changed=bool(old[ticker] != by_overlap[ticker])))
    histories = []
    for ticker in sorted(set().union(*(set(v.index) for v in aligned.values()))):
        labels = [int(aligned[d][ticker]) if ticker in aligned[d].index else None for d in dates]
        observed = all(label is not None for label in labels)
        status = ('stable' if len(set(labels)) == 1 else 'shifted') if observed else 'membership gap'
        histories.append(dict(ticker=ticker, **dict(zip(dates, labels)), observed_all_dates=observed,
                              stability_status=status))
    return (aligned, pd.DataFrame(maps), pd.DataFrame(events), pd.DataFrame(histories),
            pd.DataFrame(objective_checks), pd.DataFrame(agreement))


def membership_matrices(old, new):
    """Movement counts and Jaccard overlap between every pair of clusters, on continuing instruments."""
    if not old.index.is_unique or not new.index.is_unique:
        raise ValueError('Unique instrument keys required')
    common = old.index.intersection(new.index)
    left, right = sorted(old.unique()), sorted(new.unique())
    a = {c: set(common[(old.loc[common] == c).to_numpy()]) for c in left}
    b = {c: set(common[(new.loc[common] == c).to_numpy()]) for c in right}
    counts = pd.DataFrame([[len(a[i] & b[j]) for j in right] for i in left], index=left, columns=right)
    unions = pd.DataFrame([[len(a[i] | b[j]) for j in right] for i in left], index=left, columns=right)
    jaccard = counts.div(unions.where(unions > 0))
    counts.index.name = jaccard.index.name = 'source_aligned_cluster'
    return counts, jaccard, len(common)


def sector_context(frame):
    """Does each instrument's sector differ from the majority sector of its other cluster members?

    Singletons and tied majorities are left unresolved rather than counted as agreement.
    """
    rows = []
    for row in frame.itertuples():
        others = frame[(frame.cluster == row.cluster) & (frame.ticker != row.ticker)]
        counts = others.sector_label.value_counts()
        modes = sorted(counts[counts == counts.max()].index) if len(counts) else []
        status = 'singleton' if not modes else 'tied majority' if len(modes) > 1 else 'compared'
        rows.append(dict(ticker=row.ticker, cluster=int(row.cluster), sector_label=row.sector_label,
                         cluster_size=len(others) + 1, other_member_majority='; '.join(modes),
                         sector_divergence=(row.sector_label != modes[0]) if len(modes) == 1 else None,
                         sector_status=status))
    return pd.DataFrame(rows)
