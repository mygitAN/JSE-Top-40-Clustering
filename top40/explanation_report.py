"""Read-only cluster/constituent explanation bundle from a verified completed run.

No models, scalers or SHAP explainers are fitted. Raw local ids and aligned
history ids are separate keys. SHAP explains a date-specific surrogate, not a
causal mechanism or a longitudinal change in SHAP values.
"""
import argparse
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from .features import get_feature_set
from .tracking import digest, verify


def transition_tables(members, profiles):
    """Include stable constituents as well as movers; keep index entries/exits separate."""
    rows, changes, definitions = [], [], []
    for model, data in members.groupby('study_model', sort=False):
        dates = sorted(data.decision_date.unique())
        for before, after in zip(dates, dates[1:]):
            old = data[data.decision_date == before]
            new = data[data.decision_date == after]
            ids = sorted(set(old.aligned_cluster) | set(new.aligned_cluster))
            all_old, all_new = set(old.ticker), set(new.ticker)
            for cluster in ids:
                a = set(old.loc[old.aligned_cluster == cluster, 'ticker'])
                b = set(new.loc[new.aligned_cluster == cluster, 'ticker'])
                definitions.append(dict(study_model=model, before=before, after=after,
                    aligned_cluster=cluster, members_before=', '.join(sorted(a)), members_after=', '.join(sorted(b)),
                    retained=', '.join(sorted(a & b)), joined_from_other_clusters=', '.join(sorted((b-a)&all_old)),
                    left_for_other_clusters=', '.join(sorted((a-b)&all_new)),
                    index_entries=', '.join(sorted(b-all_old)), index_exits=', '.join(sorted(a-all_new)),
                    n_before=len(a), n_after=len(b)))
            for ticker in sorted(all_old & all_new):
                a = old[old.ticker == ticker].set_index('feature')
                b = new[new.ticker == ticker].set_index('feature').reindex(a.index)
                source, destination = int(a.aligned_cluster.iloc[0]), int(b.aligned_cluster.iloc[0])
                key = dict(study_model=model, before=before, after=after, ticker=ticker,
                           from_aligned_cluster=source, to_aligned_cluster=destination,
                           from_raw_cluster=int(a.raw_cluster.iloc[0]), to_raw_cluster=int(b.raw_cluster.iloc[0]),
                           aligned_move=source != destination)
                delta = b.scaled_value-a.scaled_value
                rows.append(dict(**key, company=b.company.iloc[0],
                    largest_scaled_changes='; '.join(f'{a.loc[f,"feature_label"]}: {delta[f]:+.4f}'
                        for f in delta.abs().sort_values(ascending=False).index[:3]),
                    surrogate_oof_accuracy_before=a.surrogate_oof_accuracy.iloc[0],
                    surrogate_oof_accuracy_after=b.surrogate_oof_accuracy.iloc[0]))
                for feature in a.index:
                    # Leave the focal constituent out of both comparison peer groups.
                    peers = new[(new.feature == feature)&(new.ticker != ticker)]
                    destination_peers = peers[peers.aligned_cluster == destination]
                    original_peers = set(old[(old.feature == feature)&(old.aligned_cluster == source)].ticker)-{ticker}
                    original_peer_values = peers[peers.ticker.isin(original_peers)]
                    changes.append(dict(**key, feature=feature, feature_label=a.loc[feature,'feature_label'],
                        value_before=a.loc[feature,'raw_value'], value_after=b.loc[feature,'raw_value'],
                        raw_change=b.loc[feature,'raw_value']-a.loc[feature,'raw_value'],
                        scaled_before=a.loc[feature,'scaled_value'], scaled_after=b.loc[feature,'scaled_value'],
                        scaled_change=delta[feature],
                        destination_peers_median_after=destination_peers.scaled_value.median(),
                        original_peers_median_after=original_peer_values.scaled_value.median(),
                        destination_peer_count=len(destination_peers), original_peer_count=len(original_peer_values),
                        own_class_shap_before=a.loc[feature,'own_class_shap'],
                        own_class_shap_after=b.loc[feature,'own_class_shap'],
                        same_date_destination_minus_source_shap=b.loc[feature,'destination_minus_source_shap']
                            if source != destination else np.nan))
    evolution = pd.DataFrame(definitions)
    # Profile changes combine constituent changes AND membership composition changes.
    deltas = []
    for item in definitions:
        p = profiles[(profiles.study_model==item['study_model']) &
                     (profiles.cluster==item['aligned_cluster'])]
        a = p[p.decision_date==item['before']].set_index('feature')
        b = p[p.decision_date==item['after']].set_index('feature')
        for feature in sorted(set(a.index)|set(b.index)):
            av = a.loc[feature,'deviation_scaled'] if feature in a.index else np.nan
            bv = b.loc[feature,'deviation_scaled'] if feature in b.index else np.nan
            deltas.append(dict(study_model=item['study_model'], before=item['before'], after=item['after'],
                aligned_cluster=item['aligned_cluster'], feature=feature,
                deviation_before=av, deviation_after=bv, deviation_change=bv-av,
                interpretation='Profile change includes membership composition and constituent feature changes'))
    return pd.DataFrame(rows), pd.DataFrame(changes), evolution, pd.DataFrame(deltas)


