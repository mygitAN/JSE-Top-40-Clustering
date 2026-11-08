"""Validate the retained 123-row retrospective dataset without third-party packages."""
import csv
import json
import math
import statistics
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/processed/Top40_Retrospective_Model_Inputs_v1.csv'
METHOD = ROOT / 'docs/Top40_Retrospective_Model_Method_v1.json'


def require(condition, message):
    """Checks remain enabled under python -O."""
    if not condition:
        raise AssertionError(message)


def percentile(values, q):
    values = sorted(values)
    index = (len(values)-1)*q
    lo = math.floor(index)
    hi = math.ceil(index)
    return values[lo] + (values[hi]-values[lo])*(index-lo)


def derive_constants(rows):
    train = [r for r in rows if r['decision_date'] == '2025-06-30']
    median = lambda key, flag: statistics.median(float(r[key]) for r in train if r[flag] == 'false')
    yields = [float(r['earnings_yield_raw']) for r in train if r['earnings_yield_raw']]
    return dict(volume=median('average_daily_volume_1y_model', 'volume_imputed'),
                revenue=median('revenue_zar_raw', 'fundamentals_imputed'),
                eps=median('eps_zar_raw', 'fundamentals_imputed'),
                earnings_yield=median('earnings_yield_raw', 'fundamentals_imputed'),
                lower=percentile(yields, .01), upper=percentile(yields, .99))


def validate(data=None, method_path=None):
    with Path(data or DATA).open(newline='', encoding='utf-8') as stream:
        rows = list(csv.DictReader(stream))
    method = json.loads(Path(method_path or METHOD).read_text(encoding='utf-8'))
    derived = derive_constants(rows)
    recorded = dict(volume=method['volume_imputation']['value'],
                    revenue=method['fundamental_imputation']['revenue_zar'],
                    eps=method['fundamental_imputation']['eps_zar'],
                    earnings_yield=method['fundamental_imputation']['earnings_yield'],
                    lower=method['earnings_yield_clipping']['lower'], upper=method['earnings_yield_clipping']['upper'])
    for key in recorded:
        require(math.isclose(derived[key], recorded[key], rel_tol=1e-12, abs_tol=1e-12), ('Derivation mismatch', key, derived[key], recorded[key]))
    dates = ['2025-06-30', '2025-12-31', '2026-06-30']
    require(len(rows) == 123, 'All 123 historical observations must be retained')
    require(Counter(r['decision_date'] for r in rows) == dict.fromkeys(dates, 41), "Input validation failed: Counter(r['decision_date'] for r in rows) == dict.fromkeys(dates, 41)")
    require(len({(r['decision_date'], r['ticker']) for r in rows}) == 123, "Input validation failed: len({(r['decision_date'], r['ticker']) for r in rows}) == 123")
    require(len({r['ticker'] for r in rows}) == 43, "Input validation failed: len({r['ticker'] for r in rows}) == 43")
    membership = {d: {r['ticker'] for r in rows if r['decision_date'] == d} for d in dates}
    require(membership[dates[1]] == (membership[dates[0]] - {'APN'}) | {'GLN'}, "Input validation failed: membership[dates[1]] == (membership[dates[0]] - {'APN'}) | {'GLN'}")
    require(membership[dates[2]] == (membership[dates[1]] - {'MNP'}) | {'PAN'}, "Input validation failed: membership[dates[2]] == (membership[dates[1]] - {'MNP'}) | {'PAN'}")
    require(all('RNI' in membership[d] and 'NPH' in membership[d] for d in dates), "Input validation failed: all('RNI' in membership[d] and 'NPH' in membership[d] for d in dates)")
    require({ (r['decision_date'], r['ticker']) for r in rows if r['volume_imputed'] == 'true'} == {(dates[0], 'AGL'), (dates[1], 'AGL')}, "Input validation failed: { (r['decision_date'], r['ticker']) for r in rows if r['volume_imputed'] == 'true'} == {(dates[0], 'AGL'), (dates[1], 'AGL')}")
    require({ (r['decision_date'], r['ticker']) for r in rows if r['fundamentals_imputed'] == 'true'} == {(d, 'RNI') for d in dates}, "Input validation failed: { (r['decision_date'], r['ticker']) for r in rows if r['fundamentals_imputed'] == 'true'} == {(d, 'RNI') for d in dates}")
    numeric = ['return_1y', 'average_daily_volume_1y_model', 'market_cap_zar', 'beta_1y',
               'shares_outstanding', 'revenue_zar_model', 'eps_zar_model',
               'annualised_volatility_1y', 'dividend_yield', 'earnings_yield_model_clipped', 'close_zar']
    for r in rows:
        require(all(r[flag] in {'true', 'false'} for flag in ['volume_imputed', 'fundamentals_imputed']), "Input validation failed: all(r[flag] in {'true', 'false'} for flag in ['volume_imputed', 'fundamentals_imputed'])")
        require(r['sector_label'] and r['membership_evidence'] == 'VERIFIED', "Input validation failed: r['sector_label'] and r['membership_evidence'] == 'VERIFIED'")
        require(all(math.isfinite(float(r[k])) for k in numeric), (r['ticker'], 'Missing model feature'))
        require(math.isclose(float(r['market_cap_zar']), float(r['shares_outstanding']) * float(r['close_zar']), rel_tol=1e-5), "Input validation failed: math.isclose(float(r['market_cap_zar']), float(r['shares_outstanding']) * float(r['close_zar']), rel_tol=1e-5)")
        if r['volume_imputed'] == 'true':
            require(math.isclose(float(r['average_daily_volume_1y_model']), method['volume_imputation']['value']), "Input validation failed: math.isclose(float(r['average_daily_volume_1y_model']), method['volume_imputation']['value'])")
        if r['ticker'] == 'RNI':
            require(all(r[k] == '' for k in ['revenue_zar_raw', 'eps_zar_raw', 'earnings_yield_raw']), "Input validation failed: all(r[k] == '' for k in ['revenue_zar_raw', 'eps_zar_raw', 'earnings_yield_raw'])")
            for column, key in [('revenue_zar_model', 'revenue_zar'), ('eps_zar_model', 'eps_zar'), ('earnings_yield_model_clipped', 'earnings_yield')]:
                require(math.isclose(float(r[column]), method['fundamental_imputation'][key]), "Input validation failed: math.isclose(float(r[column]), method['fundamental_imputation'][key])")
        else:
            require(float(r['revenue_zar_model']) == float(r['revenue_zar_raw']), "Input validation failed: float(r['revenue_zar_model']) == float(r['revenue_zar_raw'])")
            require(float(r['eps_zar_model']) == float(r['eps_zar_raw']), "Input validation failed: float(r['eps_zar_model']) == float(r['eps_zar_raw'])")
            raw = float(r['earnings_yield_raw'])
            require(math.isclose(raw, float(r['eps_zar_raw']) / float(r['close_zar']), rel_tol=1e-9), "Input validation failed: math.isclose(raw, float(r['eps_zar_raw']) / float(r['close_zar']), rel_tol=1e-9)")
            bounds = method['earnings_yield_clipping']
            expected = max(bounds['lower'], min(bounds['upper'], raw))
            require(math.isclose(float(r['earnings_yield_model_clipped']), expected, rel_tol=1e-9), "Input validation failed: math.isclose(float(r['earnings_yield_model_clipped']), expected, rel_tol=1e-9)")
    reconcile_workbook(rows, dates)
    print('PASS: 123 rows; 41 per date; 43 tickers; 3 RNI rows retained; 2 volume imputations; model features complete.')
    return {'derived_constants': derived, 'workbook_reconciled': True}


