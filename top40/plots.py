"""Figures. Every function writes one PNG and fits nothing."""
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BLUE, ORANGE, GREY = '#256b98', '#e48b35', '#a9b8c3'


def score_line(quality, compact=False):
    """Silhouette (higher is better) and Davies-Bouldin (lower is better) in both spaces."""
    def number(value):
        return 'n/a' if value is None or value != value else f'{value:.2f}'
    features = f'S {number(quality["silhouette_features"])}, DB {number(quality["davies_bouldin_features"])}'
    embedding = f'S {number(quality["silhouette_embedding"])}, DB {number(quality["davies_bouldin_embedding"])}'
    if compact:
        return f'Features: {features}\nEmbedding: {embedding}'
    return (f'Feature space: {features}   |   Embedding: {embedding}   '
            '(S = silhouette, higher is better; DB = Davies-Bouldin, lower is better)')


def _tight_below_title(fig, lines):
    """tight_layout, leaving room for a suptitle of ``lines`` lines."""
    height = fig.get_size_inches()[1]
    fig.tight_layout(rect=(0, 0, 1, 1 - (.25 * lines + .15) / height))


def _save(fig, path, dpi=145):
    fig.savefig(path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)


def _annotated_heatmap(axis, table, fmt, cmap='Blues', vmin=0, vmax=None, fontsize=8):
    values = table.to_numpy(dtype=float)
    colours = plt.get_cmap(cmap).copy()
    colours.set_bad('#dddddd')
    top = np.nanmax(values) if vmax is None else vmax
    image = axis.imshow(values, cmap=colours, vmin=vmin, vmax=top, aspect='auto')
    axis.set_xticks(range(table.shape[1]), table.columns)
    axis.set_yticks(range(table.shape[0]), table.index)
    for i in range(table.shape[0]):
        for j in range(table.shape[1]):
            value = values[i, j]
            dark = np.isfinite(value) and abs(value - vmin) > .6 * (top - vmin)
            axis.text(j, i, 'NA' if np.isnan(value) else fmt(value), ha='center', va='center',
                      fontsize=fontsize, color='white' if dark else 'black')
    return image


# --- exploratory data analysis ---------------------------------------------------------------

def population_and_sectors(population, frame, path):
    dates = list(population.decision_date)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    positions, width = np.arange(len(dates)), .36
    for offset, column, label, colour in [(-width / 2, 'economic_groups', 'Company groups', '#2e765e'),
                                          (width / 2, 'instruments', 'Listed instruments', BLUE)]:
        axes[0].bar_label(axes[0].bar(positions + offset, population[column], width, label=label, color=colour),
                          padding=3)
    axes[0].set_xticks(positions, dates)
    axes[0].set_ylim(0, 55)
    axes[0].set_ylabel('Count')
    axes[0].legend(fontsize=8, loc='upper left')
    pd.crosstab(frame.decision_date, frame.sector_label).reindex(dates).plot.bar(
        stacked=True, ax=axes[1], rot=0, cmap='tab10')
    axes[1].set_ylabel('Instruments')
    axes[1].set_xlabel('')
    axes[1].legend(fontsize=7, title='Legacy sector label', bbox_to_anchor=(1, 1))
    fig.suptitle('Population and sector context (Investec Limited and Investec plc are one company group)')
    fig.tight_layout()
    _save(fig, path)


def membership_presence(presence, path):
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Patch

    fig, axis = plt.subplots(figsize=(7, 11))
    axis.imshow(presence.to_numpy(dtype=int), cmap=ListedColormap(['#eeeeee', BLUE]), vmin=0, vmax=1, aspect='auto')
    axis.set_xticks(range(presence.shape[1]), presence.columns)
    axis.set_yticks(range(len(presence)), presence.index, fontsize=8)
    axis.set_title('Index membership at each date')
    axis.legend(handles=[Patch(color=BLUE, label='Member'), Patch(color='#eeeeee', label='Not a member')],
                loc='lower center', bbox_to_anchor=(.5, -.07), ncol=2)
    fig.tight_layout()
    _save(fig, path)


