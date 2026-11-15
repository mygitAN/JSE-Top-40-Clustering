"""Draw the paper's figures from the committed results and their source run.

    python paper/make_figures.py

Every figure uses the Jaccard-aligned cluster ids and one colour per id, so a
cluster has the same number and colour in every figure and in the text. The
source run is the one named in results/manifest.json; its folder under
experiments/runs/ supplies the UMAP coordinates, which results/ does not hold.
"""
import json
import sys
from pathlib import Path
from textwrap import fill

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from top40 import plots
from top40.features import get_feature_set
from top40.models import linkage_matrix

RESULTS = ROOT / 'results'
OUT = ROOT / 'paper' / 'figures'
MODEL = 'umap'
plt.rcParams.update({'font.size': 8, 'axes.titlesize': 9, 'axes.labelsize': 8, 'pdf.fonttype': 42})

# The six moves drawn in the movement figure: (ticker, date before the move, display name).
MOVES_SHOWN = [('ANG', '2025-06-30', 'AngloGold Ashanti'), ('PPH', '2025-06-30', 'Pepkor'),
               ('BTI', '2025-06-30', 'British American Tobacco'), ('ABG', '2025-06-30', 'Absa'),
               ('SOL', '2025-12-31', 'Sasol'), ('NPN', '2025-12-31', 'Naspers')]


def load():
    manifest = json.loads((RESULTS / 'manifest.json').read_text(encoding='utf-8'))
    run = ROOT / 'experiments' / 'runs' / manifest['run_id']
    if not (run / 'COMPLETED').is_file():
        raise SystemExit(f'Source run {manifest["run_id"]} is not in experiments/runs/. Rerun the study and '
                         'export it, or restore that folder.')
    config = json.loads((run / 'resolved_config.json').read_text(encoding='utf-8'))
    dates = config['dates']
    histories = pd.read_csv(RESULTS / f'longitudinal/{MODEL}/cluster_histories.csv')
    quality = pd.read_csv(RESULTS / 'primary_model_summary.csv').set_index('decision_date')
    return run, config, dates, histories, quality, get_feature_set(manifest['feature_set'])


def scores(quality, date):
    q = quality.loc[date]
    return (f'feature space S = {q.silhouette_features:.2f}, DB = {q.davies_bouldin_features:.2f};  '
            f'embedding S = {q.silhouette_embedding:.2f}, DB = {q.davies_bouldin_embedding:.2f}')


def cluster_maps(run, dates, histories, quality, colours):
    """One row per date: the UMAP map coloured by aligned cluster, with the members listed beside it."""
    aligned = histories.set_index('ticker')
    fig, axes = plt.subplots(len(dates), 2, figsize=(6.6, 8.9), gridspec_kw={'width_ratios': [1.25, 1]})
    for (axis, panel), date in zip(axes, dates):
        with np.load(run / f'models/{MODEL}/{date}/arrays.npz', allow_pickle=False) as saved:
            z, tickers = saved['embedding'], saved['tickers'].astype(str)
        ids = aligned.loc[tickers, date].astype(int).to_numpy()
        axis.scatter(z[:, 0], z[:, 1], c=[colours[i] for i in ids], s=22, edgecolor='white', linewidth=.4)
        panel.axis('off')
        present = sorted(set(ids))
        for row, cluster in enumerate(present):
            members = sorted(tickers[ids == cluster])
            axis.annotate(str(cluster), z[ids == cluster].mean(axis=0), fontsize=8, fontweight='bold',
                          ha='center', va='center',
                          bbox={'facecolor': 'white', 'alpha': .75, 'edgecolor': 'none', 'pad': .8})
            y = 1 - row / len(present)
            panel.scatter(.02, y - .035, marker='s', s=40, color=colours[cluster], transform=panel.transAxes,
                          clip_on=False)
            panel.text(.07, y, f'Cluster {cluster} (n = {len(members)})', fontsize=7, fontweight='bold', va='top',
                       transform=panel.transAxes)
            panel.text(.07, y - .045, fill(', '.join(members), 44), fontsize=6.3, va='top',
                       transform=panel.transAxes)
        axis.set_title(f'{date}\n{scores(quality, date)}', fontsize=7.5)
        axis.set_xlabel('UMAP 1')
        axis.set_ylabel('UMAP 2')
        axis.tick_params(labelsize=6)
    fig.tight_layout(h_pad=1.6)
    fig.savefig(OUT / 'cluster_maps.pdf')
    plt.close(fig)


