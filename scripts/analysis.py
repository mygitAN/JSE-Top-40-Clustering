"""Reproducible, descriptive three-cross-section clustering and surrogate SHAP.

Run from any directory: python scripts/run_analysis.py
This is not a portfolio backtest or an inductive prediction experiment.
"""
import argparse
import hashlib
import importlib.metadata
import json
from itertools import combinations
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import AgglomerativeClustering, DBSCAN, KMeans
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.metrics import (accuracy_score, adjusted_rand_score, davies_bouldin_score,
                             normalized_mutual_info_score, silhouette_score)
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.preprocessing import MinMaxScaler

ROOT = Path(__file__).resolve().parents[1]
DATES = ['2025-06-30', '2025-12-31', '2026-06-30']
# Original numeric concept, minus unavailable analyst ratings; E/P replaces P/E.
# Close is an input to E/P and cap, not an additional eleventh modelling feature.
FEATURES = ['return_1y', 'average_daily_volume_1y_model', 'market_cap_zar',
            'beta_1y', 'shares_outstanding', 'revenue_zar_model', 'eps_zar_model',
            'annualised_volatility_1y', 'dividend_yield', 'earnings_yield_model_clipped']
PRIMARY = 'tsne_hierarchical'
SPEC = json.loads((ROOT/'configs/baseline.json').read_text(encoding='utf-8'))
if FEATURES != SPEC['features']:
    raise ValueError('Feature contract differs from baseline configuration')


def numeric_matrix(frame):
    x = frame[FEATURES].to_numpy(dtype=float)
    if not np.isfinite(x).all():
        raise ValueError('Non-finite model inputs; repair/flag rather than drop index members')
    return x


def prepare(frame):
    """Freeze scaling on first cross-section; consume audited model-only imputations."""
    if frame.duplicated(['decision_date', 'ticker']).any():
        raise ValueError('Duplicate decision-date/ticker keys')
    if set(frame.decision_date) != set(DATES):
        raise ValueError('Expected exactly the three configured decision dates')
    scaler = MinMaxScaler(clip=False).fit(numeric_matrix(frame[frame.decision_date == DATES[0]]))
    return scaler, {d: frame[frame.decision_date == d].sort_values('ticker').reset_index(drop=True)
                    for d in DATES}


def embed(x, name, seed):
    if name == 'pca':
        return PCA(**SPEC['pca']).fit_transform(x)
    if name == 'tsne':
        return TSNE(**SPEC['tsne'], random_state=seed).fit_transform(x)
    if name != 'umap':
        raise ValueError(f'Unknown representation: {name}')
    from umap import UMAP
    return UMAP(**SPEC['umap'], random_state=seed).fit_transform(x)


def cluster(z, name, seed, k=8):
    if name == 'hierarchical':
        return AgglomerativeClustering(**{**SPEC['hierarchical'], 'n_clusters': k}).fit_predict(z)
    if name == 'kmeans':
        return KMeans(**{**SPEC['kmeans'], 'n_clusters': k}, random_state=seed).fit_predict(z)
    if name != 'dbscan':
        raise ValueError(f'Unknown clustering algorithm: {name}')
    # Fixed epsilon on standardized embedding coordinates, no forcing of eight clusters.
    sd = z.std(axis=0)
    return DBSCAN(**SPEC['dbscan']).fit_predict((z-z.mean(axis=0))/np.where(sd == 0, 1, sd))


def scores(x, z, y, sector):
    keep = y != -1
    labels = y[keep]
    valid = 1 < len(np.unique(labels)) < keep.sum()
    return dict(n_clusters=len(set(labels)), noise_count=int((~keep).sum()),
                coverage=float(keep.mean()),
                silhouette_metric='euclidean', davies_bouldin_geometry='euclidean embedding centroids',
                silhouette_embedding=float(silhouette_score(z[keep], labels)) if valid else None,
                silhouette_features=float(silhouette_score(x[keep], labels)) if valid else None,
                davies_bouldin_embedding=float(davies_bouldin_score(z[keep], labels)) if valid else None,
                sector_ari=float(adjusted_rand_score(np.asarray(sector)[keep], labels)) if keep.any() else None,
                sector_nmi=float(normalized_mutual_info_score(np.asarray(sector)[keep], labels)) if keep.any() else None)


