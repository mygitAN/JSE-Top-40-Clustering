"""Study report and completion checks shared by the CLI and notebook."""
import json
from pathlib import Path
from tracking import write_json


def validate_study_outputs(out, config):
    import numpy as np
    import pandas as pd

    out = Path(out)
    required = ['eda/population.csv', 'eda/evidence.csv', 'eda/missingness.csv', 'eda/descriptions.csv',
                'eda/population_and_sectors.png', 'eda/feature_distributions.png', 'eda/raw_missingness.png',
                'eda/membership_presence.png', 'model_comparison.csv', 'primary_model_summary.csv',
                'surrogate_fidelity.csv', 'seed_stability.csv', 'temporal_agreement.csv', 'study_summary.md']
    model_folders = {'baseline': 'models'}
    if config['include_umap_sensitivity']:
        model_folders['umap_sensitivity'] = 'umap_sensitivity'
    for date in config['dates']:
        required += [f'eda/correlation_{date}.png', f'model_quality_{date}.png']
    for name, folder in model_folders.items():
        required += [f'{folder}/transition_heatmaps.png', f'{folder}/membership_and_cluster_transitions.csv',
                     f'{folder}/cluster_count_sensitivity.png']
        for date in config['dates']:
            required += [f'{folder}/{date}/{filename}' for filename in [
                'cluster_map.png', 'feature_profile.png', 'dendrogram.png', 'shap_global.png',
                'shap_distribution.png', 'shap_values.npz', 'surrogate_fidelity.json',
                'shap_by_cluster.csv', 'shap_univariate_comparison.csv']]
    for relative in required:
        if not (out/relative).is_file():
            raise ValueError(f'Missing required study artifact: {relative}')
    population = pd.read_csv(out/'eda/population.csv')
    if list(population.instruments) != [41, 41, 41]:
        raise ValueError('Study population is incomplete')
    comparison = pd.read_csv(out/'model_comparison.csv')
    if len(comparison) != (30 if config['include_umap_sensitivity'] else 27):
        raise ValueError('Incomplete model comparison table')
    fidelity = pd.read_csv(out/'surrogate_fidelity.csv')
    if len(fidelity) != 3 * len(model_folders):
        raise ValueError('Incomplete surrogate fidelity results')
    pairs = pd.read_csv(out/'seed_stability.csv')
    if len(pairs) != len(model_folders)*3*config['stability_runs']*(config['stability_runs']-1)//2:
        raise ValueError('Incomplete seed comparisons')
    for name, folder in model_folders.items():
        for date in config['dates']:
            with np.load(out/folder/date/'shap_values.npz', allow_pickle=False) as saved:
                k = 8 if name == 'baseline' else config['umap_sensitivity']['n_clusters']
                if saved['values'].shape != (41, 10, k):
                    raise ValueError('Unexpected SHAP firm/feature/class dimensions')
                np.testing.assert_allclose(saved['values'].sum(axis=1) + saved['base_values'],
                                           saved['raw_margins'], atol=1e-4)
                if len(set(saved['tickers'])) != 41:
                    raise ValueError('SHAP tickers missing or duplicated')
        events = pd.read_csv(out/folder/'membership_and_cluster_transitions.csv')
        if events.loc[events.membership_event != 'continuing', 'cluster_changed'].notna().any():
            raise ValueError('Entries/exits must not receive ordinary cluster-change flags')
    return len(required)


