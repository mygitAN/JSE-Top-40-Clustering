"""Membership-aware descriptions; neither geometric screens nor SHAP confirm causes."""
import json
from itertools import combinations
from pathlib import Path

from tracking import write_json


def hotelling_screen(z, alpha=.05):
    """Individual D² with an explicitly descriptive mean-T² F reference.

    No n multiplier is applied to individual distances. The F cutoff is not
    their null distribution, especially on data-adaptive manifold coordinates.
    """
    import numpy as np
    from scipy.stats import f,beta
    z=np.asarray(z,dtype=float)[:,:2];n,p=z.shape
    if p!=2 or n<=p+1 or not np.isfinite(z).all():raise ValueError('Need finite n>p+1, two coordinates')
    center=z.mean(axis=0);cov=np.cov(z,rowvar=False,ddof=1)
    cutoff=float(p*(n-1)/(n-p)*f.ppf(1-alpha,p,n-p))
    internal=float((n-1)**2/n*beta.ppf(1-alpha,p/2,(n-p-1)/2))
    if np.linalg.matrix_rank(cov)<p or np.linalg.cond(cov)>1e12:
        return np.full(n,np.nan),dict(n=n,p=p,alpha=alpha,f_reference=cutoff,
            internal_beta_reference=internal,status='not estimable: singular/ill-conditioned covariance')
    delta=z-center;dist=np.einsum('ij,jk,ik->i',delta,np.linalg.inv(cov),delta)
    return dist,dict(n=n,p=p,alpha=alpha,f_reference=cutoff,internal_beta_reference=internal,
        status='descriptive only; no calibrated individual significance test',center=center.tolist(),covariance=cov.tolist())


def screen_history(values):
    """All three observations required: membership gaps cannot resolve a flag."""
    if len(values)!=3 or any(v is None for v in values):return 'not eligible: missing observation/screen'
    pattern=tuple(bool(v) for v in values)
    return {(False,False,False):'never flagged',(True,True,True):'persistent',
            (False,False,True):'emerging',(False,True,True):'emerging',
            (False,True,False):'transient',(True,False,False):'resolving',
            (True,True,False):'resolving',(True,False,True):'recurring'}[pattern]


def sector_context(frame):
    """Leave-one-out cluster majority; ties/singletons are explicitly unresolved."""
    import pandas as pd
    rows=[]
    for row in frame.itertuples():
        other=frame[(frame.cluster==row.cluster)&(frame.ticker!=row.ticker)]
        counts=other.sector_label.value_counts()
        mode=sorted(counts[counts==counts.max()].index) if len(counts) else []
        status='not estimable: singleton' if not mode else 'ambiguous: tied majority' if len(mode)>1 else 'contextual comparison'
        rows.append(dict(ticker=row.ticker,cluster=int(row.cluster),sector_label=row.sector_label,
            other_member_majority='; '.join(mode),sector_divergence=(row.sector_label!=mode[0]) if len(mode)==1 else None,
            sector_status=status,cluster_size=int((frame.cluster==row.cluster).sum()),
            singleton=bool((frame.cluster==row.cluster).sum()==1)))
    return pd.DataFrame(rows)


