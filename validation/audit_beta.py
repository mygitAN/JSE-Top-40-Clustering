"""Recompute every one-year beta from daily prices and compare it with the model inputs.

    python validation/audit_beta.py

Downloads daily closes for every instrument and for the All Share (J203) and
Top 40 (J200) indices from Yahoo Finance, caching them in .runtime/beta_prices/.
Betas are OLS slopes of daily price returns on index returns over the
workbook's trailing windows. A daily move above 40% in either series is
treated as a bad print and that day is dropped; Yahoo's J203 series is
corrupted on 23 and 24 July 2025, and a few stock series have isolated
bad prints.

Internal validation only; not reported in the paper. Writes
validation/beta_audit.csv (one row per instrument and date) and
validation/beta_audit_sasol.csv (Sasol's beta in each half of the June 2026 window).
"""
import json
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from top40.data import DATES, load_inputs
from top40.features import add_derived_columns

CACHE = ROOT / '.runtime' / 'beta_prices'
OUT = ROOT / 'validation'
WINDOWS = {'2025-06-30': ('2024-07-01', '2025-06-30'), '2025-12-31': ('2025-01-01', '2025-12-31'),
           '2026-06-30': ('2025-07-01', '2026-06-30')}
BENCHMARKS = {'J203': '^J203.JO', 'J200': '^J200.JO'}
BAD_PRINT = 0.4


def closes(symbol):
    path = CACHE / f'{symbol.replace("^", "IDX_")}.json'
    if not path.is_file():
        start, end = int(datetime(2024, 6, 1).timestamp()), int(datetime(2026, 7, 5).timestamp())
        url = (f'https://query2.finance.yahoo.com/v8/finance/chart/{symbol}'
               f'?period1={start}&period2={end}&interval=1d')
        request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        result = json.load(urllib.request.urlopen(request, timeout=30))['chart']['result'][0]
        CACHE.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result), encoding='utf-8')
        time.sleep(.3)
    result = json.loads(path.read_text(encoding='utf-8'))
    series = pd.Series(result['indicators']['quote'][0]['close'], dtype=float,
                       index=pd.to_datetime(result['timestamp'], unit='s').normalize())
    return series[~series.index.duplicated(keep='last')].dropna()


def returns(stock, index, start, end):
    """Daily returns on common trading days, with bad prints removed."""
    both = pd.concat([stock, index], axis=1, join='inner').loc[start:end].pct_change().dropna()
    bad = (both.abs() > BAD_PRINT).any(axis=1)
    return both[~bad], int(bad.sum())


def beta(both):
    return float(np.cov(both.iloc[:, 0], both.iloc[:, 1])[0, 1] / both.iloc[:, 1].var())


def main():
    frame = add_derived_columns(load_inputs(), DATES[0])
    index = {name: closes(symbol) for name, symbol in BENCHMARKS.items()}
    rows = []
    for row in frame.itertuples():
        start, end = WINDOWS[row.decision_date]
        stock = closes(row.ticker + '.JO')
        record = dict(decision_date=row.decision_date, ticker=row.ticker, workbook_beta=row.beta_1y)
        for name in BENCHMARKS:
            both, dropped = returns(stock, index[name], start, end)
            record[f'beta_{name}'] = beta(both)
            record[f'days_{name}'] = len(both)
            record[f'bad_print_days_{name}'] = dropped
        rows.append(record)
    table = pd.DataFrame(rows)
    table['difference_J203'] = table.beta_J203 - table.workbook_beta
    OUT.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUT / 'beta_audit.csv', index=False)

    sasol, _ = returns(closes('SOL.JO'), index['J200'], *WINDOWS['2026-06-30'])
    halves = [dict(period=label, beta_J200=beta(sasol.loc[a:b]),
                   correlation=float(sasol.loc[a:b].corr().iloc[0, 1]))
              for label, (a, b) in {'Jul-Dec 2025': ('2025-07-01', '2025-12-31'),
                                    'Jan-Jun 2026': ('2026-01-01', '2026-06-30')}.items()]
    pd.DataFrame(halves).to_csv(OUT / 'beta_audit_sasol.csv', index=False)

    gap = table.difference_J203.abs()
    print(f'Workbook betas reproduced against J203: median |difference| {gap.median():.3f}, '
          f'max {gap.max():.3f}, {int((gap < .05).sum())} of {len(table)} within 0.05.')
    print(pd.DataFrame(halves).round(3).to_string(index=False))


if __name__ == '__main__':
    main()