def cluster_diagram(group, profile, quality, path):
    from . import plots
    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize
    order = group.groupby('feature').own_class_shap.apply(lambda s:s.abs().mean()).sort_values().index
    labels = group.drop_duplicates('feature').set_index('feature').feature_label
    fig, axes = plt.subplots(1,2,figsize=(15,7))
    p = profile.set_index('feature').reindex(order)
    axes[0].barh(range(len(order)),p.deviation_scaled,color=np.where(p.deviation_scaled>=0,'#bf553d','#287baa'))
    axes[0].axvline(0,color='grey',lw=.8)
    axes[0].set_yticks(range(len(order)),labels.loc[order])
    axes[0].set_xlabel('Cluster median minus date median (scaled feature units)')
    axes[0].set_title('Observed cluster definition')
    for y,feature in enumerate(order):
        g=group[group.feature==feature].sort_values('ticker')
        jitter=np.linspace(-.18,.18,len(g)) if len(g)>1 else [0]
        scatter=axes[1].scatter(g.own_class_shap,y+np.asarray(jitter),c=g.feature_colour,
                               cmap='coolwarm',norm=Normalize(0,1),s=40,edgecolor='white',linewidth=.3)
    axes[1].set_yticks(range(len(order)),labels.loc[order])
    axes[1].axvline(0,color='grey',lw=.8)
    axes[1].set_title('Member SHAP for this cluster class; one dot per member')
    axes[1].set_xlabel('Surrogate raw-margin contribution; positive supports class')
    fig.colorbar(scatter,ax=axes[1],label='Feature value: low to high within date (0-1)')
    first=group.iloc[0];oof=first.surrogate_oof_accuracy
    fidelity=f'{oof:.3f}' if pd.notna(oof) else 'not estimable'
    fig.suptitle(f'{first.study_model}, {first.decision_date}: aligned cluster {first.aligned_cluster} '
                 f'(raw {first.raw_cluster}); n={group.ticker.nunique()}\n'
                 f'Surrogate out-of-fold accuracy: {fidelity}\n{plots.score_line(quality)}',fontsize=10)
    fig.text(.5,.02,'Members: '+', '.join(sorted(group.ticker.unique()))+
             '\nSeparate surrogate per date. SHAP is not a causal explanation or a cross-date effect.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.09,1,.84))
    plots._save(fig,path)


def constituent_diagram(group, path):
    """Every continuing name gets a figure, including stable peers such as Shoprite."""
    import matplotlib.pyplot as plt
    from . import plots
    group=group.sort_values('scaled_change',key=lambda s:s.abs())
    y=np.arange(len(group));first=group.iloc[0]
    fig,axes=plt.subplots(1,2,figsize=(15,7),sharey=True)
    axes[0].scatter(group.scaled_before,y,facecolors='white',edgecolors='black',label='Constituent before')
    axes[0].scatter(group.scaled_after,y,color='black',label='Constituent after')
    for i,row in enumerate(group.itertuples()):
        axes[0].annotate('',xy=(row.scaled_after,i),xytext=(row.scaled_before,i),arrowprops=dict(arrowstyle='->',color='black'))
    axes[0].scatter(group.original_peers_median_after,y,marker='x',color='#287baa',label='Original peers after (excludes focal name)')
    axes[0].scatter(group.destination_peers_median_after,y,marker='D',color='#bf553d',label='Destination peers after (excludes focal name)')
    axes[0].set_yticks(y,group.feature_label)
    axes[0].set_xlabel('Scaled value; unchanged June 2025 scaler')
    axes[0].set_title('Constituent change and peer context')
    axes[0].legend(loc='upper center',bbox_to_anchor=(.5,-.15),fontsize=8,ncol=1)
    axes[1].barh(y,group.own_class_shap_after,color=np.where(group.own_class_shap_after>=0,'#bf553d','#287baa'))
    axes[1].axvline(0,color='grey',lw=.8)
    axes[1].set_xlabel('AFTER surrogate SHAP, assigned cluster class')
    axes[1].set_title('Features supporting/opposing the AFTER assignment')
    label='aligned move' if first.aligned_move else 'stable aligned membership'
    fig.suptitle(f'{first.study_model}: {first.ticker}, {first.before} to {first.after}\n'
                 f'Aligned {first.from_aligned_cluster} to {first.to_aligned_cluster}: {label}; '
                 f'raw labels {first.from_raw_cluster} to {first.to_raw_cluster}',fontsize=12)
    fig.text(.5,.01,'Descriptive feature changes and surrogate attribution; no causal reason is identified. Empty peer groups have undefined medians.',ha='center',fontsize=9)
    fig.subplots_adjust(left=.15,right=.98,bottom=.27,top=.78,wspace=.1)
    plots._save(fig,path)


def build_report(run_folder, output):
    """Build a new derived bundle without modifying any archived run artifact."""
    run,output=Path(run_folder).resolve(),Path(output).resolve()
    if output==run or run in output.parents or output in run.parents:
        raise ValueError('Choose a separate report directory outside the source run')
    verify(run)
    status=json.loads((run/'status.json').read_text())
    if status['status']!='completed' or not (run/'COMPLETED').is_file():
        raise ValueError('Source must be completed')
    if (run/'COMPLETED').read_text().strip()!=digest(run/'artifact_checksums.json'):
        raise ValueError('Invalid completion marker')
    output.mkdir(parents=True,exist_ok=False)
    config=status['resolved_configuration'];features=get_feature_set(config['feature_set'])
    members=[];profiles=[];summaries=[];inputs={}
    def read_csv(relative):
        path=run/relative;inputs[relative]=digest(path);return pd.read_csv(path)
    quality=read_csv('primary_model_summary.csv')
    for model in config['primary_models']:
        history=read_csv(f'longitudinal/{model}/cluster_histories.csv').set_index('ticker')
        maps={}
        for date in config['dates']:
            frame=read_csv(f'models/{model}/{date}/assignments.csv')
            maps[date]={int(r.cluster):int(history.loc[r.ticker,date]) for r in frame.itertuples()}
        profile=read_csv(f'longitudinal/{model}/moves/cluster_profiles.csv')
        summary=read_csv(f'longitudinal/{model}/moves/cluster_summary.csv')
        profiles.append(profile);summaries.append(summary)
        prior_date=None
        for date in config['dates']:
            folder=run/'models'/model/date
            frame=read_csv(f'models/{model}/{date}/assignments.csv').set_index('ticker')
            paths=[folder/'arrays.npz',folder/'shap_values.npz']
            for path in paths:inputs[path.relative_to(run).as_posix()]=digest(path)
            with np.load(paths[0],allow_pickle=False) as arrays,np.load(paths[1],allow_pickle=False) as saved:
                tickers=arrays['tickers'].astype(str);columns=arrays['features'].astype(str)
                assert list(columns)==list(features.columns)
                positions={t:i for i,t in enumerate(saved['tickers'].astype(str))}
                classes={int(c):i for i,c in enumerate(saved['cluster_labels'])}
                np.testing.assert_allclose(saved['values'].sum(1)+saved['base_values'],saved['raw_margins'],atol=1e-4,rtol=0)
                minimum=arrays['scaled_features'].min(0);spread=np.ptp(arrays['scaled_features'],axis=0)
                for i,ticker in enumerate(tickers):
                    row=frame.loc[ticker];raw=int(row.cluster);aligned=maps[date][raw]
                    source_aligned=int(history.loc[ticker,prior_date]) if prior_date and pd.notna(history.loc[ticker,prior_date]) else None
                    source_raw=next((r for r,a in maps[date].items() if a==source_aligned),None)
                    for j,feature in enumerate(columns):
                        v=saved['values'][positions[ticker],j,classes[raw]]
                        contrast=(v-saved['values'][positions[ticker],j,classes[source_raw]]) if source_raw is not None else np.nan
                        members.append(dict(study_model=model,decision_date=date,ticker=ticker,company=row.company,
                            raw_cluster=raw,aligned_cluster=aligned,feature=feature,feature_label=features.label(feature),
                            raw_value=row[feature],scaled_value=arrays['scaled_features'][i,j],own_class_shap=v,
                            destination_minus_source_shap=contrast,
                            feature_colour=(arrays['scaled_features'][i,j]-minimum[j])/spread[j] if spread[j]>0 else .5,
                            surrogate_oof_accuracy=quality[(quality.study_model==model)&(quality.decision_date==date)].oof_accuracy.iloc[0],
                            data_caveat='; '.join(flag for flag in ['fundamentals_imputed','volume_imputed','volume_corrected']
                                                  if flag in row and pd.notna(row[flag]) and bool(row[flag]))))
            prior_date=date
    member=pd.DataFrame(members);profile=pd.concat(profiles,ignore_index=True);summary=pd.concat(summaries,ignore_index=True)
    label_map=member[['study_model','decision_date','aligned_cluster','raw_cluster']].drop_duplicates()
    summary=summary.merge(label_map.rename(columns={'aligned_cluster':'cluster'}),on=['study_model','decision_date','cluster'],validate='one_to_one')
    transitions,details,evolution,changes=transition_tables(member,profile)
    # Carry the full source/destination definitions into every transition row.
    for side,date_key,cluster_key in [('source','before','from_aligned_cluster'),('destination','after','to_aligned_cluster')]:
        definition=summary[['study_model','decision_date','cluster','members','defining_features','shap_top_features']].rename(
            columns={'decision_date':date_key,'cluster':cluster_key,
                     **{c:f'{side}_{c}' for c in ['members','defining_features','shap_top_features']}})
        transitions=transitions.merge(definition,on=['study_model',date_key,cluster_key],how='left',validate='many_to_one')
        definition=profile[['study_model','decision_date','cluster','feature','cluster_median','deviation_scaled','mean_abs_shap','mean_signed_shap']].rename(
            columns={'decision_date':date_key,'cluster':cluster_key,
                     **{c:f'{side}_{c}' for c in ['cluster_median','deviation_scaled','mean_abs_shap','mean_signed_shap']}})
        details=details.merge(definition,on=['study_model',date_key,cluster_key,'feature'],how='left',validate='many_to_one')
    tables={'member_feature_shap':member,'cluster_feature_profiles':profile,'cluster_definitions':summary,
            'constituent_transitions':transitions,'constituent_feature_changes':details,
            'cluster_membership_changes':evolution,'cluster_profile_changes':changes}
    for name,table in tables.items():table.to_csv(output/f'{name}.csv',index=False)
    # A single long table is convenient for an agent: repeat transition context beside each numeric feature row.
    agent=details.merge(transitions,on=[c for c in transitions.columns if c in details.columns],validate='many_to_one')
    agent['explanation_basis']='Observed feature/peer changes and date-specific surrogate attribution; not causal'
    agent['shap_units']='Surrogate raw-margin contributions, not probabilities or returns'
    agent.to_csv(output/'agent_evidence.csv',index=False)
    for (model,date,cluster),group in member.groupby(['study_model','decision_date','aligned_cluster']):
        p=profile[(profile.study_model==model)&(profile.decision_date==date)&(profile.cluster==cluster)]
        q=quality[(quality.study_model==model)&(quality.decision_date==date)].iloc[0].to_dict()
        cluster_diagram(group,p,q,output/f'cluster_{model}_{date}_{cluster}.png')
    for (model,before,after,ticker),group in details.groupby(['study_model','before','after','ticker']):
        constituent_diagram(group,output/f'constituent_{model}_{before}_{after}_{ticker}.png')
    for model in config['primary_models']:
        for path in (run/f'longitudinal/{model}/moves').glob('move_*.png'):
            shutil.copyfile(path,output/f'{model}_{path.name}')
    guide='''# Cluster and constituent explanation evidence

All numbers come from one completed saved run. No fits, SHAP evaluations or metric
recalculations. Cluster ids in histories are aligned; raw ids in scatter maps are
local to a date. Always identify model, date and label basis when describing a move.

- cluster_definitions.csv: members and top defining features per aligned cluster/date.
- cluster_feature_profiles.csv: every feature median/deviation, mean signed/absolute SHAP and fidelity.
- member_feature_shap.csv: every constituent/feature, raw/scaled value, signed own-class SHAP and both label ids.
- cluster_membership_changes.csv: retained members, arrivals/departures from other clusters, index entries/exits.
- cluster_profile_changes.csv: profile changes; combines changing inputs and changing membership composition.
- constituent_transitions.csv: every continuing constituent, including stable names, with raw and aligned ids.
- constituent_feature_changes.csv: numeric changes and leave-one-out peer references for every feature.
- agent_evidence.csv: long feature table joined to the transition summary for machine-assisted writing.

SHAP values are raw-margin contributions from a different surrogate at each date.
Do not subtract before/after SHAP as a temporal causal effect. The same-date destination
minus source SHAP is a class contrast in the AFTER surrogate; it is undefined when the
old aligned class disappeared. Leave-one-out peer medians are undefined for empty sets.
OOF fidelity measures reproduction of cluster labels, not financial validity.
Cluster changes can reflect fitting variability, membership composition and input
changes. A raw label change alone is not a peer-group move. No causal claim is established.
'''
    (output/'README.md').write_text(guide,encoding='utf8')
    verify(run)
    manifest=dict(source_run=status['run_id'],source_model_commit=status.get('git_commit'),new_fits=0,
        new_shap_evaluations=0,source_inputs=inputs,
        renderer_sha256=digest(Path(__file__)),
        files={p.name:digest(p) for p in sorted(output.iterdir()) if p.is_file()})
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
    return tables


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_folder');parser.add_argument('--output',required=True)
    args=parser.parse_args();build_report(args.run_folder,args.output)


if __name__=='__main__':
    main()