def aligned_histories(snapshots, dates):
    import pandas as pd
    from orion_review import align_members
    aligned={dates[0]:snapshots[dates[0]].set_index('ticker').cluster}
    maps=[];events=[];objective_checks=[]
    next_id=int(aligned[dates[0]].max())+1
    for before,after in zip(dates,dates[1:]):
        old=aligned[before];raw=snapshots[after].set_index('ticker').cluster
        new,details=align_members(old,raw,'jaccard')
        # Never reuse an extinct ID at a later date.
        for detail in details:
            if detail['status'].startswith('unmatched'):
                detail['aligned_cluster']=next_id;next_id+=1
        mapping={d['raw_cluster']:d['aligned_cluster'] for d in details}
        new=raw.map(mapping);aligned[after]=new
        overlap,_=align_members(old,raw,'overlap')
        maps.extend(dict(before=before,after=after,**d) for d in details)
        for ticker in sorted(old.index.union(raw.index)):
            both=ticker in old.index and ticker in raw.index
            event='continuing' if both else 'entry' if ticker in raw.index else 'exit'
            events.append(dict(before=before,after=after,ticker=ticker,membership_event=event,
                cluster_before=int(old[ticker]) if ticker in old.index else None,
                cluster_after=int(new[ticker]) if ticker in raw.index else None,
                cluster_changed=bool(old[ticker]!=new[ticker]) if both else None))
            if both:objective_checks.append(dict(before=before,after=after,ticker=ticker,
                jaccard_changed=bool(old[ticker]!=new[ticker]),overlap_changed=bool(old[ticker]!=overlap[ticker])))
    histories=[]
    direct,_=align_members(aligned[dates[0]],snapshots[dates[-1]].set_index('ticker').cluster,'jaccard')
    for ticker in sorted(set().union(*(set(v.index) for v in aligned.values()))):
        labels=[int(aligned[d][ticker]) if ticker in aligned[d].index else None for d in dates]
        eligible=all(c is not None for c in labels)
        histories.append(dict(ticker=ticker,**dict(zip(dates,labels)),observed_all_three=eligible,
            stability_status=('stable all three' if len(set(labels))==1 else 'shifted at least once') if eligible else 'membership gap: no three-date status',
            baseline_to_current_changed=bool(labels[0]!=labels[-1]) if labels[0] is not None and labels[-1] is not None else None,
            direct_baseline_to_current_changed=bool(aligned[dates[0]][ticker]!=direct[ticker]) if ticker in aligned[dates[0]].index and ticker in direct.index else None))
    return aligned,pd.DataFrame(maps),pd.DataFrame(events),pd.DataFrame(histories),pd.DataFrame(objective_checks)


def screen_regression(frame, distances, folder, seed):
    """A separate surrogate explains associations with the D² screen itself."""
    import numpy as np
    import pandas as pd
    import shap
    from xgboost import XGBRegressor
    from sklearn.metrics import r2_score,mean_absolute_error
    from sklearn.model_selection import KFold,cross_val_predict
    from analysis import FEATURES,SPEC,numeric_matrix
    x=numeric_matrix(frame)
    params={k:v for k,v in SPEC['surrogate'].items() if k not in {'objective','eval_metric'}}
    model=XGBRegressor(**params,random_state=seed,objective='reg:squarederror')
    oof=cross_val_predict(model,x,distances,cv=KFold(n_splits=5,shuffle=True,random_state=seed))
    model.fit(x,distances);pred=model.predict(x)
    explanation=shap.TreeExplainer(model)(x)
    if not np.allclose(explanation.values.sum(axis=1)+explanation.base_values,pred,atol=1e-4):
        raise ValueError('Distance-surrogate SHAP additivity failed')
    model.save_model(folder/'screen_surrogate.json')
    np.savez_compressed(folder/'screen_shap.npz',values=explanation.values,base_values=explanation.base_values,
        predictions=pred,observed_distance=distances,feature_values=x,tickers=frame.ticker.to_numpy(dtype=str),features=np.array(FEATURES))
    write_json(folder/'screen_surrogate_fidelity.json',dict(in_sample_r2=float(r2_score(distances,pred)),
        oof_r2=float(r2_score(distances,oof)),oof_mae=float(mean_absolute_error(distances,oof)),
        interpretation='Associations with full-snapshot learned-coordinate screen; OOF fidelity does not validate outlier calibration'))
    return explanation.values


