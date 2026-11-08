"""Exploratory plots/tables for all three cross-sections, before model fitting."""
import json


LABELS = ['1Y return','Average volume','Market cap','Beta','Shares','Revenue','EPS',
          'Annual volatility','Dividend yield','Earnings yield']


def eda_tables(frame,features,scaler):
    import pandas as pd
    dates=sorted(frame.decision_date.unique())
    population=frame.groupby('decision_date').agg(instruments=('ticker','size'),
        distinct_tickers=('ticker','nunique'),fundamental_imputations=('fundamentals_imputed','sum'),
        volume_imputations=('volume_imputed','sum')).reset_index()
    # Count the approved Investec DLC as one economic group, while retaining
    # both legally distinct securities in the instrument-level model inputs.
    groups=frame.assign(economic_group=frame.ticker.replace({'INL':'INVESTEC_DLC','INP':'INVESTEC_DLC'}))
    population['economic_groups']=population.decision_date.map(
        groups.groupby('decision_date').economic_group.nunique())
    presence=pd.crosstab(frame.ticker,frame.decision_date).reindex(columns=dates,fill_value=0).astype(bool)
    missing=[]
    for date,sub in frame.groupby('decision_date',sort=True):
        for feature in features:
            if feature=='average_daily_volume_1y_model':
                raw_missing=int(sub.volume_imputed.sum())
            elif feature in {'revenue_zar_model','eps_zar_model','earnings_yield_model_clipped'}:
                raw_missing=int(sub.fundamentals_imputed.sum())
            else:
                raw_missing=int(sub[feature].isna().sum())
            missing.append(dict(decision_date=date,feature=feature,raw_missing=raw_missing,
                                model_missing=int(sub[feature].isna().sum())))
    evidence=[]
    for column in ['membership_evidence','fundamentals_evidence','market_evidence','share_evidence','sector_evidence']:
        counts=frame.groupby(['decision_date',column],dropna=False).size()
        evidence.extend(dict(decision_date=date,field=column,status=str(status),n=int(n))
                        for (date,status),n in counts.items())
    scaled=frame[['decision_date','ticker','sector_label','fundamentals_imputed','volume_imputed']].copy()
    scaled[features]=scaler.transform(frame[features].to_numpy(dtype=float))
    descriptions=frame.groupby('decision_date')[features].describe().stack(level=0,future_stack=True).reset_index().rename(columns={'level_1':'feature'})
    correlations={d:s[features].corr(method='pearson') for d,s in frame.groupby('decision_date',sort=True)}
    pairs=[]
    for date,corr in correlations.items():
        for i,a in enumerate(features):
            for b in features[i+1:]:
                if abs(corr.loc[a,b])>=.8:
                    pairs.append(dict(decision_date=date,feature_a=a,feature_b=b,pearson_r=float(corr.loc[a,b])))
    return dict(population=population,presence=presence,missingness=pd.DataFrame(missing),evidence=pd.DataFrame(evidence),
                scaled=scaled,descriptions=descriptions,correlations=correlations,
                correlated_pairs=pd.DataFrame(pairs,columns=['decision_date','feature_a','feature_b','pearson_r']))


