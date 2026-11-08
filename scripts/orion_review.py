"""ORiON reporting checks derived from saved partitions; no model refit or promotion."""
import argparse
import json
from pathlib import Path

from tracking import ROOT, Run, digest, write_json
from verify_run import verify_completed

DATES = ['2025-06-30', '2025-12-31', '2026-06-30']


def align_members(old, new, objective='jaccard'):
    import numpy as np
    from scipy.optimize import linear_sum_assignment
    if objective not in {'jaccard', 'overlap'}:
        raise ValueError('Unknown alignment objective')
    if not old.index.is_unique or not new.index.is_unique:
        raise ValueError('Unique ticker keys required')
    common = old.index.intersection(new.index)
    a, b = sorted(old.unique()), sorted(new.unique())
    left = {c: set(old.loc[common][old.loc[common] == c].index) for c in a}
    right = {c: set(new.loc[common][new.loc[common] == c].index) for c in b}
    counts = np.array([[len(left[i] & right[j]) for j in b] for i in a], dtype=int).reshape(len(a), len(b))
    unions = np.array([[len(left[i] | right[j]) for j in b] for i in a], dtype=int).reshape(len(a), len(b))
    similarity = np.divide(counts, unions, out=np.zeros_like(counts, dtype=float), where=unions > 0)
    cost = similarity if objective == 'jaccard' else counts
    rows, cols = linear_sum_assignment(-cost)
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
        details.append(dict(objective=objective, raw_cluster=int(j), aligned_cluster=int(i),
                            continuing_intersection=intersection, continuing_union=union,
                            jaccard=intersection/union if union else 0,
                            status='matched' if matched else 'unmatched: fresh descriptive ID'))
    return new.map(mapping), details


def pair_events(old, new, aligned):
    rows = []
    for ticker in sorted(old.index.union(new.index)):
        before, after = ticker in old.index, ticker in new.index
        event = 'continuing' if before and after else 'entry' if after else 'exit'
        rows.append(dict(ticker=ticker, membership_event=event,
                         cluster_changed=bool(old[ticker] != aligned[ticker]) if before and after else None))
    return rows


def deviation_comparison(frame, scaled, features, shap_table):
    import numpy as np
    import pandas as pd
    overall = np.median(scaled, axis=0)
    rows = []
    for cluster in sorted(frame.cluster.unique()):
        members = frame.cluster.to_numpy() == cluster
        local = shap_table[shap_table.cluster == cluster].set_index('feature').reindex(features)
        if local.mean_abs_shap_members.isna().any():
            raise ValueError('Missing SHAP feature/cluster importance')
        dev = np.median(scaled[members], axis=0) - overall
        for j, feature in enumerate(features):
            rows.append(dict(cluster=int(cluster), n=int(members.sum()), feature=feature,
                             cluster_median_scaled=float(np.median(scaled[members, j])),
                             snapshot_median_scaled=float(overall[j]), signed_median_deviation=float(dev[j]),
                             absolute_median_deviation=float(abs(dev[j])),
                             mean_abs_shap_members=float(local.loc[feature, 'mean_abs_shap_members']),
                             imputation_sensitive=bool(frame.loc[members, ['fundamentals_imputed', 'volume_imputed']].any().any()),
                             interpretation='singleton: descriptive only' if members.sum() == 1 else 'descriptive association'))
    result = pd.DataFrame(rows)
    for value, name in [('absolute_median_deviation', 'univariate_rank'), ('mean_abs_shap_members', 'shap_rank')]:
        result[name] = result.groupby('cluster')[value].rank(method='average', ascending=False)
    summaries = []
    for cluster, sub in result.groupby('cluster', sort=True):
        estimable = sub.univariate_rank.nunique() > 1 and sub.shap_rank.nunique() > 1
        summaries.append(dict(cluster=int(cluster), n=int(sub.n.iloc[0]),
                              rank_correlation=float(sub.univariate_rank.corr(sub.shap_rank)) if estimable else None,
                              status='descriptive rank comparison; no p-value' if estimable else 'not estimable: constant ranks'))
    return result, pd.DataFrame(summaries)