def analyse_model(folder,config,features):
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    from scipy.optimize import linear_sum_assignment
    dates=config['dates'];seed=config['seeds'][0]
    snapshots={d:pd.read_csv(folder/d/'assignments.csv') for d in dates}
    aligned,maps,events,histories,objective=aligned_histories(snapshots,dates)
    maps.to_csv(folder/'jaccard_alignment.csv',index=False);events.to_csv(folder/'membership_transitions.csv',index=False)
    histories.to_csv(folder/'company_cluster_histories.csv',index=False)
    histories[histories.stability_status=='stable all three'].to_csv(folder/'stable_instruments.csv',index=False)
    histories[histories.stability_status=='shifted at least once'].to_csv(folder/'shifted_instruments.csv',index=False)
    objective.to_csv(folder/'alignment_objective_sensitivity.csv',index=False)
    screen_rows=[];calibrations=[];company_rows=[];feature_rows=[];sector_rows=[]
    for date,frame in snapshots.items():
        local=folder/date
        for s in config['seeds']:
            with np.load(local/f'seed_{s}_arrays.npz') as a:
                distance,meta=hotelling_screen(a['embedding'],config['hotelling']['alpha'])
            calibrations.append(dict(decision_date=date,seed=s,**meta))
            screen_rows.extend(dict(decision_date=date,seed=s,ticker=t,individual_d2=float(v) if np.isfinite(v) else None,
                f_reference=meta['f_reference'],flag=bool(v>meta['f_reference']) if np.isfinite(v) else None,
                internal_beta_flag=bool(v>meta['internal_beta_reference']) if np.isfinite(v) else None)
                for t,v in zip(frame.ticker,distance))
        representative=pd.DataFrame(screen_rows).query('decision_date == @date and seed == @seed').set_index('ticker').loc[frame.ticker]
        distance=representative.individual_d2.to_numpy()
        contexts=sector_context(frame).set_index('ticker');contexts.assign(decision_date=date).reset_index().to_csv(local/'sector_context.csv',index=False)
        # An additional one-to-one cluster/sector assignment is contextual only.
        contingency=pd.crosstab(frame.cluster,frame.sector_label)
        r,c=linear_sum_assignment(-contingency.to_numpy())
        sector_map={int(contingency.index[i]):str(contingency.columns[j]) for i,j in zip(r,c)}
        sector_rows.extend(dict(decision_date=date,cluster=int(cl),mapped_sector=sector_map.get(int(cl)),
            mapping='maximum-overlap contextual mapping, not truth/fitting target') for cl in contingency.index)
        screen_phi=screen_regression(frame,distance,local,seed) if np.isfinite(distance).all() else np.full((len(frame),len(features)),np.nan)
        with np.load(local/'arrays.npz') as a:scaled=a['scaled_features'];z=a['embedding']
        with np.load(local/'shap_values.npz') as a:phi=a['values'];classes=a['cluster_labels']
        class_index={int(cl):i for i,cl in enumerate(classes)}
        med=np.median(scaled,axis=0)
        for i,row in enumerate(frame.itertuples()):
            ctx=contexts.loc[row.ticker];own=class_index[int(row.cluster)]
            membership_top=np.argsort(np.abs(phi[i,:,own]))[::-1][:3]
            distance_top=np.argsort(np.abs(screen_phi[i]))[::-1][:3]
            record=dict(decision_date=date,ticker=row.ticker,company=row.company,sector_label=row.sector_label,
                raw_cluster=int(row.cluster),aligned_cluster=int(aligned[date][row.ticker]),
                sector_mapped_context=sector_map.get(int(row.cluster)),sector_mapping_disagreement=sector_map.get(int(row.cluster))!=row.sector_label,
                individual_d2=distance[i],screen_flag=representative.loc[row.ticker,'flag'],confirmed_outlier=False,
                outlier_status='screen candidate; substantive confirmation not established',
                membership_top_features='; '.join(features[j] for j in membership_top),
                distance_surrogate_top_features='; '.join(features[j] for j in distance_top),
                imputation_sensitive=bool(row.fundamentals_imputed or row.volume_imputed),
                **{k:ctx[k] for k in ['other_member_majority','sector_divergence','sector_status','cluster_size','singleton']})
            company_rows.append(record)
            sector_counts=frame.groupby('cluster').sector_label.agg(lambda v:int((v==row.sector_label).sum()))
            references=sector_counts[sector_counts==sector_counts.max()].index.tolist() if sector_counts.max()>0 else []
            reference=references[0] if len(references)==1 else None
            for j,feature in enumerate(features):
                feature_rows.append(dict(decision_date=date,ticker=row.ticker,feature=feature,
                    raw_model_value=float(getattr(row,feature)),scaled_value=float(scaled[i,j]),
                    deviation_from_snapshot_median=float(scaled[i,j]-med[j]),
                    cluster_shap=float(phi[i,j,own]),distance_surrogate_shap=float(screen_phi[i,j]),
                    sector_reference_cluster=reference,
                    own_vs_sector_reference_shap=float(phi[i,j,own]-phi[i,j,class_index[int(reference)]]) if reference is not None else None))
        fig,axes=plt.subplots(1,3,figsize=(15,4))
        axes[0].scatter(range(len(frame)),distance,c=np.where(distance>representative.f_reference.to_numpy(),'#c43c39','#397aa6'))
        axes[0].axhline(representative.f_reference.iloc[0],color='red',ls='--',label='Descriptive F reference')
        for i,t in enumerate(frame.ticker):
            if distance[i]>representative.f_reference.iloc[0]:axes[0].annotate(t,(i,distance[i]),fontsize=8)
        axes[0].set_ylabel('Individual squared distance D²');axes[0].set_xlabel('Instrument (ticker order)');axes[0].legend(fontsize=7)
        axes[1].scatter(z[:,0],z[:,1],c=frame.cluster,cmap='tab10')
        axes[1].scatter(z[distance>representative.f_reference.iloc[0],0],z[distance>representative.f_reference.iloc[0],1],
            facecolors='none',edgecolors='red',s=150,label='Screen candidate')
        axes[1].set_title('First two coordinates; no inferential separation');axes[1].legend(fontsize=7)
        counts=frame.groupby('cluster').size();axes[2].bar(counts.index.astype(str),counts);axes[2].set_ylabel('Instruments');axes[2].set_xlabel('Local cluster')
        fig.suptitle(f'{date}: geometric candidates, clusters and singleton context are distinct',fontsize=11)
        fig.tight_layout();fig.savefig(local/'outlier_screen.png',dpi=140);plt.close(fig)
    screens=pd.DataFrame(screen_rows);screens.to_csv(folder/'hotelling_all_seeds.csv',index=False)
    write_json(folder/'hotelling_calibration.json',dict(specification=config['hotelling'],per_fit=calibrations,
        coordinates='First two representation coordinates; PCA95 clustering may use more dimensions',
        caveat='Individual D² is not n times the distance, and a mean-T² F threshold is only an illustrative reference here. Beta internal-distance reference is an additional descriptive sensitivity; manifold assumptions unverified.'))
    support=screens.groupby(['decision_date','ticker']).agg(estimable_seeds=('flag','count'),seed_flag_fraction=('flag','mean')).reset_index()
    companies=pd.DataFrame(company_rows).merge(support,on=['decision_date','ticker'],validate='one_to_one')
    companies['multi_seed_supported']=((companies.estimable_seeds==len(config['seeds']))&
        (companies.seed_flag_fraction>=config['hotelling']['seed_support_fraction'])&companies.screen_flag.eq(True))
    companies.to_csv(folder/'company_case_summary.csv',index=False)
    pd.DataFrame(feature_rows).to_csv(folder/'company_feature_explanations.csv',index=False)
    pd.DataFrame(sector_rows).to_csv(folder/'contextual_sector_mapping.csv',index=False)
    flag_hist=[]
    for ticker,sub in companies.groupby('ticker'):
        observed=sub.set_index('decision_date');values=[]
        for date in dates:
            values.append(bool(observed.loc[date,'multi_seed_supported']) if date in observed.index and observed.loc[date,'estimable_seeds']==len(config['seeds']) else None)
        flag_hist.append(dict(ticker=ticker,**dict(zip(dates,values)),screen_history=screen_history(values),
                             confirmed_outlier=False))
    pd.DataFrame(flag_hist).to_csv(folder/'outlier_screen_histories.csv',index=False)
    frozen_shift_explanations(folder,snapshots,aligned,dates,features)
    longitudinal_plots(folder,events,histories,dates)
    case_report(folder,companies,histories,pd.DataFrame(flag_hist),features)
    return companies,histories


