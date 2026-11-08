import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from orion_review import align_members, pair_events, deviation_comparison


class OrionTests(unittest.TestCase):
    def test_jaccard_is_not_overlap_objective(self):
        index = [f'T{i}' for i in range(17)]
        old = pd.Series([0]*13+[1]*4, index=index)
        new = pd.Series([5]*9+[6]*4+[5]*4, index=index)
        overlap, _ = align_members(old, new, 'overlap')
        jaccard, _ = align_members(old, new, 'jaccard')
        self.assertEqual(overlap.iloc[0], 0)
        self.assertEqual(jaccard.iloc[0], 1)
        self.assertEqual(jaccard.iloc[9], 0)

    def test_permutation_unmatched_and_membership_events(self):
        old = pd.Series([0, 0, 1, 1], index=list('ABCD'))
        new = pd.Series([9, 9, 5, 7], index=list('ABCE'))
        aligned, details = align_members(old, new)
        np.testing.assert_array_equal(aligned.loc[list('ABC')], old.loc[list('ABC')])
        self.assertGreater(aligned.E, old.max())
        self.assertIn('unmatched', next(x['status'] for x in details if x['raw_cluster'] == 7))
        events = pd.DataFrame(pair_events(old, new, aligned))
        self.assertTrue(events.loc[events.membership_event != 'continuing', 'cluster_changed'].isna().all())

    def test_alignment_ignores_input_order_and_entry_only_clusters(self):
        old = pd.Series([0, 0, 1, 1], index=list('ABCD'))
        new = pd.Series([5, 5, 9, 9, 7], index=list('ABCDE'))
        a, _ = align_members(old, new)
        b, _ = align_members(old.sample(frac=1, random_state=2), new.sample(frac=1, random_state=3))
        pd.testing.assert_series_equal(a.sort_index(), b.sort_index())
        self.assertGreater(a.E, old.max())

    def test_deviation_definition_and_singleton(self):
        frame = pd.DataFrame({'cluster': [0,0,1], 'fundamentals_imputed': [False,False,True],
                              'volume_imputed': [False]*3})
        scaled = np.array([[0.,0.], [2.,2.], [4.,10.]])
        shap = pd.DataFrame({'cluster': [0,0,1,1], 'feature': ['a','b']*2,
                             'mean_abs_shap_members': [1.,2.,3.,1.]})
        table, summary = deviation_comparison(frame, scaled, ['a','b'], shap)
        np.testing.assert_array_equal(table[table.cluster == 1].signed_median_deviation, [2,8])
        self.assertTrue(table[table.cluster == 1].imputation_sensitive.all())
        self.assertTrue(table[table.cluster == 1].interpretation.str.contains('singleton').all())
        self.assertTrue(pd.isna(summary.loc[summary.cluster == 0, 'rank_correlation'].iloc[0]))

    def test_all_date_observation_population(self):
        source = Path(__file__).resolve().parents[1]/'data/processed/Top40_Retrospective_Model_Inputs_v1.csv'
        frame = pd.read_csv(source)
        counts = frame.groupby('ticker').decision_date.nunique()
        self.assertEqual(int((counts == 3).sum()), 39)
        self.assertEqual(len(counts), 43)

    def test_saved_objectives_disagree_on_four_instruments(self):
        source = Path(__file__).resolve().parents[1]/'experiments/runs/final-full-42/assignments.csv'
        frame = pd.read_csv(source)
        old = frame[frame.decision_date == '2025-12-31'].set_index('ticker').cluster
        new = frame[frame.decision_date == '2026-06-30'].set_index('ticker').cluster
        common = old.index.intersection(new.index)
        overlap, _ = align_members(old, new, 'overlap')
        jaccard, _ = align_members(old, new, 'jaccard')
        a, b = old.loc[common] != overlap.loc[common], old.loc[common] != jaccard.loc[common]
        self.assertEqual(set(common[a != b]), {'AGL', 'MTN', 'NPN', 'SOL'})
        self.assertEqual(int(a.sum()), 10)
        self.assertEqual(int(b.sum()), 10)
