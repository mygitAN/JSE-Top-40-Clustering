"""Verify complete grid coverage, memberships and numerical explanation contracts."""
import argparse
import json
from pathlib import Path

from verify_run import verify_completed


def verify_paper(out):
    import numpy as np
    import pandas as pd
    from paper_search import grid,select
    out=Path(out);artifacts=verify_completed(out)
    manifest=json.loads((out/'paper_manifest.json').read_text(encoding='utf-8'))
    config=manifest['config'];reps,pool,invalid=grid(config)
    scores=pd.read_csv(out/'search/selection_scores_all_seeds.csv')
    expected={(c['candidate_id'],s) for c in pool for s in config['seeds']}
    actual=set(zip(scores.candidate_id,scores.seed))
    if actual!=expected or scores.duplicated(['candidate_id','seed']).any():raise ValueError('Grid coverage mismatch')
    summary=pd.read_csv(out/'search/candidate_summary.csv')
    choices=manifest['selected_roles']
    for role,geometry in [('common_features_k8','features'),('embedding_k8','embedding')]:
        if select(summary,geometry,8).iloc[0].candidate_id!=choices[role]:raise ValueError('Declared selection not reproduced')
    results=pd.read_csv(out/'selected_model_scores.csv')
    expected={(cid,d,s) for cid in set(choices.values()) for d in config['dates'] for s in config['seeds']}
    if set(zip(results.candidate_id,results.decision_date,results.seed))!=expected:raise ValueError('Selected follow-up coverage mismatch')
    population=pd.read_csv(out/'eda/population.csv')
    if population.instruments.tolist()!=[41]*3 or population.economic_groups.tolist()!=[40]*3:raise ValueError('Population unit mismatch')
    counts={};max_error=0.
    for cid in set(choices[r] for r in ['baseline','common_features_k8','embedding_k8']):
        folder=out/'models'/cid
        if not (folder/'company_case_summary.csv').exists():continue
        history=pd.read_csv(folder/'company_cluster_histories.csv')
        if len(history)!=43 or history.observed_all_three.sum()!=39:raise ValueError('History population mismatch')
        if not history.loc[~history.observed_all_three,'stability_status'].eq('membership gap: no three-date status').all():
            raise ValueError('Membership gap labelled as ordinary stability')
        events=pd.read_csv(folder/'membership_transitions.csv')
        if events.loc[events.membership_event!='continuing','cluster_changed'].notna().any():raise ValueError('Entry/exit interpreted as shift')
        cases=pd.read_csv(folder/'company_case_summary.csv')
        if len(cases)!=123 or cases.confirmed_outlier.any():raise ValueError('Invalid case population or unsubstantiated confirmation')
        screen=pd.read_csv(folder/'hotelling_all_seeds.csv')
        if len(screen)!=41*3*len(config['seeds']):raise ValueError('Missing seed-level screens')
        checks=pd.read_csv(folder/'frozen_2025_shift_checks.csv')
        valid=checks.status.eq('estimated in frozen 2025 surrogate')
        if not np.allclose(checks.loc[valid,'attribution_sum'],checks.loc[valid,'margin_contrast_change'],atol=1e-4):
            raise ValueError('Temporal SHAP additivity mismatch')
        for date in config['dates']:
            local=folder/date
            with np.load(local/'shap_values.npz') as a:
                if a['values'].shape!=(41,10,8):raise ValueError('Unexpected cluster SHAP dimensions')
                err=float(np.max(np.abs(a['values'].sum(axis=1)+a['base_values']-a['raw_margins'])))
                max_error=max(max_error,err)
                if err>1e-4:raise ValueError('Cluster SHAP additivity mismatch')
            if (local/'screen_shap.npz').exists():
                with np.load(local/'screen_shap.npz') as a:
                    if not np.allclose(a['values'].sum(axis=1)+a['base_values'],a['predictions'],atol=1e-4):
                        raise ValueError('Distance SHAP additivity mismatch')
        counts[cid]=dict(stable=int(history.stability_status.eq('stable all three').sum()),
            shifted=int(history.stability_status.eq('shifted at least once').sum()),
            screened_candidates=int(cases.screen_flag.eq(True).sum()),confirmed_outliers=0)
    return dict(run_id=out.name,verified_artifacts=artifacts,representations=len(reps),configurations=len(pool),
        selection_fits=len(scores),frozen_followup_fits=len(results),invalid_ward_combinations=len(invalid),
        selected_roles=choices,reviewed_model_counts=counts,max_cluster_shap_additivity_error=max_error,
        status='passed',certifies_historical_source_values=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('run_directory');args=parser.parse_args()
    print(json.dumps(verify_paper(args.run_directory),indent=2))
