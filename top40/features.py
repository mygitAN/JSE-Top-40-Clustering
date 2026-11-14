"""Feature sets, and the derived columns that make them comparable across dates.

``original10`` is the archived reference: the ten inputs used by every result
before November 2026. It contains raw share count and EPS, which change
mechanically when a company subdivides its shares, and unlogged size variables.

The other sets were defined after those results had been examined. They are
pilot-informed candidates, not a prospectively registered specification.

Derived columns apply three corrections from ``data/reference/``; the raw
input columns are never changed:

- ``corporate_actions.csv``: share subdivisions, for common-basis audit tables.
- ``volume_corrections.csv``: trailing volumes restated to one share basis.
- ``dual_listed_shares.csv``: each Investec line's own share count, instead of
  the combined dual-listed count that both rows carry.
"""
from dataclasses import dataclass

import numpy as np

from . import CORPORATE_ACTIONS, DUAL_LISTED_SHARES, VOLUME_CORRECTIONS


@dataclass(frozen=True)
class FeatureSet:
    name: str
    status: str
    description: str
    columns: tuple
    labels: tuple

    def label(self, column):
        return self.labels[self.columns.index(column)]


_SCALE_FREE = (('return_1y', '1Y return'), ('beta_1y', 'Beta'), ('annualised_volatility_1y', 'Volatility'),
               ('dividend_yield', 'Dividend yield'), ('earnings_yield_model_clipped', 'Earnings yield'))


def _feature_set(name, status, description, pairs):
    return FeatureSet(name, status, description, tuple(c for c, _ in pairs), tuple(l for _, l in pairs))


FEATURE_SETS = {s.name: s for s in [
    _feature_set('original10', 'archived reference',
                 'The ten inputs of the original three-date analysis. Share count and EPS depend on the share basis.',
                 (('return_1y', '1Y return'), ('average_daily_volume_1y_model', 'Average volume'),
                  ('market_cap_zar', 'Market cap'), ('beta_1y', 'Beta'), ('shares_outstanding', 'Shares'),
                  ('revenue_zar_model', 'Revenue'), ('eps_zar_model', 'EPS'),
                  ('annualised_volatility_1y', 'Volatility'), ('dividend_yield', 'Dividend yield'),
                  ('earnings_yield_model_clipped', 'Earnings yield'))),
    _feature_set('logsize10', 'pilot-informed diagnostic',
                 'The original ten with log10 volume, market cap, shares and revenue, on corrected share and volume '
                 'bases. Share count and EPS still change in a subdivision.',
                 (('return_1y', '1Y return'), ('log_volume', 'Log volume'), ('log_market_cap', 'Log market cap'),
                  ('beta_1y', 'Beta'), ('log_shares', 'Log shares'), ('log_revenue', 'Log revenue'),
                  ('eps_zar_model', 'EPS'), ('annualised_volatility_1y', 'Volatility'),
                  ('dividend_yield', 'Dividend yield'), ('earnings_yield_model_clipped', 'Earnings yield'))),
    _feature_set('invariant8', 'pilot-informed candidate',
                 'No feature changes under a share subdivision: five scale-free measures, log market cap, '
                 'log revenue-to-cap and log share turnover.',
                 _SCALE_FREE + (('log_market_cap', 'Log market cap'), ('log_sales_to_cap', 'Log revenue / cap'),
                                ('log_turnover', 'Log turnover'))),
    _feature_set('market5', 'pilot-informed diagnostic',
                 'The five scale-free measures only: no size, revenue or liquidity information.',
                 _SCALE_FREE),
]}


def corporate_actions(path=None):
    import pandas as pd
    return pd.read_csv(path or CORPORATE_ACTIONS, parse_dates=['effective_date', 'trading_basis_date'])


def volume_corrections(path=None):
    import pandas as pd
    return pd.read_csv(path or VOLUME_CORRECTIONS)


def dual_listed_shares(path=None):
    """Each dual-listed line's fraction of its group's outstanding shares, by decision date.

    A date marked ``midpoint`` takes the mean of the fractions at the other dates.
    """
    import pandas as pd

    table = pd.read_csv(path or DUAL_LISTED_SHARES)
    table['fraction'] = table.line_outstanding / table.group_outstanding
    for (group, ticker), rows in table.groupby(['group', 'ticker']):
        known = rows.loc[rows.method == 'disclosed', 'fraction']
        table.loc[rows.index[rows.method == 'midpoint'], 'fraction'] = known.mean()
    if table.fraction.isna().any():
        raise ValueError('Every dual-listed row needs a disclosed count or a midpoint rule')
    totals = table.groupby(['decision_date', 'group']).fraction.sum()
    if not np.allclose(totals, 1):
        raise ValueError('Dual-listed line fractions must sum to one within each group and date')
    return table


