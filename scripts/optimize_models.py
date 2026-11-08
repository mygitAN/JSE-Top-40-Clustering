"""Bounded, June-selected silhouette/DB optimisation. Never promotes paper results."""
import argparse
import hashlib
import json
import os
from itertools import combinations, product
from pathlib import Path
import time

from tracking import ROOT, Run, digest, write_json


def identifier(value, prefix):
    return prefix + hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()[:16]


def representations(config):
    result = []
    for n in config['pca_components']:
        result.append(dict(name='pca', params=dict(n_components=n, svd_solver='full')))
    for p, lr, iterations in product(config['tsne_perplexities'], config['tsne_learning_rates'], config['tsne_iterations']):
        result.append(dict(name='tsne', params=dict(n_components=2, perplexity=p, learning_rate=lr,
                          max_iter=iterations, init=config['tsne_init'], n_jobs=1)))
    for neighbors, distance in product(config['umap_neighbors'], config['umap_min_dist']):
        result.append(dict(name='umap', params=dict(n_components=2, n_neighbors=neighbors, min_dist=distance, n_jobs=1)))
    return [{**r, 'representation_id': identifier(r, 'r_')} for r in result]


def candidates(config):
    result = []
    for rep in representations(config):
        specifications = []
        for params, k in product(config['hierarchical'], config['k']):
            specifications.append(dict(algorithm='hierarchical', params={**params, 'n_clusters': k}))
        for k in config['k']:
            specifications.append(dict(algorithm='kmeans', params=dict(n_clusters=k, n_init=config['kmeans_n_init'])))
        for eps, n in product(config['dbscan_eps'], config['dbscan_min_samples']):
            specifications.append(dict(algorithm='dbscan', params=dict(eps=eps, min_samples=n)))
        for spec in specifications:
            value = dict(representation=rep, clustering=spec)
            result.append({**value, 'candidate_id': identifier(value, 'c_')})
    return result


def fit_representation(x, spec, seed):
    from sklearn.decomposition import PCA
    from sklearn.manifold import TSNE
    if spec['name'] == 'pca':
        estimator = PCA(**spec['params'])
    elif spec['name'] == 'tsne':
        estimator = TSNE(**spec['params'], random_state=seed)
    elif spec['name'] == 'umap':
        from umap import UMAP
        estimator = UMAP(**spec['params'], random_state=seed)
    else:
        raise ValueError('Unknown representation')
    z = estimator.fit_transform(x)
    resolved = dict(dimensions=z.shape[1], estimator_parameters=estimator.get_params())
    if spec['name'] == 'tsne':
        resolved['resolved_learning_rate'] = float(estimator.learning_rate_)
    if spec['name'] == 'pca':
        resolved['explained_variance_ratio'] = estimator.explained_variance_ratio_.tolist()
    return z, resolved


def fit_cluster(z, spec, seed):
    import numpy as np
    from sklearn.cluster import AgglomerativeClustering, KMeans, DBSCAN
    if spec['algorithm'] == 'hierarchical':
        model = AgglomerativeClustering(**spec['params'])
    elif spec['algorithm'] == 'kmeans':
        model = KMeans(**spec['params'], random_state=seed)
    elif spec['algorithm'] == 'dbscan':
        sd = z.std(axis=0)
        z = (z-z.mean(axis=0))/np.where(sd == 0, 1, sd)
        model = DBSCAN(**spec['params'])
    else:
        raise ValueError('Unknown clustering algorithm')
    return model.fit_predict(z)


def quality(x, z, labels):
    import numpy as np
    from sklearn.metrics import silhouette_score, davies_bouldin_score
    keep = labels != -1
    y = labels[keep]
    n_clusters = len(np.unique(y))
    valid = 1 < n_clusters < len(y)
    sizes = np.unique(y, return_counts=True)[1]
    result = dict(n_clusters=n_clusters, noise_count=int((~keep).sum()), coverage=float(keep.mean()),
                  singleton_clusters=int((sizes == 1).sum()), score_status='valid' if valid else 'not estimable: need 2..n-1 non-noise clusters',
                  silhouette_embedding=None, davies_bouldin_embedding=None,
                  silhouette_features=None, davies_bouldin_features=None)
    if valid:
        for name, data in [('embedding', z), ('features', x)]:
            result['silhouette_'+name] = float(silhouette_score(data[keep], y, metric='euclidean'))
            result['davies_bouldin_'+name] = float(davies_bouldin_score(data[keep], y))
    return result


def pareto(table, silhouette, db):
    import numpy as np
    values = table[[silhouette, db]].to_numpy()
    keep = np.ones(len(table), dtype=bool)
    for i, (s, d) in enumerate(values):
        keep[i] = not np.any((values[:, 0] >= s) & (values[:, 1] <= d) &
                            ((values[:, 0] > s) | (values[:, 1] < d)))
    return keep