def aligned_cluster_map(run, date, histories, quality, colours):
    """One date's map in the layout of the study's cluster_map.png, numbered with aligned ids.

    Same representation and partition as the original Python map; only the
    cluster numbers and colours change, to the Jaccard-aligned ids used in
    the rest of the paper.
    """
    aligned = histories.set_index('ticker')[date]
    frame = pd.read_csv(run / f'models/{MODEL}/{date}/assignments.csv').set_index('ticker')
    with np.load(run / f'models/{MODEL}/{date}/arrays.npz', allow_pickle=False) as saved:
        z, tickers = saved['embedding'], saved['tickers'].astype(str)
    ids = aligned.loc[tickers].astype(int).to_numpy()
    fig, (axis, panel) = plt.subplots(1, 2, figsize=(13, 7), gridspec_kw={'width_ratios': [2, 1]})
    axis.scatter(z[:, 0], z[:, 1], c=[colours[i] for i in ids], s=55, edgecolor='white', linewidth=.5)
    panel.axis('off')
    groups = sorted(set(ids))
    for number, group in enumerate(groups):
        members = tickers[ids == group]
        # Label just above the cluster, so it never covers the points.
        points = z[ids == group]
        axis.annotate(str(group), (points[:, 0].mean(), points[:, 1].max()), xytext=(0, 7),
                      textcoords='offset points', ha='center', va='bottom', fontsize=13, fontweight='bold',
                      color=plots._readable(colours[group]))
        labels = [t + ('*' if frame.loc[t, 'fundamentals_imputed'] or frame.loc[t, 'volume_imputed'] else '')
                  for t in sorted(members)]
        position = .98 - number * .9 / len(groups)
        panel.text(0, position, f'Cluster {group}, n={len(members)}', fontsize=13, fontweight='bold',
                   color=plots._readable(colours[group]), va='top')
        panel.text(0, position - .04, fill(', '.join(labels), width=34), fontsize=12, va='top')
    panel.text(0, 0, '* imputed input. Cluster numbers are aligned across dates.', fontsize=11)
    q = quality.loc[date]
    axis.set_title(f'{date}: UMAP and agglomerative clustering, k=8\n'
                   f'Feature space: S {q.silhouette_features:.2f}, DB {q.davies_bouldin_features:.2f}   |   '
                   f'Embedding: S {q.silhouette_embedding:.2f}, DB {q.davies_bouldin_embedding:.2f}', fontsize=14)
    axis.set_xlabel('UMAP 1', fontsize=13)
    axis.set_ylabel('UMAP 2', fontsize=13)
    axis.tick_params(labelsize=11)
    fig.tight_layout()
    fig.savefig(OUT / f'cluster_map_{date}.pdf')
    plt.close(fig)


