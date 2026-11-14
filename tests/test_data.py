import copy
import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from top40 import INPUTS, ROOT
from top40.data import derive_constants, validate


def read_rows():
    with INPUTS.open(newline='', encoding='utf-8') as stream:
        return list(csv.DictReader(stream))


class DataTests(unittest.TestCase):
    def test_inputs_reconcile_to_workbook(self):
        self.assertTrue(validate()['workbook_reconciled'])

    def test_constants_use_only_june_2025(self):
        rows = read_rows()
        changed = copy.deepcopy(rows)
        for row in changed:
            if row['decision_date'] != '2025-06-30':
                for key in ['revenue_zar_raw', 'eps_zar_raw', 'earnings_yield_raw', 'average_daily_volume_1y_model']:
                    row[key] = '100000000000000'
        self.assertEqual(derive_constants(rows), derive_constants(changed))

    def test_missing_file_fails(self):
        with self.assertRaises(FileNotFoundError):
            validate(data=INPUTS.parent / 'absent.csv')

    def test_checks_survive_python_optimisation(self):
        code = 'from top40.data import require; require(False, "still checked")'
        result = subprocess.run([sys.executable, '-O', '-c', code], capture_output=True, text=True, cwd=ROOT)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('still checked', result.stderr)

    def test_corrupt_values_fail(self):
        rows = read_rows()
        for key, value in [('volume_imputed', 'maybe'), ('revenue_zar_model', '1'), ('ticker', 'FAKE')]:
            changed = copy.deepcopy(rows)
            changed[0][key] = value
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / 'bad.csv'
                with path.open('w', newline='', encoding='utf-8') as stream:
                    writer = csv.DictWriter(stream, fieldnames=changed[0].keys())
                    writer.writeheader()
                    writer.writerows(changed)
                with self.assertRaises(AssertionError):
                    validate(data=path)


if __name__ == '__main__':
    unittest.main()
