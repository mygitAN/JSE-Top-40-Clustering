"""Regression checks for population retention and temporal label handling."""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from analysis import DATES, FEATURES, ROOT, align_labels, prepare, scores, transitions, embed, cluster, numeric_matrix, explain


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.frame = pd.read_csv(ROOT/'data/processed/Top40_Retrospective_Model_Inputs_v1.csv')

    def test_retains_all_members_and_rni(self):
        _, snapshots = prepare(self.frame)
        self.assertEqual([len(s) for s in snapshots.values()], [41, 41, 41])
        self.assertTrue(all('RNI' in set(s.ticker) for s in snapshots.values()))
        self.assertNotIn('sector_label', FEATURES)
        self.assertEqual(len(FEATURES), 10)
        self.assertEqual(FEATURES, ['return_1y', 'average_daily_volume_1y_model', 'market_cap_zar',
            'beta_1y', 'shares_outstanding', 'revenue_zar_model', 'eps_zar_model',
            'annualised_volatility_1y', 'dividend_yield', 'earnings_yield_model_clipped'])

    def test_future_values_do_not_change_scaler(self):
        scaler, _ = prepare(self.frame)
        changed = self.frame.copy()
        changed.loc[changed.decision_date == DATES[-1], FEATURES] *= 100
        other, _ = prepare(changed)
        np.testing.assert_array_equal(scaler.data_max_, other.data_max_)
        np.testing.assert_array_equal(scaler.data_min_, other.data_min_)
        self.assertGreater(scaler.transform(numeric_matrix(changed[changed.decision_date == DATES[-1]])).max(), 1)

    def test_permuted_labels_align(self):
        old = pd.Series([0, 0, 1, 1], index=list('ABCD'))
        new = pd.Series([5, 5, 3, 3, 5], index=list('ABCDE'))
        aligned, _ = align_labels(old, new)
        np.testing.assert_array_equal(aligned.loc[old.index], old)

    def test_noise_has_no_fake_silhouette(self):
        x = np.ones((4, 2))
        result = scores(x, x, np.full(4, -1), ['a']*4)
        self.assertIsNone(result['silhouette_features'])
        self.assertEqual(result['coverage'], 0)
        self.assertEqual(result['noise_count'], 4)
        self.assertIsNone(result['sector_ari'])
        result = scores(x, x, np.zeros(4, dtype=int), ['a']*4)
        self.assertIsNone(result['silhouette_embedding'])
        self.assertEqual(result['coverage'], 1)

    def test_entries_and_exits_are_not_cluster_changes(self):
        import tempfile
        frame = self.frame.copy()
        frame['cluster'] = np.arange(len(frame)) % 8
        with tempfile.TemporaryDirectory() as tmp:
            transitions(frame, Path(tmp))
            result = pd.read_csv(Path(tmp)/'membership_and_cluster_transitions.csv')
        events = result[result.membership_event != 'continuing']
        self.assertEqual(set(zip(events.ticker, events.membership_event)),
                         {('APN','exit'),('GLN','entry'),('MNP','exit'),('PAN','entry')})
        self.assertTrue(events.cluster_changed.isna().all())
        imputed = result[result.ticker.isin(['AGL', 'RNI'])]
        self.assertTrue((imputed.interpretation == 'imputation-sensitive').all())

    def test_same_seed_and_row_order(self):
        scaler, snapshots = prepare(self.frame)
        other, shuffled = prepare(self.frame.sample(frac=1, random_state=99))
        for date in DATES:
            pd.testing.assert_frame_equal(snapshots[date], shuffled[date])
        x = scaler.transform(numeric_matrix(snapshots[DATES[0]]))
        z = embed(x, 'tsne', 42)
        np.testing.assert_allclose(z, embed(x, 'tsne', 42), rtol=1e-7, atol=1e-6)
        np.testing.assert_array_equal(cluster(z, 'hierarchical', 42), cluster(z, 'hierarchical', 42))

    def test_duplicate_and_missing_features_fail(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            prepare(pd.concat([self.frame, self.frame.iloc[:1]]))
        changed = self.frame.copy()
        changed.loc[0, FEATURES[0]] = np.nan
        with self.assertRaisesRegex(ValueError, 'Non-finite'):
            prepare(changed)
        with self.assertRaisesRegex(ValueError, 'Unknown'):
            embed(np.ones((10, 3)), 'typo', 42)

    def test_unmatched_and_disjoint_clusters(self):
        old = pd.Series([0, 0, 1], index=list('ABC'))
        new = pd.Series([5, 5, 6, 7], index=list('ABDE'))
        aligned, _ = align_labels(old, new)
        self.assertEqual(aligned.A, 0)
        self.assertGreater(aligned.D, 1)
        self.assertGreater(aligned.E, 1)
        self.assertNotEqual(aligned.D, aligned.E)
        aligned, _ = align_labels(old, pd.Series([5, 6], index=list('XY')))
        self.assertTrue((aligned > 1).all())

    def test_temporal_metrics_ignore_label_permutation(self):
        from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
        old = pd.Series([0, 0, 1, 1], index=list('ABCD'))
        new = pd.Series([9, 9, 5, 5], index=list('ABCD'))
        self.assertEqual(adjusted_rand_score(old, new), 1)
        self.assertEqual(normalized_mutual_info_score(old, new), 1)

    def test_shap_class_mapping_singleton_and_additivity(self):
        import tempfile
        import json
        sub = self.frame.iloc[:12].copy()
        labels = np.array([10]*5+[20]*6+[99])
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            explain(sub, labels, out, 42)
            fidelity = json.loads((out/'surrogate_fidelity.json').read_text())
            self.assertIsNone(fidelity['oof_accuracy'])
            self.assertIn('singleton', fidelity['oof_status'])
            self.assertEqual(fidelity['class_mapping'], {'0': 10, '1': 20, '2': 99})
            with np.load(out/'shap_values.npz', allow_pickle=False) as values:
                self.assertEqual(values['values'].shape, (12, 10, 3))
                np.testing.assert_array_equal(values['features'], FEATURES)
                np.testing.assert_array_equal(values['cluster_labels'], [10, 20, 99])
                np.testing.assert_array_equal(values['feature_values'], numeric_matrix(sub))
                np.testing.assert_allclose(values['values'].sum(1)+values['base_values'], values['raw_margins'], atol=1e-4)
            table = pd.read_csv(out/'shap_by_cluster.csv')
            self.assertTrue(table[table.cluster == 99].status.str.contains('singleton').all())

    def test_shap_oof_estimable(self):
        import tempfile
        import json
        with tempfile.TemporaryDirectory() as tmp:
            explain(self.frame.iloc[:12], np.repeat([0, 1, 2], 4), Path(tmp), 42)
            fidelity = json.loads((Path(tmp)/'surrogate_fidelity.json').read_text())
            self.assertEqual(fidelity['oof_status'], 'estimated')
            self.assertIsNotNone(fidelity['oof_accuracy'])


if __name__ == '__main__':
    unittest.main()
