"""Copy the tables and figures the paper cites from one completed run into ``results/``.

Run outputs under ``experiments/`` are not committed. ``results/`` is: it holds a
fixed selection from a single named run, plus a manifest recording that run's
id, code commit and the checksum of every copied file. Exporting replaces the
whole folder, so ``results/`` never mixes runs.

    python -m top40.export experiments/runs/<run id>
"""
import argparse
import csv
import json
import shutil
from pathlib import Path

from . import ROOT
from .tracking import digest, verify, write_json

RESULTS = ROOT / 'results'

# Paths relative to the run folder. {model} and {date} are expanded below.
SELECTION = [
    'summary.md',
    'primary_model_summary.csv',
    'model_comparison.csv',
    'seed_agreement.csv',
    'surrogate_fidelity.csv',
    'temporal_agreement.csv',
    'longitudinal_summary.csv',
    'longitudinal/feature_space_screen.csv',
    'eda/population.csv',
    'eda/descriptions.csv',
    'eda/population_and_sectors.png',
    'eda/feature_distributions.png',
    'eda/correlation_{date}.png',
    'feature_audit/dominance.csv',
    'feature_audit/quality.csv',
    'feature_audit/cross_set_agreement.csv',
    'feature_audit/shift_counts.csv',
    'feature_audit/instrument_status.csv',
    'feature_audit/share_basis.csv',
    'feature_audit/feature_dominance.png',
    'model_quality_{date}.png',
    'models/{model}/cluster_count_sensitivity.png',
    'models/{model}/{date}/assignments.csv',
    'models/{model}/{date}/median_deviations.csv',
    'models/{model}/{date}/feature_profile.png',
    'models/{model}/{date}/dendrogram.png',
    'longitudinal/{model}/cluster_histories.csv',
    'longitudinal/{model}/membership_events.csv',
    'longitudinal/{model}/cluster_flows.png',
    'longitudinal/{model}/jaccard.png',
    'longitudinal/{model}/movement_counts.png',
    'longitudinal/{model}/moves/README.md',
    'longitudinal/{model}/moves/cluster_profiles.csv',
    'longitudinal/{model}/moves/cluster_summary.csv',
    'longitudinal/{model}/moves/moves.csv',
    'longitudinal/{model}/moves/move_features.csv',
    'longitudinal/{model}/moves/cluster_profiles_{date}.png',
]


def selected_paths(config):
    paths = []
    for pattern in SELECTION:
        models = config['primary_models'] if '{model}' in pattern else [None]
        dates = config['dates'] if '{date}' in pattern else [None]
        paths += [pattern.format(model=m, date=d) for m in models for d in dates]
    return paths


def movement_figure_paths(run_folder, config):
    """Require a figure for every recorded move, including a valid empty move table."""
    paths = []
    for model in config['primary_models']:
        folder = f'longitudinal/{model}/moves'
        with (Path(run_folder) / folder / 'moves.csv').open(newline='', encoding='utf-8') as handle:
            reader = csv.DictReader(handle)
            if not {'before', 'after', 'ticker'}.issubset(reader.fieldnames or []):
                raise ValueError(f'{folder}/moves.csv lacks movement keys')
            for row in reader:
                values = [row[key] for key in ['before', 'after', 'ticker']]
                if any(not value or '/' in value or "\\" in value or value in {'.', '..'} for value in values):
                    raise ValueError('Invalid movement figure key')
                paths.append(f'{folder}/move_{values[0]}_{values[1]}_{values[2]}.png')
    return sorted(set(paths))


def export_results(run_folder, destination=RESULTS):
    """Verify ``run_folder``, then replace ``destination`` with its selected outputs. Returns the manifest."""
    run_folder, destination = Path(run_folder).resolve(), Path(destination)
    status = json.loads((run_folder / 'status.json').read_text(encoding='utf-8'))
    if status['status'] != 'completed' or not (run_folder / 'COMPLETED').is_file():
        raise ValueError(f'{run_folder.name} is not a completed run')
    if (run_folder / 'COMPLETED').read_text().strip() != digest(run_folder / 'artifact_checksums.json'):
        raise ValueError('Completion marker does not match the run manifest')
    verify(run_folder)
    config = status['resolved_configuration']
    paths = selected_paths(config)
    missing = [p for p in paths if not (run_folder / p).is_file()]
    if missing:
        raise ValueError(f'Run lacks a selected output: {missing[0]}')

    paths += movement_figure_paths(run_folder, config)
    missing = [p for p in paths if not (run_folder / p).is_file()]
    if missing:
        raise ValueError(f'Run lacks a selected output: {missing[0]}')
    destination = destination.resolve()
    if destination == run_folder or destination in run_folder.parents or run_folder in destination.parents:
        raise ValueError('Export destination must be separate from the source run')
    if destination.exists():
        shutil.rmtree(destination)
    for relative in paths:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(run_folder / relative, target)
    manifest = dict(run_id=status['run_id'], git_commit=status.get('git_commit'), git_dirty=status.get('git_dirty'),
                    started_utc=status['started_utc'], feature_set=config['feature_set'], seed=config['seed'],
                    stability_runs=config['stability_runs'], k=config['k'], input_sha256=status.get('input_sha256'),
                    files={p: digest(destination / p) for p in paths})
    write_json(destination / 'manifest.json', manifest)
    return manifest


def check_results(destination=RESULTS):
    """Raise unless every file listed in the manifest is present and unchanged, and nothing else is."""
    destination = Path(destination)
    manifest = json.loads((destination / 'manifest.json').read_text(encoding='utf-8'))
    present = {p.relative_to(destination).as_posix() for p in destination.rglob('*') if p.is_file()} - {'manifest.json'}
    if present != set(manifest['files']):
        raise ValueError('results/ holds files that are not in its manifest, or lacks some that are')
    for relative, expected in manifest['files'].items():
        if digest(destination / relative) != expected:
            raise ValueError(f'results/{relative} differs from the exported copy')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('run_folder', nargs='?', help='A completed run folder; omit with --check')
    parser.add_argument('--check', action='store_true', help='Verify the committed results/ against its manifest')
    args = parser.parse_args()
    if args.check:
        manifest = check_results()
        print(f'PASS: results/ matches run {manifest["run_id"]} ({len(manifest["files"])} files)')
        return
    if not args.run_folder:
        parser.error('give a run folder, or --check')
    manifest = export_results(args.run_folder)
    print(f'Exported {len(manifest["files"])} files from run {manifest["run_id"]} to {RESULTS}')
    if manifest['git_dirty']:
        print('WARNING: that run used uncommitted code. Commit, rerun `python -m top40`, '
              'and export the new run before citing these results.')


if __name__ == '__main__':
    main()