def align_labels(old, new):
    """Maximum overlap alignment on continuing members only. Labels are not identities."""
    common = old.index.intersection(new.index)
    if not old.index.is_unique or not new.index.is_unique:
        raise ValueError('Temporal joins require unique ticker keys')
    # Clusters absent from continuing members cannot earn a positive-overlap match.
    a, b = sorted(old.unique()), sorted(new.unique())
    counts = np.array([[((old.loc[common] == i) & (new.loc[common] == j)).sum()
                        for j in b] for i in a], dtype=int).reshape(len(a), len(b))
    rows, cols = linear_sum_assignment(-counts)
    mapping = {b[c]: a[r] for r, c in zip(rows, cols) if counts[r, c] > 0}
    next_id = max(a, default=-1) + 1
    for j in b:
        if j not in mapping:
            mapping[j] = next_id
            next_id += 1
    return new.map(mapping), counts


def transitions(assignments, out):
    if assignments.duplicated(['decision_date', 'ticker']).any():
        raise ValueError('Duplicate temporal keys')
    frames = {d: assignments[assignments.decision_date == d].set_index('ticker') for d in DATES}
    rows, metrics, alignment_rows = [], [], []
    previous = frames[DATES[0]].cluster.copy()
    for before, after in zip(DATES, DATES[1:]):
        left, right = frames[before], frames[after]
        aligned, counts = align_labels(previous, right.cluster)
        common = left.index.intersection(right.index)
        for raw in sorted(right.cluster.unique()):
            target = int(aligned[right.cluster == raw].iloc[0])
            overlap = int(((previous.loc[common] == target) & (right.loc[common, 'cluster'] == raw)).sum())
            alignment_rows.append(dict(before=before, after=after, raw_cluster=int(raw),
                                       aligned_cluster=target, continuing_overlap=overlap,
                                       status='matched' if overlap else 'unmatched: new descriptive ID'))
        metrics.append(dict(before=before, after=after, continuing=len(common),
                            entries=len(right.index.difference(left.index)), exits=len(left.index.difference(right.index)),
                            ari=adjusted_rand_score(previous.loc[common], aligned.loc[common]),
                            nmi=normalized_mutual_info_score(previous.loc[common], aligned.loc[common])))
        for ticker in sorted(left.index.union(right.index)):
            present_a, present_b = ticker in left.index, ticker in right.index
            status = 'continuing' if present_a and present_b else ('entry' if present_b else 'exit')
            imputed = any(present and any(bool(table.loc[ticker, flag]) for flag in
                          ['fundamentals_imputed', 'volume_imputed'])
                          for present, table in [(present_a, left), (present_b, right)])
            rows.append(dict(before=before, after=after, ticker=ticker, membership_event=status,
                             cluster_before=int(previous.loc[ticker]) if present_a else None,
                             cluster_after=int(aligned.loc[ticker]) if present_b else None,
                             raw_cluster_before=int(left.loc[ticker, 'cluster']) if present_a else None,
                             raw_cluster_after=int(right.loc[ticker, 'cluster']) if present_b else None,
                             sector_before=left.loc[ticker, 'sector_label'] if present_a else None,
                             sector_after=right.loc[ticker, 'sector_label'] if present_b else None,
                             cluster_changed=bool(previous.loc[ticker] != aligned.loc[ticker])
                             if status == 'continuing' else None,
                             interpretation='imputation-sensitive' if imputed else 'descriptive'))
        pd.crosstab(previous.loc[common], aligned.loc[common]).to_csv(out/f'transition_matrix_{before}_{after}.csv')
        previous = aligned
    pd.DataFrame(rows).to_csv(out/'membership_and_cluster_transitions.csv', index=False)
    pd.DataFrame(metrics).to_csv(out/'temporal_agreement.csv', index=False)
    pd.DataFrame(alignment_rows).to_csv(out/'temporal_label_alignment.csv', index=False)


