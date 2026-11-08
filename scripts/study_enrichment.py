"""Reporting additions for fixed three-cross-section models; never fits a model."""
from pathlib import Path
import numpy as np
import pandas as pd
from paper_longitudinal import aligned_histories, hotelling_screen, sector_context


def membership_matrices(old, new):
    """Pairwise Jaccard on continuing instruments; counts are a separate quantity."""
    if not old.index.is_unique or not new.index.is_unique:
        raise ValueError('Unique instrument keys required')
    common = old.index.intersection(new.index)
    left = sorted(old.unique()); right = sorted(new.unique())
    a = {c: set(old.loc[common][old.loc[common] == c].index) for c in left}
    b = {c: set(new.loc[common][new.loc[common] == c].index) for c in right}
    counts = pd.DataFrame([[len(a[i] & b[j]) for j in right] for i in left], index=left, columns=right)
    unions = pd.DataFrame([[len(a[i] | b[j]) for j in right] for i in left], index=left, columns=right)
    jaccard = counts.div(unions.where(unions > 0))
    counts.index.name = jaccard.index.name = 'source_aligned_cluster'
    return counts, jaccard, len(common)


def history_plot(histories, dates, path, title):
    import matplotlib.pyplot as plt
    from cluster_history_flows import draw_cluster_history_flows
    observed = histories.loc[histories.observed_all_three].copy()
    fig = draw_cluster_history_flows(observed, dates, title)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def transition_plots(aligned, dates, folder, title):
    import matplotlib.pyplot as plt
    summaries = []
    figures = {}
    for kind in ['jaccard', 'movement_counts']:
        fig, axes = plt.subplots(1,len(dates)-1,figsize=(13,5),squeeze=False)
        figures[kind] = (fig,axes[0])
    for index,(before,after) in enumerate(zip(dates,dates[1:])):
        counts,similarity,n = membership_matrices(aligned[before],aligned[after])
        if n == 0:
            raise ValueError('No continuing instruments; temporal comparison is undefined')
        counts.to_csv(folder/f'movement_counts_{before}_{after}.csv')
        similarity.to_csv(folder/f'jaccard_{before}_{after}.csv')
        for kind,table in [('jaccard',similarity),('movement_counts',counts)]:
            fig,axes = figures[kind];ax=axes[index]
            cmap=plt.get_cmap('Blues').copy();cmap.set_bad('#dddddd')
            image=ax.imshow(table.to_numpy(dtype=float),cmap=cmap,vmin=0,
                            vmax=1 if kind=='jaccard' else max(1,int(counts.to_numpy().max())))
            ax.set_xticks(range(len(table.columns)),table.columns)
            ax.set_yticks(range(len(table.index)),table.index)
            for i in range(len(table)):
                for j in range(len(table.columns)):
                    v=table.iloc[i,j]
                    text='NA' if pd.isna(v) else f'{v:.2f}' if kind=='jaccard' else str(int(v))
                    threshold=.5 if kind=='jaccard' else max(1,counts.to_numpy().max())/2
                    ax.text(j,i,text,ha='center',va='center',fontsize=8,
                            color='white' if pd.notna(v) and v>threshold else 'black')
            ax.set_title(f'{before} to {after}\n{n} continuing instruments')
            ax.set_xlabel('Destination aligned cluster');ax.set_ylabel('Source aligned cluster')
            fig.colorbar(image,ax=ax,label='Jaccard similarity (0-1)' if kind=='jaccard' else 'Instrument count')
        summaries.append(dict(before=before,after=after,continuing=n))
    for kind,(fig,_) in figures.items():
        fig.suptitle(f'{title}: '+('membership overlap' if kind=='jaccard' else 'instrument movements'))
        fig.tight_layout();fig.savefig(folder/f'{kind}_heatmaps.png',dpi=150,bbox_inches='tight');plt.close(fig)
    return pd.DataFrame(summaries)