def contrast_change(phi_before,phi_after,source_class,target_class):
    """Same model/classes at both dates: exact feature-level margin contrast change."""
    return (phi_after[:,target_class]-phi_after[:,source_class])-(phi_before[:,target_class]-phi_before[:,source_class])


def frozen_shift_explanations(folder,snapshots,aligned,dates,features):
    import numpy as np
    import pandas as pd
    import shap
    from xgboost import XGBClassifier
    from analysis import numeric_matrix
    model=XGBClassifier();model.load_model(folder/dates[0]/'surrogate.json')
    labels=json.loads((folder/dates[0]/'surrogate_fidelity.json').read_text())['class_mapping']
    index={int(raw):int(encoded) for encoded,raw in labels.items()}
    explainer=shap.TreeExplainer(model)
    before=snapshots[dates[0]].set_index('ticker');rows=[];checks=[]
    for date in dates[1:]:
        after=snapshots[date].set_index('ticker');common=before.index.intersection(after.index).sort_values()
        x0=numeric_matrix(before.loc[common]);x1=numeric_matrix(after.loc[common])
        e0=explainer(x0);e1=explainer(x1);m0=model.predict(x0,output_margin=True);m1=model.predict(x1,output_margin=True)
        for i,ticker in enumerate(common):
            old=int(aligned[dates[0]][ticker]);new=int(aligned[date][ticker]);changed=old!=new
            if new not in index:
                checks.append(dict(ticker=ticker,after=date,actual_aligned_cluster_changed=changed,
                    status='not estimable: unmatched destination has no 2025 class'));continue
            source,target=index[old],index[new]
            values=contrast_change(e0.values[i],e1.values[i],source,target)
            margin_change=float((m1[i,target]-m1[i,source])-(m0[i,target]-m0[i,source]))
            if not np.isclose(values.sum(),margin_change,atol=1e-4):raise ValueError('Frozen SHAP contrast delta not additive')
            checks.append(dict(ticker=ticker,after=date,actual_aligned_cluster_changed=changed,
                source_cluster=old,destination_cluster=new,margin_contrast_change=margin_change,
                attribution_sum=float(values.sum()),status='estimated in frozen 2025 surrogate'))
            for j,feature in enumerate(features):
                rows.append(dict(ticker=ticker,before=dates[0],after=date,feature=feature,
                    actual_aligned_cluster_changed=changed,source_cluster=old,destination_cluster=new,
                    value_before=float(x0[i,j]),value_after=float(x1[i,j]),feature_change=float(x1[i,j]-x0[i,j]),
                    frozen_2025_contrast_shap_change=float(values[j]),
                    imputation_sensitive=bool(before.loc[ticker,['fundamentals_imputed','volume_imputed']].any() or after.loc[ticker,['fundamentals_imputed','volume_imputed']].any()),
                    interpretation='Fixed-model association with feature changes; does not explain independent refit causally'))
    pd.DataFrame(rows).to_csv(folder/'frozen_2025_shift_shap.csv',index=False)
    pd.DataFrame(checks).to_csv(folder/'frozen_2025_shift_checks.csv',index=False)


