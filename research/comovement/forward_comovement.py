"""Forward co-movement test: do cluster peers move together more than sector peers afterwards?

    python research/comovement/forward_comovement.py

For each formation date, clusters fitted on that date's inputs are compared
with daily price returns over the following six months. Nothing is refitted.

Primary metric (per formation date):
    delta_rho = mean correlation between cluster peers - mean correlation between sector peers
where peers are pairs of instruments in the same group and correlations are
of forward daily returns. Investec Limited and Investec plc (one company,
two listings) are excluded as a pair throughout.

Uncertainty:
- Permutation null: cluster labels shuffled across instruments, keeping the
  cluster sizes; p = share of shuffles with mean peer correlation >= observed.
- Day-block bootstrap (10-day blocks): confidence interval for delta_rho.

Controls and robustness:
- Market-adjusted correlations: residuals from a regression of each stock on
  the Top 40 index (J200) within the forward window.
- Per-cluster breakdown, and the result without the precious-metals cluster.
- The t-SNE comparator and all five UMAP seeds.
- Stock-level peer R^2: each stock regressed on the equal-weighted return of
  its other group members (Bhojraj, Lee and Oler 2003).
- Incremental value: pairwise correlation regressed on same-sector and
  same-cluster indicators together, with a QAP permutation test for the
  cluster coefficient.

Prices are read from .runtime/beta_prices/ (written by validation/audit_beta.py).

Prospective test: the June 2026 clusters are not tested by default. Their
forward window ends on 31 December 2026. Once it has closed, run

    python research/comovement/forward_comovement.py --prospective

which downloads prices through early January 2027 into a separate cache and
writes to output_prospective/. The option refuses to run before 5 January 2027.
Nothing else in this file is to change before that run.
"""
import argparse
import json
import sys
import time
import urllib.request
from datetime import date as calendar_date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

PRICES = ROOT / '.runtime' / 'beta_prices'
RESULTS = ROOT / 'results'
OUT = Path(__file__).resolve().parent / 'output'
FORMATION = {'2025-06-30': ('2025-07-01', '2025-12-31'), '2025-12-31': ('2026-01-01', '2026-06-30')}
PROSPECTIVE = {'2026-06-30': ('2026-07-01', '2026-12-31')}
PROSPECTIVE_PRICES = ROOT / '.runtime' / 'comovement_prices_2026H2'
PROSPECTIVE_EARLIEST_RUN = calendar_date(2027, 1, 5)
EXCLUDED_PAIRS = {frozenset({'INL', 'INP'})}
BAD_PRINT = 0.4
PERMUTATIONS = 10000
BOOTSTRAPS = 2000
BLOCK = 10
SEED = 20261115


def download(symbol, folder):
    """Daily history to early January 2027, for the prospective window only."""
    start, end = int(datetime(2026, 6, 1).timestamp()), int(datetime(2027, 1, 10).timestamp())
    url = f'https://query2.finance.yahoo.com/v8/finance/chart/{symbol}?period1={start}&period2={end}&interval=1d'
    request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    result = json.load(urllib.request.urlopen(request, timeout=30))['chart']['result'][0]
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f'{symbol.replace("^", "IDX_")}.json').write_text(json.dumps(result), encoding='utf-8')
    time.sleep(.3)


def closes(symbol):
    path = PRICES / f'{symbol.replace("^", "IDX_")}.json'
    if PRICES == PROSPECTIVE_PRICES and not path.is_file():
        download(symbol, PRICES)
    if not path.is_file():
        raise SystemExit(f'Missing {path}. Run validation/audit_beta.py first to download prices.')
    result = json.loads(path.read_text(encoding='utf-8'))
    series = pd.Series(result['indicators']['quote'][0]['close'], dtype=float,
                       index=pd.to_datetime(result['timestamp'], unit='s').normalize())
    return series[~series.index.duplicated(keep='last')].dropna()