def feature_distributions(scaled, feature_set, dates, fit_date, path):
    columns = list(feature_set.columns)
    rows = int(np.ceil(len(columns) / 2))
    fig, axes = plt.subplots(rows, 2, figsize=(13, 3 * rows), squeeze=False)
    for axis, column in zip(axes.flat, columns):
        values = [scaled.loc[scaled.decision_date == d, column].to_numpy() for d in dates]
        axis.boxplot(values, tick_labels=dates, showfliers=False)
        for i, v in enumerate(values, 1):
            axis.scatter(i + np.linspace(-.12, .12, len(v)), v, s=8, alpha=.55, color=BLUE)
        axis.axhspan(0, 1, color='grey', alpha=.08)
        axis.set_title(feature_set.label(column))
        axis.grid(axis='y', alpha=.2)
    for axis in axes.flat[len(columns):]:
        axis.axis('off')
    fig.suptitle(f'{feature_set.name}: features in {fit_date} MinMax units (shaded band = the {fit_date} range)',
                 fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, .98))
    _save(fig, path)


def correlation(corr, feature_set, date, path):
    table = corr.copy()
    table.index = table.columns = list(feature_set.labels)
    fig, axis = plt.subplots(figsize=(1 + .9 * len(table), .9 * len(table)))
    image = _annotated_heatmap(axis, table, lambda v: f'{v:.2f}', cmap='coolwarm', vmin=-1, vmax=1, fontsize=7)
    axis.set_xticklabels(table.columns, rotation=60, ha='right', fontsize=8)
    axis.set_title(f'{date}: Spearman rank correlations, {feature_set.name}')
    fig.colorbar(image, ax=axis, shrink=.8)
    fig.tight_layout()
    _save(fig, path)


def variance_shares(dominance, path):
    """Each feature set's largest single-feature share of scaled variance, by date."""
    fig, axis = plt.subplots(figsize=(9, 4.5))
    for name, sub in dominance.groupby('feature_set', sort=False):
        axis.plot(sub.decision_date, sub.top_variance_share, marker='o', label=name)
        for row in sub.itertuples():
            axis.annotate(row.top_feature_label, (row.decision_date, row.top_variance_share), fontsize=7,
                          xytext=(4, 4), textcoords='offset points')
    axis.set_ylim(0, 1)
    axis.set_ylabel('Largest feature share of total scaled variance')
    axis.set_title('Feature dominance: how much of the geometry one feature carries')
    axis.grid(alpha=.2)
    axis.legend(fontsize=8)
    fig.tight_layout()
    _save(fig, path)


# --- models ----------------------------------------------------------------------------------

def cluster_map(frame, embedding, labels, path, title, quality=None):
    from textwrap import fill

    fig, (axis, panel) = plt.subplots(1, 2, figsize=(13, 7), gridspec_kw={'width_ratios': [2, 1]})
    points = axis.scatter(embedding[:, 0], embedding[:, 1], c=labels, cmap='tab10', s=40)
    groups = sorted(np.unique(labels))
    panel.axis('off')
    for number, group in enumerate(groups):
        members = frame[labels == group]
        axis.annotate(str(group), embedding[labels == group, :2].mean(axis=0), fontweight='bold',
                      bbox={'facecolor': 'white', 'alpha': .8, 'edgecolor': 'none'})
        tickers = [row.ticker + ('*' if row.fundamentals_imputed or row.volume_imputed else '')
                   for row in members.itertuples()]
        position = .98 - number * .9 / len(groups)
        panel.text(0, position, f'Cluster {group}, n={len(members)}', fontsize=9, fontweight='bold',
                   color=points.cmap(points.norm(group)), va='top')
        panel.text(0, position - .035, fill(', '.join(tickers), width=39), fontsize=8, va='top')
    panel.text(0, 0, '* imputed input. Cluster numbers are local to this fit.', fontsize=8)
    fig.suptitle(title, fontsize=13, fontweight='bold')
    if quality is not None:
        def value(key):
            number = quality[key]
            return 'n/a' if number is None or not np.isfinite(number) else f'{number:.3f}'
        scores = (f'Feature space: Silhouette = {value("silhouette_features")}   |   '
                  f'Davies-Bouldin = {value("davies_bouldin_features")}\n'
                  f'Embedding space: Silhouette = {value("silhouette_embedding")}   |   '
                  f'Davies-Bouldin = {value("davies_bouldin_embedding")}\n'
                  'Silhouette: higher is better. Davies-Bouldin: lower is better.')
        fig.text(.5, .925, scores, ha='center', va='top', fontsize=10,
                 bbox=dict(boxstyle='round,pad=.5', facecolor='#eef4f8', edgecolor='#a9b8c3'))
    axis.set_xlabel('Representation axis 1')
    axis.set_ylabel('Representation axis 2')
    fig.tight_layout(rect=(0, 0, 1, .80) if quality is not None else (0, 0, 1, .95))
    _save(fig, path, dpi=150)


