import csv
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from validate_data import DATA, validate, derive_constants


class DataTests(unittest.TestCase):
    def test_complete_validation_and_workbook_reconciliation(self):
        result = validate()
        self.assertTrue(result['workbook_reconciled'])

    def test_constants_use_only_june_2025(self):
        with DATA.open(newline='', encoding='utf-8') as stream:
            rows = list(csv.DictReader(stream))
        original = derive_constants(rows)
        changed = copy.deepcopy(rows)
        for r in changed:
            if r['decision_date'] != '2025-06-30':
                for key in ['revenue_zar_raw', 'eps_zar_raw', 'earnings_yield_raw', 'average_daily_volume_1y_model']:
                    r[key] = '100000000000000'
        self.assertEqual(original, derive_constants(changed))

    def test_missing_required_data_fails(self):
        with self.assertRaises(FileNotFoundError):
            validate(data=DATA.parent/'absent.csv')

    def test_validation_checks_survive_optimization(self):
        import subprocess
        result = subprocess.run([sys.executable, '-O', '-c',
            'import sys; sys.path.insert(0,sys.argv[1]); from validate_data import require; require(False,"still checked")',
            str(DATA.parents[2]/'scripts')], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('still checked', result.stderr)

    def test_corrupt_flags_and_model_values_fail(self):
        import tempfile
        with DATA.open(newline='', encoding='utf-8') as stream:
            rows = list(csv.DictReader(stream))
        for key, value in [('volume_imputed', 'maybe'), ('revenue_zar_model', '1'), ('ticker', 'FAKE')]:
            changed = copy.deepcopy(rows)
            changed[0][key] = value
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp)/'bad.csv'
                with path.open('w', newline='', encoding='utf-8') as stream:
                    writer = csv.DictWriter(stream, fieldnames=changed[0].keys())
                    writer.writeheader(); writer.writerows(changed)
                with self.assertRaises(AssertionError):
                    validate(data=path)
