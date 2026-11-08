"""Run the user's UMAP grid, print scores/parameters, and plot the chosen hierarchy.

Notebook use: result = tune_umap(scaled_data, config)
CLI use: python scripts/tune_umap.py --run-id user-umap-grid-01
"""
import argparse
import json
import os
from itertools import product
from pathlib import Path

from tracking import ROOT, Run, write_json


def rank_results(frame):
    """Use both scores, with a fully specified deterministic tie-break."""
    import numpy as np
    if frame.empty or not np.isfinite(frame[['Silhouette','Davies_Bouldin']].to_numpy()).all():
        raise ValueError('Expected nonempty, finite silhouette and DB scores')
    result=frame.copy()
    result['silhouette_rank']=result.Silhouette.rank(ascending=False,method='average')
    result['db_rank']=result.Davies_Bouldin.rank(ascending=True,method='average')
    result['joint_rank_sum']=result.silhouette_rank+result.db_rank
    return result.sort_values(['joint_rank_sum','Silhouette','Davies_Bouldin','n_neighbors','min_dist','n_clusters'],
                              ascending=[True,False,True,True,True,True]).reset_index(drop=True)


def metric_champions(frame):
    ordered=frame.sort_values(['n_neighbors','min_dist','n_clusters'])
    return {'highest_silhouette':ordered.loc[ordered.Silhouette.idxmax()].to_dict(),
            'lowest_db':ordered.loc[ordered.Davies_Bouldin.idxmin()].to_dict(),
            'joint':rank_results(frame).iloc[0].to_dict()}


def fit_umap(x,n_neighbors,min_dist,config):
    from umap import UMAP
    return UMAP(n_neighbors=int(n_neighbors),min_dist=float(min_dist),
                n_components=config['n_components'],metric=config['umap_metric'],
                random_state=config['seed'],n_jobs=config['n_jobs']).fit_transform(x)


def score_fit(x,z,k,config):
    from sklearn.cluster import AgglomerativeClustering
    from optimize_models import quality
    labels=AgglomerativeClustering(n_clusters=int(k),metric=config['clustering_metric'],
                                   linkage=config['linkage']).fit_predict(z)
    values=quality(x,z,labels)
    if values['score_status']!='valid':
        raise ValueError(f'Quality scores unavailable for k={k}: {values["score_status"]}')
    return labels,dict(Silhouette=values['silhouette_embedding'],Davies_Bouldin=values['davies_bouldin_embedding'],
                       silhouette_features=values['silhouette_features'],davies_bouldin_features=values['davies_bouldin_features'],
                       singleton_clusters=values['singleton_clusters'])


def tune_umap(scaled_data,config=None):
    """No globals or silently skipped fits; UMAP runs once per parameter pair."""
    import numpy as np
    import pandas as pd
    if config is None:
        config=json.loads((ROOT/'configs/user_umap_grid.json').read_text(encoding='utf-8'))
    x=np.asarray(scaled_data,dtype=float)
    if x.ndim!=2 or not np.isfinite(x).all():
        raise ValueError('scaled_data must be a finite 2D numeric feature matrix')
    ks=config['grid_clusters']+config['cluster_sweep']
    if not ks or min(ks)<2 or max(ks)>=len(x):
        raise ValueError('All cluster counts must be between 2 and n_observations-1')
    if not config['n_neighbors'] or min(config['n_neighbors'])<2 or max(config['n_neighbors'])>=len(x):
        raise ValueError('UMAP neighbors must be between 2 and n_observations-1')
    rows=[];embeddings={}
    for neighbors,distance in product(config['n_neighbors'],config['min_dist']):
        z=fit_umap(x,neighbors,distance,config)
        embeddings[(neighbors,distance)]=z
        for k in config['grid_clusters']:
            _,scores=score_fit(x,z,k,config)
            rows.append(dict(n_neighbors=neighbors,min_dist=distance,n_clusters=k,**scores))
    grid=rank_results(pd.DataFrame(rows))
    chosen=grid.iloc[0]
    # Explicitly select the winning embedding, never the loop's final embedding.
    key=(int(chosen.n_neighbors),float(chosen.min_dist))
    z=embeddings[key]
    sweep=[]
    for k in config['cluster_sweep']:
        _,scores=score_fit(x,z,k,config)
        sweep.append(dict(n_neighbors=key[0],min_dist=key[1],n_clusters=k,**scores))
    sweep=rank_results(pd.DataFrame(sweep))
    final=sweep.iloc[0]
    labels,_=score_fit(x,z,int(final.n_clusters),config)
    params=dict(n_neighbors=key[0],min_dist=key[1],n_components=config['n_components'],
                umap_metric=config['umap_metric'],n_clusters=int(final.n_clusters),
                clustering_metric=config['clustering_metric'],linkage=config['linkage'],
                random_state=config['seed'],n_jobs=config['n_jobs'])
    return dict(grid_results=grid,grid_champions=metric_champions(grid),
                cluster_sweep=sweep,sweep_champions=metric_champions(sweep),
                best_parameters=params,embedding=z,labels=labels)


