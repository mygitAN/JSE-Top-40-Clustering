import json
import tempfile
import unittest
from pathlib import Path

from top40.export import check_results, export_results
from top40.tracking import Run


def fake_run(base, config, paths, complete=True):
    """A tracked run containing empty placeholder files at ``paths``."""
    run = Run(base, config, 'test', 'export fixture', 'fixture')
    with run:
        for relative in paths:
            (run.out / relative).parent.mkdir(parents=True, exist_ok=True)
            (run.out / relative).write_text('before,after,ticker\n' if relative.endswith('/moves.csv') else relative)
        if not complete:
            raise RuntimeError('synthetic failure')
    return run.out


class ExportTests(unittest.TestCase):
    config = dict(feature_set='invariant8', seed=42, stability_runs=2, k=8, dates=['d1'],
                  primary_models={'baseline': {}})

    def selection(self):
        from top40.export import selected_paths
        return selected_paths(self.config)

    def test_export_copies_selection_and_check_detects_edits(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = fake_run(tmp, self.config, self.selection() + ['models/baseline/d1/seed_42.npz'])
            destination = Path(tmp) / 'results'
            (destination / 'stale').mkdir(parents=True)
            (destination / 'stale' / 'old.csv').write_text('from another run')
            manifest = export_results(run, destination)
            self.assertEqual(manifest['run_id'], 'fixture')
            self.assertEqual(set(manifest['files']), set(self.selection()))
            self.assertFalse((destination / 'stale').exists())
            self.assertFalse((destination / 'models/baseline/d1/seed_42.npz').exists())
            check_results(destination)
            (destination / 'summary.md').write_text('edited by hand')
            with self.assertRaisesRegex(ValueError, 'differs'):
                check_results(destination)
            (destination / 'summary.md').write_text('summary.md')
            (destination / 'extra.csv').write_text('not exported')
            with self.assertRaisesRegex(ValueError, 'not in its manifest'):
                check_results(destination)

    def test_each_move_figure_is_required_and_exported(self):
        from top40.export import movement_figure_paths
        with tempfile.TemporaryDirectory() as tmp:
            paths = self.selection()
            # Build and index a real move row, without fitting any model.
            with Run(tmp, self.config, 'test', 'move fixture', 'moves') as run:
                for relative in paths:
                    target = run.out / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text('before,after,ticker\n' if relative.endswith('/moves.csv') else relative)
                (run.out / 'longitudinal/baseline/moves/moves.csv').write_text(
                    'before,after,ticker\nd1,d2,ABC\n')
                figure = 'longitudinal/baseline/moves/move_d1_d2_ABC.png'
                (run.out / figure).write_bytes(b'fixture image')
            self.assertEqual(movement_figure_paths(run.out, self.config), [figure])
            export_results(run.out, Path(tmp) / 'results')
            self.assertTrue((Path(tmp) / 'results' / figure).is_file())
            (run.out / figure).unlink()
            with self.assertRaises(ValueError):
                export_results(run.out, Path(tmp) / 'results')

    def test_incomplete_or_altered_runs_are_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(RuntimeError):
                fake_run(tmp, self.config, self.selection(), complete=False)
            with self.assertRaisesRegex(ValueError, 'not a completed run'):
                export_results(Path(tmp) / 'runs' / 'fixture', Path(tmp) / 'results')
        with tempfile.TemporaryDirectory() as tmp:
            run = fake_run(tmp, self.config, self.selection())
            (run / 'summary.md').write_text('tampered')
            with self.assertRaisesRegex(ValueError, 'manifest mismatch'):
                export_results(run, Path(tmp) / 'results')

    def test_committed_results_match_their_manifest(self):
        from top40.export import RESULTS
        if not (RESULTS / 'manifest.json').is_file():
            self.skipTest('no results/ exported yet')
        manifest = check_results()
        self.assertEqual(json.loads((RESULTS / 'manifest.json').read_text())['run_id'], manifest['run_id'])


if __name__ == '__main__':
    unittest.main()