def reconcile_workbook(rows, dates):
    from audit_workbook import read_workbook
    sheets = read_workbook()
    columns = {'F': 'return_1y', 'H': 'market_cap_zar', 'I': 'beta_1y', 'K': 'shares_outstanding',
               'L': 'revenue_zar_raw', 'M': 'eps_zar_raw', 'N': 'annualised_volatility_1y',
               'O': 'dividend_yield', 'AR': 'close_zar', 'AT': 'earnings_yield_raw'}
    for date in dates:
        raw = sheets[date][1:]
        lookup = {next(v for k, v in r.items() if k.rstrip('0123456789') == 'B'): r for r in raw}
        selected = [r for r in rows if r['decision_date'] == date]
        require(set(lookup) == {r['ticker'] for r in selected}, ('Workbook membership mismatch', date))
        for r in selected:
            cells = {k.rstrip('0123456789'): v for k, v in lookup[r['ticker']].items()}
            require(cells.get('E', '') == '', 'Unavailable analyst ratings must remain blank')
            require(cells['D'] == r['sector_label'], "Input validation failed: cells['D'] == r['sector_label']")
            require(cells['AL'] == r['membership_evidence'], "Input validation failed: cells['AL'] == r['membership_evidence']")
            for col, key in columns.items():
                source = cells.get(col, '')
                require((source == '') == (r[key] == ''), (date, r['ticker'], key, 'Missingness mismatch'))
                if source:
                    require(math.isclose(float(source), float(r[key]), rel_tol=1e-12, abs_tol=1e-12), (date, r['ticker'], key))
            volume = cells.get('G', '')
            require((not volume) == (r['volume_imputed'] == 'true'), "Input validation failed: (not volume) == (r['volume_imputed'] == 'true')")
            if volume:
                require(math.isclose(float(volume), float(r['average_daily_volume_1y_model']), rel_tol=1e-12), "Input validation failed: math.isclose(float(volume), float(r['average_daily_volume_1y_model']), rel_tol=1e-12)")
    for i, date in enumerate(dates):
        members = set()
        for row in sheets['Ticker Membership'][1:]:
            cells = {k.rstrip('0123456789'): v for k, v in row.items()}
            if cells[chr(ord('E')+i)] == '1':
                members.add(cells['A'])
        require(members == {r['ticker'] for r in rows if r['decision_date'] == date}, "Input validation failed: members == {r['ticker'] for r in rows if r['decision_date'] == date}")


if __name__ == '__main__':
    validate()
