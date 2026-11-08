"""Review whether high-score partitions provide useful multi-instrument peer groups."""
import argparse
import json
import os
from itertools import combinations

from tracking import ROOT,Run,write_json,digest


def shortlist(summary,n=3):
    from optimize_models import select
    candidates=summary[summary.singleton_clusters_max.eq(0)].copy()
    return select(candidates,'features',8).head(n)


def size_profile(labels):
    import numpy as np
    _,counts=np.unique(labels[labels!=-1],return_counts=True)
    return dict(largest_cluster=int(max(counts,default=0)),smallest_cluster=int(min(counts,default=0)),
        singleton_clusters=int((counts==1).sum()),largest_fraction=float(max(counts,default=0)/len(labels)))


def derive(source,out,config):
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    from sklearn.metrics import adjusted_rand_score,normalized_mutual_info_score
    from sklearn.cluster import AgglomerativeClustering
    from sklearn.decomposition import PCA
    from scipy.cluster.hierarchy import dendrogram
    from verify_paper_experiment import verify_paper
    from paper_search import fit_representation,fit_cluster,quality
    from study_plots import cluster_map,feature_profile
    from paper_longitudinal import aligned_histories,longitudinal_plots

    verification=verify_paper(source)
    manifest=json.loads((source/'paper_manifest.json').read_text())
    models=json.loads((source/'search/selected_models.json').read_text())
    summary=pd.read_csv(source/'search/candidate_summary.csv')
    ranking=shortlist(summary,config['shortlist_size']);ranking.to_csv(out/'shortlist.csv',index=False)
    candidates={r.candidate_id:dict(representation=dict(name=r.representation,
        params=json.loads(r.representation_parameters),representation_id=r.representation_id),
        clustering=dict(algorithm=r.algorithm,params=json.loads(r.clustering_parameters)),candidate_id=r.candidate_id)
        for r in ranking.itertuples()}
    roles={r:models[r]['candidate_id'] for r in ['common_features_k8','embedding_k8','baseline']}
    dates=manifest['config']['dates'];seeds=manifest['config']['seeds'];sizes=[];metrics=[];stability=[];snapshots={}
    baseline=models['baseline']['candidate_id']
    for role,cid in roles.items():
        for date in dates:
            for seed in seeds:
                with np.load(source/'models'/cid/date/f'seed_{seed}_arrays.npz') as a:y=a['clusters']
                sizes.append(dict(model=role,candidate_id=cid,decision_date=date,seed=seed,**size_profile(y)))
    for date in dates:
        snapshots[date]=pd.read_csv(source/'models'/baseline/date/'assignments.csv').drop(columns='cluster')
    with np.load(source/'search/selection_embeddings.npz') as june_embeddings:
        for cid,candidate in candidates.items():
            directory=out/cid;directory.mkdir();assigned={}
            print(f'Review candidate {cid}: {candidate}',flush=True)
            for date in dates:
                frame=snapshots[date];local=directory/date;local.mkdir()
                with np.load(source/'models'/baseline/date/'arrays.npz') as a:
                    x=a['scaled_features'];feature_names=a['features'].tolist()
                fits=[]
                for seed in seeds:
                    if date==dates[0]:
                        z=june_embeddings[candidate['representation']['representation_id']+'__seed_'+str(seed)]
                    else:z,_=fit_representation(x,candidate['representation'],seed)
                    y=fit_cluster(z,candidate['clustering'],seed);fits.append((seed,y))
                    values=quality(x,z,y)
                    metrics.append(dict(model=cid,candidate_id=cid,decision_date=date,seed=seed,
                        sector_ari=float(adjusted_rand_score(frame.sector_label,y)),
                        sector_nmi=float(normalized_mutual_info_score(frame.sector_label,y)),**values))
                    sizes.append(dict(model=cid,candidate_id=cid,decision_date=date,seed=seed,**size_profile(y)))
                    np.savez_compressed(local/f'seed_{seed}_arrays.npz',embedding=z,clusters=y,tickers=frame.ticker.to_numpy(dtype=str))
                    if seed!=seeds[0]:continue
                    result=frame.copy();result['cluster']=y;assigned[date]=result
                    result.to_csv(local/'assignments.csv',index=False)
                    cluster_map(result,z,y,local/'cluster_map.png',f'{date}: review candidate {cid}')
                    feature_profile(result,x,feature_names,local/'feature_profile.png',f'{date}: {cid}')
                    if candidate['clustering']['algorithm']=='hierarchical':
                        tree=AgglomerativeClustering(**candidate['clustering']['params'],compute_distances=True).fit(z)
                        if not np.array_equal(y,tree.labels_):raise ValueError('Tree partition mismatch')
                        counts=np.zeros(len(tree.children_));n=len(y)
                        for i,children in enumerate(tree.children_):counts[i]=sum(1 if c<n else counts[c-n] for c in children)
                        linkage=np.column_stack([tree.children_,tree.distances_,counts])
                        fig,ax=plt.subplots(figsize=(12,11))
                        dendrogram(linkage,labels=[f'{r.ticker} | cluster {r.cluster} | {r.sector_label}' for r in result.itertuples()],
                            orientation='left',leaf_font_size=7,link_color_func=lambda _: '#555555',ax=ax)
                        ax.set_title(f'{date}: {cid}; {candidate["clustering"]["params"]}',fontsize=10)
                        fig.tight_layout();fig.savefig(local/'dendrogram.png',dpi=140);plt.close(fig)
                for (a,ya),(b,yb) in combinations(fits,2):
                    stability.append(dict(candidate_id=cid,decision_date=date,seed_a=a,seed_b=b,
                        ari=float(adjusted_rand_score(ya,yb)),nmi=float(normalized_mutual_info_score(ya,yb))))
            aligned,maps,events,histories,objective=aligned_histories(assigned,dates)
            histories.to_csv(directory/'cluster_histories.csv',index=False);events.to_csv(directory/'membership_events.csv',index=False)
            maps.to_csv(directory/'jaccard_alignment.csv',index=False)
            longitudinal_plots(directory,events,histories,dates)
    metrics=pd.DataFrame(metrics);sizes=pd.DataFrame(sizes);stability=pd.DataFrame(stability)
    metrics.to_csv(out/'shortlist_scores.csv',index=False);sizes.to_csv(out/'cluster_sizes_all_seeds.csv',index=False)
    stability.to_csv(out/'shortlist_seed_stability.csv',index=False)
    if len(metrics)!=config['shortlist_size']*3*5:raise ValueError('Incomplete shortlist refits')
    # Confirm every June refit reproduces the already archived trial, within CSV precision.
    old=pd.read_csv(source/'search/selection_scores_all_seeds.csv')
    compare=metrics[metrics.decision_date==dates[0]].merge(old,on=['candidate_id','seed'],validate='one_to_one',suffixes=('_new','_old'))
    for metric in ['silhouette_features','davies_bouldin_features','silhouette_embedding','davies_bouldin_embedding']:
        if not np.allclose(compare[metric+'_new'],compare[metric+'_old'],atol=1e-6):raise ValueError('Cached June scores differ')
    # Diagnose feature geometry without changing preprocessing or fitting new feature definitions.
    variance=[];loadings=[];extremes=[]
    primary=models['common_features_k8']['candidate_id']
    for date in dates:
        local=source/'models'/primary/date
        with np.load(local/'arrays.npz') as a:x=a['scaled_features'];features=a['features']
        pca=PCA(n_components=.95,svd_solver='full').fit(x)
        variance.extend(dict(decision_date=date,component=i+1,variance_fraction=float(v)) for i,v in enumerate(pca.explained_variance_ratio_))
        loadings.extend(dict(decision_date=date,feature=str(f),pc1_loading=float(v)) for f,v in zip(features,pca.components_[0]))
        frame=pd.read_csv(local/'assignments.csv');counts=frame.cluster.value_counts();median=np.median(x,axis=0)
        for i,row in enumerate(frame.itertuples()):
            if counts[row.cluster]!=1:continue
            for j,feature in enumerate(features):
                extremes.append(dict(decision_date=date,ticker=row.ticker,feature=str(feature),
                    scaled_deviation_from_median=float(x[i,j]-median[j]),
                    share_evidence=row.share_evidence,sector_evidence=row.sector_evidence))
    pd.DataFrame(variance).to_csv(out/'primary_pca_variance.csv',index=False)
    pd.DataFrame(loadings).to_csv(out/'primary_pca_loadings.csv',index=False)
    pd.DataFrame(extremes).to_csv(out/'singleton_feature_deviations.csv',index=False)
    size_summary=sizes.groupby(['model','decision_date']).agg(largest_cluster_max=('largest_cluster','max'),
        smallest_cluster_min=('smallest_cluster','min'),singleton_clusters_max=('singleton_clusters','max')).reset_index()
    size_summary.to_csv(out/'cluster_size_summary.csv',index=False)
    sizes_plot(sizes[sizes.seed==seeds[0]],dates,out/'cluster_size_comparison.png')
    report(out,source,roles,candidates,size_summary,metrics,stability,config)
    write_json(out/'review_manifest.json',dict(config=config,source_run=source.name,source_manifest_sha256=digest(source/'artifact_checksums.json'),
        verified_source_artifacts=verification['verified_artifacts'],june_eligible_without_singletons=int((summary.eligible_all_seeds&summary.singleton_clusters_max.eq(0)&summary.n_clusters_min.eq(8)&summary.n_clusters_max.eq(8)).sum()),
        shortlisted=list(candidates),followup_fits=len(metrics),primary_outputs_unchanged=True,
        posthoc_review=True,sectors_used_for_selection=False,promotion=False))