def forward_returns(tickers, start, end):
    """Daily returns in the window; bad prints become missing values."""
    prices = pd.concat({t: closes(t + '.JO') for t in tickers}, axis=1)
    index = closes('^J200.JO')
    frame = pd.concat([prices, index.rename('J200')], axis=1).sort_index()
    returns = frame.pct_change().loc[start:end]
    returns = returns.mask(returns.abs() > BAD_PRINT)
    return returns.drop(columns='J200'), returns['J200']


def market_residuals(returns, market):
    residual = pd.DataFrame(index=returns.index, columns=returns.columns, dtype=float)
    for ticker in returns:
        both = pd.concat([returns[ticker], market], axis=1).dropna()
        slope, intercept = np.polyfit(both.iloc[:, 1], both.iloc[:, 0], 1)
        residual.loc[both.index, ticker] = both.iloc[:, 0] - (intercept + slope * both.iloc[:, 1])
    return residual


def peer_mask(labels):
    """Boolean matrix: True where two different instruments share a group, excluding listed pairs."""
    values = labels.to_numpy()
    same = values[:, None] == values[None, :]
    np.fill_diagonal(same, False)
    tickers = list(labels.index)
    for pair in EXCLUDED_PAIRS:
        if pair <= set(tickers):
            a, b = (tickers.index(t) for t in pair)
            same[a, b] = same[b, a] = False
    return same


def mean_peer_correlation(corr, labels):
    mask = np.triu(peer_mask(labels), 1)
    return float(corr[mask].mean()) if mask.any() else np.nan


def permutation_p(corr, labels, rng):
    observed = mean_peer_correlation(corr, labels)
    values = labels.to_numpy()
    null = np.empty(PERMUTATIONS)
    for i in range(PERMUTATIONS):
        null[i] = mean_peer_correlation(corr, pd.Series(rng.permutation(values), index=labels.index))
    return observed, float(null.mean()), float((np.sum(null >= observed) + 1) / (PERMUTATIONS + 1))


def block_bootstrap_delta(returns, clusters, sectors, rng):
    """Confidence interval for delta_rho, resampling 10-day blocks of the forward window."""
    data = returns.to_numpy()
    n = len(data)
    starts = np.arange(0, n - BLOCK + 1)
    deltas = np.empty(BOOTSTRAPS)
    for i in range(BOOTSTRAPS):
        picks = rng.choice(starts, size=int(np.ceil(n / BLOCK)))
        rows = np.concatenate([np.arange(s, s + BLOCK) for s in picks])[:n]
        corr = pd.DataFrame(data[rows]).corr().to_numpy()
        deltas[i] = mean_peer_correlation(corr, clusters) - mean_peer_correlation(corr, sectors)
    return np.percentile(deltas, [2.5, 97.5]).tolist()


def peer_r2(returns, labels):
    """Mean R^2 of each stock on the equal-weighted return of its other group members."""
    r2 = []
    for ticker in returns:
        peers = [t for t in labels.index[labels == labels[ticker]] if t != ticker
                 and frozenset({t, ticker}) not in EXCLUDED_PAIRS]
        if not peers:
            continue
        both = pd.concat([returns[ticker], returns[peers].mean(axis=1)], axis=1).dropna()
        r2.append(both.corr().iloc[0, 1] ** 2)
    return float(np.mean(r2)), len(r2)