def cluster_profiles(dates, feature_set, quality, colours):
    """Cluster median minus the date median, in scaled units, at each date."""
    table = pd.read_csv(RESULTS / f'longitudinal/{MODEL}/moves/cluster_profiles.csv')
    fig, axes = plt.subplots(len(dates), 1, figsize=(6.6, 8.6))
    limit = float(table.deviation_scaled.abs().max())
    for axis, date in zip(axes, dates):
        sub = table[table.decision_date == date]
        grid = sub.pivot(index='cluster', columns='feature', values='deviation_scaled')[list(feature_set.columns)]
        sizes = sub.drop_duplicates('cluster').set_index('cluster').n
        image = axis.imshow(grid.to_numpy(), cmap='coolwarm', vmin=-limit, vmax=limit, aspect='auto')
        for i in range(grid.shape[0]):
            for j in range(grid.shape[1]):
                value = grid.iat[i, j]
                axis.text(j, i, f'{value:+.2f}', ha='center', va='center', fontsize=6,
                          color='white' if abs(value) > .6 * limit else 'black')
        axis.set_yticks(range(len(grid)), [f'Cluster {c} (n = {sizes[c]})' for c in grid.index], fontsize=7)
        for tick, cluster in zip(axis.get_yticklabels(), grid.index):
            tick.set_color(plots._readable(colours[int(cluster)]))
            tick.set_fontweight('bold')
        axis.set_xticks(range(len(feature_set.labels)), feature_set.labels if date == dates[-1] else [],
                        rotation=30, ha='right', fontsize=7)
        axis.set_title(f'{date}: {scores(quality, date)}', fontsize=7.5)
        fig.colorbar(image, ax=axis, fraction=.025, pad=.015).ax.tick_params(labelsize=6)
    fig.tight_layout()
    fig.savefig(OUT / 'cluster_profiles.pdf')
    plt.close(fig)


def movement_cases(feature_set, colours):
    """For six instruments that moved: scaled feature values before and after, against both clusters."""
    detail = pd.read_csv(RESULTS / f'longitudinal/{MODEL}/moves/move_features.csv')
    order = list(feature_set.columns)[::-1]
    y = np.arange(len(order))
    fig, axes = plt.subplots(3, 2, figsize=(6.6, 8.4), sharey=True)
    for axis, (ticker, before, name) in zip(axes.flat, MOVES_SHOWN):
        rows = detail[(detail.ticker == ticker) & (detail.before == before)].set_index('feature').loc[order]
        source, destination = int(rows.from_cluster.iloc[0]), int(rows.to_cluster.iloc[0])
        after = rows.after.iloc[0]
        axis.axvspan(0, 1, color='grey', alpha=.07)
        axis.scatter(rows.source_median_before, y + .2, marker='s', s=34, color=colours[source], edgecolor='black',
                     linewidth=.5, label=f'cluster {source} median, before')
        axis.scatter(rows.destination_median_after, y - .2, marker='D', s=30, color=colours[destination],
                     edgecolor='black', linewidth=.5, label=f'cluster {destination} median, after')
        for row, position in zip(rows.itertuples(), y):
            axis.annotate('', xy=(row.scaled_after, position), xytext=(row.scaled_before, position),
                          arrowprops={'arrowstyle': '->', 'color': 'black', 'lw': 1})
        axis.scatter(rows.scaled_before, y, facecolors='white', edgecolors='black', s=20, zorder=3,
                     label=f'{ticker} before')
        axis.scatter(rows.scaled_after, y, color='black', s=20, zorder=3, label=f'{ticker} after')
        axis.set_yticks(y, [feature_set.label(f) for f in order], fontsize=7)
        axis.set_title(f'{name} ({ticker}): cluster {source} to {destination}\n{before} to {after}', fontsize=7.5)
        axis.grid(axis='x', alpha=.2)
        axis.tick_params(axis='x', labelsize=6)
        axis.legend(fontsize=5.5, loc='upper center', bbox_to_anchor=(.5, -.1), ncol=2, frameon=False,
                    handletextpad=.2, columnspacing=.8)
    for axis in axes[-1]:
        axis.set_xlabel('Scaled value (June 2025 MinMax units)', fontsize=7)
    fig.tight_layout(h_pad=1.2)
    fig.savefig(OUT / 'movement_cases.pdf')
    plt.close(fig)


