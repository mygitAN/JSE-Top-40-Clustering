import unittest

import numpy as np
import pandas as pd

from top40.temporal import align_members, aligned_histories, membership_matrices, sector_context


class TemporalTests(unittest.TestCase):
    def test_permuted_labels_align(self):
        old = pd.Series([0, 0, 1, 1], index=list('ABCD'))
        new = pd.Series([5, 5, 3, 3, 5], index=list('ABCDE'))
        for objective in ['jaccard', 'overlap']:
            aligned, _ = align_members(old, new, objective)
            np.testing.assert_array_equal(aligned.loc[old.index], old)

    def test_unmatched_clusters_get_fresh_ids(self):
        old = pd.Series([0, 0, 1], index=list('ABC'))
        aligned, details = align_members(old, pd.Series([5, 5, 6, 7], index=list('ABDE')))
        self.assertEqual(aligned.A, 0)
        self.assertTrue(aligned.D > 1 and aligned.E > 1 and aligned.D != aligned.E)
        self.assertEqual(sum(d['matched'] for d in details), 1)
        aligned, _ = align_members(old, pd.Series([5, 6], index=list('XY')))
        self.assertTrue((aligned > 1).all())

    def test_jaccard_is_a_ratio_not_a_count(self):
        counts, jaccard, n = membership_matrices(pd.Series([0, 0, 1], index=list('ABC')),
                                                 pd.Series([7, 8, 8], index=list('ABC')))
        self.assertEqual((n, counts.loc[0, 8]), (3, 1))
        self.assertAlmostEqual(jaccard.loc[0, 8], 1 / 3)
        self.assertAlmostEqual(jaccard.loc[0, 7], .5)

    def test_entries_and_exits_do_not_lower_overlap(self):
        counts, jaccard, n = membership_matrices(pd.Series([0, 0], index=['A', 'EXIT']),
                                                 pd.Series([4, 4], index=['A', 'ENTRY']))
        self.assertEqual((n, counts.loc[0, 4], jaccard.loc[0, 4]), (1, 1, 1))

    def test_empty_unions_are_undefined(self):
        _, jaccard, _ = membership_matrices(pd.Series([0, 1], index=['A', 'EXIT']),
                                            pd.Series([3, 4], index=['A', 'ENTRY']))
        self.assertTrue(np.isnan(jaccard.loc[1, 4]))

    def test_duplicate_instruments_are_rejected(self):
        with self.assertRaises(ValueError):
            membership_matrices(pd.Series([0, 1], index=['A', 'A']), pd.Series([2], index=['A']))

    def test_histories_separate_shifts_from_membership_gaps(self):
        dates = ['a', 'b', 'c']
        frames = {d: pd.DataFrame(dict(ticker=['A', 'B', 'C', extra], cluster=labels))
                  for d, extra, labels in [('a', 'X', [0, 0, 1, 1]), ('b', 'Y', [4, 4, 7, 7]),
                                           ('c', 'Y', [8, 8, 8, 6])]}
        aligned, maps, events, histories, objective, agreement = aligned_histories(frames, dates)
        status = histories.set_index('ticker').stability_status
        self.assertEqual(status[['A', 'B', 'C', 'X', 'Y']].tolist(),
                         ['stable', 'stable', 'shifted', 'membership gap', 'membership gap'])
        self.assertTrue(events.loc[events.membership_event != 'continuing', 'cluster_changed'].isna().all())
        self.assertEqual(agreement.continuing.tolist(), [3, 4])
        self.assertEqual(agreement.changed.tolist(), [0, 1])
        self.assertEqual(agreement.ari.iloc[0], 1)

    def test_extinct_ids_are_not_reused(self):
        dates = ['a', 'b', 'c']
        frames = {'a': pd.DataFrame(dict(ticker=list('ABCD'), cluster=[0, 0, 1, 1])),
                  'b': pd.DataFrame(dict(ticker=list('ABCD'), cluster=[0, 0, 0, 0])),
                  'c': pd.DataFrame(dict(ticker=list('ABCD'), cluster=[0, 0, 1, 1]))}
        aligned, *_ = aligned_histories(frames, dates)
        self.assertNotIn(1, set(aligned['c']))

    def test_sector_context_leaves_singletons_and_ties_unresolved(self):
        frame = pd.DataFrame(dict(ticker=list('ABCDEF'), cluster=[0, 0, 0, 1, 2, 2],
                                  sector_label=['x', 'x', 'y', 'x', 'x', 'y']))
        context = sector_context(frame).set_index('ticker')
        self.assertEqual(context.sector_status['D'], 'singleton')
        self.assertIsNone(context.sector_divergence['D'])
        self.assertTrue(context.sector_divergence['C'])
        self.assertEqual(context.sector_status['A'], 'tied majority')
        self.assertEqual(context.sector_status['E'], 'compared')


if __name__ == '__main__':
    unittest.main()