def select(table, geometry, k=None):
    """Joint ordinal preference declared before execution; no sector columns read."""
    selected = table[table.eligible_all_seeds].copy()
    if k is not None:
        selected = selected[(selected.n_clusters_min == k) & (selected.n_clusters_max == k)].copy()
    if selected.empty:
        raise ValueError('No eligible candidates for selection cohort')
    sil, db = 'silhouette_'+geometry+'_mean', 'davies_bouldin_'+geometry+'_mean'
    selected['silhouette_rank'] = selected[sil].rank(ascending=False, method='average')
    selected['db_rank'] = selected[db].rank(ascending=True, method='average')
    selected['joint_rank_sum'] = selected.silhouette_rank + selected.db_rank
    selected['pareto_optimal'] = pareto(selected, sil, db)
    selected = selected.sort_values(['joint_rank_sum', 'seed_ari_mean', 'silhouette_features_mean', 'candidate_id'],
                                     ascending=[True, False, False, True]).reset_index(drop=True)
    return selected


def aggregate(rows, stability, config):
    import numpy as np
    import pandas as pd
    table = pd.DataFrame(rows)
    grouped = table.groupby('candidate_id', sort=True)
    summary = grouped.agg(seeds=('seed', 'nunique'), valid_seeds=('score_status', lambda s: int((s == 'valid').sum())),
                coverage_min=('coverage', 'min'), n_clusters_min=('n_clusters', 'min'), n_clusters_max=('n_clusters', 'max'),
                singleton_clusters_max=('singleton_clusters', 'max'))
    for metric in ['silhouette_embedding', 'davies_bouldin_embedding', 'silhouette_features', 'davies_bouldin_features']:
        for statistic in ['mean', 'std', 'min', 'max']:
            summary[metric+'_'+statistic] = getattr(grouped[metric], statistic)()
    summary = summary.join(stability.groupby('candidate_id').agg(seed_ari_mean=('ari', 'mean'), seed_ari_min=('ari','min'),
                                                                seed_nmi_mean=('nmi','mean'))).reset_index()
    summary['eligible_all_seeds'] = ((summary.seeds == len(config['seeds'])) &
        (summary.valid_seeds == len(config['seeds'])) & (summary.coverage_min == 1) &
        (summary.n_clusters_min >= 2) & (summary.n_clusters_max <= 10) &
        np.isfinite(summary[['silhouette_embedding_mean', 'davies_bouldin_embedding_mean',
                             'silhouette_features_mean', 'davies_bouldin_features_mean']]).all(axis=1))
    return summary


def baseline_candidate(pool):
    for c in pool:
        r, cl = c['representation'], c['clustering']
        if (r['name'] == 'tsne' and r['params']['perplexity'] == 5 and r['params']['learning_rate'] == 10 and
            r['params']['max_iter'] == 300 and cl['algorithm'] == 'hierarchical' and
            cl['params'] == dict(n_clusters=8, linkage='average', metric='manhattan')):
            return c
    raise ValueError('Fixed historical baseline absent from grid')


def plot_clusters(frame, z, labels, out, title):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(9, 7))
    scatter = ax.scatter(z[:, 0], z[:, 1], c=labels, cmap='tab10')
    for i, ticker in enumerate(frame.ticker):
        flag = bool(frame.iloc[i].fundamentals_imputed or frame.iloc[i].volume_imputed)
        ax.annotate(ticker+('*' if flag else ''), z[i, :2], fontsize=7)
    ax.legend(*scatter.legend_elements(), title='Local cluster ID', bbox_to_anchor=(1,1))
    ax.set_title(title, fontsize=10)
    ax.set_xlabel(f'First representation coordinate; {z.shape[1]} dimensions used for clustering; * imputed')
    ax.set_ylabel('Second representation coordinate (independent date fit)')
    fig.tight_layout(); fig.savefig(out/'clusters.png', dpi=150); plt.close(fig)