def quality_comparison(table, path, date, highlight):
    metrics = [('silhouette_embedding', 'Embedding silhouette (higher is better)'),
               ('davies_bouldin_embedding', 'Embedding Davies-Bouldin (lower is better)'),
               ('silhouette_features', 'Feature-space silhouette (higher is better)'),
               ('davies_bouldin_features', 'Feature-space Davies-Bouldin (lower is better)')]
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    labels = [f'{row.model} ({row.coverage:.0%})' for row in table.itertuples()]
    colours = [highlight.get(name, GREY) for name in table.model]
    for axis, (column, title) in zip(axes.flat, metrics):
        axis.barh(labels, table[column].astype(float), color=colours)
        axis.set_title(title)
        axis.tick_params(axis='y', labelsize=8)
        axis.grid(axis='x', alpha=.2)
    fig.suptitle(f'{date}: representative-seed comparison; brackets show non-noise coverage. '
                 'Orange: the study model. Blue: the original paper t-SNE recipe.', fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, .96))
    _save(fig, path)


def feature_profile(frame, scaled, feature_set, path, title):
    """Heatmap of cluster median minus same-date median. Returns the table."""
    values = pd.DataFrame(scaled, columns=list(feature_set.columns))
    values['cluster'] = frame.cluster.to_numpy()
    deviation = values.groupby('cluster').median() - np.median(scaled, axis=0)
    limit = max(.01, float(np.abs(deviation.to_numpy()).max()))
    table = deviation.copy()
    table.columns = list(feature_set.labels)
    table.index = [f'Cluster {c} (n={n})' for c, n in values.groupby('cluster').size().items()]
    fig, axis = plt.subplots(figsize=(12, 5))
    image = _annotated_heatmap(axis, table, lambda v: f'{v:+.2f}', cmap='coolwarm', vmin=-limit, vmax=limit, fontsize=7)
    axis.set_xticklabels(table.columns, rotation=45, ha='right', fontsize=8)
    axis.set_title(title + '\nCluster median minus same-date median, in scaled units')
    fig.colorbar(image, ax=axis)
    fig.tight_layout()
    _save(fig, path)
    return deviation


def dendrogram(matrix, frame, path, title):
    from scipy.cluster.hierarchy import dendrogram as draw

    fig, axis = plt.subplots(figsize=(12, 11))
    draw(matrix, labels=[f'{row.ticker} | {row.sector_label}' for row in frame.itertuples()],
         orientation='left', leaf_font_size=8, ax=axis)
    axis.set_title(title, fontsize=10)
    axis.set_xlabel('Linkage distance in the fitted representation')
    fig.tight_layout()
    _save(fig, path, dpi=140)


