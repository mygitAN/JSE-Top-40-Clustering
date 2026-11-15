"""Feature-validity audit: does the structure depend on how the features are defined?

The same clustering recipe is run on each feature set at each date. Scores are
computed in each set's own scaled space, so silhouette and Davies-Bouldin are
not comparable across feature sets; cluster sizes, seed agreement, feature
dominance, agreement between feature sets and temporal shifts are.
"""
from itertools import combinations

import numpy as np
import pandas as pd

from .features import get_feature_set
from .models import cluster, embed, feature_matrix, prepare, scores, seed_agreement
from .temporal import aligned_histories

# Two recipes: the study's primary model (stochastic, through an embedding), and
# a deterministic one with no embedding, so that feature effects can be separated
# from embedding noise.
WARD_FEATURES = dict(representation='none', representation_params={},
                     hierarchical={'linkage': 'ward', 'metric': 'euclidean'})


def recipes(config):
    """The first primary model under its own name, plus Ward clustering on the scaled features."""
    name, spec = next(iter(config['primary_models'].items()))
    return {name: spec, 'ward_features': WARD_FEATURES}


def feature_dominance(frame, feature_set, config):
    """Share of total scaled variance per feature, and how far each date leaves the fit-date range."""
    scaler, snapshots = prepare(frame, feature_set.columns, config['dates'], config['fit_date'])
    rows = []
    for date, sub in snapshots.items():
        x = scaler.transform(feature_matrix(sub, feature_set.columns))
        share = x.var(axis=0) / x.var(axis=0).sum()
        top = int(share.argmax())
        widest = int(np.abs(x - .5).max(axis=0).argmax())
        rows.append(dict(feature_set=feature_set.name, decision_date=date, top_feature=feature_set.columns[top],
                         top_feature_label=feature_set.labels[top], top_variance_share=float(share[top]),
                         even_share=1 / len(share), max_scaled_value=float(x.max()), min_scaled_value=float(x.min()),
                         widest_feature=feature_set.columns[widest]))
    return rows


def run_ablation(frame, config, feature_sets=None, seeds=None):
    """Return tables comparing feature sets. ``frame`` must already hold the derived columns."""
    names = feature_sets or config['ablation_feature_sets']
    seeds = seeds or list(range(config['seed'], config['seed'] + config['stability_runs']))
    dates, k = config['dates'], config['k']
    all_recipes = recipes(config)
    dominance, quality, partitions, temporal, histories = [], [], {}, [], {}
    for name in names:
        feature_set = get_feature_set(name)
        dominance += feature_dominance(frame, feature_set, config)
        scaler, snapshots = prepare(frame, feature_set.columns, dates, config['fit_date'])
        for recipe, spec in all_recipes.items():
            params, linkage = spec['representation_params'], spec['hierarchical']
            stochastic = spec['representation'] != 'none'
            labelled = {}
            for date, sub in snapshots.items():
                x = scaler.transform(feature_matrix(sub, feature_set.columns))
                fits = {}
                for seed in (seeds if stochastic else seeds[:1]):
                    z = embed(x, spec['representation'], params, seed)
                    fits[seed] = cluster(z, 'hierarchical', linkage, seed, k)
                    if seed == seeds[0]:
                        representative = scores(x, z, fits[seed], sub.sector_label)
                pairs = seed_agreement(fits)
                quality.append(dict(feature_set=name, recipe=recipe, decision_date=date, **representative,
                                    mean_seed_ari=float(np.mean([p['ari'] for p in pairs])) if pairs else None))
                labelled[date] = sub[['ticker']].assign(cluster=fits[seeds[0]])
                partitions[name, recipe, date] = pd.Series(fits[seeds[0]], index=sub.ticker)
            _, _, _, history, _, agreement = aligned_histories(labelled, dates)
            histories[name, recipe] = history.set_index('ticker').stability_status
            temporal += [dict(feature_set=name, recipe=recipe, **row) for row in agreement.to_dict('records')]

    from sklearn.metrics import adjusted_rand_score
    cross = [dict(recipe=recipe, decision_date=date, feature_set_a=a, feature_set_b=b,
                  ari=float(adjusted_rand_score(partitions[a, recipe, date], partitions[b, recipe, date])))
             for recipe in all_recipes for date in dates for a, b in combinations(names, 2)]
    status = pd.DataFrame(histories)
    status.columns = [f'{name}|{recipe}' for name, recipe in status.columns]
    shifts = pd.DataFrame([dict(feature_set=name, recipe=recipe, **histories[name, recipe].value_counts().to_dict())
                           for name, recipe in histories]).fillna(0)
    return dict(dominance=pd.DataFrame(dominance), quality=pd.DataFrame(quality), cross_set_agreement=pd.DataFrame(cross),
                temporal=pd.DataFrame(temporal), shift_counts=shifts,
                instrument_status=status.rename_axis('ticker').reset_index())
