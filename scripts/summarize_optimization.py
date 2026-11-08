"""Publish both silhouette and DB for a verified saved optimisation run."""
import argparse
import json
from pathlib import Path
import os
from itertools import combinations
from tracking import ROOT, digest, write_json
from verify_run import verify_completed


def nonnoise_agreement(a,b):
    import numpy as np
    from sklearn.metrics import adjusted_rand_score,normalized_mutual_info_score
    common=(a != -1)&(b != -1)
    valid=common.sum()>1 and len(np.unique(a[common]))>1 and len(np.unique(b[common]))>1
    return dict(common_nonnoise_members=int(common.sum()),common_coverage=float(common.mean()),
                ari=float(adjusted_rand_score(a[common],b[common])) if valid else None,
                nmi=float(normalized_mutual_info_score(a[common],b[common])) if valid else None,
                status='conditional on common non-noise members' if valid else 'not estimable: insufficient non-noise cluster structure')


def build(run_id):
    import numpy as np
    import pandas as pd
    os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.runtime/matplotlib'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    source=ROOT/'experiments/runs'/run_id
    verify_completed(source)
    report=ROOT/'reports'
    selected=json.loads((source/'selected_models.json').read_text())
    all_scores=pd.read_csv(source/'selected_model_scores.csv')
    numeric=['silhouette_embedding','davies_bouldin_embedding','silhouette_features','davies_bouldin_features',
             'sector_ari','sector_nmi','coverage','n_clusters']
    means=all_scores.groupby(['scenario','decision_date'])[numeric].mean().add_suffix('_mean').reset_index()
    std=all_scores.groupby(['scenario','decision_date'])[numeric].std().add_suffix('_std').reset_index()
    table=means.merge(std,on=['scenario','decision_date'])
    table.to_csv(report/'optimized_model_scores.csv',index=False)
    # The search independently refits its four frozen choices on June again.
    # Check those actual replays instead of assuming stochastic reproducibility.
    replay_count=0
    assignments=pd.read_csv(source/'selected_model_assignments_all_seeds.csv')
    search_scores=pd.read_csv(source/'selection_scores_all_seeds.csv').set_index(['candidate_id','seed'])
    with np.load(source/'selection_assignments.npz',allow_pickle=False) as saved:
        ids=saved['candidate_ids']; seed_values=saved['seeds']; labels=saved['labels']; tickers=saved['tickers']
        for scenario,candidate in selected.items():
            for seed in [42,43,44,45,46]:
                indices=np.flatnonzero((ids==candidate['candidate_id'])&(seed_values==seed))
                if len(indices)!=1:
                    raise ValueError('Missing or duplicated search fit for replay')
                actual=assignments[(assignments.scenario==scenario)&(assignments.decision_date=='2025-06-30')&
                                   (assignments.seed==seed)].set_index('ticker').loc[tickers,'cluster'].to_numpy()
                np.testing.assert_array_equal(labels[indices[0]],actual)
                initial=search_scores.loc[(candidate['candidate_id'],seed)]
                replay=all_scores[(all_scores.scenario==scenario)&(all_scores.decision_date=='2025-06-30')&(all_scores.seed==seed)].iloc[0]
                for metric in numeric[:4]:
                    np.testing.assert_allclose(initial[metric],replay[metric],rtol=1e-7,atol=1e-6)
                replay_count+=1
    write_json(report/'optimization_replay_verification.json',dict(status='passed',source_run=run_id,
               independent_refits_checked=replay_count,labels='exact',numeric_metrics=4,rtol=1e-7,atol=1e-6))
    champions=[]
    fig,axes=plt.subplots(1,2,figsize=(13,5))
    for i,(scenario,geometry) in enumerate([('paper_style_k8','embedding'),('common_features_k8','features')]):
        ranked=pd.read_csv(source/f'ranking_{scenario}.csv')
        sil,db=f'silhouette_{geometry}_mean',f'davies_bouldin_{geometry}_mean'
        for criterion,index in [('highest_silhouette',ranked[sil].idxmax()),('lowest_db',ranked[db].idxmin())]:
            champions.append(dict(scenario=scenario,criterion=criterion,**ranked.loc[index].to_dict()))
        ax=axes[i]
        for algorithm,group in ranked.groupby('algorithm'):
            ax.scatter(group[sil],group[db],s=15,alpha=.5,label=algorithm)
        frontier=ranked[ranked.pareto_optimal].sort_values(sil)
        ax.plot(frontier[sil],frontier[db],color='grey',linestyle='--',linewidth=1,label='Pareto frontier')
        winner=ranked.iloc[0]
        ax.scatter([winner[sil]],[winner[db]],marker='*',s=180,color='red',label='Joint selection',zorder=5)
        baseline_id=selected['baseline']['candidate_id']
        baseline=ranked[ranked.candidate_id==baseline_id].iloc[0]
        ax.scatter([baseline[sil]],[baseline[db]],marker='D',s=65,color='black',label='Fixed baseline',zorder=4)
        ax.set_xlabel('Mean silhouette (higher better)')
        ax.set_ylabel('Mean Davies-Bouldin (lower better)')
        ax.set_title(f'June 2025, k=8, {geometry} geometry')
        ax.legend(fontsize=7)
    fig.tight_layout();fig.savefig(report/'optimization_silhouette_db.png',dpi=170);plt.close(fig)
    pd.DataFrame(champions).to_csv(report/'optimization_metric_champions.csv',index=False)
    # Raw search seed agreement includes the -1 state. Provide an explicitly
    # non-noise comparison so it cannot be mistaken for ordinary cluster stability.
    registry=pd.read_csv(source/'candidate_configurations.csv')
    db_ids=set(registry.loc[registry.algorithm=='dbscan','candidate_id'])
    noise_rows=[]
    with np.load(source/'selection_assignments.npz',allow_pickle=False) as saved:
        candidate_ids=saved['candidate_ids']; seeds=saved['seeds']; labels=saved['labels']
        for cid in sorted(db_ids):
            indices=np.flatnonzero(candidate_ids==cid)
            for ia,ib in combinations(indices,2):
                noise_rows.append(dict(candidate_id=cid,seed_a=int(seeds[ia]),seed_b=int(seeds[ib]),
                                       **nonnoise_agreement(labels[ia],labels[ib])))
    pd.DataFrame(noise_rows).to_csv(report/'optimization_dbscan_nonnoise_stability.csv',index=False)
    families=[]
    summary=pd.read_csv(source/'candidate_summary.csv')
    for rep,algorithm in sorted(set(zip(summary.representation,summary.algorithm))):
        try:
            ranked=select_family(summary,rep,algorithm)
            families.append(dict(family_representation=rep,family_algorithm=algorithm,status='eligible',**ranked.iloc[0].to_dict()))
        except ValueError:
            families.append(dict(family_representation=rep,family_algorithm=algorithm,status='no full-coverage, valid five-seed candidate'))
    pd.DataFrame(families).to_csv(report/'optimized_nine_family_comparison.csv',index=False)
    # Membership panel keeps dense UMAP tickers readable without shifting points.
    from textwrap import fill
    folder=source/'paper_style_k8/2025-06-30'
    members=pd.read_csv(folder/'assignments.csv')
    with np.load(folder/'arrays.npz',allow_pickle=False) as saved:
        z=saved['embedding']; y=saved['labels']
    fig,(ax,panel)=plt.subplots(1,2,figsize=(13,7),gridspec_kw={'width_ratios':[2,1]})
    scatter=ax.scatter(z[:,0],z[:,1],c=y,cmap='tab10',s=45)
    for label in sorted(np.unique(y)):
        xy=z[y==label].mean(axis=0)
        ax.annotate(str(label),xy,fontsize=11,fontweight='bold',bbox=dict(facecolor='white',alpha=.8,edgecolor='none'))
    panel.axis('off')
    for i,label in enumerate(sorted(np.unique(y))):
        group=members[members.cluster==label]
        names=[r.ticker+('*' if r.fundamentals_imputed or r.volume_imputed else '') for r in group.itertuples()]
        panel.text(0,.97-i*.115,f'Cluster {label} (n={len(group)})',fontsize=10,fontweight='bold',
                   color=scatter.cmap(scatter.norm(label)),va='top')
        panel.text(0,.93-i*.115,fill(', '.join(names),width=36),fontsize=10,va='top')
    panel.text(0,.02,'* model-only imputation',fontsize=9)
    row=all_scores[(all_scores.scenario=='paper_style_k8')&(all_scores.decision_date=='2025-06-30')&(all_scores.seed==42)].iloc[0]
    ax.set_title(f'UMAP + complete/Manhattan, k=8, June 2025\nSeed 42: silhouette={row.silhouette_embedding:.3f}, DB={row.davies_bouldin_embedding:.3f}',fontsize=11)
    ax.set_xlabel('UMAP coordinate 1 (independent date fit)'); ax.set_ylabel('UMAP coordinate 2')
    fig.tight_layout();fig.savefig(report/'optimized_cluster_map_june2025.png',dpi=160);plt.close(fig)
    lines=['# Joint silhouette and Davies-Bouldin optimisation','',
           f'Completed run: `{run_id}`. See `docs/decisions/003-silhouette-db-search.md` for the protocol.',
           'Higher silhouette and lower DB are better. Values below average seeds 42–46.','',
           '## Selected configurations','']
    for scenario,candidate in selected.items():
        lines.append(f'- **{scenario}**: {candidate["representation"]["name"]} {candidate["representation"]["params"]}; '
                     f'{candidate["clustering"]["algorithm"]} {candidate["clustering"]["params"]}.')
    lines+=['','## June 2025 joint selections and fixed baseline','',
        '| Scenario | Silhouette (embedding) | DB (embedding) | Silhouette (features) | DB (features) | Clusters |',
        '| --- | ---: | ---: | ---: | ---: | ---: |']
    for scenario in selected:
        r=table[(table.scenario==scenario)&(table.decision_date=='2025-06-30')].iloc[0]
        lines.append(f'| {scenario} | {r.silhouette_embedding_mean:.4f} | {r.davies_bouldin_embedding_mean:.4f} | '
                     f'{r.silhouette_features_mean:.4f} | {r.davies_bouldin_features_mean:.4f} | {r.n_clusters_mean:g} |')
    lines+=['','## Frozen paper-style k=8 selection across dates','',
            '| Date | Silhouette (embedding) | DB (embedding) | Silhouette (features) | DB (features) |',
            '| --- | ---: | ---: | ---: | ---: |']
    for _,r in table[table.scenario=='paper_style_k8'].sort_values('decision_date').iterrows():
        lines.append(f'| {r.decision_date} | {r.silhouette_embedding_mean:.4f} | {r.davies_bouldin_embedding_mean:.4f} | '
                     f'{r.silhouette_features_mean:.4f} | {r.davies_bouldin_features_mean:.4f} |')
    lines+=['','## How to read this selection','',
        'The grid contains 1,426 configurations and 7,130 selection fits. Selection used June 2025 only. '
        'Later snapshots are descriptive refits of the chosen settings, not newly tuned configurations or untouched validation.',
        '',f'All {replay_count} independently refitted June winner/baseline seed fits reproduced exact assignments and '
        'all four numerical quality metrics within rtol=1e-7, atol=1e-6. See `optimization_replay_verification.json`.',
        '','Both scores enter the declared equal-rank joint rule. Pareto frontiers and individual metric champions '
        'are retained, so a trade-off is visible rather than calling one score alone optimal.',
        '','The paper-style winner optimises scores in each representation. The common-feature winner checks '
        'whether the chosen labels separate in the same financial space. PCA95 may have more than two dimensions.',
        '','The source paper reports silhouette 0.5023 and DB 0.5296 on a different 2023–2024 sample and eleven features. '
        'The new scores cannot be called a controlled improvement on that old experiment.',
        '','Full coverage and valid scores on all five selection seeds are required for eligibility. DBSCAN noise and '
        'all rejected/degenerate configurations remain in the search tables. Sector agreement is report-only.',
        '','Raw `selection_seed_stability.csv` measures agreement of all assignment states, including the DBSCAN -1 sentinel. '
        'Use `optimization_dbscan_nonnoise_stability.csv` for ordinary DBSCAN cluster agreement conditional on firms '
        'non-noise in both seeds, with coverage explicitly shown. All eligible winners have full selection-date coverage, '
        'so noise cannot influence their ranking/tie-break.',
        '','The baseline pointer remains unpromoted. Source-evidence limitations remain; internal quality is not investment usefulness.']
    (report/'optimization_results.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    write_json(report/'optimization_report_source.json',dict(run_id=run_id,artifact_manifest_sha256=digest(source/'artifact_checksums.json'),
               selection_date='2025-06-30',score_summary='five-seed means and standard deviations',baseline_promoted=False))
    print(table[table.decision_date=='2025-06-30'][['scenario','silhouette_embedding_mean','davies_bouldin_embedding_mean',
                  'silhouette_features_mean','davies_bouldin_features_mean','n_clusters_mean']].to_string(index=False))


def select_family(summary,representation,algorithm):
    from optimize_models import select
    ranked=select(summary,'embedding',None if algorithm=='dbscan' else 8)
    family=ranked[(ranked.representation==representation)&(ranked.algorithm==algorithm)]
    if family.empty:
        raise ValueError('No eligible candidate in family')
    return family


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_id')
    build(parser.parse_args().run_id)
