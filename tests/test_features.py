import unittest

import numpy as np
import pandas as pd

from top40.data import DATES, load_inputs
from top40.features import (FEATURE_SETS, add_derived_columns, dual_listed_shares, get_feature_set,
                            share_basis_audit)

BASIS_DEPENDENT = {'shares_outstanding', 'log_shares', 'eps_zar_model', 'average_daily_volume_1y_model', 'log_volume'}


class FeatureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = load_inputs()
        cls.frame = add_derived_columns(cls.raw, DATES[0])

    def test_no_row_lost_and_every_feature_finite(self):
        self.assertEqual(len(self.frame), 123)
        for feature_set in FEATURE_SETS.values():
            self.assertTrue(np.isfinite(self.frame[list(feature_set.columns)].to_numpy()).all(), feature_set.name)
            self.assertEqual(len(feature_set.columns), len(feature_set.labels))
            self.assertNotIn('sector_label', feature_set.columns)

    def test_original_set_is_unchanged(self):
        self.assertEqual(list(get_feature_set('original10').columns),
                         ['return_1y', 'average_daily_volume_1y_model', 'market_cap_zar', 'beta_1y',
                          'shares_outstanding', 'revenue_zar_model', 'eps_zar_model', 'annualised_volatility_1y',
                          'dividend_yield', 'earnings_yield_model_clipped'])
        pd.testing.assert_frame_equal(self.frame[self.raw.columns], self.raw)

    def test_invariant_sets_exclude_basis_dependent_columns(self):
        for name in ['invariant8', 'market5']:
            self.assertFalse(BASIS_DEPENDENT & set(get_feature_set(name).columns), name)

    def test_naspers_subdivision_is_removed_on_a_common_basis(self):
        audit = share_basis_audit(self.frame).set_index(['ticker', 'before'])
        row = audit.loc[('NPN', DATES[0])]
        self.assertAlmostEqual(row.shares_ratio_raw, 4.565, places=3)
        self.assertAlmostEqual(row.shares_ratio_common_basis, 0.913, places=3)
        self.assertAlmostEqual(row.eps_ratio_raw * 5, row.eps_ratio_common_basis)
        self.assertTrue(row.recorded_subdivision)
        # No other share-count jump above the threshold is left unexplained.
        self.assertTrue(audit.recorded_subdivision.all())

    def test_a_subdivision_changes_only_basis_dependent_features(self):
        split = self.raw.copy()
        target = (split.ticker == 'ABG') & (split.decision_date == DATES[1])
        split.loc[target, 'shares_outstanding'] *= 2
        split.loc[target, 'average_daily_volume_1y_model'] *= 2
        split.loc[target, ['close_zar', 'eps_zar_raw', 'eps_zar_model']] /= 2
        derived = add_derived_columns(split, DATES[0])
        invariant = list(get_feature_set('invariant8').columns)
        np.testing.assert_allclose(derived.loc[target, invariant], self.frame.loc[target, invariant])
        self.assertFalse(np.allclose(derived.loc[target, 'log_shares'], self.frame.loc[target, 'log_shares']))

    def test_naspers_volume_is_restated_to_one_basis(self):
        npn = self.frame[self.frame.ticker == 'NPN'].set_index('decision_date')
        self.assertEqual(npn.volume_corrected.tolist(), [False, True, True])
        self.assertFalse(self.frame.volume_basis_mixed.any())
        self.assertAlmostEqual(npn.volume_line_basis[DATES[1]], 2140028.5)
        # The raw column is untouched, so original10 still reproduces earlier results.
        self.assertAlmostEqual(npn.average_daily_volume_1y_model[DATES[1]], 800934.676)
        # On one basis, turnover moves by less than a quarter (0.1 in log10) between dates.
        self.assertLess(npn.log_turnover.diff().abs().max(), .1)

    def test_unrestated_mixed_window_is_flagged(self):
        no_corrections = pd.DataFrame(columns=['decision_date', 'ticker', 'average_daily_volume'])
        derived = add_derived_columns(self.raw, DATES[0], corrections=no_corrections)
        flagged = derived[derived.volume_basis_mixed]
        self.assertEqual(set(zip(flagged.ticker, flagged.decision_date)), {('NPN', DATES[1]), ('NPN', DATES[2])})

    def test_investec_lines_get_their_own_share_counts(self):
        investec = self.frame[self.frame.ticker.isin(['INL', 'INP'])]
        for date, rows in investec.groupby('decision_date'):
            rows = rows.set_index('ticker')
            # The two lines split the combined count; neither keeps all of it.
            self.assertAlmostEqual(rows.shares_line.sum(), rows.shares_outstanding.iloc[0], places=3)
            self.assertTrue(.70 < rows.shares_line['INP'] / rows.shares_outstanding['INP'] < .72, date)
            self.assertLess(rows.market_cap_line['INL'], rows.market_cap_zar['INL'] / 3)
            # Valuation uses the whole group: same revenue/cap for both lines.
            self.assertAlmostEqual(rows.log_sales_to_cap['INL'], rows.log_sales_to_cap['INP'])
        others = self.frame[~self.frame.ticker.isin(['INL', 'INP'])]
        np.testing.assert_array_equal(others.shares_line, others.shares_outstanding)

    def test_dual_listed_fractions_follow_the_disclosures(self):
        table = dual_listed_shares().set_index(['decision_date', 'ticker'])
        self.assertAlmostEqual(table.fraction[(DATES[0], 'INP')], 645162307 / 902774603)
        self.assertAlmostEqual(table.fraction[(DATES[2], 'INL')], 256396598 / 886938062)
        self.assertAlmostEqual(table.fraction[(DATES[1], 'INP')],
                               (table.fraction[(DATES[0], 'INP')] + table.fraction[(DATES[2], 'INP')]) / 2)
        self.assertTrue(set(table.index) <= set(zip(self.raw.decision_date, self.raw.ticker)))

    def test_derived_imputation_uses_fit_date_only(self):
        changed = self.raw.copy()
        changed.loc[changed.decision_date != DATES[0], 'market_cap_zar'] *= 7
        derived = add_derived_columns(changed, DATES[0])
        rni = derived.ticker == 'RNI'
        self.assertEqual(derived.loc[rni, 'log_sales_to_cap'].nunique(), 1)
        np.testing.assert_allclose(derived.loc[rni, 'log_sales_to_cap'], self.frame.loc[rni, 'log_sales_to_cap'])

    def test_unknown_feature_set(self):
        with self.assertRaisesRegex(ValueError, 'Unknown feature set'):
            get_feature_set('typo')


if __name__ == '__main__':
    unittest.main()
