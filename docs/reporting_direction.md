# Reporting direction: structural-signal dynamics

Agreed direction, 8 November 2026. This is a reporting protocol and working
example, not an update to the manuscript or a claim of submission readiness.

## Lead with the contribution

The contribution is an interpretable repeated cross-sectional screening
framework that tracks changes in peer relationships and distinguishes emerging,
persistent and resolving structural signals. The financial-profile analysis
examines characteristics associated with those changes. It does not establish
their causes or predict investment returns.

Report the analysis as a connected argument:

1. **Define the decision setting.** Use 30 June 2025, 31 December 2025 and
   30 June 2026. Each date has 41 listed instruments representing 40 economic
   groups, including the two Investec DLC securities. Membership is date-specific.
   Repeated firms and overlapping trailing windows prevent treating the 123
   records as independent cross-sectional observations. No distinct market-regime
   classification has been established.
2. **Show the EDA and information set.** Explain distributions, correlations,
   missing cases and source evidence before modelling. The current ten-feature
   variant excludes historic consensus and replaces P/E with earnings yield;
   it is not the original eleven-feature experiment. Strict PIT availability is
   the intended evidence standard, while the current reconstruction remains
   provisional in the previously documented fields.
3. **Explain how models were selected.** Show the finite grid, distances,
   linkages, dimensionality settings, clustering parameters, both silhouette/DB
   geometries, seed variability, coverage and singleton counts. Distinguish a
   score optimum from an economically useful or interpretable partition.
4. **Show structural continuity and change.** Present actual hierarchical trees
   at each date and Hungarian/Jaccard membership histories. List stable and
   shifted instruments, with entries/exits separately. Alignment is reproducible
   rather than chosen manually from sector interpretations.
5. **Report signal dynamics.** Keep cluster shifts, geometric screening and
   contextual sector divergence separate. Apply the history taxonomy to each
   binary signal independently, then show where the signals agree. An unknown
   comparison is not a normal or unflagged observation.
6. **Examine financial-profile associations.** Use case narratives that connect
   observed attribute changes, financial-feature deviations and SHAP results,
   while displaying surrogate fidelity, imputation flags and evidence limits.
   Attribute changes within a frozen 2025 model are not causal explanations of
   independently refitted partitions.

## Keep k=8 primary

The user explicitly confirmed k=8 as the primary design, with varying k as a
sensitivity. June-selected settings therefore remain fixed in the primary
three-date analysis. The new sensitivity varies only k=2..12 at each date for
the three main models, reusing their saved five-seed representations and keeping
all other parameters fixed. Its 495 clustering fits use the same joint-score
ranking rule separately in financial-feature and embedding spaces. It is not
an exhaustive independent retuning of every representation/algorithm at all
three dates.

For the primary PCA/hierarchy, both score criteria select k=2 at every date,
with one singleton. This is a result to discuss, not a reason to conceal the
sensitivity or automatically replace the primary design. Boundary optima at
k=2 or k=12 remain conditional on the tested range. Primary cluster-membership
SHAP must not be presented as an explanation of different varying-k labels.

## Version the reporting taxonomy

The example refines the existing labels. The amended reporting view distinguishes
100 **resolved** from 110 **resolving**, and 011 **emerging and sustained** from
001 **emerging**. It also retains 000 **never flagged**, 010 **transient**,
111 **persistent** and 101 **recurring**. These changes were recorded after
the existing results were examined. They must not be described as prospectively
prespecified for these data. The original immutable results retain their earlier
labels; the v2 report is a separate derived archive.

Three channels are reported: geometric screen, sector divergence and joint
agreement. Joint agreement requires both flags and both estimable comparisons.
Three-date classifications require observations and estimable signal values at
all three dates. A singleton/tied sector comparison or membership gap is not
silently converted to a negative flag. Report ordinary cluster stability and
changes independently of these signal labels.

Under the revised geometric taxonomy, ANH and BHG are resolved, SSW is transient,
and GLN has insufficient membership history for a three-date label despite
being flagged at both observed later dates. No confirmed economic outlier is
established by the F-reference screen or by SHAP. Sector labels remain contextual
legacy metadata, not certified historical ground truth.

## Working deliverables

- [Reporting example](../reports/anomaly_dynamics_reporting_example.md): the
  requested narrative direction applied to current outputs.
- `configs/anomaly_dynamics_reporting_v2.json`: exact amendment and signal rules.
- `scripts/report_anomaly_dynamics.py`: reproducible derived report and sensitivity.
- `experiments/runs/anomaly-dynamics-report-v2-01/`: signal histories, all 495
  sensitivity scores, seed stability, parameter rankings, chosen k values,
  varying-k membership histories and plots.

Reproduce with:

```bash
python scripts/report_anomaly_dynamics.py
```

Source-backed historical shares/market cap, sector history and daily-market
validation remain necessary for submission-grade findings. A prospective
replication would freeze the amended protocol before examining new data.
