"""Integrity and reserved-window checks for the frozen primary experiment."""
from datetime import date
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

import pandas as pd

from research.comovement.reproduce import verify

HERE = Path(__file__).resolve().parents[1] / 'research/comovement'


class PrimaryComovementFreezeTests(unittest.TestCase):
    def test_all_frozen_files_match_manifest(self):
        manifest = verify()
        outputs = [p for p in manifest['files_sha256'] if p.startswith('output/')]
        self.assertEqual(len(outputs), 4)

    def test_future_labels_are_frozen_but_future_returns_are_not_included(self):
        labels = pd.read_csv(HERE / 'inputs/partitions.csv')
        self.assertEqual(set(labels.formation_date), {'2025-06-30', '2025-12-31', '2026-06-30'})
        for _, group in labels.groupby(['formation_date', 'grouping']):
            self.assertEqual(len(group), 41)
            self.assertEqual(group.ticker.nunique(), 41)
        prices = pd.read_csv(HERE / 'inputs/prices.csv', parse_dates=['date'])
        self.assertEqual(prices.date.max(), pd.Timestamp('2026-06-30'))
        saved = pd.read_csv(HERE / 'output/comovement_summary.csv')
        self.assertEqual(set(saved.formation_date), {'2025-06-30', '2025-12-31'})

    def test_reserved_command_stops_before_download_or_evaluation(self):
        spec = importlib.util.spec_from_file_location('primary_guard_test', HERE / 'forward_comovement.py')
        primary = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(primary)
        clock = Mock()
        clock.today.return_value = date(2026, 11, 15)
        with patch.object(primary, 'calendar_date', clock), \
                patch.object(primary, 'download') as download, \
                patch.object(primary, 'forward_returns') as evaluate, \
                patch.object(sys, 'argv', ['forward_comovement.py', '--prospective']):
            with self.assertRaisesRegex(SystemExit, '2027-01-05'):
                primary.main()
        download.assert_not_called()
        evaluate.assert_not_called()

    def test_protocol_distinguishes_primary_and_later_exploratory_hypotheses(self):
        protocol = json.loads((HERE / 'protocol.json').read_text(encoding='utf-8'))
        self.assertIn('Primary', protocol['H1']['role'])
        self.assertIn('exploratory', protocol['H2']['role'])
        self.assertIn('after observing', protocol['status'])
        self.assertEqual(protocol['interval']['replicates'], 2000)
        self.assertEqual(protocol['random_group_test']['permutations'], 10000)


if __name__ == '__main__':
    unittest.main()