def sizes_plot(table,dates,path):
    import numpy as np
    import matplotlib.pyplot as plt
    models=list(table.model.unique());fig,axes=plt.subplots(1,3,figsize=(15,6))
    for ax,date in zip(axes,dates):
        sub=table[table.decision_date==date].set_index('model').loc[models]
        ax.barh(range(len(models)),sub.largest_cluster,color='steelblue',label='Largest cluster')
        ax.barh(range(len(models)),-sub.singleton_clusters,color='firebrick',label='Singleton clusters')
        ax.set_yticks(range(len(models)),['PCA score winner' if m=='common_features_k8' else 'UMAP score winner' if m=='embedding_k8' else m for m in models],fontsize=7)
        ax.axvline(0,color='gray');ax.set_title(date);ax.set_xlabel('Singleton count (left) / largest-group size (right)')
        for i,r in enumerate(sub.itertuples()):ax.text(r.largest_cluster+.3,i,str(r.largest_cluster),va='center',fontsize=8)
    axes[0].legend(fontsize=7,loc='lower right');fig.suptitle('Cluster suitability review: representative seed 42; all models retain k=8')
    fig.tight_layout();fig.savefig(path,dpi=145);plt.close(fig)


def report(out,source,roles,candidates,sizes,metrics,stability,config):
    import pandas as pd
    lines=['# Review of the paper-experiments notebook','',
        'The notebook provides a useful research workflow: EDA before modelling, an auditable finite tuning grid, both quality scores, '
        'frozen all-date comparisons, actual dendrograms, membership-aware tracking and separate SHAP targets. These parts should be retained.',
        '', '## Why the primary clusters are unsatisfactory','',
        'The common-feature joint-score winner is PCA95 with average-linkage Euclidean hierarchy. Its representative June-2025 partition '
        'contains one group of 28 instruments and four singletons; June 2026 contains a group of 23 and four singletons. '
        'These partitions can isolate extremes while giving limited resolution within a broad residual group. A score optimum is therefore '
        'not sufficient evidence of a useful peer-group partition. Singleton status is not itself a confirmed outlier.',
        '', 'The selection rule required valid scores, full coverage and k=8, but did not require multiple instruments per group. '
        'This explains why the winning partition passed the implemented criteria. The loss of OOF classifier fidelity in singleton '
        'solutions is already reported honestly. Stability of a broad aligned group should not be equated with stable detailed peer relationships.',
        '', 'The feature geometry also matters. By June 2026 the first PCA component has large revenue and share-count loadings, '
        'and GLN lies far outside the June-2025 feature ranges in those fields. In June 2025 the leading component instead combines '
        'volatility, dividend yield and beta more strongly. The saved loadings and singleton deviations support these descriptions; '
        'they do not establish causes. Share/capitalisation and sector evidence remain unresolved, and some raw accounting measures '
        'are not uniform across industries. This is a reason to audit feature definitions, not silently change the data.',
        '', '## A review shortlist, not a promoted replacement','',
        'The saved June search contains 488 valid full-coverage eight-cluster configurations with no singleton on any of five seeds. '
        'For this post hoc review, the top three are ranked using the same common-feature silhouette/DB rule within that cohort. '
        'No sector labels select them and equal cluster sizes are not forced. Their June settings are frozen for later refits; '
        'later singletons or weak results remain in the report.', '',
        '| Review candidate | Reduction parameters | Clustering parameters |',
        '| --- | --- | --- |']
    for cid,c in candidates.items():lines.append(f'| {cid} | {c["representation"]["name"]}: `{json.dumps(c["representation"]["params"],sort_keys=True)}` | `{json.dumps(c["clustering"]["params"],sort_keys=True)}` |')
    lines+=['','| Model | Date | Feature silhouette (mean) | Feature DB (mean) | Mean seed ARI | Smallest group, any seed | Largest group, any seed | Maximum singletons |',
        '| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    means=metrics.groupby(['candidate_id','decision_date']).mean(numeric_only=True)
    seed_means=stability.groupby(['candidate_id','decision_date']).ari.mean()
    for (cid,date),r in means.iterrows():
        size=sizes[(sizes.model==cid)&(sizes.decision_date==date)].iloc[0]
        lines.append(f'| {cid} | {date} | {r.silhouette_features:.3f} | {r.davies_bouldin_features:.3f} | {seed_means.loc[(cid,date)]:.3f} | '
            f'{size.smallest_cluster_min} | {size.largest_cluster_max} | {size.singleton_clusters_max} |')
    lines+=['','## What to keep and what to reconsider','',
        'Keep the EDA, trial-level parameter records, both score geometries, seed diagnostics, actual trees, membership rules and '
        'qualified reporting. Reconsider the rule for recommending a primary peer-group model: distinguish suitability for peer '
        'description from geometric extremeness. Show size distributions and fidelity beside scores, rather than treating a high '
        'score as sufficient. Any new no-singleton selection rule is a recorded post hoc sensitivity for these data, not a recovered '
        'historic specification.',
        '', 'Do not force every cluster to reproduce a sector, ban genuine isolated observations by definition, or choose a model '
        'because its later memberships tell a preferred story. Sector composition should help interpret financial peers, and '
        'the geometric screen should remain separate from the partition. The original baseline and both score optima remain '
        'available. No model is promoted by this review.',
        '', f'Source: `{source.name}`. See `cluster_sizes_all_seeds.csv`, `shortlist_scores.csv`, `shortlist_seed_stability.csv`, '
        '`primary_pca_loadings.csv`, `singleton_feature_deviations.csv` and the per-date membership maps/dendrograms.']
    (out/'notebook_cluster_review.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-id');args=parser.parse_args()
    for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS']:os.environ.setdefault(key,'1')
    os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.runtime/matplotlib'));os.environ.setdefault('NUMBA_CACHE_DIR',str(ROOT/'.runtime/numba'))
    config=json.loads((ROOT/'configs/cluster_suitability_review.json').read_text())
    with Run(ROOT/'experiments',config,config['experiment'],'Review peer-cluster suitability while preserving notebook strengths and primary results',args.run_id) as run:
        run.provenance();derive(ROOT/'experiments/runs'/config['source_run'],run.out,config)
        run.meta['metric_artifacts']=['cluster_size_summary.csv','shortlist_scores.csv','shortlist_seed_stability.csv']
    print(f'Completed {run.meta["run_id"]}: {run.out}',flush=True)


if __name__=='__main__':main()
