"""Verify completed bundles and compare deterministic tables/arrays, not image/ZIP bytes."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from tracking import digest, verify, write_json


def compare(left, right):
    left, right = Path(left), Path(right)
    for out in [left, right]:
        verify(out)
        if (out/'COMPLETED').read_text().strip() != digest(out/'artifact_checksums.json'):
            raise ValueError('Invalid completion marker')
        if json.loads((out/'status.json').read_text())['status'] != 'completed':
            raise ValueError('Run is not completed')
    paths = lambda out: {p.relative_to(out) for p in out.rglob('*') if p.suffix in {'.csv', '.npz'}}
    if paths(left) != paths(right):
        raise ValueError('Deterministic artifact sets differ')
    checked = []
    for relative in sorted(paths(left)):
        if relative.suffix == '.csv':
            pd.testing.assert_frame_equal(pd.read_csv(left/relative), pd.read_csv(right/relative),
                                          check_exact=False, rtol=1e-7, atol=1e-6)
        else:
            with np.load(left/relative, allow_pickle=False) as a, np.load(right/relative, allow_pickle=False) as b:
                if a.files != b.files:
                    raise ValueError(f'Array keys differ: {relative}')
                for name in a.files:
                    if np.issubdtype(a[name].dtype, np.number):
                        np.testing.assert_allclose(a[name], b[name], rtol=1e-7, atol=1e-6)
                    else:
                        np.testing.assert_array_equal(a[name], b[name])
        checked.append(relative.as_posix())
    json_paths = [Path('resolved_config.json'), Path('run_manifest.json')]
    json_paths += list(p.relative_to(left) for p in left.glob('*/surrogate*.json'))
    for relative in json_paths:
        if json.loads((left/relative).read_text()) != json.loads((right/relative).read_text()):
            raise ValueError(f'Deterministic JSON differs: {relative}')
        checked.append(relative.as_posix())
    return dict(status='passed', left=left.name, right=right.name, rtol=1e-7, atol=1e-6,
                compared=checked, exclusions='PNG rendering metadata, ZIP/NPZ container timestamps, runtime, provenance and diagnostic logs')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('left'); parser.add_argument('right'); parser.add_argument('--report', required=True)
    args = parser.parse_args()
    result = compare(args.left, args.right)
    write_json(args.report, result)
    print(f'PASS: {len(result["compared"])} deterministic artifacts compared')
