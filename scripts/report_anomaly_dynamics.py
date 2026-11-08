"""Derived reporting amendment: separate signal histories and varying-k sensitivity."""
import argparse
import json
import os
from itertools import combinations
from pathlib import Path

from tracking import ROOT,Run,write_json,digest


def classify_pattern(values,patterns):
    import pandas as pd
    if len(values)!=3 or any(pd.isna(v) for v in values):
        return 'not eligible: missing observation or unestimable signal'
    return patterns[''.join('1' if bool(v) else '0' for v in values)]


def signal_histories(cases,dates,patterns):
    import pandas as pd
    rows=[]
    for ticker,sub in cases.groupby('ticker',sort=True):
        observations=sub.set_index('decision_date')
        for channel in ['geometric_screen','sector_divergence','joint_agreement']:
            values=[]
            for date in dates:
                if date not in observations.index:
                    values.append(None);continue
                row=observations.loc[date]
                geo=row.screen_flag;sector=row.sector_divergence
                if channel=='geometric_screen':value=geo
                elif channel=='sector_divergence':value=sector
                else:value=None if pd.isna(geo) or pd.isna(sector) else bool(geo and sector)
                values.append(None if pd.isna(value) else bool(value))
            rows.append(dict(ticker=ticker,channel=channel,**dict(zip(dates,values)),
                classification=classify_pattern(values,patterns),confirmed_outlier=False))
    return pd.DataFrame(rows)


def sensitivity_summary(metrics,stability,config):
    import numpy as np
    from optimize_models import aggregate
    table=aggregate(metrics,stability,config)
    # This sensitivity explicitly tests 2..12, rather than the older search's 2..10 eligibility cap.
    table['eligible_all_seeds']=((table.seeds==len(config['seeds']))&(table.valid_seeds==len(config['seeds']))&
        (table.coverage_min==1)&(table.n_clusters_min>=2)&(table.n_clusters_max<=12)&
        np.isfinite(table[['silhouette_embedding_mean','davies_bouldin_embedding_mean',
                          'silhouette_features_mean','davies_bouldin_features_mean']]).all(axis=1))
    return table


