# Forward co-movement validation

Do equities in the same cluster move together more than equities in the same
sector over the following six months? Kept separate from the paper until the
findings have been assessed.

```powershell
.venv/Scripts/python.exe validation/audit_beta.py            # downloads and caches daily prices
.venv/Scripts/python.exe research/comovement/forward_comovement.py
```

Baseline: study commit `7a860a0`, results run `20261115T062631-0c09819ce3c0`.
Outputs are in `output/`.

## Hypotheses

- **H1, specified before any forward returns were examined:** cluster peers
  show stronger forward co-movement than sector peers, delta_rho > 0.
  **Result: rejected at both dates** (delta_rho < 0, confidence intervals
  excluding zero).
- **H2, added after the H1 result had been seen:** with sector held fixed,
  sharing a cluster raises forward correlation (cluster coefficient > 0 in
  the pairwise regression). **Result: supported at both dates.** Because H2
  was formulated after observing the H1 result, its retrospective support is
  exploratory.

Both hypotheses, the metrics and the procedures below are now fixed. The
prospective June 2026 test (below) is their first test with everything
specified in advance.

## Design

- **Formation dates:** 30 June 2025 and 31 December 2025. Clusters come from the
  saved study run; nothing is refitted on later data.
- **Forward windows:** 1 July to 31 December 2025, and 1 January to 30 June 2026.
- **Returns:** daily price returns of the instruments in the index at the
  formation date; daily moves above 40% are treated as bad prints.
  Market-adjusted returns are residuals from a regression on the Top 40 (J200)
  within each window.
- **Primary metric:** delta_rho = mean forward correlation between cluster peers
  minus the same for sector peers. The Investec pair (two listings of one
  company) is excluded throughout.
- **Uncertainty:** permutation null with cluster sizes preserved (10,000
  shuffles), and a 10-day block bootstrap of the forward window for the
  confidence interval of delta_rho (2,000 draws).
- **Incremental test:** pairwise correlation regressed on same-sector and
  same-cluster indicators together; the cluster coefficient is tested by QAP
  permutation (5,000 shuffles), which respects overlapping pairs.
- **Robustness:** t-SNE comparator, five UMAP seeds, per-cluster results,
  the result without the precious-metals cluster, and stock-level peer R^2.

## Findings

1. **Sectors co-move more than clusters.** delta_rho is negative at both dates,
   for raw and market-adjusted returns, for every UMAP seed and for t-SNE.
   Study model: -0.129 (95% CI -0.171 to -0.096) and -0.069 (-0.100 to -0.040)
   for raw returns. Clusters as a replacement for sectors are not supported.
2. **Clusters beat random groups** of the same sizes (permutation p < 0.001 at
   both dates), so they do capture real co-movement.
3. **Clusters add information beyond sectors.** With sector held fixed, sharing a
   cluster raises forward correlation at both dates, raw and adjusted
   (QAP p from 0.0008 to 0.019 for UMAP).
4. **The added information is within sectors.** Same-sector pairs in the same
   cluster co-move more than same-sector pairs in different clusters
   (raw: 0.39 vs 0.33 in June 2025, 0.55 vs 0.40 in December 2025). Clusters
   refine sectors, for example separating precious-metals producers within
   Basic Materials.
5. **Cross-sector cluster peers barely co-move.** Different-sector pairs in the
   same cluster have market-adjusted correlations of 0.007 and 0.021, close to
   unrelated pairs (-0.034 and -0.037); raw, in December 2025, they are lower
   than unrelated pairs (0.139 vs 0.195). Sector-divergent groupings reflect
   shared characteristics, not shared subsequent return behaviour.
6. **By cluster:** the precious-metals cluster co-moves strongly (raw 0.81 to
   0.82). The large-capitalisation, low-turnover cluster (AB InBev, BHP,
   Richemont, BAT, Prosus) barely co-moves (raw 0.05 to 0.11).
7. **t-SNE does at least as well as UMAP on this test,** and better in June
   2025 (cluster effect beyond sector 0.089 vs 0.038 raw; delta_rho -0.045 vs
   -0.129).

## Implications for the paper (to discuss before any change)

- The supported investment claim is that clusters refine sectors into more
  tightly co-moving sub-groups, not that they replace sectors.
- Sector-divergent cases remain screening signals about financial
  characteristics; they should not be presented as alternative risk or
  diversification peers.
- The UMAP justification should acknowledge that the economic test does not
  favour UMAP over t-SNE.

## Prospective test (reserved)

The June 2026 clusters have not been tested, and no prices for their forward
window have been downloaded. The window, 1 July to 31 December 2026, closes
after this protocol was frozen. On or after 5 January 2027, run

```powershell
.venv/Scripts/python.exe research/comovement/forward_comovement.py --prospective
```

without changing the script. It downloads prices through early January 2027
into its own cache, tests H1 and H2 with the same metrics, seeds and
permutation counts, and writes to `output_prospective/`. The option refuses to
run before 5 January 2027. Report the result whatever it shows; do not change
the model, metrics or hypotheses after seeing it.