def derive(source, out):
    import numpy as np
    import pandas as pd
    verify_completed(source)
    assignments = pd.read_csv(source/'assignments.csv')
    if len(assignments) != 123 or assignments.duplicated(['decision_date', 'ticker']).any():
        raise ValueError('Invalid source assignments')
    comparisons, summaries, alignments, events = [], [], [], []
    for date in DATES:
        sub = assignments[assignments.decision_date == date].set_index('ticker')
        with np.load(source/date/'baseline_arrays.npz', allow_pickle=False) as data:
            sub = sub.loc[data['tickers']].reset_index()
            expected = json.loads((ROOT/'configs/baseline.json').read_text(encoding='utf-8'))['features']
            if list(data['features']) != expected or not np.isfinite(data['scaled_features']).all():
                raise ValueError('Saved feature contract or finiteness check failed')
            if list(sub.cluster) != list(data['clusters']):
                raise ValueError('Saved assignment/array mismatch')
            table, summary = deviation_comparison(sub, data['scaled_features'], list(data['features']),
                                                   pd.read_csv(source/date/'shap_by_cluster.csv'))
        sectors = sub.groupby('cluster').sector_label.agg(lambda x: '; '.join(sorted(set(x))))
        table['sector_labels_context'] = table.cluster.map(sectors)
        table.insert(0, 'decision_date', date); summary.insert(0, 'decision_date', date)
        comparisons.append(table); summaries.append(summary)
    pd.concat(comparisons).to_csv(out/'shap_univariate_comparison.csv', index=False)
    pd.concat(summaries).to_csv(out/'shap_univariate_rank_summary.csv', index=False)
    snapshots = {d: assignments[assignments.decision_date == d].set_index('ticker').cluster for d in DATES}
    for before, after in zip(DATES, DATES[1:]):
        for objective in ['overlap', 'jaccard']:
            aligned, details = align_members(snapshots[before], snapshots[after], objective)
            alignments.extend(dict(before=before, after=after, **row) for row in details)
            for row in pair_events(snapshots[before], snapshots[after], aligned):
                ticker = row['ticker']
                metadata = assignments[assignments.ticker == ticker].set_index('decision_date')
                events.append(dict(before=before, after=after, objective=objective,
                                   sector_before=metadata.loc[before, 'sector_label'] if before in metadata.index else None,
                                   sector_after=metadata.loc[after, 'sector_label'] if after in metadata.index else None,
                                   imputation_sensitive=bool(metadata.loc[metadata.index.intersection([before, after]),
                                                ['fundamentals_imputed', 'volume_imputed']].any().any()), **row))
    pd.DataFrame(alignments).to_csv(out/'alignment_objective_comparison.csv', index=False)
    pd.DataFrame(events).to_csv(out/'alignment_membership_events.csv', index=False)
    tickers = sorted(assignments.ticker.unique())
    observation = pd.DataFrame({'ticker': tickers})
    for date in DATES:
        observation[date] = observation.ticker.isin(snapshots[date].index)
    observation['eligible_all_three_dates'] = observation[DATES].all(axis=1)
    observation['eligible_first_pair'] = observation[DATES[:2]].all(axis=1)
    observation['eligible_second_pair'] = observation[DATES[1:]].all(axis=1)
    observation.to_csv(out/'temporal_observation_eligibility.csv', index=False)
    # Accounting diagnostic only: a P/E-based clustering sensitivity is not claimed.
    earnings = assignments[['decision_date', 'ticker', 'sector_label', 'eps_zar_raw', 'close_zar', 'earnings_yield_raw',
                            'earnings_yield_model_clipped', 'fundamentals_imputed']].copy()
    earnings['pe_status'] = np.select([earnings.eps_zar_raw.isna(), earnings.eps_zar_raw <= 0],
                                     ['unresolved raw EPS', 'nonpositive EPS: P/E nonmeaningful'], default='positive EPS')
    earnings['raw_pe_positive_eps_only'] = (earnings.close_zar/earnings.eps_zar_raw).where(earnings.eps_zar_raw > 0)
    earnings.to_csv(out/'earnings_yield_and_pe_diagnostic.csv', index=False)
    earnings.groupby(['decision_date', 'pe_status']).size().rename('n').to_csv(out/'pe_case_counts.csv')
    write_json(out/'reporting_manifest.json', dict(source_run=source.name, model_refitted=False, promotion=False,
        observation_counts={d: int(observation[d].sum()) for d in DATES},
        observed_all_three=int(observation.eligible_all_three_dates.sum()),
        univariate_definition='cluster median minus same-snapshot median in the saved June-2025-MinMax-scaled ten-feature space',
        comparison='within-cluster feature ranks; SHAP own-class mean absolute margins; no inferential p-values',
        alignment='independent adjacent pairs on continuing-member sets; sorted labels; maximum sum Jaccard versus overlap; zero-overlap unmatched',
        pending=['Hotelling statistic/reference/cutoff specification', 'flag definitions and time windows',
                 'P/E sensitivity specification beyond missing/loss accounting', 'archived source validation']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-run', default='final-full-42')
    parser.add_argument('--run-id')
    args = parser.parse_args()
    if Path(args.source_run).name != args.source_run:
        parser.error('--source-run must be a saved run ID')
    source = ROOT/'experiments/runs'/args.source_run
    config = dict(experiment='orion-methods-results-check', source_run=args.source_run,
                  refit=False, alignment_objectives=['overlap', 'jaccard'],
                  univariate_reference='same-snapshot median, June-scaled features', tie_ranks='average')
    with Run(ROOT/'experiments', config, config['experiment'],
             'Descriptive associations and label-alignment audit of saved baseline; no promotion', args.run_id) as run:
        run.provenance()
        run.meta['derived_source_manifest_sha256'] = digest(source/'artifact_checksums.json')
        derive(source, run.out)
    print(f'Completed {run.meta["run_id"]}: {run.out}')


if __name__ == '__main__':
    main()