def cluster_count_sensitivity(table, path, dates, reference_k, title):
    fig, axes = plt.subplots(2, len(dates), figsize=(4.7 * len(dates), 7), squeeze=False)
    for column, date in enumerate(dates):
        sub = table[table.decision_date == date].sort_values('k')
        for row, metric, colours in [(0, 'silhouette', ['steelblue', 'teal']),
                                     (1, 'davies_bouldin', ['firebrick', 'darkorange'])]:
            axis = axes[row, column]
            for geometry, colour in zip(['embedding', 'features'], colours):
                axis.plot(sub.k, sub[f'{metric}_{geometry}'].astype(float), marker='o', color=colour, label=geometry)
            axis.axvline(reference_k, color='grey', linestyle='--', linewidth=1, label=f'k={reference_k}')
            axis.set_title(date)
            axis.set_xlabel('Number of clusters')
            axis.set_ylabel('Silhouette (higher is better)' if row == 0 else 'Davies-Bouldin (lower is better)')
            axis.grid(alpha=.2)
            if column == 0:
                axis.legend(fontsize=7)
    fig.suptitle(title)
    fig.tight_layout(rect=(0, 0, 1, .95))
    _save(fig, path)


# --- explanations ----------------------------------------------------------------------------

def shap_global(table, feature_set, path, title):
    ordered = table.sort_values('mean_abs_shap')
    fig, axis = plt.subplots(figsize=(8, 5))
    axis.barh([feature_set.label(f) for f in ordered.feature], ordered.mean_abs_shap, color=BLUE)
    axis.set_xlabel('Mean |SHAP| over instruments and classes (surrogate raw margin)')
    axis.set_title(title, fontsize=10)
    fig.tight_layout()
    _save(fig, path)


def shap_distribution(folder, frame, feature_set, title):
    """SHAP values for the largest cluster's class, one row of points per feature."""
    sizes = frame.groupby('cluster').size().sort_index()
    target = int(sizes.idxmax())
    with np.load(folder / 'shap_values.npz', allow_pickle=False) as saved:
        index = int(np.flatnonzero(saved['cluster_labels'] == target)[0])
        values, raw = saved['values'][:, :, index], saved['feature_values']
    order = np.argsort(np.abs(values).mean(axis=0))
    fig, axis = plt.subplots(figsize=(10, 6))
    for position, feature in enumerate(order):
        span = raw[:, feature].max() - raw[:, feature].min()
        colour = (raw[:, feature] - raw[:, feature].min()) / span if span else np.full(len(raw), .5)
        jitter = np.random.default_rng(42 + int(feature)).uniform(-.18, .18, len(raw))
        points = axis.scatter(values[:, feature], position + jitter, c=colour, cmap='coolwarm', vmin=0, vmax=1,
                              s=22, alpha=.8)
    axis.axvline(0, color='grey', linewidth=.8)
    axis.set_yticks(range(len(order)), [feature_set.labels[i] for i in order])
    axis.set_xlabel('SHAP contribution to this class margin, all instruments')
    axis.set_title(f'{title}\nClass = cluster {target}, n={sizes[target]} (largest cluster)', fontsize=10)
    fig.colorbar(points, ax=axis, label='Feature value, low to high')
    fig.tight_layout()
    _save(fig, folder / 'shap_distribution.png', dpi=150)


# --- temporal --------------------------------------------------------------------------------

def transition_heatmaps(matrices, path, title, kind):
    """``matrices`` maps (before, after) to a movement-count or Jaccard table."""
    fig, axes = plt.subplots(1, len(matrices), figsize=(6.5 * len(matrices), 5), squeeze=False)
    for axis, ((before, after), table) in zip(axes[0], matrices.items()):
        if kind == 'jaccard':
            image = _annotated_heatmap(axis, table, lambda v: f'{v:.2f}', vmax=1)
        else:
            image = _annotated_heatmap(axis, table, lambda v: str(int(v)), vmax=max(1, table.to_numpy().max()))
        axis.set_title(f'{before} to {after}')
        axis.set_xlabel('Later aligned cluster')
        axis.set_ylabel('Earlier aligned cluster')
        fig.colorbar(image, ax=axis, label='Jaccard overlap (0-1)' if kind == 'jaccard' else 'Instruments')
    fig.suptitle(f'{title}: ' + ('membership overlap' if kind == 'jaccard' else 'instrument movements')
                 + ', continuing members only')
    fig.tight_layout()
    _save(fig, path, dpi=150)


