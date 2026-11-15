"""Exploratory tables for the chosen feature set, computed before any model is fitted."""
import pandas as pd

from . import plots
from .models import feature_matrix

# Which imputation flag marks a raw-missing value behind each model column.
IMPUTATION_FLAG = {'average_daily_volume_1y_model': 'volume_imputed', 'log_volume': 'volume_imputed',
                   'log_turnover': 'volume_imputed', 'revenue_zar_model': 'fundamentals_imputed',
                   'log_revenue': 'fundamentals_imputed', 'log_sales_to_cap': 'fundamentals_imputed',
                   'eps_zar_model': 'fundamentals_imputed', 'earnings_yield_model_clipped': 'fundamentals_imputed'}
EVIDENCE = ['membership_evidence', 'fundamentals_evidence', 'market_evidence', 'share_evidence', 'sector_evidence']


def eda_tables(frame, feature_set, scaler):
    columns = list(feature_set.columns)
    dates = sorted(frame.decision_date.unique())
    population = frame.groupby('decision_date').agg(
        instruments=('ticker', 'size'), fundamental_imputations=('fundamentals_imputed', 'sum'),
        volume_imputations=('volume_imputed', 'sum'), mixed_basis_volume=('volume_basis_mixed', 'sum')).reset_index()
    # The two Investec lines are separate securities of one dual-listed company.
    groups = frame.ticker.replace({'INL': 'INVESTEC_DLC', 'INP': 'INVESTEC_DLC'})
    population['economic_groups'] = population.decision_date.map(groups.groupby(frame.decision_date).nunique())
    presence = pd.crosstab(frame.ticker, frame.decision_date).reindex(columns=dates, fill_value=0).astype(bool)
    missing = pd.DataFrame([dict(decision_date=date, feature=column,
                                 raw_missing=int(sub[IMPUTATION_FLAG[column]].sum()) if column in IMPUTATION_FLAG else 0)
                            for date, sub in frame.groupby('decision_date', sort=True) for column in columns])
    evidence = pd.DataFrame([dict(decision_date=date, field=field, status=str(status), n=int(n))
                             for field in EVIDENCE
                             for (date, status), n in frame.groupby(['decision_date', field]).size().items()])
    scaled = frame[['decision_date', 'ticker', 'sector_label', 'fundamentals_imputed', 'volume_imputed']].copy()
    scaled[columns] = scaler.transform(feature_matrix(frame, columns))
    descriptions = frame.groupby('decision_date')[columns].describe().stack(level=0, future_stack=True)
    descriptions = descriptions.reset_index().rename(columns={'level_1': 'feature'})
    descriptions['skew'] = [frame.loc[frame.decision_date == d, f].skew()
                            for d, f in zip(descriptions.decision_date, descriptions.feature)]
    # Rank correlation: several inputs are too skewed for Pearson to be informative.
    correlations = {d: s[columns].corr(method='spearman') for d, s in frame.groupby('decision_date', sort=True)}
    pairs = pd.DataFrame([dict(decision_date=date, feature_a=a, feature_b=b, spearman=float(corr.loc[a, b]))
                          for date, corr in correlations.items()
                          for i, a in enumerate(columns) for b in columns[i + 1:] if abs(corr.loc[a, b]) >= .8],
                         columns=['decision_date', 'feature_a', 'feature_b', 'spearman'])
    return dict(population=population, presence=presence, missingness=missing, evidence=evidence, scaled=scaled,
                descriptions=descriptions, correlations=correlations, correlated_pairs=pairs)


def explore(frame, feature_set, scaler, fit_date, out):
    """Write the EDA tables and figures to ``out`` and return the tables."""
    out.mkdir(parents=True, exist_ok=False)
    tables = eda_tables(frame, feature_set, scaler)
    for name in ['population', 'missingness', 'evidence', 'scaled', 'descriptions', 'correlated_pairs']:
        tables[name].to_csv(out / f'{name}.csv', index=False)
    tables['presence'].to_csv(out / 'membership_presence.csv')
    dates = list(tables['population'].decision_date)
    plots.population_and_sectors(tables['population'], frame, out / 'population_and_sectors.png')
    plots.membership_presence(tables['presence'], out / 'membership_presence.png')
    plots.feature_distributions(tables['scaled'], feature_set, dates, fit_date, out / 'feature_distributions.png')
    for date, corr in tables['correlations'].items():
        corr.to_csv(out / f'correlation_{date}.csv')
        plots.correlation(corr, feature_set, date, out / f'correlation_{date}.png')
    return tables
