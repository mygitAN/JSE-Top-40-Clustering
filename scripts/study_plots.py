"""Readable figures used by the notebook and command-line study workflow."""


def cluster_map(frame, embedding, labels, path, title):
    import numpy as np
    import matplotlib.pyplot as plt
    from textwrap import fill

    fig, (axis, panel) = plt.subplots(1, 2, figsize=(13, 7), gridspec_kw={'width_ratios': [2, 1]})
    points = axis.scatter(embedding[:, 0], embedding[:, 1], c=labels, cmap='tab10', s=40)
    groups = sorted(np.unique(labels))
    panel.axis('off')
    for number, group in enumerate(groups):
        members = frame[labels == group]
        centre = embedding[labels == group, :2].mean(axis=0)
        axis.annotate(str(group), centre, fontweight='bold',
                      bbox={'facecolor': 'white', 'alpha': .8, 'edgecolor': 'none'})
        tickers = [row.ticker + ('*' if row.fundamentals_imputed or row.volume_imputed else '')
                   for row in members.itertuples()]
        position = .98 - number * .9 / len(groups)
        panel.text(0, position, f'Cluster {group}, n={len(members)}', fontsize=9, fontweight='bold',
                   color=points.cmap(points.norm(group)), va='top')
        panel.text(0, position - .035, fill(', '.join(tickers), width=39), fontsize=8, va='top')
    panel.text(0, 0, '* model-only imputation; local cluster IDs', fontsize=8)
    axis.set_title(title, fontsize=11)
    axis.set_xlabel('Representation axis 1 (independent date fit)')
    axis.set_ylabel('Representation axis 2 (independent date fit)')
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def quality_comparison(table, path, date):
    import matplotlib.pyplot as plt

    metrics = [('silhouette_embedding', 'Embedding silhouette: higher better'),
               ('davies_bouldin_embedding', 'Embedding DB: lower better'),
               ('silhouette_features', 'Common-feature silhouette: higher better'),
               ('davies_bouldin_features', 'Common-feature DB: lower better')]
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    labels = [f'{row.model} ({row.coverage:.0%})' for row in table.itertuples()]
    colors = ['#e48b35' if name == 'umap_fixed_sensitivity' else '#256b98' if name == 'tsne_hierarchical'
              else '#a9b8c3' for name in table.model]
    for axis, (column, title) in zip(axes.flat, metrics):
        axis.barh(labels, table[column], color=colors)
        axis.set_title(title)
        axis.tick_params(axis='y', labelsize=8)
        axis.grid(axis='x', alpha=.2)
    fig.suptitle(f'{date}: seed-42 comparison; parentheses show non-noise coverage\n'
                 'Blue: recovered baseline. Orange: fixed UMAP sensitivity. DB uses Euclidean centroids.', fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, .94))
    fig.savefig(path, dpi=140)
    plt.close(fig)


def feature_profile(frame, scaled, features, path, title):
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    from study_eda import LABELS

    values = pd.DataFrame(scaled, columns=features)
    values['cluster'] = frame.cluster.to_numpy()
    deviation = values.groupby('cluster')[features].median() - np.median(scaled, axis=0)
    limit = max(.01, float(np.abs(deviation.to_numpy()).max()))
    fig, axis = plt.subplots(figsize=(12, 5))
    image = axis.imshow(deviation, cmap='coolwarm', vmin=-limit, vmax=limit, aspect='auto')
    axis.set_xticks(range(len(features)), LABELS, rotation=45, ha='right', fontsize=8)
    axis.set_yticks(range(len(deviation)), [f'Cluster {c}' for c in deviation.index])
    axis.set_title(title + '\nCluster median minus same-date median; June-scaled units')
    fig.colorbar(image, ax=axis, label='Signed median deviation')
    fig.tight_layout()
    fig.savefig(path, dpi=145)
    plt.close(fig)
    return deviation


