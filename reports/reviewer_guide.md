# Reviewer guide

This package reconstructs the documented descriptive baseline. It does not reproduce
an unavailable historical notebook or certify investor-observable point-in-time data.
The paper specification/results have not been promoted for publication.

## Start here

1. Read [research decisions](../docs/decisions/001-audit.md) and the
   [method](../docs/analysis_method.md). Starting commit:
   `59795b348a6ab447ca41219efb66ab4eddd93dce`. Implementation commit:
   `89c2cce42096ce3d2d4ee0def3b42d71a16c4c4b`.
2. Run `python scripts/checks.py`. The saved [actual test log](test_results.txt)
   records successful optimized-mode data validation and 24 passing tests.
   Expected synthetic failure tracebacks inside passing tracking tests are intentional.
3. Verify `python scripts/verify_run.py experiments/runs/final-full-42` and
   the corresponding repeat run. Each checksum manifest covers every artifact
   except itself and its completion marker; the marker hashes the manifest.
4. Read the compact tables below, then trace them into the per-date arrays,
   models and assignments in the full saved bundle. Nothing requires a tracking server.
5. Follow the [README](../README.md) reproduction commands. The repeated full
   execution passed comparisons of 89 deterministic CSV/NPZ/JSON artifacts with
   rtol=1e-7 and atol=1e-6 for numerical tables/arrays. See
   [machine-readable comparison](reproducibility.json). ZIP/PNG timestamp and
   rendering bytes are excluded. Input hashes are exact byte hashes: across Git
   newline settings, extract the archived source snapshot to reproduce identical
   CSV input bytes rather than silently changing the recorded provenance.

## Saved experiments and durability

| Run ID | Purpose | Status |
| --- | --- | --- |
| audit-full-42 | Development end-to-end audit before final export/plot additions | completed |
| final-full-42 | Fixed baseline on all dates, nine combinations/date, five seeds/date, k=2–10, SHAP | completed |
| repeat-full-42 | Identical-config complete execution and numerical comparison | completed |

[Registry](../experiments/registry.csv), [specification](../configs/baseline.json),
and [unpromoted baseline pointer](../experiments/baseline.json) are versioned.
All three complete bundles are committed under `experiments/runs/`, including
configuration, logs, source ZIP, package versions, arrays, models, plots and
checksums. Their combined uncompressed size is approximately 12 MB; Git compresses
and deduplicates them. A release asset or expiring CI artifact is unnecessary at
this size. `.gitattributes` preserves the exact experiment bytes on every platform.
See `durable_locations.json` for verified remote identifiers once uploaded.

Final and repeat runs record the implementation commit with a dirty worktree
because uncommitted result/documentation files were present. Both preserve their
actual source snapshots and tracked patches. The development run records the
original starting commit plus its actual uncommitted implementation snapshot.
Do not mistake a commit identifier alone for the full code of a dirty run.

## Baseline findings

All snapshots retain 41 instruments (123 rows, 43 distinct tickers). RNI remains
at every date with blank unresolved raw fundamentals and separate flagged model
values. The two AGL volume imputations remain. Re-derived June medians and
1st/99th percentiles match the supplied method. Scaling uses June 2025 only.
No sector, close, identifier, evidence flag or duplicate raw feature enters the
ten-column matrix. Later scaled values can exceed [0,1].

| Date | Embedding silhouette | Common-feature silhouette | Sector ARI | In-sample fidelity | OOF fidelity |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2025-06-30 | 0.571 | 0.182 | 0.236 | 1.000 | 0.537 |
| 2025-12-31 | 0.598 | 0.177 | 0.248 | 1.000 | Not estimable: singleton |
| 2026-06-30 | 0.641 | 0.223 | 0.306 | 1.000 | 0.732 |

The attractive t-SNE separation is much weaker in the shared financial space.
Sector agreement is external description using unverified legacy Listcorp labels,
not accuracy against verified historical ICB ground truth. Perfect training
surrogate accuracy does not establish fidelity beyond the fitted sample.

[Baseline results](baseline_results.csv), [all 27 comparisons](model_comparison.csv),
[k sensitivity](cluster_count_sensitivity.csv), and [surrogate diagnostics](surrogate_summary.csv)
contain the unrounded values. Silhouette uses Euclidean geometry. Davies–Bouldin
uses Euclidean embedding centroids, while hierarchical fitting uses Manhattan
distance. DBSCAN scores exclude noise and report coverage: its PCA comparison
retains 32/41, 37/41 and 35/41 firms respectively. Its apparent score advantage
must be read with those exclusions. The full-population UMAP/DBSCAN June 2026
partition has two clusters; it is not an eight-cluster substitute chosen for the paper.

