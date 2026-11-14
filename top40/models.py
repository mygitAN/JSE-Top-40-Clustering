"""Scaling, representations, clustering and internal quality scores."""
import numpy as np


def feature_matrix(frame, columns):
    x = frame[list(columns)].to_numpy(dtype=float)
    if not np.isfinite(x).all():
        raise ValueError('Non-finite model inputs; repair or flag them rather than dropping index members')
    return x


def prepare(frame, columns, dates, fit_date):
    """Fit MinMax scaling on ``fit_date`` only and split the frame by date.

    Later dates are transformed without clipping, so they can leave [0, 1].
    """
    from sklearn.preprocessing import MinMaxScaler

    if frame.duplicated(['decision_date', 'ticker']).any():
        raise ValueError('Duplicate decision-date/ticker keys')
    if set(frame.decision_date) != set(dates):
        raise ValueError('The inputs do not contain exactly the configured decision dates')
    scaler = MinMaxScaler(clip=False).fit(feature_matrix(frame[frame.decision_date == fit_date], columns))
    snapshots = {d: frame[frame.decision_date == d].sort_values('ticker').reset_index(drop=True) for d in dates}
    return scaler, snapshots


def embed(x, name, params, seed):
    if name == 'pca':
        from sklearn.decomposition import PCA
        return PCA(**params).fit_transform(x)
    if name == 'tsne':
        from sklearn.manifold import TSNE
        return TSNE(**params, random_state=seed).fit_transform(x)
    if name == 'umap':
        from umap import UMAP
        return UMAP(**params, random_state=seed).fit_transform(x)
    if name == 'none':
        return x
    raise ValueError(f'Unknown representation: {name}')


def cluster(z, name, params, seed, k):
    """Labels for one algorithm. DBSCAN ignores ``k`` and marks noise as -1."""
    from sklearn.cluster import DBSCAN, AgglomerativeClustering, KMeans

    if name == 'hierarchical':
        return AgglomerativeClustering(n_clusters=k, **params).fit_predict(z)
    if name == 'kmeans':
        return KMeans(n_clusters=k, **params, random_state=seed).fit_predict(z)
    if name == 'dbscan':
        # A fixed epsilon is only meaningful on standardised coordinates.
        spread = z.std(axis=0)
        return DBSCAN(**params).fit_predict((z - z.mean(axis=0)) / np.where(spread == 0, 1, spread))
    raise ValueError(f'Unknown clustering algorithm: {name}')


def linkage_matrix(z, params):
    """SciPy-format linkage of the full agglomerative tree, for dendrograms."""
    from sklearn.cluster import AgglomerativeClustering

    tree = AgglomerativeClustering(n_clusters=None, distance_threshold=0, compute_distances=True, **params).fit(z)
    n = len(z)
    counts = np.zeros(len(tree.children_))
    for i, children in enumerate(tree.children_):
        counts[i] = sum(1 if child < n else counts[child - n] for child in children)
    return np.column_stack([tree.children_, tree.distances_, counts])


def scores(x, z, labels, sector=None):
    """Silhouette and Davies-Bouldin in the representation ``z`` and the scaled features ``x``.

    Noise (-1) is excluded and reported as coverage. Scores are None unless
    there are between 2 and n-1 non-noise clusters. Sector agreement is context
    only and is never used to choose a model.
    """
    from sklearn.metrics import (adjusted_rand_score, davies_bouldin_score, normalized_mutual_info_score,
                                 silhouette_score)

    keep = labels != -1
    y = labels[keep]
    sizes = np.unique(y, return_counts=True)[1]
    valid = 1 < len(sizes) < len(y)
    result = dict(n_clusters=len(sizes), noise_count=int((~keep).sum()), coverage=float(keep.mean()),
                  smallest_cluster=int(sizes.min()) if len(sizes) else 0,
                  largest_cluster=int(sizes.max()) if len(sizes) else 0,
                  singleton_clusters=int((sizes == 1).sum()))
    for name, data in [('embedding', z), ('features', x)]:
        result[f'silhouette_{name}'] = float(silhouette_score(data[keep], y)) if valid else None
        result[f'davies_bouldin_{name}'] = float(davies_bouldin_score(data[keep], y)) if valid else None
    if sector is not None:
        sector = np.asarray(sector)[keep]
        result['sector_ari'] = float(adjusted_rand_score(sector, y)) if keep.any() else None
        result['sector_nmi'] = float(normalized_mutual_info_score(sector, y)) if keep.any() else None
    return result


def seed_agreement(fits):
    """Pairwise ARI/NMI between partitions fitted with different seeds."""
    from itertools import combinations
    from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

    return [dict(seed_a=a, seed_b=b, ari=float(adjusted_rand_score(left, right)),
                 nmi=float(normalized_mutual_info_score(left, right)))
            for (a, left), (b, right) in combinations(fits.items(), 2)]


def mahalanobis_screen(x, alpha=.05):
    """Squared Mahalanobis distance of each row from the same-sample mean.

    The reference is the exact distribution of an *individual* same-sample
    distance under iid multivariate normality:
    D^2 * n / (n-1)^2 ~ Beta(p/2, (n-p-1)/2). Equity cross-sections are not
    iid normal, so a flag is a descriptive screen, not a significance test.
    """
    from scipy.stats import beta

    x = np.asarray(x, dtype=float)
    n, p = x.shape
    reference = float((n - 1) ** 2 / n * beta.ppf(1 - alpha, p / 2, (n - p - 1) / 2)) if n > p + 1 else None
    meta = dict(n=n, p=p, alpha=alpha, reference=reference, reference_model='Beta, iid multivariate normal')
    covariance = np.cov(x, rowvar=False, ddof=1) if n > p + 1 else None
    if covariance is None or np.linalg.matrix_rank(covariance) < p or np.linalg.cond(covariance) > 1e12:
        return np.full(n, np.nan), {**meta, 'status': 'not estimable: singular or ill-conditioned covariance'}
    delta = x - x.mean(axis=0)
    distance = np.einsum('ij,jk,ik->i', delta, np.linalg.inv(covariance), delta)
    return distance, {**meta, 'status': 'descriptive screen'}