def varying_k(source,roles,config,out):
    import numpy as np
    import pandas as pd
    from sklearn.metrics import adjusted_rand_score,normalized_mutual_info_score
    from optimize_models import fit_cluster,quality,select
    import matplotlib.pyplot as plt
    rows=[];pairs=[];winners=[];labels_saved=[];members=[]
    models=json.loads((source/'search/selected_models.json').read_text(encoding='utf-8'))
    source_protocol=json.loads((source/'paper_manifest.json').read_text(encoding='utf-8'))['config']
    seeds=source_protocol['seeds'];dates=source_protocol['dates']
    for role in roles:
        candidate=models[role];cid=candidate['candidate_id'];directory=source/'models'/cid
        for date in dates:
            frame=pd.read_csv(directory/date/'assignments.csv')
            with np.load(directory/date/'arrays.npz') as saved:x=saved['scaled_features'];original=saved['clusters']
            local=[];local_pairs=[];fits={k:[] for k in range(2,13)}
            for seed in seeds:
                with np.load(directory/date/f'seed_{seed}_arrays.npz') as saved:
                    z=saved['embedding'];source_labels=saved['clusters']
                    if list(saved['tickers'])!=frame.ticker.tolist():raise ValueError('Source ticker order mismatch')
                for k in range(2,13):
                    spec=dict(algorithm=candidate['clustering']['algorithm'],params=dict(candidate['clustering']['params'],n_clusters=k))
                    y=fit_cluster(z,spec,seed)
                    if k==8 and not np.array_equal(y,source_labels):raise ValueError('Fixed k=8 source partition not reproduced')
                    key=f'{role}_k{k:02d}'
                    local.append(dict(candidate_id=key,role=role,decision_date=date,k=k,seed=seed,**quality(x,z,y)))
                    fits[k].append((seed,y));labels_saved.append((role,date,k,seed,y))
            for k,group in fits.items():
                for (a,ya),(b,yb) in combinations(group,2):
                    local_pairs.append(dict(candidate_id=f'{role}_k{k:02d}',role=role,decision_date=date,
                        seed_a=a,seed_b=b,ari=float(adjusted_rand_score(ya,yb)),nmi=float(normalized_mutual_info_score(ya,yb))))
            summary=sensitivity_summary(local,pd.DataFrame(local_pairs),dict(seeds=seeds))
            for geometry in ['features','embedding']:
                ranking=select(summary,geometry,None)
                chosen=str(ranking.candidate_id.iloc[0]);k=int(chosen.rsplit('_k',1)[1])
                ranking.to_csv(out/f'ranking_{role}_{date}_{geometry}.csv',index=False)
                y=fits[k][0][1]
                r=ranking.iloc[0]
                winners.append(dict(role=role,decision_date=date,geometry=geometry,selected_k=k,primary_k=8,
                    silhouette_mean=float(r[f'silhouette_{geometry}_mean']),db_mean=float(r[f'davies_bouldin_{geometry}_mean']),
                    singleton_clusters_max=int(r.singleton_clusters_max),seed_ari_mean=float(r.seed_ari_mean),
                    representative_ari_vs_primary_k8=float(adjusted_rand_score(original,y))))
                members.extend(dict(role=role,decision_date=date,geometry=geometry,ticker=t,cluster=int(c)) for t,c in zip(frame.ticker,y))
            rows.extend(local);pairs.extend(local_pairs)
        fig,axes=plt.subplots(2,3,figsize=(14,7))
        table=pd.DataFrame(rows).query('role == @role').groupby(['decision_date','k']).mean(numeric_only=True).reset_index()
        for column,date in enumerate(dates):
            sub=table[table.decision_date==date]
            for ax,metric in [(axes[0,column],'silhouette'),(axes[1,column],'davies_bouldin')]:
                for geometry,color in [('features','steelblue'),('embedding','darkorange')]:
                    ax.plot(sub.k,sub[f'{metric}_{geometry}'],marker='o',color=color,label=geometry)
                ax.axvline(8,color='gray',ls='--',label='Primary k=8');ax.set_title(date)
                ax.set_xlabel('Sensitivity k');ax.set_ylabel('Mean '+metric);ax.grid(alpha=.2)
                if column==0:ax.legend(fontsize=7)
        fig.suptitle(role+': five-seed k sensitivity; only k is selected independently at each date')
        fig.tight_layout();fig.savefig(out/f'k_sensitivity_{role}.png',dpi=145);plt.close(fig)
    pd.DataFrame(rows).to_csv(out/'varying_k_all_scores.csv',index=False)
    pd.DataFrame(pairs).to_csv(out/'varying_k_seed_stability.csv',index=False)
    winners=pd.DataFrame(winners);winners.to_csv(out/'varying_k_selected.csv',index=False)
    membership=pd.DataFrame(members);membership.to_csv(out/'varying_k_assignments.csv',index=False)
    np.savez_compressed(out/'varying_k_all_labels.npz',roles=np.array([r for r,d,k,s,y in labels_saved]),
        dates=np.array([d for r,d,k,s,y in labels_saved]),ks=np.array([k for r,d,k,s,y in labels_saved]),
        seeds=np.array([s for r,d,k,s,y in labels_saved]),labels=np.stack([y for r,d,k,s,y in labels_saved]))
    if len(rows)!=3*3*11*5:raise ValueError('Incomplete varying-k sensitivity')
    # For changing k, use the same membership-aware alignment, with no automatic reuse of primary SHAP.
    from paper_longitudinal import aligned_histories
    for role in roles:
        for geometry in ['features','embedding']:
            snapshots={d:membership[(membership.role==role)&(membership.geometry==geometry)&(membership.decision_date==d)] for d in dates}
            aligned,maps,events,histories,objective=aligned_histories(snapshots,dates)
            histories.to_csv(out/f'varying_k_histories_{role}_{geometry}.csv',index=False)
            events.to_csv(out/f'varying_k_events_{role}_{geometry}.csv',index=False)
            maps.to_csv(out/f'varying_k_alignment_{role}_{geometry}.csv',index=False)
    return winners


