"""Build compact reviewer tables from a completed saved run, without refitting."""
import argparse
import json
from pathlib import Path

import pandas as pd
from tracking import ROOT, write_json
from verify_run import verify_completed
from audit_workbook import summary


def build(run_id):
    out = ROOT/'experiments/runs'/run_id
    verify_completed(out)
    report = ROOT/'reports'
    report.mkdir(exist_ok=True)
    models = pd.read_csv(out/'model_comparison.csv')
    baseline = models[models.model == 'tsne_hierarchical'].copy()
    stability = pd.read_csv(out/'seed_stability.csv')
    stats = stability.groupby('decision_date').agg(pairs=('ari', 'size'), ari_min=('ari', 'min'),
                       ari_mean=('ari', 'mean'), ari_max=('ari', 'max'),
                       nmi_min=('nmi', 'min'), nmi_mean=('nmi', 'mean'), nmi_max=('nmi', 'max'))
    stats.to_csv(report/'seed_summary.csv')
    fidelity = []
    for date in baseline.decision_date:
        row = json.loads((out/date/'surrogate_fidelity.json').read_text())
        row = {k: v for k, v in row.items() if k not in {'class_mapping', 'shap_shape', 'meaning'}}
        fidelity.append({'decision_date': date, **row})
    pd.DataFrame(fidelity).to_csv(report/'surrogate_summary.csv', index=False)
    baseline.to_csv(report/'baseline_results.csv', index=False)
    models.to_csv(report/'model_comparison.csv', index=False)
    sensitivity = pd.read_csv(out/'cluster_count_sensitivity.csv')
    sensitivity.to_csv(report/'cluster_count_sensitivity.csv', index=False)
    temporal = pd.read_csv(out/'temporal_agreement.csv')
    temporal.to_csv(report/'temporal_agreement.csv', index=False)
    events = pd.read_csv(out/'membership_and_cluster_transitions.csv')
    events[events.membership_event != 'continuing'].to_csv(report/'membership_events.csv', index=False)
    write_json(report/'workbook_inspection.json', summary())
    write_json(report/'review_source.json', {'run_id': run_id, 'purpose': 'review candidate, not promotion',
                'run_manifest': str(out.relative_to(ROOT)/'run_manifest.json')})
    print(baseline[['decision_date', 'silhouette_embedding', 'silhouette_features', 'sector_ari']].to_string(index=False))
    print(stats.to_string())
    print(pd.DataFrame(fidelity).to_string(index=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_id')
    build(parser.parse_args().run_id)
