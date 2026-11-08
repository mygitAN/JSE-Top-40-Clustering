# JSE Top 40 Clustering

Clustering research using historical FTSE/JSE Top 40 cross-sections.

## Data

- 30 June 2025, 31 December 2025 and 30 June 2026.
- 41 instruments at each date: 123 rows and 43 distinct tickers.
- Every historical index member is retained, including unresolved observations.
- Market cap, shares outstanding, sector, return, volume, beta, volatility, dividend yield, revenue, EPS and earnings yield are included.

| File | Purpose |
| --- | --- |
| `data/processed/Top40_Retrospective_Model_Inputs_v1.csv` | Modelling inputs with raw and model-only imputed values |
| `data/source/Top40_PIT_Verification_v4.xlsx` | Audit workbook, underlying inputs, source URLs and field-level evidence |
| `docs/Top40_Retrospective_Model_Method_v1.json` | Selection, imputation, clipping and evidence policy |
| `scripts/validate_data.py` | Dataset checks using the Python standard library |

## Research policy

This is a retrospective public-source reconstruction, not a certified investor-observable point-in-time backtest. Later restatements are permitted, although this version retains the issuer values already in the v4 workbook. Prices and other market features come from reconstructed vendor daily history. Historical shares and sector labels remain unverified; market cap reconciles to close times shares. Sector uses the existing eight legacy Listcorp labels, not a newly verified historical 11-industry ICB mapping.

Membership changes are index entries/exits, not ordinary cluster transitions: NPH replaced GLN in June 2025, GLN replaced APN in September 2025, and PAN replaced MNP in March 2026.

Reinet remains in all snapshots. Its unresolved raw fundamentals stay blank. Training medians populate separate model columns and are flagged with `fundamentals_imputed`. The two missing AGL volume observations are imputed and marked `volume_imputed`. Imputed earnings yield is not an accounting identity with separately imputed EPS; do not interpret either as reported company data.

Earnings yield replaces P/E for modelling. Imputation and 1st/99th percentile clipping were fitted on June 2025 only. The supplied train/validation/test date labels are a starting configuration, not evidence that three cross-sections establish robust out-of-sample performance. Encode sector categorically and fit any scaler on training data only. Keep identifiers, evidence fields, dates and raw alternatives out of the numeric feature matrix. Examine sensitivity to imputation, correlated size features, sector inclusion and extreme observations before interpreting clusters.

## Validate

Python 3.10 or later; no packages required:

```bash
python scripts/validate_data.py
```

Validation checks membership, unique keys, retained unresolved rows, model-feature completeness, missingness flags, imputation constants, clipping, and cap arithmetic. It does not independently certify the source data. Analyst ratings are not inferred or included.

## Data reuse

Source attribution is retained in the workbook. Public availability does not imply unrestricted redistribution rights. No blanket open-data licence is asserted for third-party data.