The feature-space silhouette maxima within the fixed k sweep occur at k=6, 2
and 2 respectively. This diagnostic does not establish a unique optimum and
has not changed the historical k=8 baseline.

## Seed sensitivity and temporal comparisons

| Date | Pairwise comparisons | Mean ARI | ARI range | Mean NMI |
| --- | ---: | ---: | --- | ---: |
| 2025-06-30 | 10 | 0.727 | 0.526–0.898 | 0.872 |
| 2025-12-31 | 10 | 0.920 | 0.883–1.000 | 0.959 |
| 2026-06-30 | 10 | 0.934 | 0.836–1.000 | 0.968 |

See [seed summary](seed_summary.csv) and each run's `seed_stability.csv`,
`seed_metrics.csv`, per-date `seed_assignments.csv` and five seed array files.
These results refute a general claim of perfect seed stability. They are seed
sensitivity, not bootstrap confidence intervals.

Each adjacent comparison has 40 continuing instruments, one entry and one exit.
APN exits/GLN enters between the first two dates; MNP exits/PAN enters between
the next two. NPH is already present and GLN absent in June 2025; the June 2025
index review preceded the first study snapshot and is not an additional observed
between-snapshot transition. [Membership events](membership_events.csv) retain
blank ordinary cluster-change flags for all entries/exits.

Continuing-member temporal ARI/NMI are 0.450/0.714 then 0.604/0.788.
See [temporal agreement](temporal_agreement.csv), full membership transitions,
transition matrices and `temporal_label_alignment.csv`. Alignment maximizes
positive continuing-member overlap; zero-overlap matches receive fresh IDs.
Raw labels and both sector labels remain available. AGL and RNI interpretations
are imputation-sensitive. Numbers are descriptive labels, not persistent economic
identities; independently fitted t-SNE coordinates do not share axes.

## SHAP and source audit

Each snapshot's `shap_values.npz` contains firm tickers, ten feature names and
values, encoded classes, cluster-label mapping, assigned classes, SHAP values,
base values and raw margins. Dimensions are (41 firms, 10 features, 8 classes).
Maximum raw-margin additivity error is below 1.7e-6 (checked at atol=1e-4).
`surrogate_predictions.csv`, optional OOF predictions and `surrogate.json` allow
independent fidelity checks. `shap_global.csv`, `shap_by_cluster.csv` and their
plots expose global and own-class member importance. MTN is the December
singleton; its subgroup explanation is labelled descriptive only. All explanations
describe the supervised surrogate, without causal or return-forecast claims.

The read-only [workbook inspection](workbook_inspection.json) records all 14
sheet headers and row counts. Validation reconciles all 123 records against
the supplied workbook and checks its membership table. Existing dated source
URLs and evidence flags were inspected, not freshly verified. Native financial
units and all source values remain unchanged. Price return excludes cash
dividends; revenue/EPS accounting definitions vary across sectors.

## Implementation scope and remaining questions

The changed-file list is saved in `changed_files.txt`. Implementation includes
strict derivation/reconciliation checks that survive `python -O`, an explicit
algorithm configuration, geometry labels, positive-overlap temporal alignment,
imputation flags, robust surrogate class encoding and exports, immutable tracking,
registry locking and atomic replacement, numerical bundle verification, compact
review exports, expanded tests and selectable CI experiments.

The complete analysis ran locally with all pinned top-level packages on Windows
Python 3.11.14; [full environment lock](../configs/environment-windows-py311.txt).
Python 3.12 download failed, and temporary-fixture tests required execution with
normal Windows file permissions. CI is configured on Windows/3.11 and Ubuntu/3.12.
Check the PR for actual remote CI outcomes; configuration alone is not a pass.

No known unresolved local test or end-to-end failure remains. Review is still
needed for the short t-SNE optimization, k=8, correlated size inputs, sensitivity
to imputation and accounting differences, and the value of small-group surrogate
OOF scores. No broader search, bootstrap protocol, Hotelling T² threshold, new
historical ICB verification or source-data licence was introduced. Historical
shares, sectors and RNI remain evidence limitations. This package does not
establish economic usefulness or publication readiness. Nothing was merged.
