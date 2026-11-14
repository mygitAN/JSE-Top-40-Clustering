"""Load and validate the 123-row model-input table against its source workbook.

Validation uses only the standard library so it can run before any package is
installed: ``python -m top40.data``.
"""
import csv
import json
import math
import posixpath
import statistics
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from pathlib import Path

from . import DATA_POLICY, INPUTS, WORKBOOK

DATES = ['2025-06-30', '2025-12-31', '2026-06-30']
NUMERIC = ['return_1y', 'average_daily_volume_1y_model', 'market_cap_zar', 'beta_1y',
           'shares_outstanding', 'revenue_zar_model', 'eps_zar_model',
           'annualised_volatility_1y', 'dividend_yield', 'earnings_yield_model_clipped', 'close_zar']
_NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
_REL = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'


def require(condition, message):
    """An explicit check that stays enabled under ``python -O``."""
    if not condition:
        raise AssertionError(message)


def load_inputs(path=None):
    import pandas as pd
    return pd.read_csv(path or INPUTS)


def read_workbook(path=None):
    """Read every sheet as a list of {cell reference: text} rows, without Excel."""
    with zipfile.ZipFile(path or WORKBOOK) as archive:
        shared = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            shared = [''.join(node.itertext())
                      for node in ET.fromstring(archive.read('xl/sharedStrings.xml')).findall('s:si', _NS)]
        targets = {r.attrib['Id']: r.attrib['Target']
                   for r in ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))}
        sheets = {}
        for sheet in ET.fromstring(archive.read('xl/workbook.xml')).findall('s:sheets/s:sheet', _NS):
            target = targets[sheet.attrib[_REL]]
            target = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/' + target)
            rows = []
            for row in ET.fromstring(archive.read(target)).findall('s:sheetData/s:row', _NS):
                cells = {}
                for cell in row.findall('s:c', _NS):
                    value = cell.findtext('s:v', default='', namespaces=_NS)
                    if cell.attrib.get('t') == 's':
                        value = shared[int(value)]
                    elif cell.attrib.get('t') == 'inlineStr':
                        value = ''.join(cell.find('s:is', _NS).itertext())
                    cells[cell.attrib['r']] = value
                rows.append(cells)
            sheets[sheet.attrib['name']] = rows
        return sheets


def _percentile(values, q):
    values = sorted(values)
    index = (len(values) - 1) * q
    low, high = math.floor(index), math.ceil(index)
    return values[low] + (values[high] - values[low]) * (index - low)


def derive_constants(rows):
    """Imputation medians and earnings-yield clip bounds, from June 2025 only."""
    train = [r for r in rows if r['decision_date'] == DATES[0]]

    def median(key, flag):
        return statistics.median(float(r[key]) for r in train if r[flag] == 'false')

    yields = [float(r['earnings_yield_raw']) for r in train if r['earnings_yield_raw']]
    return dict(volume=median('average_daily_volume_1y_model', 'volume_imputed'),
                revenue=median('revenue_zar_raw', 'fundamentals_imputed'),
                eps=median('eps_zar_raw', 'fundamentals_imputed'),
                earnings_yield=median('earnings_yield_raw', 'fundamentals_imputed'),
                lower=_percentile(yields, .01), upper=_percentile(yields, .99))


