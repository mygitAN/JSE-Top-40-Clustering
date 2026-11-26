# Sector-conditioned forward co-movement sensitivity

This is a **new retrospective extension**, prompted by the 26 November 2026
peer-review audit. It does not replace the original experiment in
`research/comovement/`, modify its frozen protocol, or execute the reserved
June 2026 forward evaluation. Protocol choices were recorded before running
this extension, after the original results were already known; this is not
preregistration.

## What the audit established

- The original `incremental()` function permutes cluster labels **globally
  across instruments**, preserving global cluster sizes. Its additive
  coefficient is not itself the within-sector correlation contrast.
- The new check shuffles cluster labels **only within each recorded sector**.
  Each sector keeps its observed multiset of cluster labels, and global
  cluster sizes also remain fixed. It tests a sector-conditioned
  exchangeability null, rather than asserting that all firms are exchangeable.
- Two statistics are distinguished: the direct same-sector/same-cluster minus
  same-sector/different-cluster mean-correlation contrast, and the original
  additive shared-cluster coefficient over all pairs.
- There are 5,000 permutations per combination and a one-sided plus-one p-value.
  Holm adjustment covers all 16 tests: two dates, two mappings, two return
  bases and two statistics. This family was specified before viewing these
  new sensitivity outputs.
- Direct contrasts also receive 95% synchronous ten-day moving-block
  bootstrap intervals with 2,000 resamples. These condition on the observed
  universe and groups; they do not estimate uncertainty across market regimes.
  Market residuals are fitted once and then resampled, as in the original test.

## Saved findings

All eight observed direct differences are positive. Raw UMAP after June 2025
is not below 0.05 after Holm adjustment (p=0.059); December is (p=0.006).
Both market-adjusted UMAP contrasts remain below 0.05 after adjustment.
The adjusted coefficient test is also not uniformly below 0.05: raw UMAP
December is p=0.059. These are different statistics and must not be conflated.

| Formation | Returns | Mapping | Within-sector difference | Conditional bootstrap 95% interval | Restricted p | Holm p (16 tests) | Coefficient Holm p |
|---|---|---|---:|---|---:|---:|---:|
| 2025-06-30 | raw | UMAP (study model) | 0.062 | [0.015, 0.091] | 0.0294 | 0.0588 | 0.0240 |
| 2025-06-30 | raw | t-SNE comparator | 0.117 | [0.063, 0.157] | 0.0102 | 0.0420 | 0.0234 |
| 2025-06-30 | market-adjusted | UMAP (study model) | 0.113 | [0.076, 0.142] | 0.0042 | 0.0360 | 0.0032 |
| 2025-06-30 | market-adjusted | t-SNE comparator | 0.105 | [0.060, 0.147] | 0.0084 | 0.0420 | 0.0360 |
| 2025-12-31 | raw | UMAP (study model) | 0.157 | [0.098, 0.203] | 0.0004 | 0.0060 | 0.0588 |
| 2025-12-31 | raw | t-SNE comparator | 0.153 | [0.100, 0.198] | 0.0018 | 0.0234 | 0.0420 |
| 2025-12-31 | market-adjusted | UMAP (study model) | 0.099 | [0.027, 0.152] | 0.0004 | 0.0060 | 0.0360 |
| 2025-12-31 | market-adjusted | t-SNE comparator | 0.079 | [0.007, 0.130] | 0.0018 | 0.0234 | 0.0360 |

The bootstrap interval and permutation p-value answer different questions.
The interval resamples the realised return panel with fixed memberships.
The permutation compares membership allocations under the stated
sector-conditioned randomisation null, followed by a multiple-test adjustment.
A positive interval and an adjusted p-value above 0.05 are not contradictory.

The results support a qualified exploratory within-sector interpretation.
They do not establish causality, profitability or generalisation to independent
market regimes. Sector membership alone may not make firms exchangeable with
respect to omitted characteristics. The legacy sector labels and the treatment
of separate listings inherit the original data limitations.

## Reproduction and integrity

```powershell
.venv/Scripts/python.exe research/sector_conditioned_comovement/run.py
.venv/Scripts/python.exe -m unittest tests.test_sector_conditioned_comovement tests.test_primary_comovement_freeze
```

No arguments are accepted. The script verifies the complete original freeze,
uses only its price and partition snapshots, rejects prices after 30 June 2026,
and confirms all eight original cell means and coefficients before saving
`results.csv`. No downloads or model refits occur. All instruments share each
bootstrap calendar, and INL/INP's mutual pair is excluded. Missing comparison
cells or incomplete return panels cause failure rather than silent deletion.

`protocol.json` describes the null, estimands, multiplicity family, random seed
and timing. `manifest.json` records exact script, protocol, report, tests,
input and result hashes plus NumPy/pandas versions. The folder's Git attributes
preserve those bytes across platforms. The original frozen files remain intact.