def derive(source,out,config):
    import pandas as pd
    from verify_paper_experiment import verify_paper
    verification=verify_paper(source)
    protocol=json.loads((source/'paper_manifest.json').read_text(encoding='utf-8'))
    roles=['common_features_k8','embedding_k8','baseline'];dates=protocol['config']['dates']
    histories=[]
    for role in roles:
        directory=source/'models'/protocol['selected_roles'][role]
        table=signal_histories(pd.read_csv(directory/'company_case_summary.csv'),dates,config['patterns'])
        table.insert(0,'role',role);histories.append(table)
    histories=pd.concat(histories,ignore_index=True);histories.to_csv(out/'signal_histories_v2.csv',index=False)
    histories.groupby(['role','channel','classification']).size().rename('instruments').to_csv(out/'signal_history_counts.csv')
    winners=varying_k(source,roles,config,out)
    write_json(out/'reporting_manifest.json',dict(protocol=config,source_run=source.name,
        source_manifest_sha256=digest(source/'artifact_checksums.json'),source_verified_artifacts=verification['verified_artifacts'],
        model_features=10,instruments_per_date=41,economic_groups_per_date=40,
        independent_sample_size_increased=False,primary_models_refitted=False,
        sensitivity_clustering_fits=495,representations_refitted=False,primary_k=8,
        amendment_after_existing_results=True,confirmed_outliers=0,promotion=False))
    write_report(out,source,histories,winners,config,protocol)


