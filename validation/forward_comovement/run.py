"""Frozen-peer forward validation. Run with .venv/Scripts/python.exe validation/forward_comovement/run.py.

The initial preparation reads the existing Yahoo cache, without network calls.
Subsequent runs use the committed price/cohort snapshots and verify their hashes.
Outputs are separate from the paper and the original results/ archive.
"""
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
HERE = Path(__file__).resolve().parent
METRICS = ('sector', 'cross_cluster', 'matched')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepare(protocol):
    """Freeze source cohorts and prices; preserve original inputs and labels."""
    from top40.data import load_inputs
    from top40.features import add_derived_columns

    data = HERE / 'data'
    manifest_path = data / 'manifest.json'
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        for name, digest in manifest['snapshot_sha256'].items():
            if sha(data / name) != digest:
                raise ValueError(f'Snapshot changed: {name}')
        if manifest['protocol_sha256'] != sha(HERE / 'protocol.json'):
            raise ValueError('Protocol differs from the frozen data manifest.')
        return manifest

    manifest = json.loads((ROOT / 'results/manifest.json').read_text())
    if manifest['run_id'] != protocol['study_run']:
        raise ValueError('Unexpected source study run.')
    inputs = add_derived_columns(load_inputs(), protocol['formation_dates'][0])
    histories = pd.read_csv(ROOT / 'results/longitudinal/umap/cluster_histories.csv').set_index('ticker')
    cohorts, source_files = [], {}
    for date in protocol['formation_dates']:
        path = ROOT / f'results/models/umap/{date}/assignments.csv'
        relative = path.relative_to(ROOT / 'results').as_posix()
        if sha(path) != manifest['files'][relative]:
            raise ValueError(f'Study export checksum mismatch: {relative}')
        source_files[path.relative_to(ROOT).as_posix()] = sha(path)
        assignments = pd.read_csv(path).set_index('ticker')
        frame = inputs[inputs.decision_date == date].copy().sort_values('ticker')
        if set(frame.ticker) != set(assignments.index) or len(frame) != 41:
            raise ValueError('Formation population does not match frozen fit.')
        frame['cluster'] = histories.loc[frame.ticker, date].to_numpy(dtype=int)
        frame['raw_cluster'] = assignments.loc[frame.ticker, 'cluster'].to_numpy(dtype=int)
        # Aligned labels may rename a partition, but may not change any pair.
        a, b = frame.cluster.to_numpy(), frame.raw_cluster.to_numpy()
        if not np.array_equal(a[:, None] == a, b[:, None] == b):
            raise ValueError('Aligned history changes the frozen partition.')
        frame['economic_group'] = frame.ticker.replace({'INL': 'INVESTEC', 'INP': 'INVESTEC'})
        frame['formation_log_market_cap'] = np.log10(frame.market_cap_line)
        frame['formation_volatility'] = frame.annualised_volatility_1y
        frame['high_formation_volatility'] = frame.formation_volatility > frame.formation_volatility.quantile(.9)
        cohorts.append(frame[['decision_date', 'ticker', 'economic_group', 'sector_label', 'cluster',
                              'raw_cluster', 'formation_log_market_cap', 'formation_volatility',
                              'high_formation_volatility']])
    cohort = pd.concat(cohorts, ignore_index=True)
    prices, caches = [], {}
    symbols = sorted(set(cohort.ticker + '.JO') | {'^J200.JO'})
    for symbol in symbols:
        path = ROOT / '.runtime/beta_prices' / (symbol.replace('^', 'IDX_') + '.json')
        d = json.loads(path.read_text())
        if d['meta']['symbol'] != symbol:
            raise ValueError(f'Unexpected cache symbol for {symbol}')
        dates = pd.to_datetime(d['timestamp'], unit='s').tz_localize('UTC').tz_convert(
            d['meta']['exchangeTimezoneName']).normalize().tz_localize(None)
        table = pd.DataFrame({'date': dates, 'symbol': symbol,
                              'close': d['indicators']['quote'][0]['close'],
                              'adjusted_close': d['indicators']['adjclose'][0]['adjclose']})
        if table.date.duplicated().any():
            raise ValueError(f'Duplicate trading dates: {symbol}')
        table = table[(table.date >= protocol['formation_dates'][0]) &
                      (table.date <= protocol['evaluation_windows'][-1][1])]
        prices.append(table)
        caches[path.relative_to(ROOT).as_posix()] = sha(path)
    data.mkdir(parents=True, exist_ok=True)
    cohort.to_csv(data / 'cohorts.csv', index=False)
    pd.concat(prices, ignore_index=True).sort_values(['date', 'symbol']).to_csv(data / 'prices.csv', index=False)
    source_files['results/manifest.json'] = sha(ROOT / 'results/manifest.json')
    source_files['data/processed/Top40_Retrospective_Model_Inputs_v1.csv'] = sha(
        ROOT / 'data/processed/Top40_Retrospective_Model_Inputs_v1.csv')
    source_files['results/longitudinal/umap/cluster_histories.csv'] = sha(
        ROOT / 'results/longitudinal/umap/cluster_histories.csv')
    record = {'study_run': manifest['run_id'], 'protocol_sha256': sha(HERE / 'protocol.json'),
              'vendor': 'Yahoo Finance chart responses cached by validation/audit_beta.py',
              'cached_request': 'https://query2.finance.yahoo.com/v8/finance/chart/{symbol}?period1=2024-06-01&period2=2026-07-05&interval=1d (dates shown for readability)',
              'source_sha256': source_files, 'original_cache_sha256': caches,
              'snapshot_sha256': {name: sha(data / name) for name in ['cohorts.csv', 'prices.csv']}}
    manifest_path.write_text(json.dumps(record, indent=2) + '\n')
    return record