def longitudinal_plots(folder,events,histories,dates):
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(12,5))
    for ax,(before,after) in zip(axes,zip(dates,dates[1:])):
        common=events[(events.before==before)&(events.after==after)&(events.membership_event=='continuing')]
        table=pd.crosstab(common.cluster_before.astype(int),common.cluster_after.astype(int))
        image=ax.imshow(table,cmap='Blues',vmin=0)
        ax.set_xticks(range(len(table.columns)),table.columns);ax.set_yticks(range(len(table.index)),table.index)
        for i in range(len(table)):
            for j in range(len(table.columns)):
                v=int(table.iloc[i,j]);ax.text(j,i,str(v),ha='center',va='center',color='white' if v>table.to_numpy().max()/2 else 'black',fontsize=8)
        ax.set_title(f'{before} → {after}\nContinuing members only');ax.set_xlabel('Jaccard-aligned destination');ax.set_ylabel('Previous aligned cluster')
    fig.tight_layout();fig.savefig(folder/'jaccard_transition_heatmaps.png',dpi=140);plt.close(fig)
    observed=histories[histories.observed_all_three].sort_values(dates+['ticker'])
    fig,ax=plt.subplots(figsize=(8,11));ax.imshow(observed[dates].to_numpy(),cmap='tab20',aspect='auto',interpolation='nearest')
    ax.set_xticks(range(3),dates);ax.set_yticks(range(len(observed)),observed.ticker,fontsize=8)
    for i,row in enumerate(observed.itertuples(index=False)):
        for j,date in enumerate(dates):ax.text(j,i,str(int(observed.iloc[i][date])),ha='center',va='center',fontsize=7)
    ax.set_title('Cluster histories: 39 instruments observed at all dates\nNumbers are aligned descriptive labels, not sectors',fontsize=11)
    fig.tight_layout();fig.savefig(folder/'cluster_histories.png',dpi=140);plt.close(fig)