def _readable(colour):
    """A cluster colour dark enough for text on white."""
    rgb = np.asarray(colour[:3], dtype=float)
    luminance = rgb @ np.array([.2126, .7152, .0722])
    return tuple(rgb * min(1, .45 / luminance)) if luminance > .45 else tuple(rgb)


def cluster_profile_panels(profiles, summary, feature_set, colours, path, title, quality=None):
    """Left: cluster median minus date median. Middle: surrogate mean |SHAP|. Right: members."""
    from textwrap import fill

    deviation = profiles.pivot(index='cluster', columns='feature', values='deviation_scaled')[list(feature_set.columns)]
    shap = profiles.pivot(index='cluster', columns='feature', values='mean_abs_shap')[list(feature_set.columns)]
    deviation.columns = shap.columns = list(feature_set.labels)
    summary = summary.set_index('cluster').loc[deviation.index]
    rows = [f'Cluster {c} (n={summary.n[c]})' for c in deviation.index]
    deviation.index = shap.index = rows
    fig, axes = plt.subplots(1, 3, figsize=(20, 1.1 + .62 * len(rows)),
                             gridspec_kw={'width_ratios': [len(feature_set.columns), len(feature_set.columns), 5]})
    limit = max(.05, float(np.abs(deviation.to_numpy()).max()))
    image = _annotated_heatmap(axes[0], deviation, lambda v: f'{v:+.2f}', cmap='coolwarm', vmin=-limit, vmax=limit,
                               fontsize=7)
    axes[0].set_title('Cluster median minus date median (scaled units)\nred = high, blue = low', fontsize=10)
    fig.colorbar(image, ax=axes[0], shrink=.8)
    image = _annotated_heatmap(axes[1], shap, lambda v: f'{v:.2f}', fontsize=7)
    oof = summary.surrogate_oof_accuracy.iloc[0]
    axes[1].set_title('Surrogate mean |SHAP| for members (what the classifier uses)\n'
                      f'out-of-fold fidelity {oof:.2f}' if oof == oof and oof is not None else
                      'Surrogate mean |SHAP| for members\nout-of-fold fidelity not estimable', fontsize=10)
    fig.colorbar(image, ax=axes[1], shrink=.8)
    for axis in axes[:2]:
        axis.set_xticklabels(axis.get_xticklabels(), rotation=45, ha='right', fontsize=8)
        for tick, cluster in zip(axis.get_yticklabels(), summary.index):
            tick.set_color(_readable(colours.get(int(cluster), (0, 0, 0))))
            tick.set_fontweight('bold')
    axes[1].set_yticklabels([])
    axes[2].axis('off')
    for i, cluster in enumerate(summary.index):
        axes[2].scatter(0, i, marker='s', s=90, color=colours.get(int(cluster), GREY))
        axes[2].text(.06, i, fill(summary.members[cluster], 48), va='center', fontsize=8,
                     color=_readable(colours.get(int(cluster), (0, 0, 0))))
    axes[2].set_xlim(-.04, 1)
    axes[2].set_ylim(len(rows) - .5, -.5)
    axes[2].set_title('Members', fontsize=10, loc='left')
    fig.suptitle(title + ('\n' + score_line(quality) if quality else ''), fontsize=12)
    _tight_below_title(fig, lines=2 if quality else 1)
    _save(fig, path)


