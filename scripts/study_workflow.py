"""One staged study: validation -> EDA -> models -> SHAP -> temporal comparisons.

Used by both run_study.py and the guided notebook. Financial/model definitions
are shared with the tested analysis modules; no source values are refreshed.
"""
import json
import os
from itertools import combinations
from pathlib import Path
from types import SimpleNamespace

from tracking import ROOT, Run, write_json


class StudySession:
    def __init__(self, run_id=None, output=None, seed=None, stability_runs=None,
                 include_umap=None, config_path=None):
        self.config = json.loads(Path(config_path or ROOT/'configs/study.json').read_text(encoding='utf-8'))
        for key, value in [('seed', seed), ('stability_runs', stability_runs), ('include_umap_sensitivity', include_umap)]:
            if value is not None:
                self.config[key] = value
        if self.config['stability_runs'] < 2:
            raise ValueError('Use at least two distinct seeds for stability diagnostics')
        if self.config['dates'] != ['2025-06-30', '2025-12-31', '2026-06-30']:
            raise ValueError('This workflow requires the three historical study dates')
        self.config['resolved_baseline'] = json.loads((ROOT/self.config['baseline']).read_text(encoding='utf-8'))
        if (self.config['resolved_baseline']['hierarchical']['n_clusters'] != 8 or
            self.config['resolved_baseline']['kmeans']['n_clusters'] != 8 or
            self.config['umap_sensitivity']['n_clusters'] != 8):
            raise ValueError('The paper workflow fixes k=8; use separate sensitivity scripts for other k values')
        for name in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMBA_NUM_THREADS']:
            os.environ.setdefault(name, '1')
        os.environ.setdefault('MPLCONFIGDIR', str(ROOT/'.runtime/matplotlib'))
        os.environ.setdefault('NUMBA_CACHE_DIR', str(ROOT/'.runtime/numba'))
        self.run = Run(output or ROOT/'experiments', self.config, self.config['experiment'],
                       'Guided three-cross-section revision: EDA, model comparisons, plots, SHAP and temporal interpretation', run_id)
        self.run.__enter__()
        self.out = self.run.out
        self.state = 'started'
        self.closed = False
        try:
            self.run.provenance()
        except BaseException as error:
            self._fail(error)
            raise
        print(f'Study run: {self.run.meta["run_id"]}\nArtifacts: {self.out}', flush=True)

    def _fail(self, error):
        self.state = 'failed'
        if not self.closed:
            self.closed = True
            self.run.__exit__(type(error), error, error.__traceback__)

    def _step(self, expected, following, title, action):
        if self.closed:
            raise RuntimeError('This study is already closed. Start a new session/run ID.')
        try:
            if self.state != expected:
                raise RuntimeError(f'Run stages in order: expected {expected}, found {self.state}')
            print(f'\n{title}', flush=True)
            result = action()
            self.state = following
            self.run.meta['study_stage'] = following
            write_json(self.out/'status.json', self.run.meta)
            return result
        except BaseException as error:
            self._fail(error)
            raise

    def load_data(self):
        def action():
            import pandas as pd
            from validate_data import validate
            from analysis import FEATURES, prepare
            self.validation = validate()
            self.data = pd.read_csv(ROOT/'data/processed/Top40_Retrospective_Model_Inputs_v1.csv')
            self.features = FEATURES.copy()
            self.scaler, self.snapshots = prepare(self.data)
            write_json(self.out/'preprocessing.json', dict(features=self.features, fit_date='2025-06-30', clip=False,
                minimum=self.scaler.data_min_.tolist(), maximum=self.scaler.data_max_.tolist(),
                audited_method=json.loads((ROOT/'docs/Top40_Retrospective_Model_Method_v1.json').read_text(encoding='utf-8'))))
            return self.data
        return self._step('started', 'loaded', '1. Validate and load all historical observations', action)

    def explore(self):
        def action():
            from study_eda import explore
            self.eda = explore(self.data, self.features, self.scaler, self.out/'eda')
            print(self.eda['population'].to_string(index=False))
            print('EDA saved. No features removed or parameters selected from later dates.')
            return self.eda
        return self._step('loaded', 'explored', '2. Exploratory data analysis across all three dates', action)

    def fit_models(self):
        def action():
            import numpy as np
            import pandas as pd
            from analysis import run as baseline_analysis, scores
            from optimize_models import quality
            from study_plots import cluster_map, quality_comparison, feature_profile, cluster_count_plot
            from tune_umap import hierarchy_matrix
            from scipy.cluster.hierarchy import dendrogram
            import matplotlib.pyplot as plt

            model_folder = self.out/'models'
            self.model_args = SimpleNamespace(output=str(model_folder), mode='full', seed=self.config['seed'],
                stability_runs=self.config['stability_runs'], skip_shap=True)
            # This substage writes model artifacts only. The enclosing tracked
            # study stays running until the later SHAP/temporal stages succeed.
            baseline_analysis(self.model_args)
            self.assignments = {'baseline': pd.read_csv(model_folder/'assignments.csv')}
            self.model_folders = {'baseline': model_folder}
            k_sensitivity = pd.read_csv(model_folder/'cluster_count_sensitivity.csv')
            from analysis import cluster
            for index, row in k_sensitivity.iterrows():
                with np.load(model_folder/row.decision_date/'baseline_arrays.npz', allow_pickle=False) as saved:
                    embedding = saved['embedding']; data = saved['scaled_features']
                labels = cluster(embedding, 'hierarchical', self.config['seed'], int(row.k))
                k_sensitivity.loc[index, 'davies_bouldin_features'] = quality(data, embedding, labels)['davies_bouldin_features']
            k_sensitivity.to_csv(model_folder/'cluster_count_sensitivity.csv', index=False)
            cluster_count_plot(k_sensitivity, model_folder/'cluster_count_sensitivity.png',
                               self.config['dates'], 8, 'Recovered baseline: k sensitivity')
            comparison = pd.read_csv(model_folder/'model_comparison.csv')
            for index, row in comparison.iterrows():
                sub = self.snapshots[row.decision_date]
                labels = pd.read_csv(model_folder/row.decision_date/f'{row.model}.csv').set_index('ticker').loc[sub.ticker, 'cluster'].to_numpy()
                values = self.scaler.transform(sub[self.features].to_numpy(dtype=float))
                comparison.loc[index, 'davies_bouldin_features'] = quality(values, values, labels)['davies_bouldin_features']
            self.seed_scores = pd.read_csv(model_folder/'seed_metrics.csv')
            self.seed_scores.insert(0, 'study_model', 'baseline')
            for index, row in self.seed_scores.iterrows():
                with np.load(model_folder/row.decision_date/f'seed_{int(row.seed)}_arrays.npz', allow_pickle=False) as saved:
                    labels = saved['clusters']
                data = self.scaler.transform(self.snapshots[row.decision_date][self.features].to_numpy(dtype=float))
                self.seed_scores.loc[index, 'davies_bouldin_features'] = quality(data, data, labels)['davies_bouldin_features']
            self.seed_agreement = pd.read_csv(model_folder/'seed_stability.csv')
            self.seed_agreement.insert(0, 'study_model', 'baseline')
            if self.config['include_umap_sensitivity']:
                additional = self._fit_umap_candidate()
                comparison = pd.concat([comparison, additional], ignore_index=True)
            self.comparison = comparison
            comparison.to_csv(self.out/'model_comparison.csv', index=False)
            self.seed_scores.to_csv(self.out/'seed_scores.csv', index=False)
            self.seed_agreement.to_csv(self.out/'seed_stability.csv', index=False)
            for date in self.config['dates']:
                quality_comparison(comparison[comparison.decision_date == date], self.out/f'model_quality_{date}.png', date)
            for name, assigned in self.assignments.items():
                folder = self.model_folders[name]
                for date in self.config['dates']:
                    sub = assigned[assigned.decision_date == date].sort_values('ticker').reset_index(drop=True)
                    date_folder = folder/date
                    filename = 'baseline_arrays.npz' if name == 'baseline' else 'arrays.npz'
                    with np.load(date_folder/filename, allow_pickle=False) as arrays:
                        z = arrays['embedding']; scaled = arrays['scaled_features']
                    cluster_map(sub, z, sub.cluster.to_numpy(), date_folder/'cluster_map.png', f'{date}: {name}')
                    deviation = feature_profile(sub, scaled, self.features, date_folder/'feature_profile.png', f'{date}: {name}')
                    deviation.to_csv(date_folder/'scaled_median_deviations.csv')
                    matrix = hierarchy_matrix(z, {'linkage': 'average', 'clustering_metric': 'manhattan'})
                    np.save(date_folder/'linkage_matrix.npy', matrix)
                    fig, axis = plt.subplots(figsize=(12, 11))
                    labels = [f'{row.ticker} | {row.sector_label}' for row in sub.itertuples()]
                    dendrogram(matrix, labels=labels, orientation='left', leaf_font_size=8, ax=axis)
                    axis.set_title(f'{date}: {name}; average-linkage Manhattan hierarchy')
                    axis.set_xlabel('Linkage distance in independently fitted representation')
                    fig.tight_layout(); fig.savefig(date_folder/'dendrogram.png', dpi=140); plt.close(fig)
            print('Model stage complete. SHAP is still pending; the study run is not completed yet.', flush=True)
            return comparison
        return self._step('explored', 'modelled', '3. Fit representations/clusters and report silhouette AND Davies-Bouldin', action)

    def _fit_umap_candidate(self):
        import numpy as np
        import pandas as pd
        from umap import UMAP
        from sklearn.cluster import AgglomerativeClustering
        from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
        from analysis import scores
        from optimize_models import quality
        from study_plots import cluster_count_plot

        settings = self.config['umap_sensitivity']
        folder = self.out/'umap_sensitivity'; folder.mkdir()
        self.model_folders['umap_sensitivity'] = folder
        assignments, comparisons, seed_scores, agreement, k_rows = [], [], [], [], []
        for date, sub in self.snapshots.items():
            date_folder = folder/date; date_folder.mkdir()
            x = self.scaler.transform(sub[self.features].to_numpy(dtype=float))
            fits = []
            for seed in range(self.config['seed'], self.config['seed'] + self.config['stability_runs']):
                embedding = UMAP(**{key: settings[key] for key in ['n_neighbors', 'min_dist', 'n_components', 'metric', 'n_jobs']},
                                 random_state=seed).fit_transform(x)
                labels = AgglomerativeClustering(n_clusters=settings['n_clusters'], linkage=settings['linkage'],
                                                 metric=settings['clustering_metric']).fit_predict(embedding)
                metric = scores(x, embedding, labels, sub.sector_label)
                metric['davies_bouldin_features'] = quality(x, embedding, labels)['davies_bouldin_features']
                seed_scores.append(dict(study_model='umap_sensitivity', decision_date=date, seed=seed, **metric))
                fits.append((seed, labels))
                np.savez_compressed(date_folder/f'seed_{seed}_arrays.npz', embedding=embedding, clusters=labels,
                                    tickers=sub.ticker.to_numpy(dtype=str))
                if seed == self.config['seed']:
                    result = sub.copy(); result['cluster'] = labels; assignments.append(result)
                    result.to_csv(date_folder/'assignments.csv', index=False)
                    result.groupby('cluster')[self.features].median().to_csv(date_folder/'cluster_profiles_median.csv')
                    pd.crosstab(result.cluster, result.sector_label).to_csv(date_folder/'cluster_sector_counts.csv')
                    np.savez_compressed(date_folder/'arrays.npz', embedding=embedding, scaled_features=x, clusters=labels,
                                        tickers=sub.ticker.to_numpy(dtype=str), features=np.array(self.features))
                    comparisons.append(dict(decision_date=date, model='umap_fixed_sensitivity',
                        clustering_geometry='manhattan embedding', **metric))
                    for k in self.config['umap_sensitivity_k']:
                        alternative = AgglomerativeClustering(n_clusters=k, linkage=settings['linkage'],
                                                             metric=settings['clustering_metric']).fit_predict(embedding)
                        k_rows.append(dict(decision_date=date, k=k, **quality(x, embedding, alternative)))
            for (a, left), (b, right) in combinations(fits, 2):
                agreement.append(dict(study_model='umap_sensitivity', decision_date=date, seed_a=a, seed_b=b,
                                      ari=float(adjusted_rand_score(left, right)), nmi=float(normalized_mutual_info_score(left, right))))
        self.assignments['umap_sensitivity'] = pd.concat(assignments, ignore_index=True)
        self.assignments['umap_sensitivity'].to_csv(folder/'assignments.csv', index=False)
        self.seed_scores = pd.concat([self.seed_scores, pd.DataFrame(seed_scores)], ignore_index=True)
        self.seed_agreement = pd.concat([self.seed_agreement, pd.DataFrame(agreement)], ignore_index=True)
        k_table = pd.DataFrame(k_rows)
        k_table.to_csv(folder/'cluster_count_sensitivity.csv', index=False)
        cluster_count_plot(k_table, folder/'cluster_count_sensitivity.png', self.config['dates'],
                           settings['n_clusters'], 'Fixed UMAP sensitivity: k diagnostics')
        return pd.DataFrame(comparisons)

    def explain_clusters(self):
        def action():
            import numpy as np
            import pandas as pd
            from analysis import explain, validate_outputs
            from study_plots import shap_distribution
            from orion_review import deviation_comparison

            fidelity = []
            for name, assignments in self.assignments.items():
                for date in self.config['dates']:
                    sub = assignments[assignments.decision_date == date].sort_values('ticker').reset_index(drop=True)
                    folder = self.model_folders[name]/date
                    explain(sub, sub.cluster.to_numpy(), folder, self.config['seed'])
                    shap_distribution(folder, sub, f'{date}: {name}; supervised surrogate explanation')
                    importance = pd.read_csv(folder/'shap_by_cluster.csv')
                    scaled = self.scaler.transform(sub[self.features].to_numpy(dtype=float))
                    deviations, ranks = deviation_comparison(sub, scaled, self.features, importance)
                    deviations.to_csv(folder/'shap_univariate_comparison.csv', index=False)
                    ranks.to_csv(folder/'shap_univariate_rank_summary.csv', index=False)
                    values = json.loads((folder/'surrogate_fidelity.json').read_text(encoding='utf-8'))
                    fidelity.append(dict(study_model=name, decision_date=date,
                        in_sample_accuracy=values['in_sample_accuracy'], oof_accuracy=values['oof_accuracy'],
                        oof_status=values['oof_status'], minimum_cluster_size=values['minimum_cluster_size'],
                        shap_max_additivity_error=values['shap_max_additivity_error']))
            self.fidelity = pd.DataFrame(fidelity)
            self.fidelity.to_csv(self.out/'surrogate_fidelity.csv', index=False)
            self.model_args.skip_shap = False
            validate_outputs(self.out/'models', self.model_args)
            path = self.out/'models/run_manifest.json'
            manifest = json.loads(path.read_text(encoding='utf-8'))
            manifest['shap_completed'] = True
            write_json(path, manifest)
            print(self.fidelity.to_string(index=False))
            return self.fidelity
        return self._step('modelled', 'explained', '4. Fit gradient-boosted surrogates and explain them with SHAP', action)

    def compare_dates(self):
        def action():
            import pandas as pd
            from analysis import transitions
            from study_plots import transitions_plot

            comparisons = []
            for name, assignments in self.assignments.items():
                folder = self.model_folders[name]
                transitions(assignments, folder)
                transitions_plot(folder, self.config['dates'], name)
                table = pd.read_csv(folder/'temporal_agreement.csv')
                table.insert(0, 'study_model', name)
                comparisons.append(table)
            self.temporal = pd.concat(comparisons, ignore_index=True)
            self.temporal.to_csv(self.out/'temporal_agreement.csv', index=False)
            self.eda['presence'].assign(observed_all_three=self.eda['presence'].all(axis=1)).to_csv(
                self.out/'temporal_observation_eligibility.csv')
            print(self.temporal.to_string(index=False))
            return self.temporal
        return self._step('explained', 'compared', '5. Compare continuing members separately from index entries/exits', action)

    def finish(self):
        def action():
            from study_reporting import write_study_summary, validate_study_outputs
            write_study_summary(self)
            validate_study_outputs(self.out, self.config)
            self.run.meta['metric_artifacts'] = ['model_comparison.csv', 'primary_model_summary.csv', 'surrogate_fidelity.csv',
                                                 'seed_stability.csv', 'temporal_agreement.csv']
            self.run.meta['warnings'] = ['Three overlapping cross-sections, not 123 independent firms',
                'Retrospective source reconstruction, not fully certified PIT observations',
                'UMAP settings are a frozen sensitivity, not promoted paper results',
                'SHAP explains a surrogate, not causality or investment returns']
            return self.out
        result = self._step('compared', 'completed', '6. Validate all artifacts and complete the tracked study', action)
        self.closed = True
        try:
            self.run.__exit__(None, None, None)
        except BaseException:
            self.state = 'failed'
            raise
        print(f'COMPLETED: {self.out}\nStart with study_summary.md in that folder.', flush=True)
        return result

    def table(self, relative_path):
        """Read a saved table for a notebook cell, recording failures while active."""
        import pandas as pd
        try:
            return pd.read_csv(self.out/relative_path)
        except BaseException as error:
            if not self.closed:
                self._fail(error)
            raise

    def show_figure(self, relative_path):
        """Display a saved PNG inside VS Code/Jupyter without refitting anything."""
        try:
            from IPython.display import display, Image
            display(Image(filename=str(self.out/relative_path)))
        except BaseException as error:
            if not self.closed:
                self._fail(error)
            raise