def explain(frame, y, out, seed):
    """Post-hoc XGBoost surrogate; fidelity is not predictive investment performance."""
    import shap
    from xgboost import XGBClassifier
    x = numeric_matrix(frame)
    labels, encoded = np.unique(y, return_inverse=True)
    counts = np.bincount(encoded)
    model = XGBClassifier(**SPEC['surrogate'], random_state=seed)
    min_count = int(counts.min())
    fidelity = {'in_sample_accuracy': None, 'oof_accuracy': None,
                'minimum_cluster_size': min_count,
                'oof_status': 'not estimable: singleton cluster' if min_count < 2 else 'estimated',
                'meaning': 'surrogate fidelity to full-snapshot pseudo-labels, not predictive validity'}
    if min_count >= 2:
        cv = StratifiedKFold(n_splits=min(5, min_count), shuffle=True, random_state=seed)
        pred = cross_val_predict(model, x, encoded, cv=cv)
        fidelity['oof_accuracy'] = float(accuracy_score(encoded, pred))
        pd.DataFrame({'ticker': frame.ticker, 'cluster': y, 'oof_predicted_cluster': labels[pred]}).to_csv(out/'surrogate_oof_predictions.csv', index=False)
    model.fit(x, encoded)
    fidelity['in_sample_accuracy'] = float(accuracy_score(encoded, model.predict(x)))
    fidelity['class_mapping'] = {str(i): int(c) for i, c in enumerate(labels)}
    pd.DataFrame({'ticker': frame.ticker, 'cluster': y, 'surrogate_class': encoded,
                  'predicted_cluster': labels[model.predict(x)]}).to_csv(out/'surrogate_predictions.csv', index=False)
    model.save_model(out/'surrogate.json')
    explanation = shap.TreeExplainer(model, feature_perturbation='tree_path_dependent')(x)
    values = np.asarray(explanation.values)
    if values.shape != (len(frame), len(FEATURES), len(counts)):
        raise ValueError(f'Unexpected multiclass SHAP shape: {values.shape}')
    # Additivity checked by TreeExplainer, and independently against raw class margins.
    margins = model.predict(x, output_margin=True)
    if not np.allclose(values.sum(axis=1)+explanation.base_values, margins, atol=1e-4):
        raise ValueError('SHAP raw-margin additivity failed')
    fidelity['shap_shape'] = list(values.shape)
    fidelity['shap_max_additivity_error'] = float(np.max(np.abs(values.sum(axis=1)+explanation.base_values-margins)))
    fidelity['shap_additivity_atol'] = 1e-4
    np.savez_compressed(out/'shap_values.npz', values=values, base_values=explanation.base_values,
                        feature_values=x, tickers=frame.ticker.to_numpy(dtype=str), features=np.array(FEATURES),
                        classes=model.classes_, cluster_labels=labels, assigned_classes=encoded, raw_margins=margins)
    global_importance = np.abs(values).mean(axis=(0, 2))
    pd.DataFrame({'feature': FEATURES, 'mean_abs_shap': global_importance}).sort_values(
        'mean_abs_shap', ascending=False).to_csv(out/'shap_global.csv', index=False)
    rows = []
    for c, label in enumerate(labels):
        members = y == label
        for j, feature in enumerate(FEATURES):
            rows.append(dict(cluster=int(label), surrogate_class=c, n=int(members.sum()), feature=feature,
                             mean_abs_shap_members=float(np.abs(values[members, j, c]).mean()),
                             status='singleton: descriptive only' if members.sum() == 1 else 'small-sample descriptive'))
        importance = np.abs(values[members, :, c]).mean(axis=0)
        fig, ax = plt.subplots(figsize=(9, 5))
        order = np.argsort(importance)
        ax.barh(np.array(FEATURES)[order], importance[order])
        ax.set_title(f'Cluster {label}, n={members.sum()}: ' + ('singleton, descriptive only' if members.sum() == 1 else 'descriptive surrogate explanation'))
        ax.set_xlabel('Mean |SHAP| for member firms, own-class raw margin')
        fig.tight_layout(); fig.savefig(out/f'shap_cluster_{label}.png', dpi=120); plt.close(fig)
    pd.DataFrame(rows).to_csv(out/'shap_by_cluster.csv', index=False)
    (out/'surrogate_fidelity.json').write_text(json.dumps(fidelity, indent=2)+'\n')
    fig, ax = plt.subplots(figsize=(8, 5))
    order = np.argsort(global_importance)
    ax.barh(np.array(FEATURES)[order], global_importance[order])
    ax.set_xlabel('Mean |SHAP| over firms and classes (surrogate raw margin)')
    fig.tight_layout(); fig.savefig(out/'shap_global.png', dpi=180); plt.close(fig)