def write_report(out,source,histories,winners,config,protocol):
    import pandas as pd
    primary=histories[histories.role=='common_features_k8']
    lines=['# Tracking structural signals across repeated equity screenings','',
        'Working reporting example, not a submission-ready manuscript. This reporting amendment was written after the existing results were examined.',
        '', '## Contribution and study design','',
        'This study develops an interpretable repeated cross-sectional equity-screening framework for tracking changes in peer relationships and distinguishing emerging, persistent and resolving structural signals. It examines the financial characteristics associated with those changes, while distinguishing geometric outlier flags from sector divergence.',
        '', 'The framework is applied at three decision dates: 30 June 2025, 31 December 2025 and 30 June 2026. Each cross-section contains 41 listed instruments representing 40 company groups because Investec Limited and Investec plc form one dual-listed group. Membership is determined separately at each date. The 123 instrument-date records do not constitute 123 independent firms, and the trailing market windows overlap.',
        '', 'The historic-consensus-excluded implementation has ten features, with earnings yield replacing P/E; it is not identical to the original eleven-feature design. Strict point-in-time information availability remains the target. Current reconstructed share counts, market capitalisations, sector history and vendor series do not establish a fully verified historical information set.',
        '', '## Experimentation supports the interpretation','',
        'The primary analysis retains k=8 and the settings selected from June 2025. The earlier exhaustive finite grid contains 3,268 configurations over five seeds, with silhouette and Davies-Bouldin reported jointly in both embedding and common financial-feature spaces. Exact distance, linkage, reduction and algorithm parameters remain in the original experiment archive. These are criterion-dependent finite-grid optima, not a universal best model.',
        '', 'A separate sensitivity varies k from 2 to 12 independently at each decision date for the three existing main models. It holds representation settings and other clustering parameters fixed, reuses the saved five-seed representations, and performs 495 clustering fits. This isolates the effect of cluster count; it is not a new full retuning of every algorithm and reduction at each date. The primary k=8 classifications and SHAP results are unchanged.',
        '', '| Model role | Scoring criterion | June 2025 k | December 2025 k | June 2026 k |',
        '| --- | --- | ---: | ---: | ---: |']
    for (role,geometry),sub in winners.groupby(['role','geometry'],sort=True):
        ks=sub.set_index('decision_date').loc[protocol['config']['dates'],'selected_k'].tolist()
        lines.append(f'| {role} | {geometry} | {ks[0]} | {ks[1]} | {ks[2]} |')
    lines+=['','## From cluster changes to signal histories','',
        'A changed cluster is not automatically an anomaly. Three signals are reported separately: a geometric screen flag, contextual sector divergence, and agreement between those two signals. Cluster shifts and stability are a separate membership history. Unknown sector comparisons, singletons, ties and missing membership are not treated as normal observations.',
        '', '| Pattern: first, second, third decision date | Reporting classification |',
        '| --- | --- |']
    for pattern,label in config['patterns'].items():
        lines.append('| '+' -> '.join('flagged' if x=='1' else 'not flagged' for x in pattern)+f' | {label} |')
    lines+=['','These labels refine the earlier reporting taxonomy: 100 is now resolved, 110 remains resolving, and 011 is emerging and sustained. The amendment is explicitly post hoc for these already analysed data; the old immutable results are not relabelled or described as prospectively prespecified.',
        '', '## What the current primary results show','']
    for channel in config['channels']:
        lines.append(f'**{channel.replace("_"," ")}**')
        table=primary[primary.channel==channel]
        for classification,sub in table.groupby('classification',sort=True):
            lines.append(f'- {classification} ({len(sub)}): '+', '.join(sub.ticker)+'.')
        lines.append('')
    lines+=['For example, ANH and BHG are flagged geometrically at the first decision date but not at the subsequent two dates. Under this reporting taxonomy their geometric signals are **resolved**. SSW is flagged only at the middle date and is therefore **transient**. GLN is flagged at the two later dates, but is absent from the first cross-section: it is not assigned a three-date persistent classification.',
        '', 'These are histories of descriptive screen flags, not confirmed economic anomalies. The Hotelling-style F threshold is a descriptive reference for individual squared distances in learned coordinates, not a calibrated significance test. Repeating deterministic PCA/hierarchical fits over seeds does not provide independent confirmations. Sector divergence refers to the legacy sector comparator and does not prove that a firm is in a wrong true cluster.',
        '', '## Financial-profile interpretation','',
        'The case question is: what changed in a firm\'s financial profile when its peer relationship changed? Report the observed feature changes, cluster profiles and their SHAP associations together. The frozen 2025 classifier provides an additive comparison within the same function; independently refitted per-date SHAP values must not be subtracted as if they came from one model. A separate regression surrogate describes associations with the distance screen itself.',
        '', 'The original primary model has 29 instruments stable at all three dates and 10 that shift at least once. The individual lists and case reports remain in the source archive. These counts describe reproducibly aligned memberships rather than an increase in independent sample size. Weak surrogate fidelity and imputed values constrain interpretation; in particular, the latest distance-surrogate OOF R-squared is negative. SHAP does not establish a causal explanation or confirm an outlier.',
        '', '## Reporting boundary','',
        'The defensible contribution is repeated interpretable screening and the description of signal histories across three decision dates. It is not return prediction, confirmed anomaly detection, proof of distinct market regimes, or fully certified point-in-time empirical evidence. Source-backed historical validation and substantive case corroboration remain necessary.',
        '', f'Source experiment: `{source.name}`. This derived report contains no primary model refits and no baseline promotion.']
    (out/'anomaly_dynamics_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-id');args=parser.parse_args()
    for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS']:os.environ.setdefault(key,'1')
    os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.runtime/matplotlib'))
    config=json.loads((ROOT/'configs/anomaly_dynamics_reporting_v2.json').read_text(encoding='utf-8'))
    source=ROOT/'experiments/runs'/config['source_run']
    with Run(ROOT/'experiments',config,config['experiment'],'User-example reporting style; separate signal dynamics and varying-k sensitivity',args.run_id) as run:
        run.provenance();derive(source,run.out,config)
        run.meta['metric_artifacts']=['signal_histories_v2.csv','varying_k_all_scores.csv','varying_k_selected.csv']
    print(f'Completed {run.meta["run_id"]}: {run.out}',flush=True)


if __name__=='__main__':main()