def move_panels(move, detail, feature_set, colours, path, model, quality=None):
    """One instrument's move: its feature values against both clusters, and the surrogate's attribution."""
    order = list(feature_set.columns)[::-1]
    detail = detail.set_index('feature').loc[order]
    y = np.arange(len(order))
    source, destination = colours.get(move.from_cluster, GREY), colours.get(move.to_cluster, GREY)
    fig, (left, right) = plt.subplots(1, 2, figsize=(17, 2.5 + .55 * len(order)), sharey=True,
                                      gridspec_kw={'width_ratios': [3, 2]})
    left.scatter(detail.source_median_before, y + .18, marker='s', s=70, color=source, edgecolor='black',
                 label=f'Cluster {move.from_cluster} median, {move.before}')
    left.scatter(detail.destination_median_after, y - .18, marker='D', s=70, color=destination, edgecolor='black',
                 label=f'Cluster {move.to_cluster} median, {move.after}')
    left.scatter(detail.old_peers_median_after, y, marker='x', s=60, color='dimgrey',
                 label=f'Former peers\' median, {move.after}')
    for row, position in zip(detail.itertuples(), y):
        left.annotate('', xy=(row.scaled_after, position), xytext=(row.scaled_before, position),
                      arrowprops=dict(arrowstyle='->', color='black', lw=1.4))
    left.scatter(detail.scaled_before, y, facecolors='white', edgecolors='black', s=55, zorder=3,
                 label=f'{move.ticker}, {move.before}')
    left.scatter(detail.scaled_after, y, color='black', s=55, zorder=3, label=f'{move.ticker}, {move.after}')
    left.set_yticks(y, [feature_set.label(f) for f in order])
    left.axvspan(0, 1, color='grey', alpha=.06)
    left.set_xlabel('Scaled value (June 2025 MinMax units)')
    left.set_title('What changed, against the old and new cluster', fontsize=10)
    left.grid(axis='x', alpha=.2)
    left.legend(fontsize=7, loc='upper center', bbox_to_anchor=(.5, -.22), ncol=2, frameon=False)
    height = .36
    right.barh(y + height / 2, detail.shap_destination_after, height, color=destination,
               label=f'toward cluster {move.to_cluster}, {move.after}')
    right.barh(y - height / 2, detail.shap_source_before, height, color=source, alpha=.6,
               label=f'toward cluster {move.from_cluster}, {move.before}')
    right.axvline(0, color='grey', lw=.8)
    oof = move.surrogate_oof_accuracy_after
    right.set_title('Surrogate SHAP for its own cluster at each date\n(separate models per date; '
                    + (f'out-of-fold fidelity {oof:.2f} at {move.after})' if oof == oof and oof is not None
                       else f'fidelity not estimable at {move.after})'), fontsize=10)
    right.set_xlabel('SHAP contribution (positive pushes toward that cluster)')
    right.legend(fontsize=7, loc='upper center', bbox_to_anchor=(.5, -.22), ncol=1, frameon=False)

    def share(value):
        return 'n/a' if value is None or value != value else f'{value:.0%}'
    fig.suptitle(f'{model}: {move.ticker} ({move.company}) moved from cluster {move.from_cluster} to '
                 f'{move.to_cluster}, {move.before} to {move.after}\n'
                 f'{move.move_type}; kept {share(move.peer_retention)} of old peers; across seeds it sits with '
                 f'{share(move.support_new_peers)} of new peers and {share(move.support_old_peers)} of old peers'
                 + (f'; caveat: {move.data_caveat}' if move.data_caveat else '')
                 + (''.join('\n' + f'{date}: {score_line(quality[date])}' for date in [move.before, move.after])
                    if quality else ''), fontsize=11)
    # Keep the multi-line title and legends clear of axes and labels.
    fig.subplots_adjust(left=.12, right=.985, bottom=.25, top=.72, wspace=.05)
    _save(fig, path)


def cluster_colours(histories, dates):
    """One colour per aligned cluster id, shared by every figure of a model."""
    ids = sorted({int(v) for v in histories[dates].to_numpy().ravel() if v == v and v is not None})
    return dict(zip(ids, plt.get_cmap('tab20')(np.linspace(0, 1, len(ids)))))


