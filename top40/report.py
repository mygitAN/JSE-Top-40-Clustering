"""The run's summary.md and the completeness check that gates a COMPLETED run."""
import pandas as pd


def _markdown(table, digits=3):
    """A small GitHub-flavoured table without needing the tabulate package."""
    def cell(value):
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return 'n/a'
        return f'{value:.{digits}f}' if isinstance(value, float) else str(value)
    lines = ['| ' + ' | '.join(table.columns) + ' |', '| ' + ' | '.join('---' for _ in table.columns) + ' |']
    lines += ['| ' + ' | '.join(cell(v) for v in row) + ' |' for row in table.itertuples(index=False)]
    return lines


def primary_summary(study):
    """One row per primary model and date: representative-seed scores, seed agreement, fidelity."""
    scores = study.seed_scores[study.seed_scores.seed == study.config['seed']]
    ari = study.seed_agreement.groupby(['study_model', 'decision_date']).ari.mean().rename('mean_seed_ari')
    table = scores.merge(study.fidelity, on=['study_model', 'decision_date'], validate='one_to_one')
    return table.join(ari, on=['study_model', 'decision_date'])[[
        'study_model', 'decision_date', 'smallest_cluster', 'largest_cluster', 'singleton_clusters',
        'silhouette_features', 'davies_bouldin_features', 'silhouette_embedding', 'davies_bouldin_embedding',
        'mean_seed_ari', 'in_sample_accuracy', 'oof_accuracy']]


def write_summary(study):
    feature_set, config = study.feature_set, study.config
    summary = primary_summary(study)
    summary.to_csv(study.out / 'primary_model_summary.csv', index=False)
    audit = study.audit
    dominance = audit['dominance'][['feature_set', 'decision_date', 'top_feature_label', 'top_variance_share',
                                    'even_share', 'max_scaled_value']]
    shifts = audit['shift_counts']
    flagged = study.screens[study.screens.flag == 1]
    lines = [
        '# Three-cross-section study', '',
        f'Run `{study.run.meta["run_id"]}`. Feature set **{feature_set.name}** ({feature_set.status}): '
        f'{feature_set.description}', '',
        f'{len(study.data)} instrument-date rows over {len(config["dates"])} dates; scaling fitted on '
        f'{config["fit_date"]} only; k={config["k"]}; seeds {study.seeds[0]}-{study.seeds[-1]}. '
        'Each date is clustered independently. These are overlapping cross-sections of mostly the same firms, '
        'not independent samples, and nothing here is a return prediction.', '',
        '## Feature validity (`feature_audit/`)', '',
        'Largest single-feature share of scaled variance. A share far above the even share means one feature '
        'drives the geometry at that date.', '',
        *_markdown(dominance), '',
        'Instruments observed at all dates, by whether their aligned cluster ever changed:', '',
        *_markdown(shifts), '',
        'Silhouette and Davies-Bouldin are computed in each feature set\'s own space and cannot be compared '
        'across feature sets. See `feature_audit/quality.csv`, `cross_set_agreement.csv` and '
        '`share_basis.csv`.', '',
        '## Primary models (`models/`)', '',
        *_markdown(summary), '',
        'Surrogate fidelity is agreement with the cluster labels, not predictive validity. Out-of-fold '
        'fidelity is not estimable when a cluster has one member.', '',
        '## Across dates (`longitudinal/`)', '',
        *_markdown(study.temporal[['study_model', 'before', 'after', 'continuing', 'entries', 'exits', 'ari',
                                   'changed']]), '',
        'A changed label is not yet evidence of a changed firm: compare `changed` with the seed agreement '
        'above, which is the only noise reference this run computes.', '',
        f'Feature-space distance screen (descriptive, alpha={config["screen_alpha"]}): '
        + (', '.join(f'{r.ticker} {r.decision_date}' for r in flagged.itertuples()) or 'no instrument flagged') + '.',
        '', '## Known data limits', '',
        '- Historical share counts, market capitalisation and sector labels are reconstructed, not verified '
        'point-in-time.',
        '- Reinet fundamentals and two Anglo American volume observations are imputed with June 2025 medians.',
        '- Investec line share counts split the combined count by fractions disclosed in June 2024 and June 2026; '
        'December 2025 uses their midpoint.',
        '- Volume is JSE trading only, so turnover understates liquidity for companies whose main listing is abroad.']
    (study.out / 'summary.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def check_outputs(study):
    """Raise unless every expected artifact exists and the tables have the expected shape."""
    out, config = study.out, study.config
    dates, models = config['dates'], list(config['primary_models'])
    required = ['summary.md', 'preprocessing.json', 'model_comparison.csv', 'primary_model_summary.csv',
                'seed_agreement.csv', 'surrogate_fidelity.csv', 'temporal_agreement.csv',
                'longitudinal_summary.csv', 'longitudinal/feature_space_screen.csv',
                'eda/population.csv', 'eda/feature_distributions.png', 'feature_audit/dominance.csv',
                'feature_audit/quality.csv', 'feature_audit/share_basis.csv', 'feature_audit/feature_dominance.png']
    required += [f'model_quality_{d}.png' for d in dates] + [f'eda/correlation_{d}.png' for d in dates]
    for name in models:
        required += [f'longitudinal/{name}/{f}' for f in ['cluster_histories.csv', 'membership_events.csv',
                                                          'cluster_flows.png', 'jaccard.png', 'movement_counts.png',
                                                          'moves/README.md', 'moves/cluster_profiles.csv',
                                                          'moves/cluster_summary.csv', 'moves/moves.csv',
                                                          'moves/move_features.csv']]
        required += [f'longitudinal/{name}/moves/cluster_profiles_{d}.png' for d in dates]
        required += [f'models/{name}/{d}/{f}' for d in dates for f in [
            'assignments.csv', 'cluster_map.png', 'feature_profile.png', 'dendrogram.png', 'shap_values.npz',
            'shap_global.png', 'shap_distribution.png', 'surrogate_fidelity.json', 'profile_vs_shap.csv']]
    missing = [path for path in required if not (out / path).is_file()]
    if missing:
        raise ValueError(f'Missing required study artifact: {missing[0]}')
    from .export import movement_figure_paths
    movement_figures = movement_figure_paths(out, config)
    missing = [path for path in movement_figures if not (out / path).is_file()]
    if missing:
        raise ValueError(f'Missing required study artifact: {missing[0]}')
    required += movement_figures
    expected = len(study.data)
    for name in models:
        if len(study.assignments[name]) != expected:
            raise ValueError(f'{name}: an instrument-date row was lost')
        events = pd.read_csv(out / 'longitudinal' / name / 'membership_events.csv')
        if events.loc[events.membership_event != 'continuing', 'cluster_changed'].notna().any():
            raise ValueError('Entries and exits must not be counted as cluster changes')
    pairs = len(study.seeds) * (len(study.seeds) - 1) // 2
    if len(study.seed_agreement) != len(models) * len(dates) * pairs:
        raise ValueError('Incomplete seed comparisons')
    return len(required)