def case_report(folder,companies,histories,flags,features):
    import numpy as np
    import pandas as pd
    from study_eda import LABELS
    import matplotlib.pyplot as plt
    lines=['# Instrument case review','',
        'Screens are candidates, not confirmed outliers. Sector divergence and singletons are separate contextual flags. '
        'SHAP describes surrogates, not causal explanations. Review fidelity and imputation flags before interpreting attributes.','',
        '## Stable and shifted memberships','',
        'Stable at every observed study date: '+', '.join(histories.loc[histories.stability_status=='stable all three','ticker'])+'.','',
        'Changed at least once among all-three-date members: '+', '.join(histories.loc[histories.stability_status=='shifted at least once','ticker'])+'.','',
        'Membership gaps: '+', '.join(histories.loc[~histories.observed_all_three,'ticker'])+'. Entries/exits receive no ordinary shift or resolving flag.','',
        '## Screen histories','']
    lines.extend(f'- {r.ticker}: {r.screen_history}.' for r in flags.itertuples() if r.screen_history!='never flagged')
    lines+=['','## Per-date candidates and sector divergence','']
    feature_table=pd.read_csv(folder/'company_feature_explanations.csv')
    shifts=pd.read_csv(folder/'frozen_2025_shift_shap.csv')
    case_folder=folder/'cases';case_folder.mkdir()
    for row in companies.itertuples():
        if not (row.screen_flag is True or row.screen_flag==True or row.sector_divergence is True or row.sector_divergence==True or row.singleton):continue
        lines.append(f'- {row.decision_date} **{row.ticker}**: D²={row.individual_d2:.3f}; screen={row.screen_flag}; '
            f'seed support={row.seed_flag_fraction:.0%}; sector divergence={row.sector_divergence}; singleton={row.singleton}; '
            f'imputed={row.imputation_sensitive}. Cluster-surrogate features: {row.membership_top_features}. '
            f'Distance-surrogate features: {row.distance_surrogate_top_features}.')
        data=feature_table[(feature_table.decision_date==row.decision_date)&(feature_table.ticker==row.ticker)]
        fig,axes=plt.subplots(1,2,figsize=(12,4))
        for ax,column,title in zip(axes,['cluster_shap','distance_surrogate_shap'],['Own-cluster margin surrogate','Geometric-distance surrogate']):
            sub=data.sort_values(column);ax.barh(sub.feature,sub[column],color=np.where(sub[column]>=0,'#bb4545','#397aa6'))
            ax.axvline(0,color='gray',lw=.6);ax.set_title(title);ax.tick_params(axis='y',labelsize=7)
        fig.suptitle(f'{row.decision_date} {row.ticker}: associations; confirmed outlier = False',fontsize=11)
        fig.tight_layout();fig.savefig(case_folder/f'{row.decision_date}_{row.ticker}.png',dpi=130);plt.close(fig)
    lines+=['','## 2025-to-later attribute shifts in the frozen 2025 surrogate','',
        'The same 2025 model is evaluated at both feature vectors. We subtract destination-versus-source class '
        'SHAP contrasts. Their sum equals the change in the same-model raw-margin contrast. This does not prove '
        'why independently refitted clusters changed; changing peers and the representation also matter. Stable '
        'firms have identical source/destination labels and a zero contrast by construction; inspect their raw '
        'feature changes rather than interpreting zero as no financial change.','']
    changed=shifts[shifts.actual_aligned_cluster_changed]
    for (ticker,date),sub in changed.groupby(['ticker','after']):
        top=sub.reindex(sub.frozen_2025_contrast_shap_change.abs().sort_values(ascending=False).index).head(3)
        lines.append(f'- **{ticker}**, 2025-06-30 → {date}: '+ '; '.join(
            f'{r.feature}: value {r.value_before:.4g} → {r.value_after:.4g}, contrast-SHAP change {r.frozen_2025_contrast_shap_change:+.3f}' for r in top.itertuples())+'.')
        sub=sub.sort_values('frozen_2025_contrast_shap_change')
        fig,ax=plt.subplots(figsize=(10,5));ax.barh(sub.feature,sub.frozen_2025_contrast_shap_change,
            color=np.where(sub.frozen_2025_contrast_shap_change>=0,'#bb4545','#397aa6'))
        ax.axvline(0,color='gray');ax.set_title(f'{ticker}: 2025-06-30 → {date}; frozen 2025 surrogate\nChange in destination-versus-source margin attribution',fontsize=11)
        ax.set_xlabel('SHAP contrast change; association, not cause');ax.tick_params(axis='y',labelsize=8)
        fig.tight_layout();fig.savefig(case_folder/f'shift_{date}_{ticker}.png',dpi=130);plt.close(fig)
    (folder/'case_review.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