def write_study_summary(study):
    import pandas as pd

    table = study.comparison[study.comparison.model.isin(['tsne_hierarchical', 'umap_fixed_sensitivity'])].copy()
    table['study_model'] = table.model.map({'tsne_hierarchical': 'baseline', 'umap_fixed_sensitivity': 'umap_sensitivity'})
    table = table.merge(study.fidelity, on=['study_model', 'decision_date'], validate='one_to_one')
    mean = study.seed_agreement.groupby(['study_model', 'decision_date']).ari.mean().rename('mean_seed_ari')
    table = table.join(mean, on=['study_model', 'decision_date'])
    table.to_csv(study.out/'primary_model_summary.csv', index=False)
    write_json(study.out/'study_manifest.json', dict(run_id=study.run.meta['run_id'],
        stage_order=study.config['stage_order'], dates=study.config['dates'], observations=123, instruments_per_date=41,
        distinct_tickers=43, observed_all_three=39, model_comparisons=len(study.comparison),
        explained_partitions=len(study.fidelity), preprocessing_fit_on='2025-06-30',
        shap_completed=True, promotion=False, configuration=study.config,
        validation=study.validation, interpretation='Repeated descriptive cross-sections; not return prediction or 123 independent firms'))
    lines = ['# Three-cross-section study: results and reading order', '',
             f'Run ID: `{study.run.meta["run_id"]}`. Each date retains 41 instruments representing 40 company groups; 123 records, 43 distinct tickers, '
             '39 observed at all three dates. These are overlapping historical cross-sections.', '',
             'Investec Limited (INL) and Investec plc (INP) are distinct securities in one dual-listed company (DLC) group. '
             'Both remain separate rows in this instrument-level analysis. Membership is determined independently at each date; '
             'an exited instrument is absent until its re-entry takes effect. Group counts do not imply independent observations.', '',
             '## 1. Start with EDA', '',
             '- `eda/population.csv`: population counts and flagged imputations.',
             '- `eda/evidence.csv` and `eda/missingness.csv`: evidence/missing-case accounting.',
             '- `eda/feature_distributions.png`: all ten model features, all three dates, June-scaled units.',
             '- `eda/correlation_<date>.png`: correlations for each date, including model-only imputations.',
             '- `eda/membership_presence.png`: observed membership rather than a balanced independent panel.', '',
             '## 2. Compare models using both scores', '',
             'Scores below use the representative seed fit. All nine baseline model families are in `model_comparison.csv`. '
             'DBSCAN noise/coverage remain explicit. DB and silhouette use Euclidean score geometry; '
             'the hierarchical fits use average/Manhattan linkage.', '',
             '| Model | Date | Embedding silhouette | Embedding DB | Feature silhouette | Feature DB | Mean seed ARI |',
             '| --- | --- | ---: | ---: | ---: | ---: | ---: |']
    for row in table.itertuples():
        lines.append(f'| {row.study_model} | {row.decision_date} | {row.silhouette_embedding:.3f} | '
                     f'{row.davies_bouldin_embedding:.3f} | {row.silhouette_features:.3f} | '
                     f'{row.davies_bouldin_features:.3f} | {row.mean_seed_ari:.3f} |')
    lines += ['', 'The UMAP case uses frozen neighbors=3/min_dist=0.01 and k=8 fixed by the original sector-count design. '
              'Other k values are diagnostics only. Its settings are reused across dates and seeds. It is not silently promoted over the historical '
              't-SNE k=8 baseline. No new search occurs on later dates.', '',
              '## 3. Read cluster plots, profiles and SHAP together', '',
              '`models/<date>/` contains the recovered baseline. `umap_sensitivity/<date>/` contains the additional '
              'candidate when enabled. Each has a cluster map/membership panel, dendrogram, median-deviation heatmap, '
              'global and per-cluster SHAP bars, and a SHAP distribution plot for the largest local class.', '',
              '| Model | Date | In-sample fidelity | OOF fidelity | OOF status |',
              '| --- | --- | ---: | ---: | --- |']
    for row in study.fidelity.itertuples():
        oof = 'not estimable' if pd.isna(row.oof_accuracy) else f'{row.oof_accuracy:.3f}'
        lines.append(f'| {row.study_model} | {row.decision_date} | {row.in_sample_accuracy:.3f} | {oof} | {row.oof_status} |')
    lines += ['', 'SHAP describes a supervised surrogate of cluster membership, not the clustering algorithm, '
              'causality or investment returns. Dimensions, class mapping and raw-margin additivity are checked. '
              'Singleton explanations are descriptive only. OOF fidelity to full-snapshot pseudo-labels does not validate discovery.', '',
              '## 4. Compare dates with membership-aware joins', '',
              '`temporal_agreement.csv` contains continuing-member ARI/NMI. Each model folder contains aligned '
              'transition tables, entry/exit events and `transition_heatmaps.png`. Each adjacent pair has 40 continuing '
              'instruments, one entry and one exit. Entry/exit events have no ordinary cluster-change flag. '
              'RNI/AGL imputation sensitivity remains flagged. Cluster numbers and independently fitted map axes '
              'are not persistent economic identities/shared coordinates.', '',
              '## Research boundary', '',
              'Three cross-sections extend the single-window SACJ study, but repetition alone does not certify '
              'historical inputs or guarantee publication readiness. Archived shares/capitalisation, sector history '
              'and daily vendor-series evidence remain unresolved. Analyst recommendations are not invented. '
              'The ten-feature variant and historical baseline remain distinct from the original eleven-feature experiment. '
              'No Hotelling cutoff or temporal outlier taxonomy is invented in this workflow.']
    (study.out/'study_summary.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
