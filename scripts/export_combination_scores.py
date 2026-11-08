"""Export one readable row per searched combination: overall silhouette and Davies-Bouldin.

Reads a completed paper-experiment search (default: the verified `paper-exhaustive-k8-01`
archive) without modifying it. "Overall" means the mean over the five June-2025 seeds that
produced a valid score; seed standard deviations and the number of scored seeds are shown.
Silhouette/DB are Euclidean, computed in (a) the common June-scaled financial features and
(b) the fitted representation (embedding). DBSCAN noise points are excluded from scoring.
"""
import argparse
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def build(run_dir):
    search = Path(run_dir)/'search'
    summary = pd.read_csv(search/'candidate_summary.csv')
    ranking = pd.read_csv(search/'ranking_common_features_k8.csv')[['candidate_id', 'joint_rank_sum']]
    ranking['k8_selection_rank'] = range(1, len(ranking)+1)
    rows = []
    for r in summary.itertuples():
        rep, clu = json.loads(r.representation_parameters), json.loads(r.clustering_parameters)
        dims = rep.get('n_components')
        rows.append(dict(
            combination_id=r.candidate_id,
            reduction=r.representation,
            reduction_dims='95% variance' if dims == 0.95 else dims,
            reduction_metric=rep.get('metric') if r.representation != 'pca' else None,
            tsne_perplexity=rep.get('perplexity'),
            tsne_learning_rate=rep.get('learning_rate'),
            tsne_max_iter=rep.get('max_iter'),
            umap_n_neighbors=rep.get('n_neighbors'),
            umap_min_dist=rep.get('min_dist'),
            algorithm=r.algorithm,
            linkage=clu.get('linkage'),
            cluster_metric=clu.get('metric') if r.algorithm != 'kmeans' else 'euclidean',
            k=clu.get('n_clusters'),
            dbscan_eps=clu.get('eps'),
            dbscan_min_samples=clu.get('min_samples'),
            scored_seeds=f'{r.valid_seeds}/{r.seeds}',
            clusters_found=(None if pd.isna(r.n_clusters_min) else
                            f'{int(r.n_clusters_min)}' if r.n_clusters_min == r.n_clusters_max
                            else f'{int(r.n_clusters_min)}-{int(r.n_clusters_max)}'),
            min_coverage=r.coverage_min,
            max_singleton_clusters=r.singleton_clusters_max,
            silhouette_features=r.silhouette_features_mean,
            silhouette_features_sd=r.silhouette_features_std,
            davies_bouldin_features=r.davies_bouldin_features_mean,
            davies_bouldin_features_sd=r.davies_bouldin_features_std,
            silhouette_embedding=r.silhouette_embedding_mean,
            silhouette_embedding_sd=r.silhouette_embedding_std,
            davies_bouldin_embedding=r.davies_bouldin_embedding_mean,
            davies_bouldin_embedding_sd=r.davies_bouldin_embedding_std,
            mean_seed_ari=r.seed_ari_mean,
            status=('scored on all seeds' if r.valid_seeds == r.seeds else
                    'not scored: DBSCAN found fewer than 2 non-noise clusters on every seed' if r.valid_seeds == 0 else
                    f'partly scored: means use {r.valid_seeds} of {r.seeds} seeds')))
    table = pd.DataFrame(rows).merge(ranking, left_on='combination_id', right_on='candidate_id', how='left')
    table = table.drop(columns='candidate_id')
    order = {'pca': 0, 'tsne': 1, 'umap': 2}, {'hierarchical': 0, 'kmeans': 1, 'dbscan': 2}
    table = table.assign(_r=table.reduction.map(order[0]), _a=table.algorithm.map(order[1]))
    table = table.sort_values(['_r', '_a', 'silhouette_features'], ascending=[True, True, False], na_position='last')
    return table.drop(columns=['_r', '_a']).reset_index(drop=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', default=str(ROOT/'experiments/runs/paper-exhaustive-k8-01'))
    parser.add_argument('--out', default=str(ROOT/'reports/all_combination_scores.csv'))
    args = parser.parse_args()
    table = build(args.run)
    table.to_csv(args.out, index=False, float_format='%.4f')
    print(f'{len(table)} combinations -> {args.out}')


if __name__ == '__main__':
    main()