def explore(frame,features,scaler,out):
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Patch
    out.mkdir(parents=True,exist_ok=False)
    tables=eda_tables(frame,features,scaler)
    for name in ['population','missingness','evidence','scaled','descriptions','correlated_pairs']:
        tables[name].to_csv(out/f'{name}.csv',index=False)
    tables['presence'].to_csv(out/'membership_presence.csv')
    frame[['decision_date','ticker','company','volume_imputed','fundamentals_imputed']].query(
        'volume_imputed or fundamentals_imputed').to_csv(out/'imputed_observations.csv',index=False)
    dates=list(tables['population'].decision_date)
    fig,axes=plt.subplots(1,2,figsize=(12,4))
    positions=np.arange(len(dates));width=.36
    for offset,column,label,color in [(-width/2,'economic_groups','Company groups','#2e765e'),
                                      (width/2,'instruments','Listed instruments','steelblue')]:
        bars=axes[0].bar(positions+offset,tables['population'][column],width,label=label,color=color)
        axes[0].bar_label(bars,padding=3)
    axes[0].set_xticks(positions,dates)
    axes[0].set_ylabel('Count at each snapshot');axes[0].set_ylim(0,55)
    axes[0].legend(fontsize=8,loc='upper left')
    sectors=pd.crosstab(frame.decision_date,frame.sector_label).reindex(dates)
    sectors.plot.bar(stacked=True,ax=axes[1],rot=0,cmap='tab10')
    axes[1].set_ylabel('Instruments');axes[1].set_xlabel('Snapshot')
    axes[1].legend(fontsize=7,title='Legacy sector context',bbox_to_anchor=(1,1))
    fig.suptitle('Population and sector context: repeated, overlapping cross-sections')
    fig.text(.5,.01,'40 company groups / 41 listed instruments: Investec Limited (INL) and Investec plc (INP) form one DLC group.',
             ha='center',fontsize=8)
    fig.tight_layout(rect=(0,.06,1,1));fig.savefig(out/'population_and_sectors.png',dpi=150);plt.close(fig)
    presence=tables['presence']
    fig,ax=plt.subplots(figsize=(8,12))
    ax.imshow(presence.to_numpy(dtype=int),cmap=ListedColormap(['#eeeeee','#276d9b']),vmin=0,vmax=1,aspect='auto')
    ax.set_xticks(range(3),dates);ax.set_yticks(range(len(presence)),presence.index,fontsize=8)
    ax.set_title('Membership observations: absence is not a negative screening flag')
    ax.legend(handles=[Patch(color='#276d9b',label='Observed member'),Patch(color='#eeeeee',label='Not observed')],
              loc='lower center',bbox_to_anchor=(.5,-.08),ncol=2)
    fig.tight_layout();fig.savefig(out/'membership_presence.png',dpi=150);plt.close(fig)
    missing=tables['missingness'].pivot(index='feature',columns='decision_date',values='raw_missing').reindex(features)
    fig,ax=plt.subplots(figsize=(9,5))
    image=ax.imshow(missing.to_numpy(),cmap='Blues',vmin=0,vmax=max(1,int(missing.max().max())),aspect='auto')
    ax.set_xticks(range(3),dates);ax.set_yticks(range(10),LABELS)
    for i in range(10):
        for j in range(3):
            ax.text(j,i,str(missing.iloc[i,j]),ha='center',va='center',
                    color='white' if missing.iloc[i,j]>.5*max(1,int(missing.max().max())) else 'black')
    ax.set_title('Raw missing cases before flagged model-only imputation')
    fig.colorbar(image,ax=ax,label='Count');fig.tight_layout();fig.savefig(out/'raw_missingness.png',dpi=150);plt.close(fig)
    fig,axes=plt.subplots(5,2,figsize=(13,15))
    for j,(ax,feature,label) in enumerate(zip(axes.flat,features,LABELS)):
        values=[tables['scaled'].loc[tables['scaled'].decision_date==d,feature].to_numpy() for d in dates]
        ax.boxplot(values,tick_labels=dates,showfliers=False)
        for i,v in enumerate(values,1):ax.scatter(i+np.linspace(-.12,.12,len(v)),v,s=8,alpha=.55,color='steelblue')
        ax.set_title(label);ax.set_ylabel('June-2025 MinMax units');ax.grid(axis='y',alpha=.2)
    fig.suptitle('Feature distributions: every instrument retained, including flagged imputations',fontsize=13)
    fig.tight_layout(rect=(0,0,1,.98));fig.savefig(out/'feature_distributions.png',dpi=145);plt.close(fig)
    for date,corr in tables['correlations'].items():
        corr.to_csv(out/f'correlation_{date}.csv')
        fig,ax=plt.subplots(figsize=(10,9))
        image=ax.imshow(corr.to_numpy(),vmin=-1,vmax=1,cmap='coolwarm')
        ax.set_xticks(range(10),LABELS,rotation=60,ha='right',fontsize=8)
        ax.set_yticks(range(10),LABELS,fontsize=8)
        for i in range(10):
            for j in range(10):
                v=corr.iloc[i,j]
                ax.text(j,i,f'{v:.2f}',ha='center',va='center',fontsize=7,color='white' if abs(v)>.7 else 'black')
        ax.set_title(f'{date}: Pearson feature correlations\nModel-only imputations included; no automatic feature removal')
        fig.colorbar(image,ax=ax,shrink=.8);fig.tight_layout();fig.savefig(out/f'correlation_{date}.png',dpi=140);plt.close(fig)
    summary=dict(total_rows=len(frame),distinct_tickers=int(frame.ticker.nunique()),
                 observed_all_three=int(presence.all(axis=1).sum()),
                 raw_missingness_source='RNI raw fields and validated volume/fundamental imputation flags',
                 evidence='Recorded flags, not fresh external certification',
                 interpretation='Three overlapping index cross-sections; not 123 independent firms')
    (out/'eda_summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    return tables