def run(args):
    from validate_data import validate
    data_validation = validate()
    source = ROOT/'data/processed/Top40_Retrospective_Model_Inputs_v1.csv'
    frame = pd.read_csv(source)
    scaler, snapshots = prepare(frame)
    out = Path(args.output).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if (out/'run_manifest.json').exists() or (out/'assignments.csv').exists():
        raise FileExistsError('Choose a new --output directory to preserve the previous run')
    metrics, assignments, stability, sensitivity, seed_metrics = [], [], [], [], []
    for date, sub in snapshots.items():
        print(f'Analysing {date}: {len(sub)} retained instruments', flush=True)
        x = scaler.transform(numeric_matrix(sub))
        date_out = out/date; date_out.mkdir(exist_ok=True)
        representations = ['pca', 'tsne', 'umap'] if args.mode == 'full' else ['tsne']
        embeddings = {name: embed(x, name, args.seed) for name in representations}
        for name, z in embeddings.items():
            for algorithm in (['hierarchical', 'kmeans', 'dbscan'] if args.mode == 'full' else ['hierarchical']):
                y = cluster(z, algorithm, args.seed)
                key = f'{name}_{algorithm}'
                metrics.append(dict(decision_date=date, model=key, **scores(x, z, y, sub.sector_label)))
                metrics[-1]['clustering_geometry'] = ('manhattan embedding' if algorithm == 'hierarchical' else
                                                       'euclidean standardized embedding' if algorithm == 'dbscan' else 'euclidean embedding')
                pd.DataFrame({'ticker': sub.ticker, 'sector_label': sub.sector_label,
                              'fundamentals_imputed': sub.fundamentals_imputed, 'volume_imputed': sub.volume_imputed,
                              'axis1': z[:, 0], 'axis2': z[:, 1],
                              'cluster': y}).to_csv(date_out/f'{key}.csv', index=False)
        y = cluster(embeddings['tsne'], 'hierarchical', args.seed)
        result = sub.copy(); result['cluster'] = y; assignments.append(result)
        sizes = result.groupby('cluster').agg(n=('ticker', 'size'),
                    fundamental_imputations=('fundamentals_imputed', 'sum'),
                    volume_imputations=('volume_imputed', 'sum'))
        sizes['interpretation'] = np.where(sizes.n == 1, 'singleton: descriptive only', 'small-sample descriptive')
        sizes.to_csv(date_out/'cluster_sizes.csv')
        result.groupby('cluster')[FEATURES].median().to_csv(date_out/'cluster_profiles_median.csv')
        pd.crosstab(result.cluster, result.sector_label).to_csv(date_out/'cluster_sector_counts.csv')
        z = embeddings['tsne']
        fig, ax = plt.subplots(figsize=(9, 7))
        scatter = ax.scatter(z[:, 0], z[:, 1], c=y, cmap='tab10')
        flagged = (sub.fundamentals_imputed | sub.volume_imputed).to_numpy()
        for ticker, xy, imputed in zip(sub.ticker, z, flagged):
            ax.annotate(ticker + ('*' if imputed else ''), xy, fontsize=7)
        handles, labels = scatter.legend_elements()
        ax.legend(handles, labels, title='Local cluster ID', loc='upper left', bbox_to_anchor=(1, 1))
        ax.set_xlabel('t-SNE dimension 1 (independent fit); * model-only imputation')
        ax.set_ylabel('t-SNE dimension 2 (independent fit)')
        ax.set_title(f'{date}: t-SNE + average/Manhattan hierarchical (k=8)')
        fig.tight_layout(); fig.savefig(date_out/'clusters.png', dpi=180); plt.close(fig)
        # k=8 is a legacy baseline, not selected to maximise agreement with sector labels.
        for k in range(2, 11):
            alt = cluster(z, 'hierarchical', args.seed, k)
            sensitivity.append(dict(decision_date=date, k=k, **scores(x, z, alt, sub.sector_label)))
        runs = {}
        for seed in range(args.seed, args.seed+args.stability_runs):
            seed_z = embed(x, 'tsne', seed)
            runs[seed] = cluster(seed_z, 'hierarchical', seed)
            seed_metrics.append(dict(decision_date=date, seed=seed,
                                     **scores(x, seed_z, runs[seed], sub.sector_label)))
            np.savez_compressed(date_out/f'seed_{seed}_arrays.npz', embedding=seed_z, clusters=runs[seed],
                                tickers=sub.ticker.to_numpy(dtype=str))
        pd.DataFrame({'ticker': sub.ticker, 'sector_label': sub.sector_label,
                      **{f'seed_{s}': labels for s, labels in runs.items()}}).to_csv(date_out/'seed_assignments.csv', index=False)
        np.savez_compressed(date_out/'baseline_arrays.npz', scaled_features=x, embedding=z, clusters=y,
                            tickers=sub.ticker.to_numpy(dtype=str), features=np.array(FEATURES))
        for (a, ya), (b, yb) in combinations(runs.items(), 2):
            stability.append(dict(decision_date=date, seed_a=a, seed_b=b,
                                  ari=adjusted_rand_score(ya, yb), nmi=normalized_mutual_info_score(ya, yb)))
        if not args.skip_shap:
            explain(sub, y, date_out, args.seed)
    combined = pd.concat(assignments, ignore_index=True)
    combined.to_csv(out/'assignments.csv', index=False)
    pd.DataFrame(metrics).to_csv(out/'model_comparison.csv', index=False)
    pd.DataFrame(sensitivity).to_csv(out/'cluster_count_sensitivity.csv', index=False)
    pd.DataFrame(stability, columns=['decision_date','seed_a','seed_b','ari','nmi']).to_csv(out/'seed_stability.csv', index=False)
    pd.DataFrame(seed_metrics).to_csv(out/'seed_metrics.csv', index=False)
    transitions(combined, out)
    manifest = dict(seed=args.seed, stability_runs=args.stability_runs, features=FEATURES,
                    primary=PRIMARY, source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                    scaling_fit_on=DATES[0], scaler_min=scaler.data_min_.tolist(),
                    scaler_max=scaler.data_max_.tolist(), shap_completed=not args.skip_shap,
                    versions={p: importlib.metadata.version(p) for p in
                              ['numpy','pandas','scikit-learn','scipy','matplotlib','umap-learn','xgboost','shap']},
                    settings=dict(tsne_perplexity=5, tsne_learning_rate=10, tsne_max_iter=300,
                                  tsne_init='random', hierarchical_linkage='average',
                                  hierarchical_metric='manhattan', k=8, umap_neighbors=10,
                                  umap_min_dist=0.1, dbscan_eps=0.5, dbscan_min_samples=3),
                    interpretation='Independent descriptive refits, not out-of-sample predictions; membership transitions separate')
    manifest.update(data_validation=data_validation, population_counts={d: len(s) for d, s in snapshots.items()},
                    distinct_tickers=int(frame.ticker.nunique()),
                    imputation_counts={flag: int(frame[flag].sum()) for flag in ['fundamentals_imputed', 'volume_imputed']},
                    preprocessing_method=json.loads((ROOT/'docs/Top40_Retrospective_Model_Method_v1.json').read_text(encoding='utf-8')),
                    resolved_specification=SPEC,
                    warnings=['Historical shares/sectors unverified', 'Independent t-SNE coordinates have no shared axes',
                              'Seed sensitivity is not bootstrap uncertainty', 'OOF pseudo-label fidelity does not validate discovery'])
    validate_outputs(out, args)
    (out/'run_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(f'Complete: {out}', flush=True)


def validate_outputs(out, args):
    assignments = pd.read_csv(out/'assignments.csv')
    if len(assignments) != 123 or assignments.duplicated(['decision_date', 'ticker']).any():
        raise ValueError('Output population failed validation')
    comparisons = pd.read_csv(out/'model_comparison.csv')
    if len(comparisons) != (27 if args.mode == 'full' else 3):
        raise ValueError('Incomplete model comparisons')
    if len(pd.read_csv(out/'cluster_count_sensitivity.csv')) != 27:
        raise ValueError('Incomplete k sensitivity')
    if len(pd.read_csv(out/'seed_stability.csv')) != 3*args.stability_runs*(args.stability_runs-1)//2:
        raise ValueError('Incomplete pairwise seed sensitivity')
    for date in DATES:
        if not args.skip_shap:
            for name in ['shap_values.npz', 'shap_global.csv', 'shap_by_cluster.csv', 'surrogate_fidelity.json']:
                if not (out/date/name).is_file():
                    raise ValueError(f'Missing required SHAP artifact: {date}/{name}')
