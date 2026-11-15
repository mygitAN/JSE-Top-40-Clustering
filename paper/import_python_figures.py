"""Copy the original Python study figures into the self-contained LaTeX project.

No model is rerun and no figure is redrawn. Each image is checked against the
immutable run's artifact_checksums.json before copying.
"""
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / 'paper'
DATES = ('2025-06-30', '2025-12-31', '2026-06-30')


def main():
    manifest = json.loads((ROOT / 'results/manifest.json').read_text())
    run = ROOT / 'experiments/runs' / manifest['run_id']
    checksums = json.loads((run / 'artifact_checksums.json').read_text())
    if not (run / 'COMPLETED').is_file():
        raise ValueError('The source run is incomplete.')
    destination = PAPER / 'figures/python'
    destination.mkdir(parents=True, exist_ok=True)
    sources = {}
    for date in DATES:
        for kind in ('cluster_map', 'dendrogram'):
            relative = f'models/umap/{date}/{kind}.png'
            source = run / relative
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            if digest != checksums[relative]:
                raise ValueError(f'Archive checksum mismatch: {relative}')
            target = destination / f'{kind}_{date}.png'
            shutil.copyfile(source, target)
            sources[target.relative_to(PAPER).as_posix()] = {
                'archive_path': relative, 'sha256': digest,
            }
    relative = 'longitudinal/umap/jaccard.png'
    source = ROOT / 'results' / relative
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != manifest['files'][relative] or digest != checksums[relative]:
        raise ValueError(f'Export/archive checksum mismatch: {relative}')
    target = destination / 'jaccard.png'
    shutil.copyfile(source, target)
    sources[target.relative_to(PAPER).as_posix()] = {
        'archive_path': relative, 'sha256': digest,
        'export_path': f'results/{relative}',
    }
    record = {
        'run_id': manifest['run_id'],
        'implementation_commit': manifest['git_commit'],
        'operation': 'Unmodified copies of original Python-generated PNGs',
        'labels': 'Cluster-map identifiers are local to each fit; tree leaves carry ticker and sector labels.',
        'files': sources,
    }
    (PAPER / 'python_figure_sources.json').write_text(json.dumps(record, indent=2) + '\n')
    print(f'Copied and checksum-verified {len(sources)} original Python figures.')


if __name__ == '__main__':
    main()
