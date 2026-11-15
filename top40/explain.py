"""Surrogate explanations of a fitted partition.

An XGBoost classifier learns the cluster labels from the unscaled features and
Tree SHAP explains that classifier's raw class margins. This describes the
surrogate, not the clustering algorithm, a cause, or a return.
"""
import json

import numpy as np

from .models import feature_matrix


def explain(frame, labels, feature_set, params, seed, out):
    """Fit the surrogate, check SHAP additivity and save every table. Returns the fidelity record."""
    import pandas as pd
    import shap
    from sklearn.metrics import accuracy_score
    from sklearn.model_selection import StratifiedKFold, cross_val_predict
    from xgboost import XGBClassifier

    columns = list(feature_set.columns)
    x = feature_matrix(frame, columns)
    classes, encoded = np.unique(labels, return_inverse=True)
    counts = np.bincount(encoded)
    smallest = int(counts.min())
    model = XGBClassifier(**params, random_state=seed)
    fidelity = dict(in_sample_accuracy=None, oof_accuracy=None, minimum_cluster_size=smallest,
                    oof_status='estimated' if smallest >= 2 else 'not estimable: singleton cluster')
    if smallest >= 2:
        folds = StratifiedKFold(n_splits=min(5, smallest), shuffle=True, random_state=seed)
        predicted = cross_val_predict(model, x, encoded, cv=folds)
        fidelity['oof_accuracy'] = float(accuracy_score(encoded, predicted))
        pd.DataFrame({'ticker': frame.ticker, 'cluster': labels, 'oof_predicted_cluster': classes[predicted]}
                     ).to_csv(out / 'surrogate_oof_predictions.csv', index=False)
    model.fit(x, encoded)
    fidelity['in_sample_accuracy'] = float(accuracy_score(encoded, model.predict(x)))
    fidelity['class_mapping'] = {str(i): int(c) for i, c in enumerate(classes)}

    explanation = shap.TreeExplainer(model, feature_perturbation='tree_path_dependent')(x)
    values = np.asarray(explanation.values)
    if values.shape != (len(frame), len(columns), len(classes)):
        raise ValueError(f'Unexpected multiclass SHAP shape: {values.shape}')
    margins = model.predict(x, output_margin=True)
    error = float(np.max(np.abs(values.sum(axis=1) + explanation.base_values - margins)))
    if error > 1e-4:
        raise ValueError('SHAP values do not sum to the surrogate raw margins')
    fidelity['shap_max_additivity_error'] = error
    np.savez_compressed(out / 'shap_values.npz', values=values, base_values=explanation.base_values,
                        feature_values=x, tickers=frame.ticker.to_numpy(dtype=str), features=np.array(columns),
                        cluster_labels=classes, assigned_classes=encoded, raw_margins=margins)

    importance = np.abs(values).mean(axis=(0, 2))
    pd.DataFrame({'feature': columns, 'mean_abs_shap': importance}).sort_values(
        'mean_abs_shap', ascending=False).to_csv(out / 'shap_global.csv', index=False)
    rows = []
    for index, label in enumerate(classes):
        members = labels == label
        for j, column in enumerate(columns):
            rows.append(dict(cluster=int(label), n=int(members.sum()), feature=column,
                             mean_abs_shap_members=float(np.abs(values[members, j, index]).mean())))
    by_cluster = pd.DataFrame(rows)
    by_cluster.to_csv(out / 'shap_by_cluster.csv', index=False)
    (out / 'surrogate_fidelity.json').write_text(json.dumps(fidelity, indent=2) + '\n', encoding='utf-8')
    return fidelity, by_cluster


def profile_comparison(frame, scaled, feature_set, shap_by_cluster):
    """Cluster median deviations beside SHAP importance, and their rank agreement.

    The median deviation needs no surrogate, so it is the primary description;
    SHAP supports it only where surrogate fidelity is adequate.
    """
    import pandas as pd

    columns = list(feature_set.columns)
    overall = np.median(scaled, axis=0)
    rows = []
    for label in sorted(frame.cluster.unique()):
        members = frame.cluster.to_numpy() == label
        local = shap_by_cluster[shap_by_cluster.cluster == label].set_index('feature').reindex(columns)
        deviation = np.median(scaled[members], axis=0) - overall
        for j, column in enumerate(columns):
            rows.append(dict(cluster=int(label), n=int(members.sum()), feature=column,
                             signed_median_deviation=float(deviation[j]),
                             mean_abs_shap_members=float(local.loc[column, 'mean_abs_shap_members'])))
    table = pd.DataFrame(rows)
    table['deviation_rank'] = table.signed_median_deviation.abs().groupby(table.cluster).rank(ascending=False)
    table['shap_rank'] = table.groupby('cluster').mean_abs_shap_members.rank(ascending=False)
    summary = []
    for label, sub in table.groupby('cluster', sort=True):
        estimable = sub.deviation_rank.nunique() > 1 and sub.shap_rank.nunique() > 1
        summary.append(dict(cluster=int(label), n=int(sub.n.iloc[0]),
                            rank_correlation=float(sub.deviation_rank.corr(sub.shap_rank)) if estimable else None))
    return table, pd.DataFrame(summary)
