"""Tracked descriptive cross-section experiments; no automatic result promotion."""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path

from tracking import ROOT, Run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default=str(ROOT/'experiments'), help='Registry root, containing unique runs/')
    parser.add_argument('--run-id', help='Optional immutable run ID; collisions fail')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--stability-runs', type=int, default=5)
    parser.add_argument('--mode', choices=['baseline', 'full'], default='full')
    parser.add_argument('--skip-shap', action='store_true', help='Explicit incomplete smoke test only')
    parser.add_argument('--experiment', default='fixed-reconstruction')
    parser.add_argument('--purpose', default='Audit fixed baseline and descriptive sensitivity; no selection')
    args = parser.parse_args()
    if args.stability_runs < 2:
        parser.error('--stability-runs must be at least 2')
    for key in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMBA_NUM_THREADS']:
        os.environ.setdefault(key, '1')
    os.environ.setdefault('MPLCONFIGDIR', str(ROOT/'.runtime/matplotlib'))
    os.environ.setdefault('NUMBA_CACHE_DIR', str(ROOT/'.runtime/numba'))
    config = json.loads((ROOT/'configs/baseline.json').read_text(encoding='utf-8'))
    config.update(seed=args.seed, stability_runs=args.stability_runs, mode=args.mode, skip_shap=args.skip_shap)
    with Run(args.output, config, args.experiment, args.purpose, args.run_id) as run:
        run.provenance()
        try:
            from analysis import run as analyse
        except ImportError as error:
            raise RuntimeError('Required analysis dependency missing; install requirements.txt in the active environment') from error
        args.output = str(run.out)
        analyse(args)
        manifest = json.loads((run.out/'run_manifest.json').read_text(encoding='utf-8'))
        run.meta['warnings'] = manifest['warnings']
        run.meta['metric_artifacts'] = ['model_comparison.csv', 'seed_metrics.csv', 'seed_stability.csv',
                                        'cluster_count_sensitivity.csv', 'temporal_agreement.csv']
        run.meta['versions'] = {d.metadata['Name']: d.version for d in importlib.metadata.distributions()}
    print(f'Completed run {run.meta["run_id"]}: {run.out}')


if __name__ == '__main__':
    main()