def incremental(corr, tickers, sectors, clusters, rng, permutations=5000):
    """Does sharing a cluster raise forward correlation once sharing a sector is accounted for?

    Regresses pairwise correlation on same-sector and same-cluster indicators.
    The cluster coefficient is tested by QAP: cluster labels are shuffled
    across instruments, which keeps the dependence between overlapping pairs.
    """
    upper = np.triu_indices(len(tickers), 1)
    keep = np.array([frozenset({tickers[i], tickers[j]}) not in EXCLUDED_PAIRS for i, j in zip(*upper)])
    y = corr[upper][keep]
    sector = sectors.to_numpy()
    same_sector = (sector[:, None] == sector[None, :])[upper][keep].astype(float)

    def fit(labels):
        same_cluster = (labels[:, None] == labels[None, :])[upper][keep].astype(float)
        design = np.column_stack([np.ones_like(y), same_sector, same_cluster])
        return np.linalg.lstsq(design, y, rcond=None)[0], same_cluster

    (intercept, beta_sector, beta_cluster), same_cluster = fit(clusters.to_numpy())
    null = np.array([fit(rng.permutation(clusters.to_numpy()))[0][2] for _ in range(permutations)])
    cells = {'same sector, same cluster': (same_sector == 1) & (same_cluster == 1),
             'same sector, other cluster': (same_sector == 1) & (same_cluster == 0),
             'other sector, same cluster': (same_sector == 0) & (same_cluster == 1),
             'other sector, other cluster': (same_sector == 0) & (same_cluster == 0)}
    row = dict(beta_sector=beta_sector, beta_cluster=beta_cluster,
               qap_p_cluster=float((np.sum(null >= beta_cluster) + 1) / (permutations + 1)))
    for name, mask in cells.items():
        row[f'rho: {name}'] = float(y[mask].mean())
        row[f'pairs: {name}'] = int(mask.sum())
    return row


def partitions(date, tickers, run):
    """Every grouping tested at one formation date, as Series indexed by ticker."""
    assigned = pd.read_csv(RESULTS / f'models/umap/{date}/assignments.csv').set_index('ticker')
    groups = {'UMAP (study model)': assigned.cluster, 'Sector': assigned.sector_label}
    tsne = pd.read_csv(run / f'comparison/{date}_tsne_hierarchical.csv').set_index('ticker').cluster
    groups['t-SNE comparator'] = tsne
    for seed in range(42, 47):
        with np.load(run / f'models/umap/{date}/seed_{seed}.npz', allow_pickle=False) as saved:
            groups[f'UMAP seed {seed}'] = pd.Series(saved['clusters'], index=saved['tickers'].astype(str))
    return {name: g.reindex(tickers) for name, g in groups.items()}


