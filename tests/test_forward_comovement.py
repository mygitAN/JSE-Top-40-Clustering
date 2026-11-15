"""Checks on the economic units, temporal boundary and matched-control design."""
import unittest

import numpy as np
import pandas as pd

from validation.forward_comovement.run import block_draws, estimate, residualise, return_panel, weight_system


def cohort():
    return pd.DataFrame({
        'ticker': ['A', 'B', 'C', 'D', 'INL', 'INP'],
        'economic_group': ['A', 'B', 'C', 'D', 'INVESTEC', 'INVESTEC'],
        'cluster': [0, 0, 1, 1, 0, 0],
        'sector_label': ['S', 'T', 'S', 'T', 'S', 'S'],
        'formation_log_market_cap': [1., 2., 1.1, 2.1, 1.5, 1.5],
        'formation_volatility': [.1, .2, .11, .21, .15, .15],
    })


class ForwardComovementTests(unittest.TestCase):
    def test_first_forward_day_uses_formation_close(self):
        rows = []
        for symbol, values in [('A.JO', [100, 110, 121]), ('^J200.JO', [200, 220, 242])]:
            for date, value in zip(pd.to_datetime(['2025-06-30', '2025-07-01', '2025-07-02']), values):
                rows.append(dict(date=date, symbol=symbol, close=value))
        x, market, dates = return_panel(pd.DataFrame(rows), ['A'], '2025-06-30',
                                       '2025-07-01', '2025-07-02', 'close')
        np.testing.assert_allclose(x[:, 0], [.1, .1])
        np.testing.assert_allclose(market, [.1, .1])
        self.assertEqual(dates[0], pd.Timestamp('2025-07-01'))

    def test_missing_price_stops_instead_of_filling(self):
        p = pd.DataFrame({'date': pd.to_datetime(['2025-06-30'] * 2 + ['2025-07-01'] * 2),
                          'symbol': ['A.JO', '^J200.JO'] * 2,
                          'close': [100., 100., np.nan, 101.]})
        with self.assertRaisesRegex(ValueError, 'Missing/nonpositive'):
            return_panel(p, ['A'], '2025-06-30', '2025-07-01', '2025-07-01', 'close')

    def test_own_company_and_dual_line_pair_are_excluded(self):
        weights, _, _, _ = weight_system(cohort())
        for matrix in weights.values():
            np.testing.assert_array_equal(np.diag(matrix), 0)
            self.assertEqual(matrix[4, 5], 0)
            self.assertEqual(matrix[5, 4], 0)

    def test_company_balance_does_not_double_weight_investec(self):
        weights, _, _, _ = weight_system(cohort())
        row_mass = weights['sector_cluster'].sum(axis=1)
        self.assertAlmostEqual(row_mass[0], .2)
        self.assertAlmostEqual(row_mass[4], .1)
        self.assertAlmostEqual(row_mass[5], .1)

    def test_controls_match_peer_sector_and_are_cross_cluster(self):
        frame = cohort().set_index('ticker')
        _, _, matches, _ = weight_system(cohort())
        self.assertGreater(len(matches), 0)
        for match in matches.itertuples():
            self.assertEqual(frame.loc[match.peer, 'sector_label'], frame.loc[match.alternative, 'sector_label'])
            self.assertNotEqual(frame.loc[match.focal, 'cluster'], frame.loc[match.alternative, 'cluster'])
            self.assertNotEqual(frame.loc[match.focal, 'economic_group'], frame.loc[match.alternative, 'economic_group'])

    def test_matched_selection_does_not_use_forward_outcomes(self):
        weights, _, matches, _ = weight_system(cohort())
        x = np.random.default_rng(4).normal(size=(100, 6))
        first, _ = estimate(x, weights)
        second, _ = estimate(x * np.array([1, -1, 1, -1, 1, 1]), weights)
        pd.testing.assert_frame_equal(matches, weight_system(cohort())[2])
        self.assertNotEqual(first['matched_delta'], second['matched_delta'])

    def test_constant_correlations_have_zero_contrasts(self):
        weights, _, _, _ = weight_system(cohort())
        x = np.tile(np.arange(100.)[:, None], (1, 6))
        values, _ = estimate(x, weights)
        for name in ['sector_delta', 'matched_delta', 'cross_cluster_delta']:
            self.assertAlmostEqual(values[name], 0, places=12)

    def test_residuals_are_orthogonal_to_market_and_intercept(self):
        rng = np.random.default_rng(21)
        market = rng.normal(size=100)
        x = 2 + np.outer(market, [1, 2]) + rng.normal(size=(100, 2))
        residual = residualise(x, market)
        np.testing.assert_allclose(residual.mean(axis=0), 0, atol=1e-12)
        np.testing.assert_allclose(market @ residual, 0, atol=1e-10)

    def test_synchronous_bootstrap_preserves_identical_columns(self):
        weights, _, _, _ = weight_system(cohort())
        x = np.tile(np.arange(100.)[:, None], (1, 6))
        keys, draws = block_draws(x, weights, 10, 25, np.random.default_rng(3))
        for name in ['sector_delta', 'matched_delta', 'cross_cluster_delta']:
            np.testing.assert_allclose(draws[:, keys.index(name)], 0, atol=1e-12)


if __name__ == '__main__':
    unittest.main()
