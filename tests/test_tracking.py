import csv
import json
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from tracking import ROOT, Run, register, verify, digest


class TrackingTests(unittest.TestCase):
    def test_completion_collision_and_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            with Run(tmp, {}, 'test', 'synthetic fixture', 'same') as run:
                (run.out/'result.csv').write_text('a\n1\n')
            self.assertTrue((run.out/'COMPLETED').is_file())
            self.assertEqual((run.out/'COMPLETED').read_text().strip(), digest(run.out/'artifact_checksums.json'))
            self.assertGreater(verify(run.out), 0)
            with self.assertRaises(FileExistsError):
                Run(tmp, {}, 'test', 'collision', 'same')
            (run.out/'result.csv').write_text('corrupted')
            with self.assertRaisesRegex(ValueError, 'manifest'):
                verify(run.out)

    def test_failed_runs_preserve_diagnostics(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(RuntimeError, 'synthetic failure'):
                with Run(tmp, {}, 'test', 'failure', 'failed') as run:
                    raise RuntimeError('synthetic failure')
            self.assertFalse((run.out/'COMPLETED').exists())
            self.assertEqual(json.loads((run.out/'status.json').read_text())['status'], 'failed')
            self.assertIn('synthetic failure', (run.out/'run.log').read_text())
            self.assertGreater(verify(run.out), 0)
            with (Path(tmp)/'registry.csv').open() as stream:
                self.assertEqual(list(csv.DictReader(stream))[0]['status'], 'failed')

    def test_concurrent_registry_updates_and_finalization(self):
        with tempfile.TemporaryDirectory() as tmp:
            def add(i):
                record = {'run_id': str(i), 'status': 'running'}
                register(tmp, record)
                register(tmp, {**record, 'status': 'completed'})
            with ThreadPoolExecutor(max_workers=6) as pool:
                list(pool.map(add, range(18)))
            with (Path(tmp)/'registry.csv').open() as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 18)
            self.assertEqual(len({r['run_id'] for r in rows}), 18)
            self.assertTrue(all(r['status'] == 'completed' for r in rows))
            with self.assertRaises(FileExistsError):
                register(tmp, {'run_id': '1', 'status': 'running'})

    def test_invalid_run_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            for bad in ['..', '../escape', 'a/b', 'a\\b']:
                with self.assertRaises(ValueError):
                    Run(tmp, {}, 'test', 'bad ID', bad)

    def test_finalization_failure_never_completes(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, 'synthetic checksum failure'):
                with patch('tracking.verify', side_effect=ValueError('synthetic checksum failure')):
                    with Run(tmp, {}, 'test', 'finalization failure', 'bad-finalization') as run:
                        pass
            self.assertFalse((run.out/'COMPLETED').exists())
            self.assertEqual(json.loads((run.out/'status.json').read_text())['status'], 'failed')

    def test_registry_rejects_invalid_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, 'status'):
                register(tmp, {'run_id': 'bad', 'status': 'success-ish'})

    def test_registry_serializes_independent_processes(self):
        with tempfile.TemporaryDirectory() as tmp:
            code = ('import sys; sys.path.insert(0, sys.argv[1]); '
                    'from tracking import register; '
                    'register(sys.argv[2], {"run_id": sys.argv[3], "status": "running"})')
            def add(i):
                return subprocess.run([sys.executable, '-c', code, str(ROOT/'scripts'), tmp, str(i)],
                                      capture_output=True, text=True)
            with ThreadPoolExecutor(max_workers=4) as pool:
                results = list(pool.map(add, range(8)))
            for result in results:
                self.assertEqual(result.returncode, 0, result.stderr)
            with (Path(tmp)/'registry.csv').open() as stream:
                self.assertEqual(len(list(csv.DictReader(stream))), 8)

    def test_dependency_failure_tracked_before_heavy_imports(self):
        with tempfile.TemporaryDirectory() as tmp:
            # -S hides third-party site-packages while preserving standard library tracking.
            result = subprocess.run([sys.executable, '-S', str(ROOT/'scripts/run_analysis.py'),
                                     '--output', tmp, '--run-id', 'missing-deps'], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('dependency missing', result.stderr)
            status = json.loads((Path(tmp)/'runs/missing-deps/status.json').read_text())
            self.assertEqual(status['status'], 'failed')
            self.assertFalse((Path(tmp)/'runs/missing-deps/COMPLETED').exists())
