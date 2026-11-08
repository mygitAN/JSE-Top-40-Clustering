# Review of the paper repository's draft research protocol v1.1

Reviewed on 8 November 2026. This is a review of the supplied draft, not author
approval, a new protocol freeze, or an implementation of v1.1. The source is
`C:/Users/HP/Documents/GitHub/JSE-Top-40-Clustering-paper/docs/research_protocol.md`.
That repository has the `protocol-v1` tag; its current v1.1 protocol file is
modified relative to its commit. Numerical checks are in
[research_protocol_v1_1_calibration_check.json](research_protocol_v1_1_calibration_check.json).

## Overall assessment

The draft addresses the peer-cluster problem directly. Retain its comparison
of unreduced features with dimensionality reduction, June-only eligibility
rules, fixed-k primary analysis, separate free-k diagnostic, data perturbations,
explicit isolation signal, source availability requirements and pilot disclosure.
The main issues below should be resolved before a new freeze. They affect what
the signals mean, rather than merely the manuscript's wording.

## 1. Essential correction: individual-distance calibration

Section 8 uses an individual squared Mahalanobis distance about the same sample's
mean and covariance, then applies a mean-Hotelling-T-squared F reference. These
are different statistical setups. NIST distinguishes
[mean-vector testing](https://www.itl.nist.gov/div898/handbook/pmc/section5/pmc543.htm)
from [same-sample individual control-chart distances](https://www.itl.nist.gov/div898/software/dataplot/refman1/auxillar/hotell.htm).
The arithmetic value 27.78265 is correct for the stated F expression; its claimed
5% individual false-positive interpretation is not established.

For n=41, p=10 and unbiased nonsingular sample covariance, numerical checks give:

| Quantity | Value |
| --- | ---: |
| Proposed 5% F reference | 27.78265345 |
| Maximum possible internal individual squared distance | 39.02439024 |
| Proposed Bonferroni F reference, alpha=0.05/41 | 52.62052212 |
| One-sided 5% internal-distance Beta reference, under iid multivariate normality | 16.35591137 |
| Ideal-normal internal tail probability above the proposed F reference | 0.0000086181 |
| Expected number above that F reference among 41 ideal-normal observations | 0.00035334 |

The Bonferroni F reference exceeds the mathematical maximum of the very distances
being screened. It can never flag an observation in this setup. The statement
that about two flags are expected by chance cannot accompany this rule.

The one-sided internal-reference calculation uses

$$D_i^2 / [(n-1)^2/n] \sim \operatorname{Beta}(p/2,(n-p-1)/2),$$

under the iid multivariate-normal model, with the upper quantile 1-alpha. This is
a reference model, not a demonstrated distribution for heterogeneous equities,
two related Investec securities, imputed values or clipped earnings yields.
An illustrative simulation of 3,000 independent Gaussian samples of size 41
produced a mean 0.000333 flags with the proposed F reference and 2.025 with the
one-sided Beta reference. These are synthetic checks, not JSE results.

**Required decision:** either keep the SACJ F rule as a descriptive replication
sensitivity and remove nominal error-rate claims, or specify and justify a
primary individual-distance reference/calibration. Record covariance estimator,
ddof, rank/conditioning checks and a failure rule. A pseudoinverse, shrinkage,
leave-one-out distance or MCD changes the setup and must not silently inherit
the old degrees of freedom or cutoff. Recompute any multiplicity sensitivity
using the chosen reference; define its family across instruments/dates/signals.

MCD plus a chi-squared cutoff is a sensitivity, not automatic finite-sample
confirmation. The pinned
[scikit-learn 1.6 documentation](https://scikit-learn.org/1.6/modules/generated/sklearn.covariance.MinCovDet.html)
warns about applying MCD to multimodal distributions. A cross-sector equity
population need not be a single elliptical population. Report convergence,
conditioning and support settings.

## 2. Essential correction: confirmatory status

Section 11 correctly discloses that pilot outcomes influenced eligibility and
isolation definitions. A newly assembled PIT version of the same historical
firms and dates improves measurement and source validity; it is not automatically
an independent confirmatory sample. Recommended label: **protocol-frozen PIT
reanalysis of pilot-informed historical cross-sections**. State which empirical
claims and decision rules were already informed by v1.

The future 31 December 2026 snapshot can provide a prospectively specified
follow-up. Its complete endpoint is unseen on 8 November 2026, but much of its
trailing window and some annual results are already public. It also overlaps
the June 2026 window. Avoid claiming that none of its data have been seen or
that it supplies an independent sample. Define how model selection and all
thresholds are locked before outcome access, record the data-access log, and
preserve an independently timestamped protocol/commit identifier. A Git tag is
useful versioning; do not imply external preregistration unless it has occurred.

The full three-date Ward/unreduced pilot claim must cite its exact run, config,
data hash and eligibility rule. The current original-workspace exhaustive run
did not include unreduced features, so it cannot substantiate that particular
claim. A separate pilot may do so; keep their provenance distinct.

## 3. Essential correction: per-share and instrument basis

Sections 2 and 4 need a common corporate-action basis. Record each instrument's
ISIN, quote unit (including ZAc/ZAR), share class, receipt/ordinary-share ratio,
split/consolidation adjustments and the effective dates known at the snapshot.
Annual EPS may need a source-backed conversion to the share basis of that
date's price, even when no new annual results were published. Trailing dividends
and traded volumes need a consistent split basis too. Specify treatment of
special distributions, unobserved trading days and currency-conversion dates.

Keep issuer/security shares separate from combined economic-group shares.
Neither Investec line should automatically inherit the combined DLC count as
its own share count. A receipt price cannot be multiplied by an incompatible
ordinary-share count. Specify issued versus treasury-adjusted/outstanding shares
and report the basis. The existing reconstructed NPN example demonstrates why
this audit matters; it does not establish that its share-count change is an
economic change.

The same native-currency annual result can produce different ZAR revenue/EPS
at later spot rates. Report native amounts, release date and FX effects
separately. “No new annual results” means unchanged source accounting figures,
not necessarily unchanged converted model values. If an audited report was not
available with the initial results release, the availability date must reflect
the actual chosen source, not automatically the earlier announcement.

## 4. Remove stronger interpretations than the design establishes

- Prefer **three decision-date cross-sections** to three distinct market states
  unless a regime definition is supplied.
- Use **external sector comparator**, with evidence flags, rather than verified
  eight-sector ground truth. Matching k to eight sector categories does not
  establish that a cluster should equal a sector.
- A later increase in singleton counts is a structural observation conditional
  on the fitted method. It does not alone establish economic isolation; data
  revisions, membership, imputation and fitting variability also matter.
- An isolated instrument is not inherently sector-divergent. Its separate S3
  definition is useful without calling isolation the strongest sector mismatch.
- Endpoint windows can be defined as non-overlapping return intervals, but the
  same annual fundamentals, firms, share/sector metadata and preprocessing may
  persist. Describe endpoint recurrence as less mechanically overlapping market
  evidence, not an independent persistence test.
- Fixed hyperparameters remove repeated parameter selection, not all model
  randomness. State that refitted memberships are affected by the data and
  fitting variability, with perturbations used to assess robustness.

## 5. Make eligibility and perturbations executable

Specify that the 95% coverage, singleton and largest-cluster bounds apply to
every June seed if that is intended. Define the largest-cluster denominator.
For DBSCAN, calculate seed ARI on common non-noise members, report their coverage,
and define later noise states. Requiring “k=8” must mean eight non-noise clusters
for a density candidate, not an unsupported n_clusters parameter. Define the
outcome when no candidate qualifies, all quality scores tie, or a fit fails.

There is also a direct design conflict: unchanged DBSCAN parameters cannot
guarantee eight clusters at later dates. To preserve fixed k=8, keep DBSCAN as
a comparator rather than an eligible primary method, or explicitly amend the
fixed-k requirement for density models. Retuning epsilon to force eight would
break the unchanged-method rule. Noise is not a singleton cluster; specify its
signal and history treatment instead of silently treating it as S3 or S1=0.

For subsampling, fix the sorted instrument order, sampling implementation and
whether b starts at zero. Store every draw, included instruments, seed, success
status and property numerator/denominator. Generalise the 37-of-41 rule for
other actual universe sizes, including t4. Report conditional support as a
stability proportion, not an 80% posterior confidence or type-I error rate.
Define failed-fit handling and a minimum estimable-run count.

For paired-date properties, state whether independently drawn subsamples are
paired by b, then restricted to their observed intersection. This is not the
same design as sampling a common continuing-member set. Fix that choice before
v2 evaluation. To quote support for a full-sample cluster match or split, specify
how each perturbed cluster is first related to the full-sample cluster.

## 6. Specify matching and undefined signals

“Hungarian then discard J<0.30” can differ from optimising accepted matches
with sub-threshold edges forbidden and dummy unmatched nodes. Choose the
intended objective, tie rule and unmatched cost. Compute Jaccard on continuing
members for both its numerator and denominator. Distinguish disappearance due
solely to index exit from dissolution among continuing members. Keep split/merge
relations separate from the one-to-one assignment.

Define S1=0 with no dominant sector as **no detected dominance-based divergence**,
not proven sector coherence. Keep structural non-applicability for isolated
firms distinct from unavailable historical sector labels. Define three-valued
S1/S2/S3/union logic, applicable-signal counting for “multi-signal”, and taxonomy
eligibility when a state is undefined. Membership alone is insufficient.

The peer-set-Jaccard “same-date noise” comparison also needs an exact statistic,
reference procedure and threshold before implementation can be reproduced.

## 7. Preprocessing and SHAP details

Specify log handling for zero/negative revenue or volume: plain log10 is not
defined there. State transform/imputation order, the frozen median on the
transformed scale, and failure rules for an all-missing or constant June feature.
Do not silently switch to log1p or delete firms.

Ordinary same-sample Mahalanobis distance is invariant to nonsingular affine
feature rescaling when the centre and covariance are transformed consistently.
Thus frozen versus refitted MinMax alone should not change full-feature D² if
other preprocessing is held fixed. Log transformations can change it. Treat
that invariance as an implementation check; distinguish skewness/leverage
effects from raw units simply “dominating T²”. Decomposition terms may be signed
and should not be described as independent positive feature importances.

For temporal SHAP, the essential requirement is the same fitted surrogate and
feature definitions/bases at both inputs. Frozen MinMax supports comparable
clustering geometry but is not what validates a classifier trained on raw
features. Define ties, the reference cluster and absent baseline firms. “Most
current peers” may differ from accepted Hungarian/Jaccard matching: disclose
which reference is being explained. Retain additivity checks and weak-fidelity
warnings. Outside-range flags indicate unsupported extrapolation; they do not
establish that the attribution bias is necessarily downward.

## Suggested short replacement passages

**Section 1:** “The framework is applied at three decision dates. It describes
changes in financial peer relationships and the characteristics associated
with those changes. The repeated cross-sections do not constitute an
independently enlarged sample or causal attribution.”

**Section 8, if retaining the SACJ expression:** “The individual squared
Mahalanobis distance is screened against the SACJ F expression as a descriptive
replication reference. It is not assigned a calibrated 5% per-firm error rate.
Counts are not interpreted as approximately n times alpha chance flags. The
primary individual-distance reference and its assumptions are specified
separately before v2 evaluation.”

**Section 11:** “The v2 historical dataset supports a frozen-protocol,
source-validated reanalysis of pilot-informed dates. The complete December 2026
endpoint is reserved for prospective follow-up under the locked procedure.
Both stages retain the dependence created by repeated firms, shared accounting
information and overlapping windows.”

The first required revision is the S2 calibration and its chance-flag/Bonferroni
claims. The next are validation-status wording and instrument-basis rules.
The remaining definitions can then be resolved in an executable protocol
without changing the preserved v1.0 record.
