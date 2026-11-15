import ast
import json
import tempfile
import unittest
from unittest.mock import patch

from top40 import CONFIG, ROOT
from top40.ablation import run_ablation
from top40.data import DATES, load_inputs
from top40.eda import eda_tables
from top40.features import add_derived_columns, get_feature_set
from top40.models import prepare
from top40.study import StudySession


def status(study):
    return json.loads((study.out / 'status.json').read_text(encoding='utf-8'))['status']


class StudyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(CONFIG.read_text(encoding='utf-8'))
        cls.frame = add_derived_columns(load_inputs(), DATES[0])

    def test_notebook_parses_and_has_no_partial_or_error_outputs(self):
        notebook = json.loads((ROOT / 'notebooks/three_cross_section_study.ipynb').read_text(encoding='utf-8'))
        code = [cell for cell in notebook['cells'] if cell['cell_type'] == 'code']
        executed = [cell.get('execution_count') is not None for cell in code]
        if any(executed) and not all(executed):
            # VS Code can retain setup outputs without its execution counter.
            # Accept this only with all outputs and a verified completed run.
            import re
            from top40.tracking import digest, verify
            self.assertTrue(all(cell.get('outputs') for cell in code))
            text = ''.join(''.join(o.get('text', [])) for o in code[0].get('outputs', [])
                           if o['output_type'] == 'stream')
            match = re.search(r'Run ([A-Za-z0-9_-]+) ->', text)
            self.assertIsNotNone(match)
            run = ROOT / 'experiments' / 'runs' / match.group(1)
            self.assertEqual(json.loads((run / 'status.json').read_text())['status'], 'completed')
            self.assertEqual((run / 'COMPLETED').read_text().strip(), digest(run / 'artifact_checksums.json'))
            verify(run)
        for cell in code:
            ast.parse(''.join(cell['source']))
            self.assertFalse(any(output['output_type'] == 'error' for output in cell.get('outputs', [])))
            if not any(executed):
                self.assertEqual(cell['outputs'], [])
        if any(executed):
            image_count = sum('image/png' in output.get('data', {})
                              for cell in code for output in cell.get('outputs', []))
            self.assertGreaterEqual(image_count, 20 * len(self.config["primary_models"]), 'Completed notebook must retain the visual evidence')

    def test_configured_feature_sets_exist(self):
        for name in [self.config['feature_set'], *self.config['ablation_feature_sets']]:
            get_feature_set(name)

    def test_eda_population_and_missingness(self):
        feature_set = get_feature_set('invariant8')
        scaler, _ = prepare(self.frame, feature_set.columns, DATES, DATES[0])
        tables = eda_tables(self.frame, feature_set, scaler)
        self.assertEqual(tables['population'].instruments.tolist(), [41, 41, 41])
        self.assertEqual(tables['population'].economic_groups.tolist(), [40, 40, 40])
        self.assertEqual(int(tables['presence'].all(axis=1).sum()), 39)
        missing = tables['missingness'].groupby('feature').raw_missing.sum()
        self.assertEqual((missing['log_sales_to_cap'], missing['log_turnover'], missing['beta_1y']), (3, 2, 0))
        self.assertEqual(len(tables['scaled']), 123)

    def test_ablation_tables(self):
        result = run_ablation(self.frame, self.config, feature_sets=['original10', 'invariant8'], seeds=[42, 43])
        self.assertEqual(len(result['dominance']), 2 * 3)
        self.assertEqual(len(result['quality']), 2 * 2 * 3)
        self.assertEqual(len(result['cross_set_agreement']), 2 * 3)
        self.assertTrue((result['quality'].n_clusters == self.config['k']).all())
        self.assertEqual(len(result['instrument_status']), 43)
        # The deterministic recipe has no seed pairs to compare.
        ward = result['quality'][result['quality'].recipe == 'ward_features']
        self.assertTrue(ward.mean_seed_ari.isna().all())

    def test_stages_cannot_be_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            study = StudySession(output=tmp, run_id='bad-order', stability_runs=2)
            with self.assertRaisesRegex(RuntimeError, 'stages in order'):
                study.fit_models()
            self.assertEqual(status(study), 'failed')
            self.assertFalse((study.out / 'COMPLETED').exists())

    def test_stage_failure_is_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            study = StudySession(output=tmp, run_id='eda-failure', stability_runs=2)
            study.load_data()
            with patch('top40.eda.explore', side_effect=RuntimeError('synthetic failure')):
                with self.assertRaisesRegex(RuntimeError, 'synthetic failure'):
                    study.explore()
            self.assertEqual(status(study), 'failed')
            with self.assertRaisesRegex(RuntimeError, 'closed'):
                study.audit_features()


if __name__ == '__main__':
    unittest.main()