def print_results(result):
    for stage,key in [(f'Your {len(result["grid_results"])}-combination grid','grid_champions'),('k sweep on the selected embedding','sweep_champions')]:
        print('\n'+stage)
        for criterion,row in result[key].items():
            print(f'{criterion}: n_neighbors={int(row["n_neighbors"])}, min_dist={row["min_dist"]:g}, '
                  f'n_clusters={int(row["n_clusters"])}, silhouette={row["Silhouette"]:.6f}, DB={row["Davies_Bouldin"]:.6f}')
    print('\nFinal parameters:')
    print(json.dumps(result['best_parameters'],indent=2))
    print('\nTop 10 grid rows (joint silhouette/DB ranking):')
    print(result['grid_results'][['n_neighbors','min_dist','n_clusters','Silhouette','Davies_Bouldin','joint_rank_sum']]
          .head(10).to_string(index=False))


def hierarchy_matrix(z,config):
    import numpy as np
    from sklearn.cluster import AgglomerativeClustering
    tree=AgglomerativeClustering(n_clusters=None,distance_threshold=0,compute_distances=True,
                                 metric=config['clustering_metric'],linkage=config['linkage']).fit(z)
    counts=np.zeros(len(tree.children_)); n=len(z)
    for i,children in enumerate(tree.children_):
        counts[i]=sum(1 if child<n else counts[child-n] for child in children)
    return np.column_stack([tree.children_,tree.distances_,counts])


def plot_results(result,frame,out,config):
    import numpy as np
    import matplotlib.pyplot as plt
    from scipy.cluster.hierarchy import dendrogram
    sweep=result['cluster_sweep'].sort_values('n_clusters')
    k=result['best_parameters']['n_clusters']
    fig,axes=plt.subplots(1,2,figsize=(12,4))
    for ax,column,title in zip(axes,['Silhouette','Davies_Bouldin'],['Silhouette (higher better)','Davies-Bouldin (lower better)']):
        ax.plot(sweep.n_clusters,sweep[column],marker='o')
        best=sweep[sweep.n_clusters==k].iloc[0]
        ax.scatter([k],[best[column]],marker='*',s=140,color='red',zorder=3,label='Joint choice')
        ax.set_xlabel('Number of clusters');ax.set_ylabel(title);ax.grid(alpha=.25);ax.legend()
    fig.suptitle(f'Selected UMAP embedding; seed {config["seed"]}, {config["selection_date"]}')
    fig.tight_layout();fig.savefig(out/'cluster_count_scores.png',dpi=160);plt.close(fig)
    matrix=hierarchy_matrix(result['embedding'],config)
    np.save(out/'linkage_matrix.npy',matrix)
    n=len(frame);merges=n-k
    lower=matrix[merges-1,2] if merges else 0
    upper=matrix[merges,2]
    threshold=float((lower+upper)/2)
    labels=[r.ticker+('*' if r.fundamentals_imputed or r.volume_imputed else '')+' | '+r.sector_label
            for r in frame.itertuples()]
    fig,ax=plt.subplots(figsize=(12,12))
    dendrogram(matrix,labels=labels,orientation='left',leaf_font_size=8,color_threshold=threshold,ax=ax)
    ax.axvline(threshold,color='red',linestyle='--',linewidth=1,label=f'Cut reference: k={k}')
    ax.set_title(f'Average-linkage Manhattan hierarchy in selected UMAP space\nk={k}; * model-only imputation')
    ax.set_xlabel('Average Manhattan linkage distance');ax.set_ylabel('Instruments (legacy sector context)');ax.legend()
    fig.tight_layout();fig.savefig(out/'dendrogram.png',dpi=160);plt.close(fig)
    write_json(out/'dendrogram_reference.json',dict(k=k,lower_merge=float(lower),upper_merge=float(upper),
               color_threshold=threshold,tied_heights=bool(lower==upper),
               note='Tied merge heights may make a horizontal tree cut ambiguous; exact labels are exported separately'))