def distance_screen(dates):
    """Squared Mahalanobis distance at each date for every instrument flagged at least once."""
    table = pd.read_csv(RESULTS / 'longitudinal/feature_space_screen.csv')
    flagged = table[table.flag == 1].ticker.unique()
    wide = table[table.ticker.isin(flagged)].pivot(index='ticker', columns='decision_date', values='squared_distance')
    wide = wide.loc[wide.max(axis=1).sort_values().index]
    reference = float(table.reference.iloc[0])
    fig, axis = plt.subplots(figsize=(6.6, 3.2))
    height = .26
    for offset, date, colour in zip([height, 0, -height], dates, ['#9ecae1', '#4292c6', '#08519c']):
        axis.barh(np.arange(len(wide)) + offset, wide[date], height, color=colour, label=date)
    axis.axvline(reference, color='firebrick', linestyle='--', linewidth=1)
    axis.text(reference + .3, -.55, f'reference {reference:.2f}', color='firebrick', fontsize=7, va='bottom')
    axis.set_yticks(range(len(wide)), wide.index)
    axis.set_xlabel('Squared Mahalanobis distance from the same-date mean (eight scaled features)')
    axis.legend(fontsize=7, frameon=False, loc='lower right')
    axis.grid(axis='x', alpha=.2)
    fig.tight_layout()
    fig.savefig(OUT / 'distance_screen.pdf')
    plt.close(fig)


def dendrogram(run, config, date, histories, colours):
    """The agglomerative tree at one date; leaf labels carry the aligned cluster id and its colour."""
    from scipy.cluster.hierarchy import dendrogram as draw

    aligned = histories.set_index('ticker')[date]
    frame = pd.read_csv(run / f'models/{MODEL}/{date}/assignments.csv')
    with np.load(run / f'models/{MODEL}/{date}/arrays.npz', allow_pickle=False) as saved:
        z, tickers = saved['embedding'], saved['tickers'].astype(str)
    names = frame.set_index('ticker').company.str.title().reindex(tickers)
    labels = [f'{names[t]} ({t}), cluster {int(aligned[t])}' for t in tickers]
    matrix = linkage_matrix(z, config['primary_models'][MODEL]['hierarchical'])
    # Cutting between the 8th- and 9th-last merges gives the eight clusters.
    threshold = (matrix[-config['k'], 2] + matrix[-config['k'] + 1, 2]) / 2
    fig, axis = plt.subplots(figsize=(6.6, 7.6))
    draw(matrix, labels=labels, orientation='left', leaf_font_size=6.5, ax=axis, color_threshold=0,
         above_threshold_color='#555555')
    axis.axvline(threshold, color='firebrick', linestyle='--', linewidth=.8)
    for tick in axis.get_ymajorticklabels():
        cluster = int(tick.get_text().rsplit(' ', 1)[1])
        tick.set_color(plots._readable(colours[cluster]))
    axis.set_xlabel('Average-linkage Manhattan distance in the UMAP coordinates')
    axis.tick_params(axis='x', labelsize=6)
    for side in ['top', 'right', 'left']:
        axis.spines[side].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / f'dendrogram_{date}.pdf')
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    run, config, dates, histories, quality, feature_set = load()
    colours = plots.cluster_colours(histories, dates)
    cluster_maps(run, dates, histories, quality, colours)
    for date in dates:
        aligned_cluster_map(run, date, histories, quality, colours)
    cluster_profiles(dates, feature_set, quality, colours)
    movement_cases(feature_set, colours)
    distance_screen(dates)
    dendrogram(run, config, dates[-1], histories, colours)
    flow_scores = {date: quality.loc[date].to_dict() for date in dates}
    plots.cluster_flows(histories, dates, OUT / 'cluster_flows.pdf', 'Study model', flow_scores)
    plots.variance_shares(pd.read_csv(RESULTS / 'feature_audit/dominance.csv'), OUT / 'feature_dominance.pdf')
    k_table = pd.read_csv(run / f'models/{MODEL}/cluster_count_sensitivity.csv')
    plots.cluster_count_sensitivity(k_table, OUT / 'cluster_count_sensitivity.pdf', dates, config['k'],
                                    'Sensitivity to the number of clusters')
    print(f'Wrote {len(list(OUT.glob("*.pdf")))} figures to {OUT}')


if __name__ == '__main__':
    main()
