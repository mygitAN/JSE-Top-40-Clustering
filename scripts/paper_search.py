"""Declared finite search, with cached representations and every trial retained."""
import json
from itertools import product, combinations
from pathlib import Path

from optimize_models import identifier, fit_representation, fit_cluster, quality, aggregate, select
from tracking import write_json


def grid(config):
    reps=[]; invalid=[]
    for n in config['pca_components']:
        reps.append(dict(name='pca',params=dict(n_components=n,svd_solver='full')))
    for p,lr,it,metric in product(config['tsne_perplexities'],config['tsne_learning_rates'],
                                 config['tsne_iterations'],config['reduction_metrics']):
        reps.append(dict(name='tsne',params=dict(n_components=2,perplexity=p,learning_rate=lr,
                          max_iter=it,metric=metric,init='random',n_jobs=1)))
    for nn,md,metric in product(config['umap_neighbors'],config['umap_min_dist'],config['reduction_metrics']):
        reps.append(dict(name='umap',params=dict(n_components=2,n_neighbors=nn,min_dist=md,metric=metric,n_jobs=1)))
    reps=[dict(**r,representation_id=identifier(r,'r_')) for r in reps]
    cluster=[]
    for linkage,metric in product(config['linkages'],config['clustering_metrics']):
        if linkage=='ward' and metric!='euclidean':
            invalid.append(dict(linkage=linkage,metric=metric,reason='Ward requires Euclidean distance'))
        else:
            cluster.append(dict(algorithm='hierarchical',params=dict(n_clusters=config['k'],linkage=linkage,metric=metric)))
    cluster.append(dict(algorithm='kmeans',params=dict(n_clusters=config['k'],n_init=config['kmeans_n_init'])))
    for eps,n,metric in product(config['dbscan_eps'],config['dbscan_min_samples'],config['dbscan_metrics']):
        cluster.append(dict(algorithm='dbscan',params=dict(eps=eps,min_samples=n,metric=metric)))
    pool=[]
    for r,c in product(reps,cluster):
        value=dict(representation=r,clustering=c)
        pool.append(dict(**value,candidate_id=identifier(value,'c_')))
    return reps,pool,invalid


def run_search(snapshots,scaler,features,config,out):
    import numpy as np
    import pandas as pd
    from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
    out.mkdir()
    reps,pool,invalid=grid(config)
    if (len(reps),len(pool),len(pool)*len(config['seeds'])) != (
        config['maximum_representations'],config['maximum_configurations'],config['maximum_selection_fits']):
        raise ValueError('Actual search differs from the declared budget')
    write_json(out/'grid_manifest.json',dict(representations=len(reps),configurations=len(pool),
        selection_fits=len(pool)*len(config['seeds']),reused_representation_fits=len(reps)*len(config['seeds']),
        skipped_invalid_linkage_pairs=invalid,selection_date=config['selection_date'],
        score_geometry='Euclidean silhouette and centroid DB in representation and common June-scaled features',
        dbscan='Axis-standardized representation before fitting; scores on unstandardized representation and common features; noise excluded and coverage explicit',
        exhaustive_scope=config['scope']))
    descriptions=pd.DataFrame([dict(candidate_id=c['candidate_id'],representation=c['representation']['name'],
        representation_id=c['representation']['representation_id'],algorithm=c['clustering']['algorithm'],
        representation_parameters=json.dumps(c['representation']['params'],sort_keys=True),
        clustering_parameters=json.dumps(c['clustering']['params'],sort_keys=True)) for c in pool])
    descriptions.to_csv(out/'candidate_configurations.csv',index=False)
    x=scaler.transform(snapshots[config['selection_date']][features].to_numpy(dtype=float))
    rows=[];pairs=[];assignments=[];embeddings={};resolved=[]
    for number,r in enumerate(reps,1):
        print(f'Search representation {number}/{len(reps)}: {r["name"]} {r["params"]}',flush=True)
        members=[c for c in pool if c['representation']['representation_id']==r['representation_id']]
        fits={c['candidate_id']:[] for c in members}
        for seed in config['seeds']:
            z,metadata=fit_representation(x,r,seed)
            embeddings[r['representation_id']+'__seed_'+str(seed)]=z
            resolved.append(dict(representation_id=r['representation_id'],seed=seed,**metadata))
            for c in members:
                cid=c['candidate_id']
                try:
                    y=fit_cluster(z,c['clustering'],seed)
                    values=quality(x,z,y)
                except ValueError as error:
                    y=np.full(len(x),-1)
                    values=quality(x,z,y);values['score_status']='fit failed: '+str(error)
                rows.append(dict(candidate_id=cid,seed=seed,**values))
                fits[cid].append((seed,y));assignments.append((cid,seed,y))
        for c in members:
            for (a,ya),(b,yb) in combinations(fits[c['candidate_id']],2):
                keep=(ya!=-1)&(yb!=-1)
                valid=keep.sum()>1 and len(np.unique(ya[keep]))>1 and len(np.unique(yb[keep]))>1
                pairs.append(dict(candidate_id=c['candidate_id'],seed_a=a,seed_b=b,
                    common_nonnoise_members=int(keep.sum()),common_coverage=float(keep.mean()),
                    ari=float(adjusted_rand_score(ya[keep],yb[keep])) if valid else None,
                    nmi=float(normalized_mutual_info_score(ya[keep],yb[keep])) if valid else None))
    metrics=pd.DataFrame(rows);stability=pd.DataFrame(pairs)
    metrics.to_csv(out/'selection_scores_all_seeds.csv',index=False)
    stability.to_csv(out/'selection_seed_stability.csv',index=False)
    np.savez_compressed(out/'selection_assignments.npz',candidate_ids=np.array([a for a,b,c in assignments]),
        seeds=np.array([b for a,b,c in assignments]),labels=np.stack([c for a,b,c in assignments]),
        tickers=snapshots[config['selection_date']].ticker.to_numpy(dtype=str),scaled_features=x)
    np.savez_compressed(out/'selection_embeddings.npz',**embeddings)
    write_json(out/'resolved_representations.json',resolved)
    summary=aggregate(rows,stability,config).merge(descriptions,on='candidate_id',validate='one_to_one')
    summary.to_csv(out/'candidate_summary.csv',index=False)
    if len(metrics)!=config['maximum_selection_fits'] or len(stability)!=len(pool)*len(list(combinations(config['seeds'],2))):
        raise ValueError('Incomplete exhaustive search')
    return pool,summary