def main():
    global FORMATION, PRICES, OUT
    parser = argparse.ArgumentParser(description='Forward co-movement test.')
    parser.add_argument('--prospective', action='store_true',
                        help='Test the June 2026 clusters on July-December 2026 returns (from 5 January 2027)')
    if parser.parse_args().prospective:
        if calendar_date.today() < PROSPECTIVE_EARLIEST_RUN:
            raise SystemExit(f'The prospective window closes on 31 December 2026; run this on or after '
                             f'{PROSPECTIVE_EARLIEST_RUN.isoformat()}.')
        FORMATION, PRICES = PROSPECTIVE, PROSPECTIVE_PRICES
        OUT = OUT.parent / 'output_prospective'
    manifest = json.loads((RESULTS / 'manifest.json').read_text(encoding='utf-8'))
    run = ROOT / 'experiments' / 'runs' / manifest['run_id']
    rng = np.random.default_rng(SEED)
    OUT.mkdir(exist_ok=True)
    summary, clusters_rows, r2_rows, incremental_rows = [], [], [], []
    for date, (start, end) in FORMATION.items():
        tickers = sorted(pd.read_csv(RESULTS / f'models/umap/{date}/assignments.csv').ticker)
        returns, market = forward_returns(tickers, start, end)
        returns = returns[tickers]
        residuals = market_residuals(returns, market)
        groups = partitions(date, tickers, run)
        for kind, data in [('raw', returns), ('market-adjusted', residuals)]:
            corr = data.corr().to_numpy()
            upper = np.triu(np.ones_like(corr, dtype=bool), 1)
            all_pairs = float(corr[upper].mean())
            sector_mean = mean_peer_correlation(corr, groups['Sector'])
            for name, labels in groups.items():
                observed, null_mean, p = permutation_p(corr, labels, rng)
                row = dict(formation_date=date, window=f'{start} to {end}', returns=kind, grouping=name,
                           peer_pairs=int(np.triu(peer_mask(labels), 1).sum()), mean_peer_rho=observed,
                           mean_all_pairs_rho=all_pairs, permutation_null_mean=null_mean, permutation_p=p,
                           delta_vs_sector=observed - sector_mean if name != 'Sector' else np.nan)
                if name == 'UMAP (study model)':
                    row['delta_ci_low'], row['delta_ci_high'] = block_bootstrap_delta(
                        data, labels, groups['Sector'], rng)
                summary.append(row)
            labels = groups['UMAP (study model)']
            aligned = pd.read_csv(RESULTS / 'longitudinal/umap/cluster_histories.csv').set_index('ticker')[date]
            mask = np.triu(peer_mask(labels), 1)
            for cluster in sorted(labels.unique()):
                members = labels.index[labels == cluster]
                idx = [tickers.index(t) for t in members]
                sub = mask[np.ix_(idx, idx)]
                clusters_rows.append(dict(
                    formation_date=date, returns=kind, aligned_cluster=int(aligned[members[0]]),
                    members=', '.join(members), n=len(members), peer_pairs=int(sub.sum()),
                    mean_peer_rho=float(corr[np.ix_(idx, idx)][sub].mean()) if sub.any() else np.nan))
            # Without the precious-metals cluster (aligned id 3): drop its members' pairs only.
            metals = labels.index[aligned.reindex(labels.index) == 3]
            keep = ~labels.index.isin(metals)
            sub_corr = corr[np.ix_(keep, keep)]
            summary.append(dict(formation_date=date, window=f'{start} to {end}', returns=kind,
                                grouping='UMAP without precious-metals cluster',
                                peer_pairs=int(np.triu(peer_mask(labels[keep]), 1).sum()),
                                mean_peer_rho=mean_peer_correlation(sub_corr, labels[keep]),
                                mean_all_pairs_rho=float(sub_corr[np.triu(np.ones_like(sub_corr, dtype=bool), 1)].mean()),
                                delta_vs_sector=mean_peer_correlation(sub_corr, labels[keep])
                                - mean_peer_correlation(sub_corr, groups['Sector'][keep])))
            for name in ['UMAP (study model)', 't-SNE comparator', 'Sector']:
                value, stocks = peer_r2(data, groups[name])
                r2_rows.append(dict(formation_date=date, returns=kind, grouping=name, mean_peer_r2=value,
                                    stocks_with_peers=stocks))
            for name in ['UMAP (study model)', 't-SNE comparator']:
                incremental_rows.append(dict(formation_date=date, returns=kind, grouping=name,
                                             **incremental(corr, tickers, groups['Sector'], groups[name], rng)))
    summary = pd.DataFrame(summary)
    summary.to_csv(OUT / 'comovement_summary.csv', index=False)
    pd.DataFrame(clusters_rows).to_csv(OUT / 'comovement_by_cluster.csv', index=False)
    pd.DataFrame(r2_rows).to_csv(OUT / 'peer_r2.csv', index=False)
    pd.DataFrame(incremental_rows).to_csv(OUT / 'incremental_beyond_sector.csv', index=False)
    pd.set_option('display.width', 220)
    cols = ['formation_date', 'returns', 'grouping', 'peer_pairs', 'mean_peer_rho', 'mean_all_pairs_rho',
            'permutation_p', 'delta_vs_sector', 'delta_ci_low', 'delta_ci_high']
    print(summary[cols].round(3).to_string(index=False))
    print(pd.DataFrame(clusters_rows).round(3).to_string(index=False))
    print(pd.DataFrame(r2_rows).round(3).to_string(index=False))
    print(pd.DataFrame(incremental_rows).round(4).to_string(index=False))


if __name__ == '__main__':
    main()