def execute(config, out):
    import numpy as np
    import pandas as pd
    from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
    from analysis import FEATURES, numeric_matrix, prepare, explain, transitions
    from validate_data import validate
    validation = validate()
    frame = pd.read_csv(ROOT/'data/processed/Top40_Retrospective_Model_Inputs_v1.csv')
    scaler, snapshots = prepare(frame)
    pool = candidates(config)
    if len(pool) != config['maximum_configurations'] or len(pool)*len(config['seeds']) != config['maximum_selection_fits']:
        raise ValueError('Grid budget does not match declared protocol')
    by_id = {c['candidate_id']: c for c in pool}
    descriptions = pd.DataFrame([dict(candidate_id=c['candidate_id'], representation_id=c['representation']['representation_id'],
        representation=c['representation']['name'], algorithm=c['clustering']['algorithm'],
        representation_parameters=json.dumps(c['representation']['params'], sort_keys=True),
        clustering_parameters=json.dumps(c['clustering']['params'], sort_keys=True)) for c in pool])
    descriptions.to_csv(out/'candidate_configurations.csv', index=False)
    train = snapshots[config['selection_date']]
    x = scaler.transform(numeric_matrix(train))
    metrics, label_rows, resolved = [], [], []
    embedding_arrays = {}
    start = time.monotonic()
    for number, rep in enumerate(representations(config), 1):
        members = [c for c in pool if c['representation']['representation_id'] == rep['representation_id']]
        print(f'Selection representation {number}/23: {rep["name"]} {rep["params"]}', flush=True)
        for seed in config['seeds']:
            z, metadata = fit_representation(x, rep, seed)
            key = rep['representation_id']+'__seed_'+str(seed)
            embedding_arrays[key] = z
            resolved.append(dict(representation_id=rep['representation_id'], seed=seed, **metadata))
            for candidate in members:
                y = fit_cluster(z, candidate['clustering'], seed)
                metrics.append(dict(candidate_id=candidate['candidate_id'], seed=seed, **quality(x,z,y)))
                label_rows.append((candidate['candidate_id'],seed,y))
    pd.DataFrame(metrics).to_csv(out/'selection_scores_all_seeds.csv', index=False)
    np.savez_compressed(out/'selection_assignments.npz', candidate_ids=np.array([a for a,b,c in label_rows]),
                        seeds=np.array([b for a,b,c in label_rows]), labels=np.stack([c for a,b,c in label_rows]),
                        tickers=train.ticker.to_numpy(dtype=str), features=np.array(FEATURES), scaled_features=x)
    np.savez_compressed(out/'selection_embeddings.npz', **embedding_arrays)
    write_json(out/'resolved_representations.json', resolved)
    print('Computing all pairwise seed ARI/NMI', flush=True)
    pairs = []
    for candidate in pool:
        fits = [(seed,y) for cid,seed,y in label_rows if cid == candidate['candidate_id']]
        for (a, ya), (b, yb) in combinations(fits,2):
            pairs.append(dict(candidate_id=candidate['candidate_id'], seed_a=a, seed_b=b,
                              ari=float(adjusted_rand_score(ya,yb)), nmi=float(normalized_mutual_info_score(ya,yb))))
    stability = pd.DataFrame(pairs)
    stability.to_csv(out/'selection_seed_stability.csv',index=False)
    summary = aggregate(metrics, stability, config).merge(descriptions,on='candidate_id', validate='one_to_one')
    summary.to_csv(out/'candidate_summary.csv',index=False)
    choices = {'baseline': baseline_candidate(pool)['candidate_id']}
    for name, policy in config['selections'].items():
        ranked = select(summary, policy['geometry'], policy['clusters'])
        ranked.to_csv(out/f'ranking_{name}.csv',index=False)
        ranked[ranked.pareto_optimal].to_csv(out/f'pareto_{name}.csv',index=False)
        choices[name] = str(ranked.candidate_id.iloc[0])
    write_json(out/'selected_models.json', {name:by_id[cid] for name,cid in choices.items()})
    print('Selections frozen on June 2025; refitting selected models at each date',flush=True)
    followup_metrics, followup_assignments, followup_pairs, representative = [], [], [], []
    for scenario, cid in choices.items():
        candidate = by_id[cid]
        directory = out/scenario; directory.mkdir()
        dates = []
        for date, sub in snapshots.items():
            data = scaler.transform(numeric_matrix(sub))
            date_out = directory/date; date_out.mkdir()
            fits = []
            for seed in config['seeds']:
                z, metadata = fit_representation(data,candidate['representation'],seed)
                y = fit_cluster(z,candidate['clustering'],seed)
                score = quality(data,z,y)
                keep = y != -1
                score.update(sector_ari=float(adjusted_rand_score(sub.sector_label[keep],y[keep])) if keep.any() else None,
                             sector_nmi=float(normalized_mutual_info_score(sub.sector_label[keep],y[keep])) if keep.any() else None)
                row = dict(scenario=scenario,candidate_id=cid,decision_date=date,seed=seed,**score)
                followup_metrics.append(row)
                fits.append((seed,y))
                followup_assignments.extend(dict(scenario=scenario,decision_date=date,seed=seed,ticker=ticker,
                                                sector_label=sector,cluster=int(cluster))
                                            for ticker,sector,cluster in zip(sub.ticker,sub.sector_label,y))
                if seed == config['seeds'][0]:
                    representative.append(row)
                    result = sub.copy();result['cluster']=y;dates.append(result)
                    result.to_csv(date_out/'assignments.csv',index=False)
                    result.groupby('cluster')[FEATURES].median().to_csv(date_out/'cluster_profiles.csv')
                    pd.crosstab(result.cluster,result.sector_label).to_csv(date_out/'cluster_sector_counts.csv')
                    np.savez_compressed(date_out/'arrays.npz',embedding=z,scaled_features=data,labels=y,
                                        tickers=sub.ticker.to_numpy(dtype=str),features=np.array(FEATURES))
                    plot_clusters(sub,z,y,date_out,f'{date}: {scenario}\n{candidate["representation"]["name"]} + {candidate["clustering"]["algorithm"]}, {len(np.unique(y))} clusters')
                    # Existing multiclass explanation contract: eight-cluster comparisons only.
                    if scenario in {'paper_style_k8','common_features_k8'}:
                        if len(np.unique(y)) == 8 and keep.all():
                            explain(sub,y,date_out,seed)
                        else:
                            write_json(date_out/'explanation_status.json',dict(status='not run',
                                reason='Eight-class explanation contract not met at follow-up; see cluster/noise counts'))
                    write_json(date_out/'resolved_representation.json',metadata)
            for (a,ya),(b,yb) in combinations(fits,2):
                followup_pairs.append(dict(scenario=scenario,decision_date=date,seed_a=a,seed_b=b,
                                           ari=float(adjusted_rand_score(ya,yb)),nmi=float(normalized_mutual_info_score(ya,yb))))
        # Noise-free selected scenarios; descriptive alignment, never prediction.
        combined = pd.concat(dates,ignore_index=True)
        if (combined.cluster < 0).any():
            write_json(directory/'temporal_status.json',dict(status='not computed',
                reason='DBSCAN noise in follow-up requires dedicated transition semantics; never treated as an ordinary cluster',
                assignments_retained=True))
        else:
            transitions(combined,directory)
    pd.DataFrame(followup_metrics).to_csv(out/'selected_model_scores.csv',index=False)
    pd.DataFrame(followup_assignments).to_csv(out/'selected_model_assignments_all_seeds.csv',index=False)
    pd.DataFrame(followup_pairs).to_csv(out/'selected_model_seed_stability.csv',index=False)
    pd.DataFrame(representative).to_csv(out/'representative_seed42_scores.csv',index=False)
    if len(metrics) != config['maximum_selection_fits'] or len(pairs) != len(pool)*10:
        raise ValueError('Incomplete search or pairwise stability artifacts')
    if len(followup_metrics) != 4*3*5:
        raise ValueError('Incomplete frozen follow-up analysis')
    for name, cid in choices.items():
        if name != 'baseline' and not bool(summary.set_index('candidate_id').loc[cid,'eligible_all_seeds']):
            raise ValueError('Ineligible winner')
    manifest = dict(configuration_count=len(pool),selection_fits=len(metrics),pairwise_seed_comparisons=len(pairs),
        followup_fits=len(followup_metrics),selection_date=config['selection_date'],selections=choices,
        validation=validation,scaling_fit_on=config['selection_date'],features=FEATURES,
        scaler_min=scaler.data_min_.tolist(),scaler_max=scaler.data_max_.tolist(),
        runtime_seconds=time.monotonic()-start,promotion=False,
        quality_geometry='Euclidean silhouette and centroid DB in embedding and common June-scaled features',
        warnings=['Finite-grid exploratory optimum, not a global optimum',
                  'Later dates were previously examined and are descriptive follow-ups',
                  'PCA95 score space may have more than two dimensions',
                  'Sectors excluded from selection; reconstruction evidence limits unchanged',
                  'SHAP fitted only for the two selected eight-cluster scenarios, seed 42'])
    write_json(out/'optimization_manifest.json',manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',default=str(ROOT/'configs/optimization.json'))
    parser.add_argument('--run-id')
    args = parser.parse_args()
    for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS']:
        os.environ.setdefault(key,'1')
    os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.runtime/matplotlib'))
    os.environ.setdefault('NUMBA_CACHE_DIR',str(ROOT/'.runtime/numba'))
    config=json.loads(Path(args.config).read_text(encoding='utf-8'))
    with Run(ROOT/'experiments',config,config['experiment'],
             'User-requested finite-grid joint silhouette/DB optimisation; no promotion',args.run_id) as run:
        run.provenance()
        manifest=execute(config,run.out)
        run.meta['metric_artifacts']=['selection_scores_all_seeds.csv','candidate_summary.csv','selected_model_scores.csv']
        run.meta['warnings']=manifest['warnings']
    print(f'Completed {run.meta["run_id"]}: {run.out}')


if __name__ == '__main__':
    main()