def descriptive_screens(snapshots, model_folder, dates, seed, stability_runs):
    """Reuse Paper's descriptive references; no surrogate, model or threshold fitting."""
    rows=[]
    for date in dates:
        frame=snapshots[date].sort_values('ticker').reset_index(drop=True)
        observed={};metas={}
        for current_seed in range(seed,seed+stability_runs):
            path=Path(model_folder)/date/f'seed_{current_seed}_arrays.npz'
            with np.load(path,allow_pickle=False) as saved:
                ticks=saved['tickers'].astype(str)
                distances,meta=hotelling_screen(saved['embedding'])
            if set(ticks)!=set(frame.ticker) or len(ticks)!=len(frame):
                raise ValueError('Saved embedding and assignment instruments differ')
            observed[current_seed]=pd.Series(distances,index=ticks).reindex(frame.ticker).to_numpy()
            metas[current_seed]=meta
        representative=observed[seed];meta=metas[seed]
        stack=np.array(list(observed.values()));finite=np.isfinite(stack)
        exceed=np.array([observed[s]>metas[s]['f_reference'] for s in observed])
        sectors=sector_context(frame)
        for i,row in enumerate(frame.itertuples()):
            valid=int(finite[:,i].sum());above=int((exceed[:,i]&finite[:,i]).sum())
            flag=bool(representative[i]>meta['f_reference']) if np.isfinite(representative[i]) else None
            context=sectors.iloc[i].to_dict();context['raw_cluster']=context.pop('cluster')
            context.update(decision_date=date,individual_d2=float(representative[i]),
                f_reference=meta['f_reference'],internal_beta_reference=meta['internal_beta_reference'],
                screen_flag=flag,multi_seed_supported=bool(flag and above>=3) if flag is not None and valid>=3 else None,
                estimable_seeds=valid,reference_exceeding_seeds=above,total_seeds=stability_runs,
                screen_status=meta['status'])
            for field in ['fundamentals_imputed','volume_imputed']:
                if hasattr(row,field):context[field]=bool(getattr(row,field))
            rows.append(context)
    return pd.DataFrame(rows)


def enrich_model(assignments, model_folder, dates, destination, name, seed=42, stability_runs=5):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=False)
    if assignments.duplicated(['decision_date','ticker']).any():
        raise ValueError('Duplicate instrument/date assignment')
    snapshots={date:assignments[assignments.decision_date==date].copy() for date in dates}
    if any(frame.empty for frame in snapshots.values()):
        raise ValueError('Missing study date')
    aligned,maps,events,histories,sensitivity=aligned_histories(snapshots,dates)
    maps.to_csv(destination/'jaccard_alignment.csv',index=False)
    events.to_csv(destination/'membership_transitions.csv',index=False)
    histories.to_csv(destination/'company_cluster_histories.csv',index=False)
    sensitivity.to_csv(destination/'alignment_objective_sensitivity.csv',index=False)
    histories[histories.stability_status=='stable all three'].to_csv(destination/'stable_instruments.csv',index=False)
    histories[histories.stability_status=='shifted at least once'].to_csv(destination/'shifted_instruments.csv',index=False)
    history_plot(histories,dates,destination/'cluster_histories.png',name)
    pair_summary=transition_plots(aligned,dates,destination,name)
    pair_summary.to_csv(destination/'pair_summary.csv',index=False)
    screens=descriptive_screens(snapshots,model_folder,dates,seed,stability_runs)
    screens.to_csv(destination/'sector_and_screen_diagnostics.csv',index=False)
    return dict(study_model=name,observed_all_three=int(histories.observed_all_three.sum()),
                stable=int((histories.stability_status=='stable all three').sum()),
                shifted=int((histories.stability_status=='shifted at least once').sum()),
                membership_gaps=int((~histories.observed_all_three).sum()),
                screen_candidates=int(screens.screen_flag.eq(True).sum()),
                multi_seed_supported_candidates=int(screens.multi_seed_supported.eq(True).sum()),
                interpretation='Additional descriptive reporting; original models and selection unchanged')