def add_derived_columns(frame, fit_date, actions=None, corrections=None, dual_listed=None):
    """Return a copy of the model inputs with every candidate feature column.

    Imputation uses the ``fit_date`` median of observed values only, mirroring
    the audited policy for the original columns. No row is dropped.
    """
    import pandas as pd

    actions = corporate_actions() if actions is None else actions
    corrections = volume_corrections() if corrections is None else corrections
    dual_listed = dual_listed_shares() if dual_listed is None else dual_listed
    out = frame.copy()
    dates = pd.to_datetime(out.decision_date)
    key = list(zip(out.decision_date, out.ticker))

    # Each dual-listed line's own outstanding shares: the combined count in the
    # inputs times the line's disclosed fraction. Other instruments are unchanged.
    fraction = pd.Series(dict(zip(zip(dual_listed.decision_date, dual_listed.ticker), dual_listed.fraction)))
    out['dual_listed_group'] = pd.Series(dict(zip(zip(dual_listed.decision_date, dual_listed.ticker),
                                                  dual_listed.group))).reindex(key).to_numpy()
    out['shares_line'] = out.shares_outstanding * fraction.reindex(key).fillna(1).to_numpy()
    out['market_cap_line'] = out.close_zar * out.shares_line

    # Trailing volume on the share basis of the decision date.
    corrected = pd.Series(dict(zip(zip(corrections.decision_date, corrections.ticker),
                                   corrections.average_daily_volume)), dtype=float).reindex(key).to_numpy()
    out['volume_corrected'] = ~np.isnan(corrected)
    out['volume_line_basis'] = np.where(out.volume_corrected, corrected, out.average_daily_volume_1y_model)

    # Shares restated to the basis in force after the last recorded subdivision,
    # for audit tables only. It is never a model feature.
    factor = pd.Series(1.0, index=out.index)
    mixed = pd.Series(False, index=out.index)
    for action in actions[actions.action == 'share_subdivision'].itertuples():
        same = out.ticker == action.ticker
        factor[same & (dates < action.effective_date)] *= action.ratio
        window_start = dates - pd.DateOffset(years=1)
        mixed |= same & (window_start < action.trading_basis_date) & (dates >= action.trading_basis_date)
    out['share_basis_factor'] = factor
    out['shares_common_basis'] = out.shares_line * factor
    out['eps_common_basis'] = out.eps_zar_raw / factor
    # Only a window that spans a subdivision and has not been restated is still mixed.
    out['volume_basis_mixed'] = mixed & ~out.volume_corrected

    for column, source in [('log_market_cap', 'market_cap_line'), ('log_shares', 'shares_line'),
                           ('log_revenue', 'revenue_zar_model'), ('log_volume', 'volume_line_basis')]:
        if (out[source] <= 0).any():
            raise ValueError(f'{source} must be positive to take logarithms')
        out[column] = np.log10(out[source])

    # Revenue relative to market value. For a dual-listed group each share is a
    # claim on the whole group (EPS and dividends are group figures), so both
    # lines use group revenue over group market cap. Each Investec row's revenue
    # is its own issuer's silo, so the group figure is their sum.
    revenue, cap = out.revenue_zar_raw.copy(), out.market_cap_line.copy()
    grouped = out.dual_listed_group.notna()
    if grouped.any():
        by_group = out[grouped].groupby(['decision_date', 'dual_listed_group'])
        revenue[grouped] = by_group.revenue_zar_raw.transform(lambda v: v.sum(min_count=len(v)))
        cap[grouped] = by_group.market_cap_line.transform('sum')

    fit = out.decision_date == fit_date
    sales_to_cap = np.log10(revenue / cap)
    turnover = np.log10(out.volume_line_basis / out.shares_line)
    for column, values, flag in [('log_sales_to_cap', sales_to_cap, 'fundamentals_imputed'),
                                 ('log_turnover', turnover, 'volume_imputed')]:
        observed = ~out[flag]
        if not np.isfinite(values[observed]).all():
            raise ValueError(f'{column} is undefined for an observed row')
        out[column] = values.where(observed, values[fit & observed].median())
    return out


def get_feature_set(name):
    if name not in FEATURE_SETS:
        raise ValueError(f'Unknown feature set {name!r}; choose from {sorted(FEATURE_SETS)}')
    return FEATURE_SETS[name]


def share_basis_audit(frame, threshold=.05):
    """Consecutive-date share-count changes above ``threshold``, raw and on a common basis."""
    import pandas as pd

    dates = sorted(frame.decision_date.unique())
    wide = frame.pivot(index='ticker', columns='decision_date')
    rows = []
    for before, after in zip(dates, dates[1:]):
        raw = wide['shares_outstanding'][after] / wide['shares_outstanding'][before]
        for ticker in raw[(raw - 1).abs() > threshold].index:
            ratio = lambda column: float(wide[column][after][ticker] / wide[column][before][ticker])
            rows.append(dict(ticker=ticker, before=before, after=after,
                             shares_ratio_raw=ratio('shares_outstanding'),
                             shares_ratio_common_basis=ratio('shares_common_basis'),
                             eps_ratio_raw=ratio('eps_zar_raw'), eps_ratio_common_basis=ratio('eps_common_basis'),
                             market_cap_ratio=ratio('market_cap_zar'),
                             recorded_subdivision=bool(wide['share_basis_factor'][before][ticker]
                                                       != wide['share_basis_factor'][after][ticker])))
    return pd.DataFrame(rows, columns=['ticker', 'before', 'after', 'shares_ratio_raw', 'shares_ratio_common_basis',
                                       'eps_ratio_raw', 'eps_ratio_common_basis', 'market_cap_ratio',
                                       'recorded_subdivision'])