def execute(config,out):
    import numpy as np
    import pandas as pd
    from analysis import FEATURES,prepare,numeric_matrix
    from validate_data import validate
    validate()
    frame=pd.read_csv(ROOT/'data/processed/Top40_Retrospective_Model_Inputs_v1.csv')
    scaler,snapshots=prepare(frame)
    first=snapshots[config['selection_date']]
    x=scaler.transform(numeric_matrix(first))
    result=tune_umap(x,config)
    print_results(result)
    result['grid_results'].to_csv(out/'grid_results.csv',index=False)
    result['cluster_sweep'].sort_values('n_clusters').to_csv(out/'cluster_count_scores.csv',index=False)
    write_json(out/'best_parameters.json',result['best_parameters'])
    write_json(out/'metric_champions.json',{'grid':result['grid_champions'],'sweep':result['sweep_champions']})
    np.savez_compressed(out/'selected_arrays.npz',scaled_features=x,embedding=result['embedding'],
                        labels=result['labels'],tickers=first.ticker.to_numpy(dtype=str),features=np.array(FEATURES))
    output=first.copy();output['cluster']=result['labels'];output.to_csv(out/'selection_assignments.csv',index=False)
    plot_results(result,first,out,config)
    followup=[]
    for date,sub in snapshots.items():
        data=scaler.transform(numeric_matrix(sub));params=result['best_parameters']
        z=result['embedding'] if date==config['selection_date'] else fit_umap(data,params['n_neighbors'],params['min_dist'],config)
        labels,scores=score_fit(data,z,params['n_clusters'],config)
        followup.append(dict(decision_date=date,**scores))
        assigned=sub.copy();assigned['cluster']=labels;assigned.to_csv(out/f'assignments_{date}.csv',index=False)
    pd.DataFrame(followup).to_csv(out/'frozen_followup_scores.csv',index=False)
    expected=len(config['n_neighbors'])*len(config['min_dist'])*len(config['grid_clusters'])
    if len(result['grid_results'])!=expected or len(result['cluster_sweep'])!=len(config['cluster_sweep']):
        raise ValueError('Incomplete grid or cluster-count sweep')
    write_json(out/'tuning_manifest.json',dict(selection_date=config['selection_date'],seed=config['seed'],
               grid_combinations=expected,cluster_sweep_fits=len(config['cluster_sweep']),
               umap_grid_fits=len(config['n_neighbors'])*len(config['min_dist']),
               scope=config['scope'],features=FEATURES,scaling_fit_on='2025-06-30',
               silhouette_geometry='Euclidean embedding distances',db_geometry='Euclidean embedding centroids',
               linkage_geometry='average/Manhattan',baseline_promoted=False,
               warnings=['Single-seed exploratory result, not five-seed stability evidence',
                         'Two-stage search is not a complete 9x14 search',
                         'Later snapshots are descriptive frozen-parameter refits; source evidence limitations unchanged']))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',default=str(ROOT/'configs/user_umap_grid.json'))
    parser.add_argument('--run-id')
    parser.add_argument('--print-run',help='Print a verified saved run without fitting models or creating a new run')
    args=parser.parse_args()
    for name in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS']:
        os.environ.setdefault(name,'1')
    os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.runtime/matplotlib'))
    os.environ.setdefault('NUMBA_CACHE_DIR',str(ROOT/'.runtime/numba'))
    if args.print_run:
        if args.run_id:
            parser.error('--print-run and --run-id cannot be combined')
        if Path(args.print_run).name!=args.print_run:
            parser.error('--print-run must be a run ID')
        from verify_run import verify_completed
        import pandas as pd
        source=ROOT/'experiments/runs'/args.print_run
        verify_completed(source)
        champs=json.loads((source/'metric_champions.json').read_text(encoding='utf-8'))
        print_results(dict(grid_results=pd.read_csv(source/'grid_results.csv'),
                           grid_champions=champs['grid'],sweep_champions=champs['sweep'],
                           best_parameters=json.loads((source/'best_parameters.json').read_text(encoding='utf-8'))))
        return
    config=json.loads(Path(args.config).read_text(encoding='utf-8'))
    with Run(ROOT/'experiments',config,config['experiment'],
             'Correct and execute user-supplied UMAP grid, print winners/parameters and plot hierarchy',args.run_id) as run:
        run.provenance()
        execute(config,run.out)
    print(f'Completed {run.meta["run_id"]}: {run.out}')


if __name__=='__main__':
    main()
