"""Regression checks for population retention and temporal label handling."""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from run_analysis import DATES, FEATURES, ROOT, align_labels, prepare, scores, transitions


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.frame = pd.read_csv(ROOT/'data/processed/Top40_Retrospective_Model_Inputs_v1.csv')

    def test_retains_all_members_and_rni(self):
        _, snapshots = prepare(self.frame)
        self.assertEqual([len(s) for s in snapshots.values()], [41, 41, 41])
        self.assertTrue(all('RNI' in set(s.ticker) for s in snapshots.values()))
        self.assertNotIn('sector_label', FEATURES)
        self.assertEqual(len(FEATURES), 10)

    def test_future_values_do_not_change_scaler(self):
        scaler, _ = prepare(self.frame)
        changed = self.frame.copy()
        changed.loc[changed.decision_date == DATES[-1], FEATURES] *= 100
        other, _ = prepare(changed)
        np.testing.assert_array_equal(scaler.data_max_, other.data_max_)

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


if __name__ == '__main__':
    unittest.main()
