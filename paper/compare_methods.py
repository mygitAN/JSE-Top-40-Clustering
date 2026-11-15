"""Fit the UMAP study model and the t-SNE comparator through the same pipeline and compare them.

    python paper/compare_methods.py

Both use the invariant8 features, June 2025 scaling, average-linkage Manhattan
clustering into eight groups, seeds 42-46 and Jaccard alignment across dates.
Writes three tables to paper/data/:

- method_quality.csv: per method and date, scores of the seed-42 partition,
  mean pairwise seed ARI, singletons and sector agreement.
- method_groups.csv: share of seeds in which each named group is together.
- method_histories.csv: each instrument's stable/shifted verdict per method.
"""
import json
import os
import sys
from itertools import combinations
from pathlib import Path

for name in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMBA_NUM_THREADS']:
    os.environ.setdefault(name, '1')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

from top40 import CONFIG
from top40.data import DATES, load_inputs
from top40.features import add_derived_columns, get_feature_set
from top40.models import cluster, embed, feature_matrix, prepare, scores
from top40.temporal import aligned_histories

OUT = ROOT / 'paper' / 'data'
GROUPS = {
    'Platinum core (IMP, NPH, SSW)': ['IMP', 'NPH', 'SSW'],
    'Platinum core with gold miners (ANG, GFI, HAR)': ['IMP', 'NPH', 'SSW', 'ANG', 'GFI', 'HAR'],
    'Platinum core, gold miners and Valterra (VAL)': ['IMP', 'NPH', 'SSW', 'ANG', 'GFI', 'HAR', 'VAL'],
    'Scale core (ANH, BHG, CFR)': ['ANH', 'BHG', 'CFR'],
    'Naspers and Prosus (NPN, PRX)': ['NPN', 'PRX'],
    'Absa and Old Mutual (ABG, OMU)': ['ABG', 'OMU'],
}


def main():
    config = json.loads(CONFIG.read_text(encoding='utf-8'))
    primary = config['primary_models']['umap']
    methods = {'UMAP': ('umap', primary['representation_params']),
               't-SNE': ('tsne', config['representations']['tsne'])}
    linkage, k = primary['hierarchical'], config['k']
    seeds = list(range(config['seed'], config['seed'] + config['stability_runs']))
    feature_set = get_feature_set(config['feature_set'])
    frame = add_derived_columns(load_inputs(), config['fit_date'])
    scaler, snapshots = prepare(frame, feature_set.columns, DATES, config['fit_date'])

    fits, quality = {}, []
    for method, (representation, params) in methods.items():
        for date, sub in snapshots.items():
            x = scaler.transform(feature_matrix(sub, feature_set.columns))
            labels = {}
            for seed in seeds:
                z = embed(x, representation, params, seed)
                labels[seed] = pd.Series(cluster(z, 'hierarchical', linkage, seed, k), index=sub.ticker)
                if seed == seeds[0]:
                    q = scores(x, z, labels[seed].to_numpy(), sub.sector_label)
            fits[method, date] = labels
            quality.append(dict(method=method, decision_date=date,
                                silhouette_features=q['silhouette_features'],
                                davies_bouldin_features=q['davies_bouldin_features'],
                                silhouette_embedding=q['silhouette_embedding'],
                                davies_bouldin_embedding=q['davies_bouldin_embedding'],
                                singleton_clusters=q['singleton_clusters'], sector_ari=q['sector_ari'],
                                mean_seed_ari=float(np.mean([adjusted_rand_score(labels[a], labels[b])
                                                             for a, b in combinations(seeds, 2)]))))
    quality = pd.DataFrame(quality)
    for date in DATES:
        quality.loc[quality.decision_date == date, 'cross_method_ari'] = adjusted_rand_score(
            fits['UMAP', date][seeds[0]], fits['t-SNE', date][seeds[0]])

    groups = []
    for group, members in GROUPS.items():
        for method in methods:
            row = dict(group=group, method=method)
            for date in DATES:
                labels = fits[method, date]
                row[date] = (float(np.mean([labels[s][members].nunique() == 1 for s in seeds]))
                             if all(m in labels[seeds[0]].index for m in members) else None)
            groups.append(row)

    histories, switches = {}, []
    for method in methods:
        snaps = {d: fits[method, d][seeds[0]].rename('cluster').reset_index() for d in DATES}
        _, _, _, history, _, agreement = aligned_histories(snaps, DATES)
        histories[method] = history.set_index('ticker').stability_status
        for row in agreement.itertuples():
            switches.append(dict(method=method, before=row.before, after=row.after, changed=row.changed,
                                 temporal_ari=row.ari))
    verdicts = pd.DataFrame(histories).rename_axis('ticker').reset_index()
    verdicts = verdicts[verdicts.UMAP != 'membership gap']
    verdicts['agreement'] = np.select(
        [(verdicts.UMAP == 'shifted') & (verdicts['t-SNE'] == 'shifted'),
         (verdicts.UMAP == 'stable') & (verdicts['t-SNE'] == 'stable'),
         verdicts.UMAP == 'shifted'],
        ['shifted under both', 'stable under both', 'shifted under UMAP only'], 'shifted under t-SNE only')

    OUT.mkdir(parents=True, exist_ok=True)
    quality.to_csv(OUT / 'method_quality.csv', index=False)
    pd.DataFrame(groups).to_csv(OUT / 'method_groups.csv', index=False)
    verdicts.to_csv(OUT / 'method_histories.csv', index=False)
    pd.DataFrame(switches).to_csv(OUT / 'method_switches.csv', index=False)

    pd.set_option('display.width', 200)
    print(quality.round(3).to_string(index=False))
    print(pd.DataFrame(groups).to_string(index=False))
    print(pd.DataFrame(switches).round(3).to_string(index=False))
    for verdict, rows in verdicts.groupby('agreement'):
        print(f'{verdict} ({len(rows)}): {", ".join(sorted(rows.ticker))}')


if __name__ == '__main__':
    main()
