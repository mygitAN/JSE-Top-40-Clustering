import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from analysis import ROOT, FEATURES, prepare
from study_eda import eda_tables
from study_workflow import StudySession
from study_reporting import validate_study_outputs


class StudyTests(unittest.TestCase):
    def test_clean_notebook_cells_have_valid_python(self):
        import ast
        notebook = json.loads((ROOT/'notebooks/three_cross_section_study.ipynb').read_text(encoding='utf-8'))
        self.assertEqual(notebook['nbformat'], 4)
        code_cells = [cell for cell in notebook['cells'] if cell['cell_type'] == 'code']
        self.assertEqual(len(code_cells), 11)
        for cell in code_cells:
            source = ''.join(cell['source']) if isinstance(cell['source'], list) else cell['source']
            ast.parse(source)
            self.assertEqual(cell['outputs'], [])
            self.assertIsNone(cell['execution_count'])

    def test_eda_population_missingness_and_evidence(self):
        frame = pd.read_csv(ROOT/'data/processed/Top40_Retrospective_Model_Inputs_v1.csv')
        scaler, _ = prepare(frame)
        tables = eda_tables(frame, FEATURES, scaler)
        self.assertEqual(tables['population'].instruments.tolist(), [41, 41, 41])
        self.assertEqual(int(tables['presence'].all(axis=1).sum()), 39)
        self.assertEqual(int(tables['missingness'].model_missing.sum()), 0)
        self.assertEqual(int(tables['missingness'].query('feature == "revenue_zar_model"').raw_missing.sum()), 3)
        self.assertEqual(int(tables['missingness'].query('feature == "average_daily_volume_1y_model"').raw_missing.sum()), 2)
        self.assertEqual(len(tables['descriptions']), 30)
        self.assertIn('feature', tables['descriptions'])
        self.assertEqual(len(tables['scaled']), 123)
        self.assertEqual(set(tables['correlations']), set(frame.decision_date))

    def test_eda_does_not_refit_scaler_on_future(self):
        frame = pd.read_csv(ROOT/'data/processed/Top40_Retrospective_Model_Inputs_v1.csv')
        scaler, _ = prepare(frame)
        before = scaler.data_max_.copy()
        frame.loc[frame.decision_date != '2025-06-30', FEATURES] *= 100
        tables = eda_tables(frame, FEATURES, scaler)
        self.assertTrue((scaler.data_max_ == before).all())
        self.assertGreater(tables['scaled'][FEATURES].max().max(), 1)

    def test_study_failure_is_tracked_and_not_completed(self):
        with tempfile.TemporaryDirectory() as temporary:
            study = StudySession(output=temporary, run_id='eda-failure', include_umap=False, stability_runs=2)
            study.load_data()
            with patch('study_eda.explore', side_effect=RuntimeError('synthetic EDA failure')):
                with self.assertRaisesRegex(RuntimeError, 'synthetic EDA failure'):
                    study.explore()
            self.assertFalse((study.out/'COMPLETED').exists())
            self.assertEqual(json.loads((study.out/'status.json').read_text())['status'], 'failed')

    def test_stage_order_cannot_bypass_eda(self):
        with tempfile.TemporaryDirectory() as temporary:
            study = StudySession(output=temporary, run_id='bad-order', include_umap=False, stability_runs=2)
            with self.assertRaisesRegex(RuntimeError, 'stages in order'):
                study.fit_models()
            self.assertFalse((study.out/'COMPLETED').exists())
            self.assertEqual(study.state, 'failed')

    def test_missing_required_outputs_fail_completion(self):
        config = json.loads((ROOT/'configs/study.json').read_text())
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, 'Missing required study artifact'):
                validate_study_outputs(temporary, config)

    def test_paper_workflow_requires_eight_clusters(self):
        config = json.loads((ROOT/'configs/study.json').read_text())
        self.assertEqual(config['umap_sensitivity']['n_clusters'], 8)
        with tempfile.TemporaryDirectory() as temporary:
            config['umap_sensitivity']['n_clusters'] = 5
            path = Path(temporary)/'wrong-k.json'
            path.write_text(json.dumps(config), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'fixes k=8'):
                StudySession(output=temporary, config_path=path)