def return_panel(prices, tickers, formation, start, end, field):
    """Compute returns before slicing, retaining the first forward day's return."""
    symbols = [t + '.JO' for t in tickers] + ['^J200.JO']
    wide = prices.pivot(index='date', columns='symbol', values=field).sort_index().reindex(columns=symbols)
    window = wide.loc[formation:end]
    if window.empty or (window <= 0).any().any() or window.isna().any().any():
        raise ValueError('Missing/nonpositive price in frozen forward calendar.')
    returns = window.pct_change(fill_method=None).loc[start:end]
    if returns.isna().any().any() or (returns.abs() > .4).any().any():
        raise ValueError('Missing return or daily move above 40%; inspect source, do not silently trim.')
    if (returns.index <= pd.Timestamp(formation)).any():
        raise ValueError('Evaluation includes formation/training returns.')
    return returns.iloc[:, :-1].to_numpy(), returns.iloc[:, -1].to_numpy(), returns.index


def residualise(x, market):
    xc, mc = x - x.mean(axis=0), market - market.mean()
    return xc - np.outer(mc, mc @ xc / (mc @ mc))


def weight_system(frame):
    """Build formation-only contrasts, balanced by economic company, not pairs."""
    frame = frame.reset_index(drop=True)
    n = len(frame)
    sectors, labels, groups = [frame[k].to_numpy() for k in ['sector_label', 'cluster', 'economic_group']]
    attributes = frame[['formation_log_market_cap', 'formation_volatility']].to_numpy()
    scale = attributes.std(axis=0, ddof=0)
    attributes = (attributes - attributes.mean(axis=0)) / np.where(scale > 0, scale, 1)
    rows = {metric: {} for metric in METRICS}
    matches, coverage = [], []
    for i in range(n):
        eligible = groups != groups[i]  # excludes the focal line and its corporate twin
        within = np.flatnonzero(eligible & (labels == labels[i]))
        sector = np.flatnonzero(eligible & (sectors == sectors[i]))
        cross = np.flatnonzero(eligible & (labels != labels[i]))

        def row(indices):
            result = np.zeros((n, n))
            result[i, indices] = 1 / len(indices)
            return result

        for metric, controls in [('sector', sector), ('cross_cluster', cross)]:
            if len(within) and len(controls):
                rows[metric][i] = (row(within), row(controls))
        matched = []
        for j in within:
            candidates = np.flatnonzero(eligible & (groups != groups[j]) &
                                        (labels != labels[i]) & (sectors == sectors[j]))
            if not len(candidates):
                continue
            distance = np.linalg.norm(attributes[candidates] - attributes[j], axis=1)
            k = int(candidates[np.argmin(distance)])  # sorted tickers break ties deterministically
            matched.append((j, k))
            matches.append(dict(focal=frame.ticker[i], peer=frame.ticker[j], alternative=frame.ticker[k],
                                peer_sector=sectors[j], distance=float(distance.min())))
        if matched:
            original, baseline = np.zeros((n, n)), np.zeros((n, n))
            for j, k in matched:
                original[i, j] += 1 / len(matched)
                baseline[i, k] += 1 / len(matched)
            rows['matched'][i] = (original, baseline)
        coverage.append(dict(ticker=frame.ticker[i], economic_group=groups[i],
                             cluster_peers=len(within), sector_peers=len(sector),
                             cross_cluster_peers=len(cross), matched_targets=len(matched),
                             unmatched_targets=len(within) - len(matched)))
    weights, company_weights = {}, {}
    for metric, instruments in rows.items():
        company_weights[metric] = {}
        for group in sorted(set(groups)):
            eligible_rows = [v for i, v in instruments.items() if groups[i] == group]
            if eligible_rows:
                company_weights[metric][group] = np.mean(np.array(eligible_rows), axis=0)
        if not company_weights[metric]:
            raise ValueError(f'No eligible economic groups for {metric}')
        paired = np.mean(list(company_weights[metric].values()), axis=0)
        weights[metric + '_cluster'] = paired[0]
        weights[metric + '_baseline'] = paired[1]
        weights[metric + '_delta'] = paired[0] - paired[1]
    return weights, company_weights, pd.DataFrame(matches), pd.DataFrame(coverage)


