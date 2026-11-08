"""Validate the retained 123-row retrospective dataset without third-party packages."""
import csv
import json
import math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/processed/Top40_Retrospective_Model_Inputs_v1.csv'
METHOD = ROOT / 'docs/Top40_Retrospective_Model_Method_v1.json'


def validate():
    with DATA.open(newline='', encoding='utf-8') as stream:
        rows = list(csv.DictReader(stream))
    method = json.loads(METHOD.read_text(encoding='utf-8'))
    dates = ['2025-06-30', '2025-12-31', '2026-06-30']
    assert len(rows) == 123, 'All 123 historical observations must be retained'
    assert Counter(r['decision_date'] for r in rows) == dict.fromkeys(dates, 41)
    assert len({(r['decision_date'], r['ticker']) for r in rows}) == 123
    assert len({r['ticker'] for r in rows}) == 43
    membership = {d: {r['ticker'] for r in rows if r['decision_date'] == d} for d in dates}
    assert membership[dates[1]] == (membership[dates[0]] - {'APN'}) | {'GLN'}
    assert membership[dates[2]] == (membership[dates[1]] - {'MNP'}) | {'PAN'}
    assert all('RNI' in membership[d] and 'NPH' in membership[d] for d in dates)
    assert { (r['decision_date'], r['ticker']) for r in rows if r['volume_imputed'] == 'true'} == {(dates[0], 'AGL'), (dates[1], 'AGL')}
    assert { (r['decision_date'], r['ticker']) for r in rows if r['fundamentals_imputed'] == 'true'} == {(d, 'RNI') for d in dates}
    numeric = ['return_1y', 'average_daily_volume_1y_model', 'market_cap_zar', 'beta_1y',
               'shares_outstanding', 'revenue_zar_model', 'eps_zar_model',
               'annualised_volatility_1y', 'dividend_yield', 'earnings_yield_model_clipped', 'close_zar']
    for r in rows:
        assert r['sector_label'] and r['membership_evidence'] == 'VERIFIED'
        assert all(math.isfinite(float(r[k])) for k in numeric), (r['ticker'], 'Missing model feature')
        assert math.isclose(float(r['market_cap_zar']), float(r['shares_outstanding']) * float(r['close_zar']), rel_tol=1e-5)
        if r['volume_imputed'] == 'true':
            assert math.isclose(float(r['average_daily_volume_1y_model']), method['volume_imputation']['value'])
        if r['ticker'] == 'RNI':
            assert all(r[k] == '' for k in ['revenue_zar_raw', 'eps_zar_raw', 'earnings_yield_raw'])
            for column, key in [('revenue_zar_model', 'revenue_zar'), ('eps_zar_model', 'eps_zar'), ('earnings_yield_model_clipped', 'earnings_yield')]:
                assert math.isclose(float(r[column]), method['fundamental_imputation'][key])
        else:
            raw = float(r['earnings_yield_raw'])
            assert math.isclose(raw, float(r['eps_zar_raw']) / float(r['close_zar']), rel_tol=1e-9)
            bounds = method['earnings_yield_clipping']
            expected = max(bounds['lower'], min(bounds['upper'], raw))
            assert math.isclose(float(r['earnings_yield_model_clipped']), expected, rel_tol=1e-9)
    print('PASS: 123 rows; 41 per date; 43 tickers; 3 RNI rows retained; 2 volume imputations; model features complete.')


if __name__ == '__main__':
    validate()
