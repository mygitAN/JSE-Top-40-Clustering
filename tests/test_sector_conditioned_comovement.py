"""Check the new conditional randomisation separately from the frozen protocol."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import numpy as np

from research.sector_conditioned_comovement.run import (
    eligible_pairs, holm, main, permute_within_sectors, statistics,
)


class SectorConditionedComovementTests(unittest.TestCase):
    def test_saved_evidence_matches_manifest(self):
        root = Path(__file__).resolve().parents[1]
        manifest = json.loads((root / 'research/sector_conditioned_comovement/manifest.json').read_text(encoding='utf-8'))
        for name, expected in manifest['files_sha256'].items():
            self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), expected, name)

    def test_permutations_preserve_every_sector_cluster_multiset(self):
        sectors = np.array(['a', 'a', 'a', 'b', 'b', 'b', 'c'])
        labels = np.array([0, 0, 1, 0, 2, 2, 3])
        rng = np.random.default_rng(42)
        changed = False
        for _ in range(100):
            shuffled = permute_within_sectors(labels, sectors, rng)
            changed |= not np.array_equal(shuffled, labels)
            for sector in set(sectors):
                self.assertEqual(Counter(shuffled[sectors == sector]), Counter(labels[sectors == sector]))
        self.assertTrue(changed)

    def test_pair_exclusion_keeps_other_pairs(self):
        tickers = ['A', 'INL', 'INP', 'B']
        i, j = eligible_pairs(tickers)
        pairs = {frozenset((tickers[a], tickers[b])) for a, b in zip(i, j)}
        self.assertEqual(len(pairs), 5)
        self.assertNotIn(frozenset(('INL', 'INP')), pairs)

    def test_known_within_sector_contrast_and_coefficient(self):
        # AB shares both labels; CD shares a sector but not a cluster.
        y = np.array([.8, 0., 0., 0., 0., .2])
        sector = np.array([True, False, False, False, False, True])
        cluster = np.array([True, False, False, False, False, False])
        difference, coefficient = statistics(y, sector, cluster)
        self.assertAlmostEqual(difference, .6)
        self.assertAlmostEqual(coefficient, .6)
        with self.assertRaises(ValueError):
            statistics(y, sector, np.zeros(6, dtype=bool))

    def test_holm_adjustment_hand_calculated(self):
        np.testing.assert_allclose(holm([.03, .01, .04]), [.06, .03, .06])

    def test_future_window_option_is_rejected_before_loading_inputs(self):
        with patch.object(sys, 'argv', ['run.py', '--prospective']):
            with self.assertRaises(SystemExit):
                main()


if __name__ == '__main__':
    unittest.main()