def estimate(x, weights):
    corr = np.corrcoef(x, rowvar=False)
    if not np.isfinite(corr).all():
        raise ValueError('Undefined correlation; do not drop pairs silently.')
    return {key: float(np.sum(corr * weight)) for key, weight in weights.items()}, corr


def block_draws(x, weights, block_length, replicates, rng):
    """Resample dates synchronously, preserving common shocks across companies."""
    n = len(x)
    keys = list(weights)
    coefficients = np.stack([weights[k] for k in keys])
    draws = np.empty((replicates, len(keys)))
    for b in range(replicates):
        starts = rng.integers(n, size=math.ceil(n / block_length))
        indices = ((starts[:, None] + np.arange(block_length)) % n).ravel()[:n]
        corr = np.corrcoef(x[indices], rowvar=False)
        if not np.isfinite(corr).all():
            raise ValueError('Undefined bootstrap correlation.')
        draws[b] = np.einsum('kij,ij->k', coefficients, corr)
    return keys, draws


def main():
    protocol = json.loads((HERE / 'protocol.json').read_text())
    source_manifest = prepare(protocol)
    prices = pd.read_csv(HERE / 'data/prices.csv', parse_dates=['date'])
    cohorts = pd.read_csv(HERE / 'data/cohorts.csv')
    out = HERE / 'results'
    out.mkdir(exist_ok=True)
    summaries, intervals, companies, deletions, match_rows, coverage_rows = [], [], [], [], [], []
    for date_index, (formation, (start, end)) in enumerate(zip(
            protocol['formation_dates'], protocol['evaluation_windows'])):
        full = cohorts[cohorts.decision_date == formation].sort_values('ticker').reset_index(drop=True)
        variants = [('adjusted', full, 'adjusted_close', False),
                    ('price', full, 'close', False),
                    ('exclude_high_formation_volatility', full[~full.high_formation_volatility], 'adjusted_close', False),
                    ('J200_residual', full, 'adjusted_close', True)]
        for case_index, (variant, frame, field, residual) in enumerate(variants):
            frame = frame.reset_index(drop=True)
            x, market, calendar = return_panel(prices, frame.ticker, formation, start, end, field)
            if len(x) < protocol['minimum_daily_observations']:
                raise ValueError('Forward coverage below protocol minimum.')
            if residual:
                x = residualise(x, market)
            weights, company_weights, matches, coverage = weight_system(frame)
            values, corr = estimate(x, weights)
            key = dict(formation_date=formation, evaluation_start=start, evaluation_end=end, variant=variant)
            summary = dict(**key, trading_days=len(x), instruments=len(frame),
                           economic_groups=frame.economic_group.nunique(), **values)
            summary.update({metric + '_eligible_groups': len(company_weights[metric]) for metric in METRICS})
            summary.update(matched_targets=len(matches), unmatched_targets=int(coverage.unmatched_targets.sum()),
                           mean_match_distance=float(matches.distance.mean()),
                           max_match_distance=float(matches.distance.max()),
                           unique_matched_alternatives=int(matches.alternative.nunique()))
            summaries.append(summary)
            match_rows.append(matches.assign(**key))
            coverage_rows.append(coverage.assign(**key))
            for metric, group_weights in company_weights.items():
                for group, paired in group_weights.items():
                    a, b = np.einsum('kij,ij->k', paired, corr)
                    companies.append(dict(**key, comparator=metric, economic_group=group,
                                          cluster_mean=a, baseline_mean=b, delta=a - b))
            for block in protocol['block_lengths']:
                rng = np.random.default_rng(protocol['random_seed'] + 10000 * date_index + 100 * case_index + block)
                keys, draws = block_draws(x, weights, block, protocol['bootstrap_replicates'], rng)
                bounds = np.quantile(draws, [.025, .975], axis=0)
                for j, metric in enumerate(keys):
                    intervals.append(dict(**key, metric=metric, block_length=block,
                                          replicates=len(draws), estimate=values[metric],
                                          lower_95=bounds[0, j], upper_95=bounds[1, j]))
            for group in sorted(frame.economic_group.unique()):
                keep = frame.economic_group.to_numpy() != group
                subweights, _, _, _ = weight_system(frame[keep])
                deleted, _ = estimate(x[:, keep], subweights)
                deletions.append(dict(**key, deleted_group=group, **deleted))
            print(f'{formation} {variant}: ' + ', '.join(f'{m} delta={values[m + "_delta"]:+.4f}' for m in METRICS), flush=True)
    pd.DataFrame(summaries).to_csv(out / 'summary.csv', index=False)
    pd.DataFrame(intervals).to_csv(out / 'conditional_block_intervals.csv', index=False)
    pd.DataFrame(companies).to_csv(out / 'company_contrasts.csv', index=False)
    pd.DataFrame(deletions).to_csv(out / 'delete_company.csv', index=False)
    pd.concat(match_rows).to_csv(out / 'matched_pairs.csv', index=False)
    pd.concat(coverage_rows).to_csv(out / 'coverage.csv', index=False)
    record = {'protocol_sha256': sha(HERE / 'protocol.json'), 'script_sha256': sha(__file__),
              'data_manifest_sha256': sha(HERE / 'data/manifest.json'),
              'study_run': source_manifest['study_run'],
              'base_manuscript_commit': protocol['frozen_manuscript_commit'],
              'python': sys.version, 'numpy': np.__version__, 'pandas': pd.__version__,
              'output_sha256': {name: sha(out / name) for name in [
                  'summary.csv', 'conditional_block_intervals.csv', 'company_contrasts.csv',
                  'delete_company.csv', 'matched_pairs.csv', 'coverage.csv']}}
    (out / 'manifest.json').write_text(json.dumps(record, indent=2) + '\n')


if __name__ == '__main__':
    main()
