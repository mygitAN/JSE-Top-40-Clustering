import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from top40 import CONFIG
from top40.data import DATES, load_inputs
from top40.explain import explain
from top40.features import add_derived_columns, get_feature_set
from top40.models import cluster, embed, feature_matrix, mahalanobis_screen, prepare, scores

CONFIGURATION = json.loads(CONFIG.read_text(encoding='utf-8'))


class ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frame = add_derived_columns(load_inputs(), DATES[0])
        cls.features = get_feature_set('invariant8')

    def prepared(self, frame=None):
        return prepare(self.frame if frame is None else frame, self.features.columns, DATES, DATES[0])

    def test_every_member_retained(self):
        _, snapshots = self.prepared()
        self.assertEqual([len(s) for s in snapshots.values()], [41, 41, 41])
        self.assertTrue(all('RNI' in set(s.ticker) for s in snapshots.values()))

    def test_later_dates_do_not_change_scaler(self):
        scaler, _ = self.prepared()
        changed = self.frame.copy()
        changed.loc[changed.decision_date == DATES[-1], list(self.features.columns)] *= 100
        other, snapshots = self.prepared(changed)
        np.testing.assert_array_equal(scaler.data_max_, other.data_max_)
        self.assertGreater(other.transform(feature_matrix(snapshots[DATES[-1]], self.features.columns)).max(), 1)

    def test_row_order_and_seed_are_deterministic(self):
        scaler, snapshots = self.prepared()
        _, shuffled = self.prepared(self.frame.sample(frac=1, random_state=99))
        self.assertEqual(list(snapshots[DATES[0]].ticker), list(shuffled[DATES[0]].ticker))
        x = scaler.transform(feature_matrix(snapshots[DATES[0]], self.features.columns))
        params = CONFIGURATION['representations']['tsne']
        z = embed(x, 'tsne', params, 42)
        np.testing.assert_allclose(z, embed(x, 'tsne', params, 42), rtol=1e-7, atol=1e-6)
        labels = cluster(z, 'hierarchical', CONFIGURATION['clusterers']['hierarchical'], 42, 8)
        self.assertEqual(len(np.unique(labels)), 8)

    def test_bad_inputs_fail(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            self.prepared(pd.concat([self.frame, self.frame.iloc[:1]]))
        changed = self.frame.copy()
        changed.loc[0, self.features.columns[0]] = np.nan
        with self.assertRaisesRegex(ValueError, 'Non-finite'):
            self.prepared(changed)
        with self.assertRaisesRegex(ValueError, 'Unknown'):
            embed(np.ones((10, 3)), 'typo', {}, 42)

    def test_noise_and_single_cluster_have_no_scores(self):
        x = np.ones((4, 2))
        result = scores(x, x, np.full(4, -1), ['a'] * 4)
        self.assertIsNone(result['silhouette_features'])
        self.assertEqual((result['coverage'], result['noise_count']), (0, 4))
        self.assertIsNone(result['sector_ari'])
        self.assertIsNone(scores(x, x, np.zeros(4, dtype=int))['davies_bouldin_embedding'])

    def test_scores_report_cluster_sizes(self):
        x = np.array([[0., 0], [0, 1], [5, 5], [5, 6], [9, 0]])
        result = scores(x, x, np.array([0, 0, 1, 1, 2]))
        self.assertEqual((result['smallest_cluster'], result['largest_cluster'], result['singleton_clusters']),
                         (1, 2, 1))
        self.assertGreater(result['silhouette_features'], 0)

    def test_screen_reference_and_singular_covariance(self):
        x = np.random.default_rng(0).normal(size=(41, 8))
        distance, meta = mahalanobis_screen(x)
        # Same-sample squared distances always sum to p(n-1) and cannot exceed (n-1)^2/n.
        self.assertAlmostEqual(distance.sum(), 8 * 40)
        self.assertLess(meta['reference'], 40 ** 2 / 41)
        self.assertLess(distance.max(), 40 ** 2 / 41)
        distance, meta = mahalanobis_screen(np.column_stack([x[:, 0], 2 * x[:, 0]]))
        self.assertTrue(np.isnan(distance).all())
        self.assertIn('not estimable', meta['status'])

    def test_screen_is_invariant_to_feature_rescaling(self):
        x = np.random.default_rng(1).normal(size=(30, 4))
        np.testing.assert_allclose(mahalanobis_screen(x)[0], mahalanobis_screen(x * [1, 10, 100, .01] + 3)[0])

    def test_surrogate_class_mapping_singleton_and_additivity(self):
        sub = self.frame.iloc[:12]
        labels = np.array([10] * 5 + [20] * 6 + [99])
        with tempfile.TemporaryDirectory() as tmp:
            fidelity, by_cluster = explain(sub, labels, self.features, CONFIGURATION['surrogate'], 42, Path(tmp))
            self.assertIsNone(fidelity['oof_accuracy'])
            self.assertIn('singleton', fidelity['oof_status'])
            self.assertEqual(fidelity['class_mapping'], {'0': 10, '1': 20, '2': 99})
            with np.load(Path(tmp) / 'shap_values.npz', allow_pickle=False) as saved:
                self.assertEqual(saved['values'].shape, (12, 8, 3))
                np.testing.assert_array_equal(saved['features'], self.features.columns)
                np.testing.assert_allclose(saved['values'].sum(1) + saved['base_values'], saved['raw_margins'],
                                           atol=1e-4)
            self.assertEqual(set(by_cluster.cluster), {10, 20, 99})

    def test_surrogate_out_of_fold_when_estimable(self):
        with tempfile.TemporaryDirectory() as tmp:
            fidelity, _ = explain(self.frame.iloc[:12], np.repeat([0, 1, 2], 4), self.features,
                                  CONFIGURATION['surrogate'], 42, Path(tmp))
        self.assertEqual(fidelity['oof_status'], 'estimated')
        self.assertIsNotNone(fidelity['oof_accuracy'])


if __name__ == '__main__':
    unittest.main()
