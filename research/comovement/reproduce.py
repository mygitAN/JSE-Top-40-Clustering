"""Reproduce the frozen 2025 formations offline without modifying the original script.

    .venv/Scripts/python.exe research/comovement/reproduce.py

The adapter changes only input/output locations and data loading. The original
analytical functions, parameters, RNG sequence and June-2026 guard are unchanged.
It never executes the reserved evaluation or overwrites the frozen outputs.
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def verify():
    manifest = json.loads((HERE / 'manifest.json').read_text(encoding='utf-8'))
    for name, digest in manifest['files_sha256'].items():
        path = HERE / name
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError(f'Frozen evidence changed: {name}')
    return manifest


def main():
    if len(sys.argv) != 1:
        raise SystemExit('This offline adapter reproduces only the two frozen 2025 formations; it accepts no arguments.')
    verify()
    spec = importlib.util.spec_from_file_location('frozen_primary_comovement', HERE / 'forward_comovement.py')
    primary = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(primary)
    if set(primary.FORMATION) != {'2025-06-30', '2025-12-31'}:
        raise ValueError('Unexpected formation dates in the frozen script.')
    prices = pd.read_csv(HERE / 'inputs/prices.csv', parse_dates=['date'], float_precision='round_trip')
    labels = pd.read_csv(HERE / 'inputs/partitions.csv', dtype={'label': str})

    def closes(symbol):
        table = prices[prices.symbol == symbol].sort_values('date')
        if table.empty:
            raise ValueError(f'No frozen price series for {symbol}')
        return pd.Series(table.close.to_numpy(), index=pd.DatetimeIndex(table.date), dtype=float).dropna()

    def partitions(date, tickers, unused_run):
        if date not in {'2025-06-30', '2025-12-31'}:
            raise ValueError('The reserved June-2026 evaluation is unavailable to this adapter.')
        groups = {}
        for name, frame in labels[labels.formation_date == date].groupby('grouping', sort=False):
            values = frame.label if name == 'Sector' else pd.to_numeric(frame.label).astype(int)
            groups[name] = pd.Series(values.to_numpy(), index=frame.ticker).reindex(tickers)
            if groups[name].isna().any():
                raise ValueError(f'Missing frozen labels for {date}/{name}')
        return groups

    def no_download(*args, **kwargs):
        raise RuntimeError('Network downloads are disabled for frozen reproduction.')

    destination = ROOT / '.runtime/comovement-reproduction'
    destination.mkdir(parents=True, exist_ok=True)
    primary.closes = closes
    primary.partitions = partitions
    primary.download = no_download
    primary.RESULTS = HERE / 'inputs/results'
    primary.OUT = destination
    primary.main()
    for name in sorted((HERE / 'output').glob('*.csv')):
        expected = pd.read_csv(name, float_precision='round_trip')
        actual = pd.read_csv(destination / name.name, float_precision='round_trip')
        pd.testing.assert_frame_equal(expected, actual, check_exact=False, rtol=1e-10, atol=1e-12)
        print(f'Verified {name.name}: {len(actual)} rows', flush=True)
    print('Frozen outputs reproduced offline. Reserved June-2026 evaluation was not executed.')


if __name__ == '__main__':
    main()
