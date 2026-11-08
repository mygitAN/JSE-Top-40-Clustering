# Draft v1.3: completion of the protocol review

Prepared on 8 November 2026 from frozen v1.2. The active
[research_protocol.md](research_protocol.md) and tags `protocol-v1`,
`protocol-v1.1` and `protocol-v1.2` are preserved. The proposed standalone
[v1.3 draft](research_protocol_v1_3_draft.md) is not a new frozen version.

V1.2 already adopted the main calibration, corporate-action, DBSCAN and
validation-status corrections. This amendment therefore retains its author
choices, rather than replacing them with a parallel rewrite:

- k=8 primary; DBSCAN comparator only; primary Beta descriptive reference;
- conditioning limit 10^8, minimum 20 evaluable perturbations, paired-by-b draws
  and the separately seeded t4 generator;
- grid-order ranking ties, the predeclared no-eligible fallback, thresholded
  Hungarian assignment, issued-share basis, FX and special-dividend choices;
- disclosure of pilot results already seen, including the Beta-reference counts.

## Remaining changes

| Issue | Draft correction |
| --- | --- |
| Missing S2 or other unavailable states can disappear from the union | Unknown applicable states remain unknown; only structural S1 non-applicability is excluded; explicit union/multi-signal logic |
| Insufficient singleton support could be reported as S3=0 | Isolated full-sample firms with fewer than 20 evaluable runs get NA |
| General log order conflicts with the sensitivity definition | Separate primary clip/fill/scale and sensitivity log/fill/scale orders; specify frozen statistics and sensitivity failure |
| Perturbation/event agreement lacks some denominators | Store attempts, evaluable and positive counts; define represented cluster-event recovery and failed-match handling |
| Entry-only clusters and comparison domains are ambiguous | Separate membership-only appearances; state continuing/included peer domains and empty-set convention |
| Free-k diagnostic and final fallback failures are underspecified | Only k varies; preserve the approved fallback and explicitly report final no-eligible cases |
| Numerical failures may masquerade as negative signals | Add finite/domain/inversion checks and conditional covariance/decomposition validation |
| OOF or SHAP references can change interpretation | Specify conditional OOF coverage, raw-margin checks, direct baseline mapping and hypothetical reference/basis flags |

For strict PIT S1, unavailable historical labels are not replaced by the legacy
exploratory comparison. Cluster dominance with incomplete labels is undefined.
The legacy comparison remains available as a separately flagged analysis.

## Verification and scope

[protocol_v1_3_validation.json](protocol_v1_3_validation.json) records document
consistency, preserved numerical choices, the Beta reference arithmetic, 27
known/unknown-state combinations and three structural-NA examples. These are
documentation/logic diagnostics, not production implementation or v2 model tests.

The draft preserves the original twelve-section structure and v1.2 change log,
then appends its own dated change-log rows. No data collection, notebook run,
new empirical result, tag creation or retrospective confirmation claim is
implied. Author review of the concrete draft precedes any new protocol freeze.
