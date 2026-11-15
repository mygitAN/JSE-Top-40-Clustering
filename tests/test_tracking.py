import csv
import json
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from top40 import ROOT
from top40.tracking import Run, digest, register, verify


def registry(folder):
    with (Path(folder) / 'registry.csv').open(encoding='utf-8') as stream:
        return list(csv.DictReader(stream))


def status(run):
    return json.loads((run.out / 'status.json').read_text(encoding='utf-8'))['status']


class TrackingTests(unittest.TestCase):
    def test_completion_collision_and_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            with Run(tmp, {}, 'test', 'fixture', 'same') as run:
                (run.out / 'result.csv').write_text('a\n1\n')
            self.assertEqual((run.out / 'COMPLETED').read_text().strip(), digest(run.out / 'artifact_checksums.json'))
            self.assertGreater(verify(run.out), 0)
            with self.assertRaises(FileExistsError):
                Run(tmp, {}, 'test', 'collision', 'same')
            (run.out / 'result.csv').write_text('corrupted')
            with self.assertRaisesRegex(ValueError, 'manifest'):
                verify(run.out)

    def test_failed_runs_keep_diagnostics(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(RuntimeError, 'synthetic failure'):
                with Run(tmp, {}, 'test', 'failure', 'failed') as run:
                    raise RuntimeError('synthetic failure')
            self.assertFalse((run.out / 'COMPLETED').exists())
            self.assertEqual(status(run), 'failed')
            self.assertIn('synthetic failure', (run.out / 'run.log').read_text())
            self.assertEqual(registry(tmp)[0]['status'], 'failed')

    def test_concurrent_registry_updates(self):
        with tempfile.TemporaryDirectory() as tmp:
            def add(i):
                register(tmp, {'run_id': str(i), 'status': 'running'})
                register(tmp, {'run_id': str(i), 'status': 'completed'})
            with ThreadPoolExecutor(max_workers=6) as pool:
                list(pool.map(add, range(18)))
            rows = registry(tmp)
            self.assertEqual(len({r['run_id'] for r in rows}), 18)
            self.assertTrue(all(r['status'] == 'completed' for r in rows))
            with self.assertRaises(FileExistsError):
                register(tmp, {'run_id': '1', 'status': 'running'})

    def test_registry_serialises_independent_processes(self):
        code = ('import sys; from top40.tracking import register; '
                'register(sys.argv[1], {"run_id": sys.argv[2], "status": "running"})')
        with tempfile.TemporaryDirectory() as tmp:
            def add(i):
                return subprocess.run([sys.executable, '-c', code, tmp, str(i)], capture_output=True, text=True,
                                      cwd=ROOT)
            with ThreadPoolExecutor(max_workers=4) as pool:
                results = list(pool.map(add, range(8)))
            for result in results:
                self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(registry(tmp)), 8)

    def test_invalid_run_id_and_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            for bad in ['..', '../escape', 'a/b', 'a\\b']:
                with self.assertRaises(ValueError):
                    Run(tmp, {}, 'test', 'bad id', bad)
            with self.assertRaisesRegex(ValueError, 'status'):
                register(tmp, {'run_id': 'bad', 'status': 'success-ish'})

    def test_finalisation_failure_never_completes(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, 'synthetic checksum failure'):
                with patch('top40.tracking.verify', side_effect=ValueError('synthetic checksum failure')):
                    with Run(tmp, {}, 'test', 'finalisation failure', 'bad') as run:
                        pass
            self.assertFalse((run.out / 'COMPLETED').exists())
            self.assertEqual(status(run), 'failed')

    def test_completion_marker_failure_marks_registry_failed(self):
        original = Path.write_text

        def write(path, *args, **kwargs):
            if path.name == 'COMPLETED':
                raise OSError('synthetic marker failure')
            return original(path, *args, **kwargs)

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(OSError, 'marker failure'):
                with patch.object(Path, 'write_text', write):
                    with Run(tmp, {}, 'test', 'marker failure', 'marker') as run:
                        pass
            self.assertEqual(status(run), 'failed')
            self.assertEqual(registry(tmp)[0]['status'], 'failed')


if __name__ == '__main__':
    unittest.main()