def shap_distribution(folder, frame, title):
    import numpy as np
    import matplotlib.pyplot as plt
    from study_eda import LABELS

    counts = frame.groupby('cluster').size().sort_index()
    target = int(counts.idxmax())
    with np.load(folder / 'shap_values.npz', allow_pickle=False) as saved:
        class_index = int(np.flatnonzero(saved['cluster_labels'] == target)[0])
        values = saved['values'][:, :, class_index]
        features = saved['feature_values']
    importance = np.abs(values).mean(axis=0)
    order = np.argsort(importance)
    fig, axis = plt.subplots(figsize=(10, 6))
    for position, feature in enumerate(order):
        raw = features[:, feature]
        span = raw.max() - raw.min()
        color = (raw - raw.min()) / span if span else np.full(len(raw), .5)
        jitter = np.random.default_rng(42 + int(feature)).uniform(-.18, .18, len(raw))
        points = axis.scatter(values[:, feature], position + jitter, c=color, cmap='coolwarm',
                              vmin=0, vmax=1, s=22, alpha=.8)
    axis.axvline(0, color='grey', linewidth=.8)
    axis.set_yticks(range(10), [LABELS[i] for i in order])
    axis.set_xlabel('SHAP contribution to this surrogate class raw margin (all instruments)')
    axis.set_title(f'{title}\nClass = local cluster {target}, n={counts[target]} (largest group example)', fontsize=10)
    fig.colorbar(points, ax=axis, label='Relative feature value: colour normalised for display only')
    fig.tight_layout()
    fig.savefig(folder / 'shap_distribution.png', dpi=150)
    plt.close(fig)


def transitions_plot(folder, dates, title):
    import pandas as pd
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for axis, before, after in zip(axes, dates, dates[1:]):
        matrix = pd.read_csv(folder / f'transition_matrix_{before}_{after}.csv', index_col=0)
        image = axis.imshow(matrix, cmap='Blues', aspect='auto', vmin=0)
        axis.set_xticks(range(len(matrix.columns)), matrix.columns)
        axis.set_yticks(range(len(matrix)), matrix.index)
        for i in range(len(matrix)):
            for j in range(len(matrix.columns)):
                axis.text(j, i, str(matrix.iloc[i, j]), ha='center', va='center', fontsize=8,
                          color='white' if matrix.iloc[i,j]>.6*matrix.to_numpy().max() else 'black')
        axis.set_title(f'{before} to {after}', fontsize=10)
        axis.set_xlabel('Following aligned cluster ID')
        axis.set_ylabel('Previous descriptive cluster ID')
        fig.colorbar(image, ax=axis, label='Continuing instruments')
    fig.suptitle(title + ': continuing members only; IDs do not establish economic identities')
    fig.tight_layout(rect=(0, 0, 1, .94))
    fig.savefig(folder / 'transition_heatmaps.png', dpi=150)
    plt.close(fig)


def cluster_count_plot(table, path, dates, reference_k, title):
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 3, figsize=(14, 7))
    for column, date in enumerate(dates):
        sub = table[table.decision_date == date].sort_values('k')
        for row, metric, colors in [(0, 'silhouette', ['steelblue', 'teal']),
                                     (1, 'davies_bouldin', ['firebrick', 'darkorange'])]:
            axis = axes[row, column]
            for geometry, color in zip(['embedding', 'features'], colors):
                axis.plot(sub.k, sub[f'{metric}_{geometry}'], marker='o', color=color, label=geometry)
            axis.axvline(reference_k, color='grey', linestyle='--', linewidth=1, label=f'Fixed k={reference_k}')
            axis.set_title(date)
            axis.set_xlabel('Number of clusters')
            axis.set_ylabel('Silhouette: higher better' if row == 0 else 'DB: lower better')
            axis.grid(alpha=.2)
            if column == 0:
                axis.legend(fontsize=7)
    fig.suptitle(title + '\nSensitivity plots only: settings are not retuned on later dates')
    fig.tight_layout(rect=(0, 0, 1, .93))
    fig.savefig(path, dpi=145)
    plt.close(fig)
