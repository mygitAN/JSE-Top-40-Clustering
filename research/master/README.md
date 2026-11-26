# Preserved research master and validation baseline

These are historical versions of **one complete paper**, not a main paper and
supplement. All seventeen research figures are retained in both archived
versions; neither was shortened to impose a page limit.

The editable manuscript remains `paper/main.tex`. Since commit `85c9137` it is
a condensed 26-page version of the research master: figures and tables that
repeated evidence given elsewhere were removed or merged, with their values
kept in the text. No analysis was rerun and no reported number changed. The
removed diagrams remain in `paper/figures/` and in the `paper/diagrams.tex`
atlas.

| Version | Exact manuscript source | Rebuilt pages | Archive |
|---|---|---:|---|
| Before forward validation | `7a860a0` | 29 | [PDF](pre_validation_master_7a860a0.pdf), [LaTeX source](pre_validation_source_7a860a0.zip) |
| Research master including assessed validation | `e1b393a` | 32 | [PDF](research_master_e1b393a.pdf), [LaTeX source](research_master_source_e1b393a.zip) |

The reference to a 28-page master predates the present source versions. These
archives preserve the complete material at the stated commits. Actual page
counts come from recompiling with Tectonic 0.17.0; no padding or trimming was used.
`manifest.json` records full commit identifiers and SHA-256 hashes of both PDFs
and both source archives. Each ZIP contains the complete tracked `paper/` project.

Commit identifiers written in this repository's files and archive names were
recorded before 26 November 2026, when commit messages were edited. File
contents and dates are unchanged; [COMMIT_MAP.md](COMMIT_MAP.md) maps each
recorded identifier to its current one.

## What was frozen before validation

The empirical source is run `20261115T062631-0c09819ce3c0`, with its numerical
implementation and inputs identified in `results/manifest.json`. The manuscript
baseline used by the forward experiment is **`7a860a0`**. The newer research-master
commit incorporates the observed validation findings and cannot retroactively
be described as the pre-experiment baseline.

Authoritative validation code and numerical outputs remain separate from the
LaTeX manuscript; `paper/data/` and `paper/tables/` contain derived reporting
copies for the article:

- `research/comovement/`: the primary, pair-weighted comparison, random-group
  comparisons, seed/method checks and explicitly exploratory conditional analysis.
- `validation/forward_comovement/`: the company-balanced sensitivity analysis,
  sector-and-characteristic-matched alternatives, high-volatility exclusion,
  company-deletion checks, synchronous time-block intervals, frozen prices and
  checksummed provenance.

The primary metric is the proposed difference between mean within-cluster and
mean within-sector forward correlations. Its raw-price estimates are **−0.129**
and **−0.069** for the June and December 2025 formations. The company-balanced
estimates (**−0.117**, **−0.083**) use a different weighting scheme and are labelled
as sensitivities rather than substituted into the primary table.

These results do not support replacing sector peers to obtain stronger overall
subsequent co-movement. Positive matched contrasts and the conditional within-sector
analysis warrant further investigation as complementary financial relationships.
The conditional hypothesis was formulated after the primary result was known;
its evidence remains exploratory. None of these analyses establishes portfolio
outperformance, risk reduction or a causal investment effect.

## Agreed journal and research roadmap

1. **Preserve the full research version — done.** Aligned maps, full model
   comparison, sector divergence and the analyst-investigation table are retained.
2. **Forward co-movement — done.** Frozen June and December 2025 assignments
   are evaluated in July–December 2025 and January–June 2026 without refitting.
3. **Financial significance and robustness — assessed for these two windows.**
   Results are reported against sectors and matched alternatives with uncertainty
   and sensitivity checks that do not assume equity pairs are independent.
4. **Transparent integration — retained in the current master.** Negative overall
   findings and exploratory within-sector evidence are distinguished throughout.
5. **Submission preparation — next stage.** Investment Analysts Journal is the
   primary target; ORiON is the fallback. A later submission copy can be edited
   to verified journal requirements while this complete master remains preserved.

No seven-date extension has been fabricated or initiated. It requires four
additional dated input universes and financial statements. The July–December
2026 window remains incomplete when the protocol is fixed in November; a later
evaluation is held out, not a fully prospective preregistration of that entire
window. The legacy `--prospective` option name does not alter this distinction.

## Rebuild

Extract either source ZIP, select its `paper/main.tex`, and compile with a
standard LaTeX engine. For a repository checkout at the corresponding source
commit, use `./paper/build.ps1`. Overleaf's working main document remains
`paper/main.tex`; archived ZIPs do not create another live manuscript tree.