def validate(data=None, policy=None):
    """Raise AssertionError unless the model inputs match the policy and workbook."""
    with Path(data or INPUTS).open(newline='', encoding='utf-8') as stream:
        rows = list(csv.DictReader(stream))
    method = json.loads(Path(policy or DATA_POLICY).read_text(encoding='utf-8'))
    derived = derive_constants(rows)
    recorded = dict(volume=method['volume_imputation']['value'],
                    revenue=method['fundamental_imputation']['revenue_zar'],
                    eps=method['fundamental_imputation']['eps_zar'],
                    earnings_yield=method['fundamental_imputation']['earnings_yield'],
                    lower=method['earnings_yield_clipping']['lower'],
                    upper=method['earnings_yield_clipping']['upper'])
    for key, value in recorded.items():
        require(math.isclose(derived[key], value, rel_tol=1e-12, abs_tol=1e-12),
                f'Recorded {key} constant differs from its June 2025 derivation')

    require(len(rows) == 123, 'Expected 123 instrument-date rows')
    require(Counter(r['decision_date'] for r in rows) == dict.fromkeys(DATES, 41), 'Expected 41 rows per date')
    require(len({(r['decision_date'], r['ticker']) for r in rows}) == 123, 'Duplicate date/ticker key')
    require(len({r['ticker'] for r in rows}) == 43, 'Expected 43 distinct tickers')
    members = {d: {r['ticker'] for r in rows if r['decision_date'] == d} for d in DATES}
    require(members[DATES[1]] == (members[DATES[0]] - {'APN'}) | {'GLN'}, 'Unexpected December 2025 membership')
    require(members[DATES[2]] == (members[DATES[1]] - {'MNP'}) | {'PAN'}, 'Unexpected June 2026 membership')
    flagged = lambda flag: {(r['decision_date'], r['ticker']) for r in rows if r[flag] == 'true'}
    require(flagged('volume_imputed') == {(DATES[0], 'AGL'), (DATES[1], 'AGL')}, 'Unexpected volume imputations')
    require(flagged('fundamentals_imputed') == {(d, 'RNI') for d in DATES}, 'Unexpected fundamental imputations')

    bounds = method['earnings_yield_clipping']
    imputed = method['fundamental_imputation']
    for r in rows:
        key = (r['decision_date'], r['ticker'])
        require(all(r[flag] in {'true', 'false'} for flag in ['volume_imputed', 'fundamentals_imputed']),
                f'{key}: invalid imputation flag')
        require(r['sector_label'] and r['membership_evidence'] == 'VERIFIED', f'{key}: sector or membership missing')
        require(all(math.isfinite(float(r[k])) for k in NUMERIC), f'{key}: missing model feature')
        require(math.isclose(float(r['market_cap_zar']), float(r['shares_outstanding']) * float(r['close_zar']),
                             rel_tol=1e-5), f'{key}: market cap is not close times shares')
        if r['volume_imputed'] == 'true':
            require(math.isclose(float(r['average_daily_volume_1y_model']), method['volume_imputation']['value']),
                    f'{key}: imputed volume is not the recorded median')
        if r['fundamentals_imputed'] == 'true':
            require(all(r[k] == '' for k in ['revenue_zar_raw', 'eps_zar_raw', 'earnings_yield_raw']),
                    f'{key}: raw fundamentals must stay blank')
            for column, name in [('revenue_zar_model', 'revenue_zar'), ('eps_zar_model', 'eps_zar'),
                                 ('earnings_yield_model_clipped', 'earnings_yield')]:
                require(math.isclose(float(r[column]), imputed[name]), f'{key}: {column} is not the recorded median')
        else:
            require(float(r['revenue_zar_model']) == float(r['revenue_zar_raw']), f'{key}: revenue model/raw differ')
            require(float(r['eps_zar_model']) == float(r['eps_zar_raw']), f'{key}: EPS model/raw differ')
            raw = float(r['earnings_yield_raw'])
            require(math.isclose(raw, float(r['eps_zar_raw']) / float(r['close_zar']), rel_tol=1e-9),
                    f'{key}: earnings yield is not EPS over close')
            clipped = max(bounds['lower'], min(bounds['upper'], raw))
            require(math.isclose(float(r['earnings_yield_model_clipped']), clipped, rel_tol=1e-9),
                    f'{key}: earnings yield clipping differs')
    _reconcile_workbook(rows)
    return {'derived_constants': derived, 'workbook_reconciled': True}


def _reconcile_workbook(rows):
    """Every model input must equal its cell in the source workbook."""
    sheets = read_workbook()
    columns = {'F': 'return_1y', 'H': 'market_cap_zar', 'I': 'beta_1y', 'K': 'shares_outstanding',
               'L': 'revenue_zar_raw', 'M': 'eps_zar_raw', 'N': 'annualised_volatility_1y',
               'O': 'dividend_yield', 'AR': 'close_zar', 'AT': 'earnings_yield_raw'}
    by_column = lambda row: {ref.rstrip('0123456789'): value for ref, value in row.items()}
    for i, date in enumerate(DATES):
        selected = [r for r in rows if r['decision_date'] == date]
        lookup = {by_column(row)['B']: by_column(row) for row in sheets[date][1:]}
        require(set(lookup) == {r['ticker'] for r in selected}, f'{date}: workbook membership differs')
        for r in selected:
            cells, key = lookup[r['ticker']], (date, r['ticker'])
            require(cells.get('E', '') == '', f'{key}: analyst rating must stay blank')
            require(cells['D'] == r['sector_label'], f'{key}: sector differs from workbook')
            require(cells['AL'] == r['membership_evidence'], f'{key}: membership evidence differs')
            for column, name in columns.items():
                source = cells.get(column, '')
                require((source == '') == (r[name] == ''), f'{key}: {name} missingness differs from workbook')
                if source:
                    require(math.isclose(float(source), float(r[name]), rel_tol=1e-12, abs_tol=1e-12),
                            f'{key}: {name} differs from workbook')
            volume = cells.get('G', '')
            require((not volume) == (r['volume_imputed'] == 'true'), f'{key}: volume flag differs from workbook')
            if volume:
                require(math.isclose(float(volume), float(r['average_daily_volume_1y_model']), rel_tol=1e-12),
                        f'{key}: volume differs from workbook')
        listed = {by_column(row)['A'] for row in sheets['Ticker Membership'][1:]
                  if by_column(row)[chr(ord('E') + i)] == '1'}
        require(listed == {r['ticker'] for r in selected}, f'{date}: membership sheet differs')


if __name__ == '__main__':
    validate()
    print('PASS: 123 rows; 41 per date; 43 tickers; model inputs reconcile to the source workbook.')
