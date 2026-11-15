"""The staged study used by both the notebook and ``python -m top40``.

Stages run in a fixed order and each writes its outputs into one tracked run
directory: load -> explore -> audit features -> fit models -> explain -> compare
dates -> finish. A failure at any stage marks the run failed.
"""
import json
import os
from pathlib import Path

from . import CONFIG, DATA_POLICY, ROOT
from .tracking import Run, write_json

STAGES = ['started', 'loaded', 'explored', 'audited', 'modelled', 'explained', 'compared', 'completed']


class StudySession:
    def __init__(self, feature_set=None, run_id=None, output=None, seed=None, stability_runs=None,
                 config_path=None):
        self.config = json.loads(Path(config_path or CONFIG).read_text(encoding='utf-8'))
        for key, value in [('feature_set', feature_set), ('seed', seed), ('stability_runs', stability_runs)]:
            if value is not None:
                self.config[key] = value
        if self.config['stability_runs'] < 2:
            raise ValueError('Use at least two seeds for stability diagnostics')
        from .features import get_feature_set
        self.feature_set = get_feature_set(self.config['feature_set'])
        self.seeds = list(range(self.config['seed'], self.config['seed'] + self.config['stability_runs']))
        # Single-threaded numerics keep repeated runs numerically identical.
        for name in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMBA_NUM_THREADS']:
            os.environ.setdefault(name, '1')
        os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.runtime/matplotlib'))
        os.environ.setdefault('NUMBA_CACHE_DIR', str(ROOT / '.runtime/numba'))
        self.run = Run(output or ROOT / 'experiments', self.config, self.config['experiment'],
                       f'Three-cross-section study, feature set {self.feature_set.name}', run_id)
        self.run.__enter__()
        self.out = self.run.out
        self.state = 'started'
        self.closed = False
        try:
            self.run.provenance()
        except BaseException as error:
            self._fail(error)
            raise
        print(f'Run {self.run.meta["run_id"]} -> {self.out}\n'
              f'Feature set: {self.feature_set.name} ({self.feature_set.status})', flush=True)

    # --- stage machinery -------------------------------------------------------------------

    def _fail(self, error):
        self.state = 'failed'
        if not self.closed:
            self.closed = True
            self.run.__exit__(type(error), error, error.__traceback__)

    def _step(self, expected, title, action):
        if self.closed:
            raise RuntimeError('This study is closed. Start a new session.')
        try:
            if self.state != expected:
                raise RuntimeError(f'Run stages in order: expected {expected}, found {self.state}')
            print(f'\n{title}', flush=True)
            result = action()
            self.state = STAGES[STAGES.index(expected) + 1]
            self.run.meta['study_stage'] = self.state
            write_json(self.out / 'status.json', self.run.meta)
            return result
        except BaseException as error:
            self._fail(error)
            raise

    def _scaled(self, sub):
        from .models import feature_matrix
        return self.scaler.transform(feature_matrix(sub, self.feature_set.columns))

    # --- stages ------------------------------------------------------------------------------

    def load_data(self):
        def action():
            from .data import load_inputs, validate
            from .features import add_derived_columns
            from .models import prepare
            self.validation = validate()
            self.data = add_derived_columns(load_inputs(), self.config['fit_date'])
            self.scaler, self.snapshots = prepare(self.data, self.feature_set.columns, self.config['dates'],
                                                  self.config['fit_date'])
            write_json(self.out / 'preprocessing.json', dict(
                feature_set=self.feature_set.name, status=self.feature_set.status,
                features=list(self.feature_set.columns), fit_date=self.config['fit_date'],
                scaler_minimum=self.scaler.data_min_.tolist(), scaler_maximum=self.scaler.data_max_.tolist(),
                data_policy=json.loads(DATA_POLICY.read_text(encoding='utf-8'))))
            return self.data
        return self._step('started', '1. Validate and load the model inputs', action)

    def explore(self):
        def action():
            from .eda import explore
            self.eda = explore(self.data, self.feature_set, self.scaler, self.config['fit_date'], self.out / 'eda')
            return self.eda
        return self._step('loaded', '2. Exploratory data analysis', action)

    def audit_features(self):
        def action():
            from . import plots
            from .ablation import run_ablation
            from .features import share_basis_audit
            folder = self.out / 'feature_audit'
            folder.mkdir()
            self.audit = run_ablation(self.data, self.config, seeds=self.seeds)
            self.audit['share_basis'] = share_basis_audit(self.data)
            for name, table in self.audit.items():
                table.to_csv(folder / f'{name}.csv', index=False)
            plots.variance_shares(self.audit['dominance'], folder / 'feature_dominance.png')
            return self.audit
        return self._step('explored', '3. Feature validity: share basis, dominance and ablation', action)

    def fit_models(self):
        def action():
            import numpy as np
            import pandas as pd
            from . import plots
            from .models import cluster, embed, linkage_matrix, scores, seed_agreement

            config, seed, k = self.config, self.config['seed'], self.config['k']
            columns = list(self.feature_set.columns)
            comparison, seed_scores, agreement = [], [], []
            self.assignments, self.model_folders = {}, {}

            # (a) Every representation x algorithm at the representative seed.
            (self.out / 'comparison').mkdir()
            for date, sub in self.snapshots.items():
                x = self._scaled(sub)
                for rep, params in config['representations'].items():
                    z = embed(x, rep, params, seed)
                    for algorithm, settings in config['clusterers'].items():
                        labels = cluster(z, algorithm, settings, seed, k)
                        comparison.append(dict(decision_date=date, model=f'{rep}_{algorithm}',
                                               **scores(x, z, labels, sub.sector_label)))
                        pd.DataFrame({'ticker': sub.ticker, 'cluster': labels}).to_csv(
                            self.out / 'comparison' / f'{date}_{rep}_{algorithm}.csv', index=False)

            # (b) The primary models, over every seed, with full outputs.
            for name, spec in config['primary_models'].items():
                folder = self.out / 'models' / name
                self.model_folders[name] = folder
                assigned, k_rows = [], []
                for date, sub in self.snapshots.items():
                    date_folder = folder / date
                    date_folder.mkdir(parents=True)
                    x = self._scaled(sub)
                    fits = {}
                    for current in self.seeds:
                        z = embed(x, spec['representation'], spec['representation_params'], current)
                        fits[current] = cluster(z, 'hierarchical', spec['hierarchical'], current, k)
                        quality = scores(x, z, fits[current], sub.sector_label)
                        seed_scores.append(dict(study_model=name, decision_date=date, seed=current, **quality))
                        np.savez_compressed(date_folder / f'seed_{current}.npz', embedding=z, clusters=fits[current],
                                            tickers=sub.ticker.to_numpy(dtype=str))
                        if current != seed:
                            continue
                        result = sub.assign(cluster=fits[current])
                        assigned.append(result)
                        result.to_csv(date_folder / 'assignments.csv', index=False)
                        result.groupby('cluster')[columns].median().to_csv(date_folder / 'cluster_medians.csv')
                        pd.crosstab(result.cluster, result.sector_label).to_csv(date_folder / 'cluster_sectors.csv')
                        np.savez_compressed(date_folder / 'arrays.npz', embedding=z, scaled_features=x,
                                            clusters=fits[current], tickers=sub.ticker.to_numpy(dtype=str),
                                            features=np.array(columns))
                        plots.cluster_map(result, z, fits[current], date_folder / 'cluster_map.png',
                                          f'{date}: {name}', quality=quality)
                        plots.feature_profile(result, x, self.feature_set, date_folder / 'feature_profile.png',
                                              f'{date}: {name}').to_csv(date_folder / 'median_deviations.csv')
                        plots.dendrogram(linkage_matrix(z, spec['hierarchical']), sub, date_folder / 'dendrogram.png',
                                         f'{date}: {name}\n{plots.score_line(quality)}')
                        if 'comparison_row' not in spec:
                            comparison.append(dict(decision_date=date, model=name, **quality))
                        for other in config['k_sensitivity']:
                            alternative = cluster(z, 'hierarchical', spec['hierarchical'], current, other)
                            k_rows.append(dict(decision_date=date, k=other, **scores(x, z, alternative)))
                    agreement += [dict(study_model=name, decision_date=date, **pair) for pair in seed_agreement(fits)]
                self.assignments[name] = pd.concat(assigned, ignore_index=True)
                k_table = pd.DataFrame(k_rows)
                k_table.to_csv(folder / 'cluster_count_sensitivity.csv', index=False)
                plots.cluster_count_sensitivity(k_table, folder / 'cluster_count_sensitivity.png', config['dates'], k,
                                                f'{name}: sensitivity to the number of clusters')

            self.comparison = pd.DataFrame(comparison).sort_values(['decision_date', 'model'], ignore_index=True)
            self.seed_scores = pd.DataFrame(seed_scores)
            self.seed_agreement = pd.DataFrame(agreement)
            self.comparison.to_csv(self.out / 'model_comparison.csv', index=False)
            self.seed_scores.to_csv(self.out / 'seed_scores.csv', index=False)
            self.seed_agreement.to_csv(self.out / 'seed_agreement.csv', index=False)
            self.model_specification().to_csv(self.out / 'model_specification.csv', index=False)
            # Orange: the study's model(s). Blue: the original paper's t-SNE recipe, kept as the reference row.
            highlight = {'tsne_hierarchical': plots.BLUE,
                         **{spec.get('comparison_row', name): plots.ORANGE
                            for name, spec in config['primary_models'].items()}}
            for date in config['dates']:
                plots.quality_comparison(self.comparison[self.comparison.decision_date == date],
                                         self.out / f'model_quality_{date}.png', date, highlight)
            return self.comparison
        return self._step('audited', '4. Fit representations and clusters', action)

    def explain_clusters(self):
        def action():
            import pandas as pd
            from . import plots
            from .explain import explain, profile_comparison

            rows = []
            for name, assigned in self.assignments.items():
                for date in self.config['dates']:
                    sub = assigned[assigned.decision_date == date].reset_index(drop=True)
                    folder = self.model_folders[name] / date
                    fidelity, by_cluster = explain(sub, sub.cluster.to_numpy(), self.feature_set,
                                                   self.config['surrogate'], self.config['seed'], folder)
                    plots.shap_global(pd.read_csv(folder / 'shap_global.csv'), self.feature_set,
                                      folder / 'shap_global.png', f'{date}: {name}, surrogate importance')
                    plots.shap_distribution(folder, sub, self.feature_set, f'{date}: {name}')
                    table, ranks = profile_comparison(sub, self._scaled(sub), self.feature_set, by_cluster)
                    table.to_csv(folder / 'profile_vs_shap.csv', index=False)
                    ranks.to_csv(folder / 'profile_vs_shap_ranks.csv', index=False)
                    rows.append(dict(study_model=name, decision_date=date,
                                     **{key: fidelity[key] for key in ['in_sample_accuracy', 'oof_accuracy',
                                                                       'oof_status', 'minimum_cluster_size']}))
            self.fidelity = pd.DataFrame(rows)
            self.fidelity.to_csv(self.out / 'surrogate_fidelity.csv', index=False)
            return self.fidelity
        return self._step('modelled', '5. Explain cluster membership with a surrogate and SHAP', action)

    def compare_dates(self):
        def action():
            import numpy as np
            import pandas as pd
            from . import plots
            from .models import mahalanobis_screen
            from .movement import explain_moves
            from .temporal import aligned_histories, membership_matrices, sector_context

            dates = self.config['dates']
            agreement, summary = [], []
            self.moves = {}
            for name, assigned in self.assignments.items():
                folder = self.out / 'longitudinal' / name
                folder.mkdir(parents=True)
                snapshots = {d: assigned[assigned.decision_date == d] for d in dates}
                aligned, maps, events, histories, objective, pairs = aligned_histories(snapshots, dates)
                imputed = assigned.groupby('ticker')[['fundamentals_imputed', 'volume_imputed', 'volume_basis_mixed']
                                                     ].any().any(axis=1)
                histories['data_caveat'] = histories.ticker.map(imputed)
                for filename, table in [('alignment.csv', maps), ('membership_events.csv', events),
                                        ('cluster_histories.csv', histories),
                                        ('alignment_objective_sensitivity.csv', objective)]:
                    table.to_csv(folder / filename, index=False)
                counts, overlaps = {}, {}
                for before, after in zip(dates, dates[1:]):
                    counts[before, after], overlaps[before, after], _ = membership_matrices(aligned[before],
                                                                                            aligned[after])
                    counts[before, after].to_csv(folder / f'movement_counts_{before}_{after}.csv')
                    overlaps[before, after].to_csv(folder / f'jaccard_{before}_{after}.csv')
                plots.transition_heatmaps(counts, folder / 'movement_counts.png', name, 'counts')
                plots.transition_heatmaps(overlaps, folder / 'jaccard.png', name, 'jaccard')
                representative = self.seed_scores[(self.seed_scores.study_model == name) &
                                                  (self.seed_scores.seed == self.config['seed'])]
                quality = {row.decision_date: row._asdict() for row in representative.itertuples()}
                plots.cluster_flows(histories, dates, folder / 'cluster_flows.png', name, quality)
                pd.concat([sector_context(snapshots[d]).assign(decision_date=d) for d in dates]).to_csv(
                    folder / 'sector_context.csv', index=False)
                moves = explain_moves(name, assigned, aligned, self.snapshots,
                                      {d: self._scaled(s) for d, s in self.snapshots.items()}, self.feature_set,
                                      self.model_folders[name], self.fidelity[self.fidelity.study_model == name],
                                      self.seeds, folder / 'moves', quality)
                self.moves[name] = moves
                agreement.append(pairs.assign(study_model=name))
                status = histories.stability_status.value_counts()
                summary.append(dict(study_model=name, **{s: int(status.get(s, 0))
                                                         for s in ['stable', 'shifted', 'membership gap']}))

            # The distance screen lives in the scaled feature space, so it does not depend on the model.
            screens = []
            for date, sub in self.snapshots.items():
                distance, meta = mahalanobis_screen(self._scaled(sub), self.config['screen_alpha'])
                flag = np.where(np.isfinite(distance), distance > (meta['reference'] or np.inf), np.nan)
                screens.append(pd.DataFrame(dict(
                    decision_date=date, ticker=sub.ticker, squared_distance=distance, reference=meta['reference'],
                    flag=flag, status=meta['status'], fundamentals_imputed=sub.fundamentals_imputed,
                    volume_imputed=sub.volume_imputed, volume_basis_mixed=sub.volume_basis_mixed)))
            self.screens = pd.concat(screens, ignore_index=True)
            self.screens.to_csv(self.out / 'longitudinal' / 'feature_space_screen.csv', index=False)
            self.temporal = pd.concat(agreement, ignore_index=True)
            self.temporal.to_csv(self.out / 'temporal_agreement.csv', index=False)
            self.longitudinal = pd.DataFrame(summary)
            self.longitudinal.to_csv(self.out / 'longitudinal_summary.csv', index=False)
            return self.temporal
        return self._step('explained', '6. Compare continuing members across dates', action)

    def finish(self):
        def action():
            from .report import check_outputs, write_summary
            write_summary(self)
            check_outputs(self)
            return self.out
        result = self._step('compared', '7. Check outputs and complete the run', action)
        self.closed = True
        try:
            self.run.__exit__(None, None, None)
        except BaseException:
            self.state = 'failed'
            raise
        print(f'COMPLETED: {self.out}\nStart with summary.md in that folder.', flush=True)
        return result

    # --- notebook helpers --------------------------------------------------------------------

    def model_specification(self):
        """Every setting of the primary model(s), one row each, in report-ready form."""
        import importlib.metadata
        import pandas as pd

        config, rows = self.config, []
        versions = {p: importlib.metadata.version(p) for p in ['umap-learn', 'scikit-learn', 'xgboost', 'shap']}
        for name, spec in config['primary_models'].items():
            add = lambda step, setting, value, note='': rows.append(
                dict(model=name, step=step, setting=setting, value=str(value), note=note))
            add('Model', 'description', spec['description'])
            add('Inputs', 'feature set', self.feature_set.name, self.feature_set.status)
            add('Inputs', 'features', ', '.join(self.feature_set.labels))
            add('Inputs', 'instruments', '41 per date, 123 rows', 'all index members retained')
            add('Scaling', 'method', 'MinMaxScaler(clip=False)',
                f'fitted on {config["fit_date"]} only and applied unchanged to later dates')
            implementation = {'umap': f'umap.UMAP (umap-learn {versions["umap-learn"]})',
                              'tsne': f'sklearn.manifold.TSNE (scikit-learn {versions["scikit-learn"]})',
                              'pca': f'sklearn.decomposition.PCA (scikit-learn {versions["scikit-learn"]})'}
            add('Dimensionality reduction', 'algorithm', implementation.get(spec['representation'],
                                                                            spec['representation']))
            for key, value in spec['representation_params'].items():
                add('Dimensionality reduction', key, value)
            add('Dimensionality reduction', 'random_state',
                f'{self.seeds[0]}-{self.seeds[-1]}', f'{len(self.seeds)} seeds; {config["seed"]} is the representative fit')
            add('Clustering', 'algorithm',
                f'sklearn.cluster.AgglomerativeClustering (scikit-learn {versions["scikit-learn"]})',
                'hierarchical, bottom-up; fitted on the 2-D reduced coordinates')
            add('Clustering', 'n_clusters', config['k'], 'reference specification from the original paper')
            for key, value in spec['hierarchical'].items():
                add('Clustering', key, value)
            add('Fitting', 'dates', ', '.join(config['dates']),
                'each date fitted independently with identical settings; nothing re-tuned on later dates')
            add('Evaluation', 'silhouette, Davies-Bouldin',
                'Euclidean, in the 2-D embedding and in the scaled feature space')
            add('Evaluation', 'stability', 'pairwise adjusted Rand index between seeds')
            add('Evaluation', 'cluster count sensitivity', ', '.join(map(str, config['k_sensitivity'])))
            add('Explanation', 'surrogate', f'xgboost.XGBClassifier (xgboost {versions["xgboost"]})',
                ', '.join(f'{k}={v}' for k, v in config['surrogate'].items()))
            add('Explanation', 'SHAP', f'shap.TreeExplainer (shap {versions["shap"]})',
                'explains the surrogate, not the clustering')
            add('Provenance', 'how the settings were chosen', spec.get('provenance', ''))
        return pd.DataFrame(rows)

    def table(self, relative_path):
        import pandas as pd
        return pd.read_csv(self.out / relative_path)

    def show(self, relative_path):
        """Display a saved PNG in a notebook without refitting anything."""
        from IPython.display import Image, display
        display(Image(filename=str(self.out / relative_path)))


def run_all(**kwargs):
    study = StudySession(**kwargs)
    study.load_data()
    study.explore()
    study.audit_features()
    study.fit_models()
    study.explain_clusters()
    study.compare_dates()
    return study.finish()