def choose(pool,summary,out):
    """Both joint-score objectives and nine family comparisons, sectors excluded."""
    import pandas as pd
    by_id={c['candidate_id']:c for c in pool}
    choices={};family=[]
    for geometry,name in [('features','common_features_k8'),('embedding','embedding_k8')]:
        ranking=select(summary,geometry,8)
        ranking.to_csv(out/f'ranking_{name}.csv',index=False)
        ranking[ranking.pareto_optimal].to_csv(out/f'pareto_{name}.csv',index=False)
        choices[name]=str(ranking.candidate_id.iloc[0])
        for (rep,algo),sub in summary.groupby(['representation','algorithm'],sort=True):
            try:
                ranked=select(sub,geometry,8 if algo!='dbscan' else None)
                cid=str(ranked.candidate_id.iloc[0]);choices[f'{geometry}_{rep}_{algo}']=cid
                family.append(dict(geometry=geometry,representation=rep,algorithm=algo,candidate_id=cid,
                    status='full-coverage all-seed joint winner',**{k:ranked.iloc[0][k] for k in [
                    'silhouette_embedding_mean','davies_bouldin_embedding_mean','silhouette_features_mean',
                    'davies_bouldin_features_mean','seed_ari_mean','n_clusters_min','n_clusters_max']}))
            except ValueError:
                family.append(dict(geometry=geometry,representation=rep,algorithm=algo,candidate_id=None,
                    status='No valid full-coverage candidate on every seed; inspect all trials and noise/coverage'))
    # Include the original fixed reference using the new explicit Euclidean t-SNE metric.
    baseline=[c for c in pool if c['representation']['name']=='tsne'
        and c['representation']['params']['perplexity']==5 and c['representation']['params']['learning_rate']==10
        and c['representation']['params']['max_iter']==300 and c['representation']['params']['metric']=='euclidean'
        and c['clustering']['params']==dict(n_clusters=8,linkage='average',metric='manhattan')]
    if len(baseline)!=1:raise ValueError('Missing historical reference')
    choices['baseline']=baseline[0]['candidate_id']
    pd.DataFrame(family).to_csv(out/'family_best_models.csv',index=False)
    pd.DataFrame([dict(role=role,**next(r for r in summary.to_dict('records') if r['candidate_id']==cid))
                  for role,cid in choices.items()]).to_csv(out/'best_parameters.csv',index=False)
    write_json(out/'selected_models.json',{role:by_id[cid] for role,cid in choices.items()})
    parameter_rows=[]
    for row in summary.to_dict('records'):
        c=by_id[row['candidate_id']]
        parameter_rows.append(dict(**row,linkage=c['clustering']['params'].get('linkage','not applicable'),
            distance=c['clustering']['params'].get('metric','Euclidean objective'),
            reduction_distance=c['representation']['params'].get('metric','Euclidean linear projection')))
    detailed=pd.DataFrame(parameter_rows)
    detailed.groupby(['representation','algorithm','linkage','distance','reduction_distance']).agg(
        configurations=('candidate_id','size'),eligible=('eligible_all_seeds','sum'),
        best_feature_silhouette=('silhouette_features_mean','max'),lowest_feature_db=('davies_bouldin_features_mean','min')
        ).to_csv(out/'distance_linkage_inventory.csv')
    # These two extrema can belong to different configurations; never label them one model.
    tradeoff_plot(summary,choices,out/'search_tradeoffs.png')
    return choices


def tradeoff_plot(table,choices,path):
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(12,5))
    eligible=table[table.eligible_all_seeds & (table.n_clusters_min==8)&(table.n_clusters_max==8)]
    for ax,geometry in zip(axes,['features','embedding']):
        for name,sub in eligible.groupby('representation'):
            ax.scatter(sub['silhouette_'+geometry+'_mean'],sub['davies_bouldin_'+geometry+'_mean'],label=name,alpha=.4,s=14)
        for role,marker in [('common_features_k8','*'),('embedding_k8','X'),('baseline','s')]:
            row=table.set_index('candidate_id').loc[choices[role]]
            ax.scatter(row['silhouette_'+geometry+'_mean'],row['davies_bouldin_'+geometry+'_mean'],marker=marker,
                       s=120,edgecolors='black',label=role)
        ax.set_xlabel('Mean silhouette (higher better)');ax.set_ylabel('Mean Davies–Bouldin (lower better)')
        ax.set_title(geometry+' score space; five seeds; k=8');ax.legend(fontsize=7)
    fig.suptitle('All eligible grid trials: joint-score trade-offs, not a global optimum')
    fig.tight_layout();fig.savefig(path,dpi=140);plt.close(fig)
