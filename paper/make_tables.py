"""Write the paper's data-driven LaTeX tables from the committed results.

    python paper/make_tables.py

Reads results/ and the source run named in results/manifest.json, writes
CSVs to paper/data/ and LaTeX tables to paper/tables/. Rerun after a new
study run is exported so the tables and their numbers stay in step.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd

RESULTS = ROOT / 'results'
DATA = ROOT / 'paper' / 'data'
TABLES = ROOT / 'paper' / 'tables'
DATE_LABEL = {'2025-06-30': 'Jun 2025', '2025-12-31': 'Dec 2025', '2026-06-30': 'Jun 2026'}
MODELS = [('umap', 'UMAP (study model)', 'Hierarchical'),
          ('tsne_hierarchical', 't-SNE', 'Hierarchical'), ('tsne_kmeans', 't-SNE', 'K-Means'),
          ('tsne_dbscan', 't-SNE', 'DBSCAN'), ('umap_hierarchical', 'UMAP (default)', 'Hierarchical'),
          ('umap_kmeans', 'UMAP (default)', 'K-Means'), ('umap_dbscan', 'UMAP (default)', 'DBSCAN'),
          ('pca_hierarchical', 'PCA', 'Hierarchical'), ('pca_kmeans', 'PCA', 'K-Means'),
          ('pca_dbscan', 'PCA', 'DBSCAN')]


def number(value, digits=3):
    return '--' if pd.isna(value) else f'{value:.{digits}f}'


def model_comparison():
    """One row per combination, dates as column groups; silhouette and Davies-Bouldin panels.

    Group counts and coverage that differ from eight groups and 100% are given
    beside the method name, so every number of the long-format CSV is shown.
    """
    table = pd.read_csv(RESULTS / 'model_comparison.csv').set_index(['model', 'decision_date'])
    dates = list(DATE_LABEL)
    lines = [r'\begin{tabularx}{\linewidth}{@{}>{\raggedright\arraybackslash}X rr rr rr@{}}', r'\toprule',
             ' & ' + ' & '.join(rf'\multicolumn{{2}}{{c}}{{{DATE_LABEL[d]}}}' for d in dates) + r' \\',
             ''.join(rf'\cmidrule(lr){{{2 + 2 * i}-{3 + 2 * i}}}' for i in range(3)),
             'Reduction and clustering' + ' & Map & Feature' * 3 + r' \\']
    for title, metric in [('Silhouette (higher is better)', 'silhouette'),
                          ('Davies--Bouldin (lower is better)', 'davies_bouldin')]:
        lines += [r'\midrule', rf'\multicolumn{{7}}{{@{{}}l}}{{\textit{{{title}}}}} \\']
        for model, reduction, method in MODELS:
            rows = [table.loc[(model, d)] for d in dates]
            label = f'{reduction} + {method}'
            if any(r.n_clusters != 8 for r in rows):
                label += ' (' + ', '.join(str(int(r.n_clusters)) for r in rows) + ' groups'
                if any(r.coverage < 1 for r in rows):
                    label += '; ' + ', '.join(f'{r.coverage:.0%}' for r in rows).replace('%', r'\%') + ' coverage'
                label += ')'
            cells = [number(getattr(r, f'{metric}_{space}')) for r in rows for space in ('embedding', 'features')]
            lines.append(' & '.join([label] + cells) + r' \\')
    lines += [r'\bottomrule', r'\end{tabularx}']
    (TABLES / 'model_comparison.tex').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def sector_divergence():
    manifest = json.loads((RESULTS / 'manifest.json').read_text(encoding='utf-8'))
    run = ROOT / 'experiments' / 'runs' / manifest['run_id']
    context = pd.read_csv(run / 'longitudinal/umap/sector_context.csv')
    histories = pd.read_csv(RESULTS / 'longitudinal/umap/cluster_histories.csv').set_index('ticker')
    context['aligned_cluster'] = [int(histories.loc[t, d]) for t, d in zip(context.ticker, context.decision_date)]
    context.to_csv(DATA / 'sector_context.csv', index=False)

    quality = pd.read_csv(RESULTS / 'model_comparison.csv').set_index(['model', 'decision_date'])
    lines = [r'\begin{tabularx}{\linewidth}{@{}l r r r >{\raggedright\arraybackslash}X@{}}', r'\toprule',
             r'Date & Sector ARI & Sector NMI & Divergent & Instruments whose sector differs from their cluster majority \\',
             r'\midrule']
    for date, label in DATE_LABEL.items():
        rows = context[(context.decision_date == date) & (context.sector_divergence == True)]  # noqa: E712
        q = quality.loc[('umap', date)]
        lines.append(f'{label} & {q.sector_ari:.3f} & {q.sector_nmi:.3f} & {len(rows)} & '
                     f'{", ".join(sorted(rows.ticker))}' + r' \\')
    lines += [r'\bottomrule', r'\end{tabularx}']
    (TABLES / 'sector_agreement.tex').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    wide = context.pivot(index='ticker', columns='decision_date', values='sector_divergence')
    persistent = sorted(wide[(wide == True).all(axis=1)].index)  # noqa: E712
    print('Divergent at every date:', ', '.join(persistent))


def comovement():
    """Forward co-movement tables from research/comovement/output/ (study model only)."""
    source = ROOT / 'research' / 'comovement' / 'output'
    summary = pd.read_csv(source / 'comovement_summary.csv')
    incremental = pd.read_csv(source / 'incremental_beyond_sector.csv')
    summary.to_csv(DATA / 'comovement_summary.csv', index=False)
    incremental.to_csv(DATA / 'comovement_incremental.csv', index=False)
    returns_label = {'raw': 'Raw', 'market-adjusted': 'Market-adjusted'}

    study = summary[summary.grouping == 'UMAP (study model)'].set_index(['formation_date', 'returns'])
    sector = summary[summary.grouping == 'Sector'].set_index(['formation_date', 'returns'])
    lines = [r'\begin{tabularx}{\linewidth}{@{}l >{\raggedright\arraybackslash}X r r r r r@{}}', r'\toprule',
             r'Formed & Returns & Cluster peers & Sector peers & All pairs & $\Delta\rho$ & 95\% interval \\',
             r'\midrule']
    for date, label in list(DATE_LABEL.items())[:2]:
        for kind in ['raw', 'market-adjusted']:
            row, sec = study.loc[(date, kind)], sector.loc[(date, kind)]
            lines.append(f'{label} & {returns_label[kind]} & {row.mean_peer_rho:.3f} & {sec.mean_peer_rho:.3f} & '
                         f'{row.mean_all_pairs_rho:.3f} & {row.delta_vs_sector:+.3f} & '
                         f'[{row.delta_ci_low:+.3f}, {row.delta_ci_high:+.3f}]' + r' \\')
    lines += [r'\bottomrule', r'\end{tabularx}']
    (TABLES / 'comovement.tex').write_text('\n'.join(lines) + '\n', encoding='utf-8')

    cells = ['same sector, same cluster', 'same sector, other cluster', 'other sector, same cluster',
             'other sector, other cluster']
    study = incremental[incremental.grouping == 'UMAP (study model)'].set_index(['formation_date', 'returns'])
    keys = [(d, k) for d in list(DATE_LABEL)[:2] for k in ['raw', 'market-adjusted']]
    header = ' & '.join(f'{DATE_LABEL[d]} {"raw" if k == "raw" else "adj."}' for d, k in keys)
    lines = [r'\begin{tabularx}{\linewidth}{@{}>{\raggedright\arraybackslash}X r r r r@{}}', r'\toprule',
             f'Pairs & {header}' + r' \\', r'\midrule']
    for cell in cells:
        values = ' & '.join(f'{study.loc[key, "rho: " + cell]:.3f}' for key in keys)
        pairs = int(study.loc[keys[0], 'pairs: ' + cell])
        later = int(study.loc[keys[2], 'pairs: ' + cell])
        lines.append(f'{cell.capitalize()} ({pairs}; {later} pairs) & {values}' + r' \\')
    lines.append(r'\midrule')
    lines.append('Cluster coefficient & ' + ' & '.join(f'{study.loc[key, "beta_cluster"]:.3f}' for key in keys) + r' \\')
    lines.append('Permutation $p$ & ' + ' & '.join(f'{study.loc[key, "qap_p_cluster"]:.3f}' for key in keys) + r' \\')
    lines += [r'\bottomrule', r'\end{tabularx}']
    (TABLES / 'comovement_pairs.tex').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def sector_conditioned():
    """Supplementary direct contrasts from the byte-verified retrospective sensitivity."""
    folder = ROOT / 'research' / 'sector_conditioned_comovement'
    source = folder / 'results.csv'
    manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
    expected_hash = manifest['files_sha256']['research/sector_conditioned_comovement/results.csv']
    if hashlib.sha256(source.read_bytes()).hexdigest() != expected_hash:
        raise ValueError('Sector-conditioned sensitivity results do not match their manifest.')
    frame = pd.read_csv(source)
    expected = {(date, basis, method) for date in list(DATE_LABEL)[:2]
                for basis in ('raw', 'market-adjusted')
                for method in ('UMAP (study model)', 't-SNE comparator')}
    keys = list(zip(frame.formation_date, frame.returns, frame.grouping))
    if len(keys) != 8 or set(keys) != expected:
        raise ValueError('Expected exactly the eight completed sensitivity combinations.')
    lines = [r'\begin{tabularx}{\linewidth}{@{}l >{\raggedright\arraybackslash}X l r r r r@{}}',
             r'\toprule',
             r'Formed & Returns & Map & $D_{\mathrm{within}}$ & 95\% interval & \shortstack{Restricted\\$p$} & \shortstack{Holm-adjusted\\$p$} \\',
             r'\midrule']
    for row in frame.itertuples():
        method = 'UMAP' if row.grouping == 'UMAP (study model)' else 't-SNE'
        basis = 'Raw' if row.returns == 'raw' else 'Market-adjusted'
        lines.append(f'{DATE_LABEL[row.formation_date]} & {basis} & {method} & '
                     f'{row.within_sector_difference:+.3f} & '
                     f'[{row.difference_ci_low:+.3f}, {row.difference_ci_high:+.3f}] & '
                     f'{row.within_sector_p:.4f} & {row.within_sector_p_holm:.4f}' + r' \\')
    lines += [r'\bottomrule', r'\end{tabularx}']
    (TABLES / 'sector_conditioned_sensitivity.tex').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sector-conditioned-only', action='store_true',
                        help='Generate only Table S1, using committed sensitivity evidence offline.')
    args = parser.parse_args()
    TABLES.mkdir(parents=True, exist_ok=True)
    if not args.sector_conditioned_only:
        model_comparison()
        sector_divergence()
        comovement()
    sector_conditioned()
    written = ['sector_conditioned_sensitivity.tex'] if args.sector_conditioned_only else [
        p.name for p in sorted(TABLES.glob('*.tex'))]
    print(f'Wrote {", ".join(written)} to {TABLES}')


if __name__ == '__main__':
    main()
