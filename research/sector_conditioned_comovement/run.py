"""Offline, post-hoc sector-conditioned sensitivity; never evaluates June 2026.

Run: .venv/Scripts/python.exe research/sector_conditioned_comovement/run.py
The frozen primary implementation and its outputs are read, never overwritten.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
PRIMARY = HERE.parent / 'comovement'


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def permute_within_sectors(labels, sectors, rng):
    result = np.asarray(labels).copy()
    for sector in np.unique(sectors):
        indices = np.flatnonzero(sectors == sector)
        result[indices] = rng.permutation(result[indices])
    return result


def eligible_pairs(tickers):
    i, j = np.triu_indices(len(tickers), 1)
    keep = np.array([frozenset((tickers[a], tickers[b])) != frozenset(('INL', 'INP'))
                     for a, b in zip(i, j)])
    return i[keep], j[keep]


def statistics(y, same_sector, same_cluster):
    shared = same_sector & same_cluster
    different = same_sector & ~same_cluster
    if not shared.any() or not different.any():
        raise ValueError('Both within-sector comparison cells must be nonempty.')
    difference = float(y[shared].mean() - y[different].mean())
    design = np.column_stack((np.ones(len(y)), same_sector, same_cluster))
    coefficient = float(np.linalg.lstsq(design, y, rcond=None)[0][2])
    return difference, coefficient


def holm(p_values):
    values = np.asarray(p_values, dtype=float)
    order = np.argsort(values)
    result = np.empty(len(values))
    result[order] = np.minimum(1, np.maximum.accumulate(values[order] * np.arange(len(values), 0, -1)))
    return result


def main():
    if len(sys.argv) != 1:
        raise SystemExit('No arguments accepted; only the two completed 2025 formations are available.')
    protocol = json.loads((HERE / 'protocol.json').read_text(encoding='utf-8-sig'))
    load_module('primary_freeze_verifier', PRIMARY / 'reproduce.py').verify()
    primary = load_module('primary_analytical_functions', PRIMARY / 'forward_comovement.py')
    prices = pd.read_csv(PRIMARY / 'inputs/prices.csv', parse_dates=['date'], float_precision='round_trip')
    if prices.date.max() > pd.Timestamp('2026-06-30'):
        raise ValueError('Post-June-2026 prices are forbidden in this sensitivity.')
    labels = pd.read_csv(PRIMARY / 'inputs/partitions.csv', dtype={'label': str})

    def closes(symbol):
        frame = prices[prices.symbol == symbol].sort_values('date')
        if frame.empty:
            raise ValueError(f'Missing frozen prices: {symbol}')
        return pd.Series(frame.close.to_numpy(), index=pd.DatetimeIndex(frame.date), dtype=float).dropna()

    primary.closes = closes
    rng = np.random.default_rng(protocol['random_seed'])
    rows = []
    for formation in protocol['formation_dates']:
        if formation not in {'2025-06-30', '2025-12-31'}:
            raise ValueError('Reserved formation is not permitted.')
        frame = labels[labels.formation_date == formation]
        tickers = sorted(frame[frame.grouping == 'Sector'].ticker)
        sectors = frame[frame.grouping == 'Sector'].set_index('ticker').loc[tickers, 'label'].to_numpy()
        i, j = eligible_pairs(tickers)
        same_sector = sectors[i] == sectors[j]
        returns, market = primary.forward_returns(tickers, *primary.FORMATION[formation])
        residuals = primary.market_residuals(returns, market)
        for basis, data in [('raw', returns), ('market-adjusted', residuals)]:
            x = data[tickers].to_numpy()
            if not np.isfinite(x).all():
                raise ValueError('A complete finite return panel is required.')
            y = np.corrcoef(x, rowvar=False)[i, j]
            # One shared bootstrap calendar across instruments and model comparisons.
            n = len(x)
            calendars = [np.concatenate([np.arange(s, s + 10) for s in
                         rng.choice(np.arange(n - 10 + 1), size=int(np.ceil(n / 10)))])[:n]
                         for _ in range(2000)]
            bootstrap_y = np.array([np.corrcoef(x[calendar], rowvar=False)[i, j] for calendar in calendars])
            for grouping in protocol['groupings']:
                cluster = pd.to_numeric(frame[frame.grouping == grouping].set_index('ticker')
                                        .loc[tickers, 'label']).to_numpy()
                same_cluster = cluster[i] == cluster[j]
                observed = statistics(y, same_sector, same_cluster)
                null = np.empty((protocol['permutations'], 2))
                for b in range(len(null)):
                    shuffled = permute_within_sectors(cluster, sectors, rng)
                    null[b] = statistics(y, same_sector, shuffled[i] == shuffled[j])
                p_values = (1 + (null >= observed).sum(axis=0)) / (len(null) + 1)
                shared, different = same_sector & same_cluster, same_sector & ~same_cluster
                bootstrap_differences = bootstrap_y[:, shared].mean(axis=1) - bootstrap_y[:, different].mean(axis=1)
                low, high = np.percentile(bootstrap_differences, [2.5, 97.5])
                rows.append(dict(formation_date=formation, returns=basis, grouping=grouping,
                                 trading_days=n, same_sector_same_cluster_pairs=int(shared.sum()),
                                 same_sector_other_cluster_pairs=int(different.sum()),
                                 rho_same_sector_same_cluster=float(y[shared].mean()),
                                 rho_same_sector_other_cluster=float(y[different].mean()),
                                 within_sector_difference=observed[0], difference_ci_low=low,
                                 difference_ci_high=high, within_sector_p=p_values[0],
                                 cluster_coefficient=observed[1], coefficient_p=p_values[1]))
    result = pd.DataFrame(rows)
    p_columns = ['within_sector_p', 'coefficient_p']
    adjusted = holm(result[p_columns].to_numpy().ravel()).reshape(len(result), 2)
    result['within_sector_p_holm'], result['coefficient_p_holm'] = adjusted.T
    # Confirm alignment/return preparation matches the original saved cell means and coefficient.
    original = pd.read_csv(PRIMARY / 'output/incremental_beyond_sector.csv')
    for row in rows:
        saved = original[(original.formation_date == row['formation_date']) &
                         (original.returns == row['returns']) & (original.grouping == row['grouping'])].iloc[0]
        for actual, expected in [('rho_same_sector_same_cluster', 'rho: same sector, same cluster'),
                                 ('rho_same_sector_other_cluster', 'rho: same sector, other cluster'),
                                 ('cluster_coefficient', 'beta_cluster')]:
            if not np.isclose(row[actual], saved[expected], atol=1e-12, rtol=1e-10):
                raise ValueError(f'Original result mismatch: {actual}')
    result.to_csv(HERE / 'results.csv', index=False, lineterminator='\n')
    paths = [HERE / 'protocol.json', HERE / 'run.py', HERE / 'results.csv', HERE / 'README.md',
             HERE.parents[1] / 'tests/test_sector_conditioned_comovement.py',
             PRIMARY / 'manifest.json', PRIMARY / 'inputs/prices.csv', PRIMARY / 'inputs/partitions.csv']
    root = HERE.parents[1]
    manifest = {'analysis': 'Post-hoc sector-conditioned sensitivity, 2026-11-26',
                'files_sha256': {str(p.relative_to(root)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in paths},
                'versions': {'numpy': np.__version__, 'pandas': pd.__version__}}
    (HERE / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(result.to_string(index=False))
    print('Original cell means/coefficients verified. Frozen files unchanged; no June-2026 forward evaluation.')


if __name__ == '__main__':
    main()
