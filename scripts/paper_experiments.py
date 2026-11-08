"""Guided EDA -> exhaustive finite experiment -> selection -> longitudinal review."""
import json
import os
from itertools import combinations
from pathlib import Path

from tracking import ROOT,Run,write_json
from study_workflow import StudySession


class PaperExperiment:
    _step=StudySession._step
    _fail=StudySession._fail
    table=StudySession.table
    show_figure=StudySession.show_figure

    def __init__(self,run_id=None,config_path=None):
        self.config=json.loads(Path(config_path or ROOT/'configs/paper_experiments.json').read_text(encoding='utf-8'))
        if self.config['k']!=8:raise ValueError('Paper hierarchical/K-Means comparisons fix k=8')
        for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS']:
            os.environ.setdefault(key,'1')
        os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.runtime/matplotlib'))
        os.environ.setdefault('NUMBA_CACHE_DIR',str(ROOT/'.runtime/numba'))
        self.run=Run(ROOT/'experiments',self.config,self.config['experiment'],
            'EDA, exhaustive finite-grid optimisation, frozen follow-ups and descriptive longitudinal screens',run_id)
        self.run.__enter__();self.state='started';self.closed=False
        try:self.run.provenance()
        except BaseException as error:self._fail(error);raise
        self.out=self.run.out
        print(f'Paper experiment: {self.run.meta["run_id"]}\n{self.out}',flush=True)

    def explore(self):
        def action():
            import pandas as pd
            from validate_data import validate
            from analysis import prepare,FEATURES
            from study_eda import explore
            self.validation=validate();self.features=FEATURES
            self.frame=pd.read_csv(ROOT/'data/processed/Top40_Retrospective_Model_Inputs_v1.csv')
            self.scaler,self.snapshots=prepare(self.frame)
            self.eda=explore(self.frame,self.features,self.scaler,self.out/'eda')
            return self.eda['population']
        return self._step('started','explored','1. Data validation and EDA before experimentation',action)

    def experiment(self):
        def action():
            from paper_search import run_search
            self.pool,self.summary=run_search(self.snapshots,self.scaler,self.features,self.config,self.out/'search')
            return self.summary
        return self._step('explored','searched','2. Exhaustive finite-grid experiment; all scores and seeds saved',action)

    def select_models(self):
        def action():
            from paper_search import choose
            self.choices=choose(self.pool,self.summary,self.out/'search')
            write_json(self.out/'selection_policy.json',dict(primary=self.config['primary_selection'],
                rule=self.config['selection_rule'],selection_date=self.config['selection_date'],
                roles=self.choices,universal_best_claim=False,later_dates_used_for_selection=False,
                caveat='Later dates were examined in earlier work: not untouched holdouts; this is an explicitly recorded exploratory protocol'))
            return self.table('search/best_parameters.csv')
        return self._step('searched','selected','3. Freeze June-2025 choices under both score objectives',action)

    def fit_results(self):
        def action():
            import numpy as np
            import pandas as pd
            import matplotlib.pyplot as plt
            from sklearn.metrics import adjusted_rand_score,normalized_mutual_info_score
            from sklearn.cluster import AgglomerativeClustering
            from scipy.cluster.hierarchy import dendrogram
            from paper_search import fit_representation,fit_cluster,quality
            from paper_longitudinal import hotelling_screen
            from study_plots import cluster_map,feature_profile,shap_distribution
            from analysis import explain
            from orion_review import deviation_comparison
            by_id={c['candidate_id']:c for c in self.pool};cache={};scores=[];agreements=[];diagnostics=[];fidelity=[]
            self.model_folders={};self.explained=set()
            main={self.choices[r] for r in ['baseline','common_features_k8','embedding_k8']}
            for cid in sorted(set(self.choices.values())):
                candidate=by_id[cid];directory=self.out/'models'/cid;directory.mkdir(parents=True)
                self.model_folders[cid]=directory
                print(f'Refitting frozen {cid}: {candidate["representation"]["name"]} / {candidate["clustering"]}',flush=True)
                write_json(directory/'parameters.json',candidate)
                for date,sub in self.snapshots.items():
                    x=self.scaler.transform(sub[self.features].to_numpy(dtype=float));local=directory/date;local.mkdir()
                    fits=[]
                    for seed in self.config['seeds']:
                        rep=candidate['representation'];key=(date,rep['representation_id'],seed)
                        if key not in cache:cache[key]=fit_representation(x,rep,seed)
                        z,metadata=cache[key];y=fit_cluster(z,candidate['clustering'],seed)
                        keep=y!=-1
                        score=quality(x,z,y)
                        scores.append(dict(candidate_id=cid,decision_date=date,seed=seed,
                            sector_ari=float(adjusted_rand_score(sub.sector_label[keep],y[keep])) if keep.any() else None,
                            sector_nmi=float(normalized_mutual_info_score(sub.sector_label[keep],y[keep])) if keep.any() else None,**score))
                        fits.append((seed,y));np.savez_compressed(local/f'seed_{seed}_arrays.npz',embedding=z,clusters=y,tickers=sub.ticker.to_numpy(dtype=str))
                        if seed!=self.config['seeds'][0]:continue
                        result=sub.copy();result['cluster']=y;result.to_csv(local/'assignments.csv',index=False)
                        np.savez_compressed(local/'arrays.npz',embedding=z,clusters=y,scaled_features=x,
                            features=np.array(self.features),tickers=sub.ticker.to_numpy(dtype=str))
                        write_json(local/'resolved_representation.json',metadata)
                        pd.crosstab(result.cluster,result.sector_label).to_csv(local/'cluster_sector_counts.csv')
                        cluster_map(result,z,y,local/'cluster_map.png',f'{date}: {cid}; {candidate["representation"]["name"]} / {candidate["clustering"]["algorithm"]}')
                        feature_profile(result,x,self.features,local/'feature_profile.png',f'{date}: {cid}')
                        if candidate['clustering']['algorithm']=='hierarchical':
                            tree=AgglomerativeClustering(**candidate['clustering']['params'],compute_distances=True).fit(z)
                            if not np.array_equal(tree.labels_,y):raise ValueError('Dendrogram labels differ from fitted hierarchy')
                            counts=np.zeros(len(tree.children_));n=len(z)
                            for i,pair in enumerate(tree.children_):counts[i]=sum(1 if child<n else counts[child-n] for child in pair)
                            matrix=np.column_stack([tree.children_,tree.distances_,counts]).astype(float)
                            np.save(local/'linkage_matrix.npy',matrix)
                            fig,ax=plt.subplots(figsize=(12,11))
                            dendrogram(matrix,labels=[f'{r.ticker} | cluster {r.cluster} | {r.sector_label}' for r in result.itertuples()],
                                orientation='left',leaf_font_size=7,link_color_func=lambda k:'#555555',ax=ax)
                            ax.set_title(f'{date}: {candidate["representation"]["name"]}; {candidate["clustering"]["params"]}',fontsize=10)
                            ax.set_xlabel('Actual fitted-tree linkage distance; leaf labels show fitted clusters')
                            fig.tight_layout();fig.savefig(local/'dendrogram.png',dpi=140);plt.close(fig)
                            for k in self.config['k_diagnostics']:
                                spec=dict(candidate['clustering']['params'],n_clusters=k)
                                alt=AgglomerativeClustering(**spec).fit_predict(z)
                                diagnostics.append(dict(candidate_id=cid,decision_date=date,k=k,**quality(x,z,alt)))
                        if cid in main and keep.all() and len(np.unique(y))==8:
                            explain(result,y,local,seed);shap_distribution(local,result,f'{date}: {cid}')
                            deviations,ranks=deviation_comparison(result,x,self.features,pd.read_csv(local/'shap_by_cluster.csv'))
                            deviations.to_csv(local/'shap_univariate_comparison.csv',index=False)
                            ranks.to_csv(local/'shap_univariate_rank_summary.csv',index=False)
                            fit=json.loads((local/'surrogate_fidelity.json').read_text())
                            fidelity.append(dict(candidate_id=cid,decision_date=date,**fit))
                    for (a,ya),(b,yb) in combinations(fits,2):
                        keep=(ya!=-1)&(yb!=-1);valid=keep.sum()>1 and len(np.unique(ya[keep]))>1 and len(np.unique(yb[keep]))>1
                        agreements.append(dict(candidate_id=cid,decision_date=date,seed_a=a,seed_b=b,common_coverage=float(keep.mean()),
                            ari=float(adjusted_rand_score(ya[keep],yb[keep])) if valid else None,
                            nmi=float(normalized_mutual_info_score(ya[keep],yb[keep])) if valid else None))
                if cid in main and all((directory/d/'shap_values.npz').exists() for d in self.config['dates']):self.explained.add(cid)
            self.results=pd.DataFrame(scores);self.results.to_csv(self.out/'selected_model_scores.csv',index=False)
            self.results[self.results.seed==self.config['seeds'][0]].to_csv(self.out/'representative_scores.csv',index=False)
            pd.DataFrame(agreements).to_csv(self.out/'selected_seed_stability.csv',index=False)
            pd.DataFrame(diagnostics).to_csv(self.out/'selected_k_diagnostics.csv',index=False)
            pd.DataFrame(fidelity).to_csv(self.out/'cluster_surrogate_fidelity.csv',index=False)
            from study_plots import cluster_count_plot
            for cid,sub in pd.DataFrame(diagnostics).groupby('candidate_id'):
                cluster_count_plot(sub,self.model_folders[cid]/'k_diagnostics.png',self.config['dates'],8,cid)
            return self.table('representative_scores.csv')
        return self._step('selected','fitted','4. Frozen all-date results, dendrograms, seed sensitivity and cluster SHAP',action)

    def longitudinal_review(self):
        def action():
            import pandas as pd
            from paper_longitudinal import analyse_model
            summary=[]
            for role in ['baseline','common_features_k8','embedding_k8']:
                cid=self.choices[role];directory=self.model_folders[cid]
                if cid not in self.explained:
                    summary.append(dict(role=role,candidate_id=cid,status='Not eligible: follow-up contains noise or violates eight-class explanation contract'))
                    continue
                if not (directory/'company_case_summary.csv').exists():analyse_model(directory,self.config,self.features)
                companies=pd.read_csv(directory/'company_case_summary.csv');histories=pd.read_csv(directory/'company_cluster_histories.csv')
                summary.append(dict(role=role,candidate_id=cid,status='completed descriptive review',
                    stable_all_three=int((histories.stability_status=='stable all three').sum()),
                    shifted_all_three=int((histories.stability_status=='shifted at least once').sum()),
                    membership_gaps=int((~histories.observed_all_three).sum()),
                    screen_candidates=int(companies.screen_flag.eq(True).sum()),
                    multi_seed_supported_candidates=int(companies.multi_seed_supported.sum()),confirmed_outliers=0,
                    sector_divergences=int(companies.sector_divergence.eq(True).sum())))
            self.longitudinal=pd.DataFrame(summary);self.longitudinal.to_csv(self.out/'longitudinal_summary.csv',index=False)
            return self.longitudinal
        return self._step('fitted','reviewed','5. Jaccard histories, Hotelling reference screens, sector context and attribute-shift SHAP',action)

    def finish(self):
        def action():
            import pandas as pd
            required=['eda/population.csv','search/candidate_summary.csv','search/best_parameters.csv',
                'search/selection_scores_all_seeds.csv','selected_model_scores.csv','longitudinal_summary.csv']
            if any(not (self.out/p).exists() for p in required):raise ValueError('Missing required paper artifacts')
            trials=pd.read_csv(self.out/'search/selection_scores_all_seeds.csv')
            if len(trials)!=self.config['maximum_selection_fits']:raise ValueError('Incomplete search')
            for role in ['baseline','common_features_k8','embedding_k8']:
                cid=self.choices[role]
                if cid not in self.explained:continue
                for name in ['company_cluster_histories.csv','membership_transitions.csv','hotelling_all_seeds.csv',
                             'company_case_summary.csv','frozen_2025_shift_checks.csv','case_review.md']:
                    if not (self.model_folders[cid]/name).exists():raise ValueError('Incomplete longitudinal explanations')
            write_json(self.out/'paper_manifest.json',dict(config=self.config,validation=self.validation,
                search_configurations=len(self.pool),selection_fits=len(trials),selected_roles=self.choices,
                selected_followup_fits=len(self.results),scaler_fit_on='2025-06-30',
                scaler_min=self.scaler.data_min_.tolist(),scaler_max=self.scaler.data_max_.tolist(),
                confirmed_outliers=0,promotion=False,limitations=['Finite-grid exploratory selection, not universal optimum',
                'Sector labels are historically unverified external context',
                'F-reference screens and seed support do not confirm outliers',
                'Surrogates describe associations; frozen 2025 contrast decomposition does not causally explain refitted clusters',
                'Source certification blockers remain']))
            self.write_report()
            self.run.meta['metric_artifacts']=['search/candidate_summary.csv','search/best_parameters.csv',
                'selected_model_scores.csv','longitudinal_summary.csv']
            return self.out
        result=self._step('reviewed','completed','6. Validate and archive the entire experiment and report',action)
        try:self.run.__exit__(None,None,None)
        finally:self.closed=True
        print(f'Completed paper experiment: {result}',flush=True)
        return result

    def write_report(self):
        import pandas as pd
        lines=['# EDA, experimentation, optimisation and longitudinal results','',
            f'Run: `{self.run.meta["run_id"]}`. 40 groups / 41 instruments per date; k=8 for hierarchical/K-Means.',
            '',f'The declared grid exhaustively tested **{len(self.pool):,} configurations × {len(self.config["seeds"])} seeds '
            f'= {self.config["maximum_selection_fits"]:,} selection fits** on June 2025. '
            'These are finite-grid exploratory optima; later dates are descriptive refits with frozen settings.',
            '', '## Read in order','',
            '1. `eda/`: populations, missingness, evidence, distributions and correlations.',
            '2. `search/grid_manifest.json` and `candidate_configurations.csv`: exact parameter combinations and invalid Ward exclusions.',
            '3. `search/selection_scores_all_seeds.csv`, `selection_seed_stability.csv`, `candidate_summary.csv`: every trial, invalid/noise result and seed variability.',
            '4. `search/ranking_*.csv`, `pareto_*.csv`, `family_best_models.csv`, `best_parameters.csv`: both silhouette/DB objectives and nine family comparisons.',
            '5. `selected_model_scores.csv`: frozen settings across dates; sector ARI/NMI are contextual only.',
            '6. `models/<candidate>/<date>/`: actual hierarchical dendrograms, membership maps, feature profiles and available SHAP.',
            '7. `models/<candidate>/`: stable/shifted instrument lists, entry/exit events, Jaccard/overlap sensitivity, screens, case reports and frozen-2025 shift attribution.',
            '', '## Main model parameters','']
        models=json.loads((self.out/'search/selected_models.json').read_text())
        for role in ['common_features_k8','embedding_k8','baseline']:
            c=models[role];lines.append(f'- **{role}** (`{c["candidate_id"]}`): {c["representation"]["name"]} '
                f'`{json.dumps(c["representation"]["params"],sort_keys=True)}` + {c["clustering"]["algorithm"]} '
                f'`{json.dumps(c["clustering"]["params"],sort_keys=True)}`.')
        lines+=['','## Representative scores (seed 42)','',
            '| Role | Date | Feature silhouette | Feature DB | Embedding silhouette | Embedding DB | Sector ARI |',
            '| --- | --- | ---: | ---: | ---: | ---: | ---: |']
        for role in ['common_features_k8','embedding_k8','baseline']:
            rows=self.results[(self.results.candidate_id==self.choices[role])&(self.results.seed==self.config['seeds'][0])]
            for r in rows.itertuples():lines.append(f'| {role} | {r.decision_date} | {r.silhouette_features:.3f} | {r.davies_bouldin_features:.3f} | '
                f'{r.silhouette_embedding:.3f} | {r.davies_bouldin_embedding:.3f} | {r.sector_ari:.3f} |')
        lines+=['','## Stability and candidate counts','']
        for r in self.longitudinal.to_dict('records'):lines.append('- '+json.dumps(r,default=str)+'.')
        lines+=['','## Interpretation boundaries','',
            'Primary selection jointly ranks silhouette and DB in the common June-scaled original financial features. '
            'The embedding criterion is reported separately because nonlinear layouts can exaggerate separation. '
            'The sum of ranks is an explicit trade-off rule, not evidence of a universal best model. '
            'Both metric champions and Pareto sets remain inspectable in the ranking files.',
            '', 'Individual D² uses the first two representation coordinates and same-date sample covariance. '
            'The p(n−1)/(n−p) F(0.95;p,n−p) cutoff is an illustrative paper-style reference, not an individual-distance '
            'significance test. An internal Beta reference and seed support are sensitivity descriptions. '
            'No confirmed outlier is claimed without substantive validation. Sector divergence and singletons are distinct flags.',
            '', 'Cluster SHAP explains each date’s surrogate. A separate regression surrogate describes attributes associated '
            'with the geometric distance. Its fidelity is reported separately. For temporal explanations, the same frozen '
            '2025 classifier is evaluated at both feature vectors: contrast-SHAP differences sum to the margin-contrast change. '
            'They describe associations within that fixed function, not the causal mechanism of an independent refit.',
            '', 'All source-certification limitations remain; no baseline pointer is promoted.']
        (self.out/'paper_results.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


class SavedPaperExperiment:
    """Read-only notebook replay: completed results are verified, never refitted."""
    table=StudySession.table
    show_figure=StudySession.show_figure

    def __init__(self,run_id):
        from verify_run import verify_completed
        if Path(run_id).name!=run_id:raise ValueError('Use a saved run ID, not a path')
        self.out=ROOT/'experiments/runs'/run_id
        verify_completed(self.out)
        manifest=json.loads((self.out/'paper_manifest.json').read_text(encoding='utf-8'))
        self.config=manifest['config'];self.choices=manifest['selected_roles'];self.closed=True
        self.model_folders={cid:self.out/'models'/cid for cid in set(self.choices.values())}
        print(f'READ-ONLY saved results: {self.out}; no experiment is rerun',flush=True)

    def explore(self):return self.table('eda/population.csv')
    def experiment(self):return self.table('search/candidate_summary.csv')
    def select_models(self):return self.table('search/best_parameters.csv')
    def fit_results(self):return self.table('representative_scores.csv')
    def longitudinal_review(self):return self.table('longitudinal_summary.csv')
    def finish(self):return self.out


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-id');parser.add_argument('--config')
    args=parser.parse_args();study=PaperExperiment(args.run_id,args.config)
    study.explore();study.experiment();study.select_models();study.fit_results();study.longitudinal_review();study.finish()


if __name__=='__main__':main()