def cluster_flows(histories, dates, path, title, quality=None):
    """One strand per instrument observed at every date; a colour change is a cluster shift.

    ``quality`` maps each date to its scores, which are printed under the date.
    """
    from matplotlib.patches import Patch, PathPatch, Rectangle
    from matplotlib.path import Path as MplPath

    observed = histories[histories.observed_all_dates]
    ordered = observed.sort_values([dates[0], 'ticker']).set_index('ticker')
    labels = sorted(set(ordered[dates].to_numpy().astype(int).ravel()))
    colours = cluster_colours(histories, dates)
    rank = {ticker: i for i, ticker in enumerate(ordered.index)}
    shifted = {ticker: row[dates].nunique() > 1 for ticker, row in ordered.iterrows()}
    positions, groups, height = {}, {}, 0
    for date in dates:
        positions[date], groups[date], cursor = {}, [], 0
        for label in labels:
            members = sorted(ordered.index[ordered[date] == label], key=rank.get)
            if members:
                groups[date].append((label, cursor - .45, len(members) - .10))
                positions[date].update({ticker: cursor + i for i, ticker in enumerate(members)})
                cursor += len(members) + 1.1
        height = max(height, cursor)
    fig, axis = plt.subplots(figsize=(10.5, max(7, .30 * len(ordered) + 2)))
    for ticker in sorted(ordered.index, key=lambda t: (shifted[t], rank[t])):
        for j, (before, after) in enumerate(zip(dates, dates[1:])):
            y0, y1 = positions[before][ticker], positions[after][ticker]
            # One smooth cubic from (j+.19, y0) to (j+.81, y1), split at its midpoint so
            # that each half can take the colour of its own date.
            mid = np.array([j + .5, (y0 + y1) / 2])
            halves = [(np.array([[j + .19, y0], [j + .325, y0], [j + .4125, (3 * y0 + y1) / 4], mid]), before),
                      (np.array([mid, [j + .5875, (y0 + 3 * y1) / 4], [j + .675, y1], [j + .81, y1]]), after)]
            for vertices, date in halves:
                axis.add_patch(PathPatch(MplPath(vertices, [MplPath.MOVETO] + [MplPath.CURVE4] * 3),
                                         facecolor='none', edgecolor=colours[int(ordered.loc[ticker, date])],
                                         linewidth=2.3 if shifted[ticker] else 1.1,
                                         alpha=.82 if shifted[ticker] else .28, zorder=2 if shifted[ticker] else 1))
    for j, date in enumerate(dates):
        for label, top, size in groups[date]:
            axis.add_patch(Rectangle((j - .19, top), .38, size, facecolor=colours[label], edgecolor='white', zorder=3))
        for ticker in ordered.index:
            colour = colours[int(ordered.loc[ticker, date])]
            dark = colour[:3] @ np.array([.2126, .7152, .0722]) < .46
            axis.text(j, positions[date][ticker], ticker, ha='center', va='center', fontsize=9, zorder=4,
                      fontweight='bold' if shifted[ticker] else 'normal', color='white' if dark else 'black')
    moved = sum(shifted.values())
    axis.set_xlim(-.35, len(dates) - .65)
    axis.set_ylim(height - .1, -1.1)
    date_labels = [date + ('\n' + score_line(quality[date], compact=True) if quality else '') for date in dates]
    axis.set_xticks(range(len(dates)), date_labels, fontsize=10)
    axis.xaxis.tick_top()
    axis.tick_params(axis='both', length=0)
    axis.set_yticks([])
    for spine in axis.spines.values():
        spine.set_visible(False)
    axis.set_title(f'{title}: cluster membership across dates\n'
                   f'{len(ordered)} instruments, {len(ordered) - moved} stable, {moved} shifted', pad=35)
    axis.legend(handles=[Patch(facecolor=colours[label], label=f'Cluster {label}') for label in labels],
                loc='upper center', bbox_to_anchor=(.5, -.015), ncol=min(5, len(labels)), frameon=False, fontsize=9)
    note = ('A colour change is a cluster shift; shifted instruments are bold. '
            'Cluster ids are aligned labels, not sectors. Vertical position is layout only.')
    if quality:
        note += '\nScores are for the representative seed: S = silhouette (higher is better), DB = Davies-Bouldin (lower is better).'
    fig.text(.5, .005, note, ha='center', fontsize=9)
    fig.tight_layout(rect=(0, .05, 1, 1))
    _save(fig, path, dpi=150)
