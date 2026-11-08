# Bounded model optimisation protocol

Recorded before executing the search, 8 November 2026. The user explicitly asks
to optimise combinations and report both silhouette and Davies-Bouldin (DB).
This authorises a new exploratory selection experiment; it does not promote a
replacement paper baseline or permit data refreshes.

## Paper review

The supplied local `SACJ_JSE_Top40.pdf` has 16 pages. Pages 5–8 and 11 were
rendered and inspected; all text was extracted for reading. Page 7, Table 2
reports t-SNE/hierarchical as highest silhouette (0.5023) and lowest DB (0.5296)
among nine combinations. This supports a within-comparison model-selection
claim. It is not a proof of a global optimum across unsearched configurations.

The manuscript's original observations cover 6 February 2023–5 February 2024,
40 source-listed equities and 11 numeric features, including analyst consensus
and P/E. It acknowledges that RMH was not an official index member. The current
data are different: three later membership-correct cross-sections, 41 instruments
per date, ten numeric features, consensus excluded, P/E replaced with E/P.
Original and new score magnitudes must not be presented as a controlled improvement.
The original eleven-feature list is now established by manuscript page 4.

Two implementation differences are explicit: manuscript page 5 uses PCA with
95% retained variance and automatic t-SNE learning rate; the recovered historical
settings currently frozen in the repository use PCA(2) for comparison and t-SNE
learning rate 10. Both variants enter this search. The original DBSCAN grid and
complete seed/settings logs are not specified in the PDF, so this is a new grid.
Sector labels remain contextual comparators despite the manuscript's stronger
ground-truth wording. The original 1.0 stability claim cannot be verified or
rejected by different dates/features; current seed results must be reported afresh.

The PDF page 11 supplies n=40, p=2, 5% and a T² cutoff approximately 6.66.
This resolves those previously unavailable manuscript details. It does not by
itself establish the individual-distance/F-reference calibration for new
data-adaptive embeddings. No Hotelling extension is part of this optimisation.

## Purpose and budget

`configs/optimization.json` defines 23 representations: PCA(2)/PCA(95%),
12 t-SNE settings and nine UMAP settings. Each is crossed with 45 hierarchical
settings (five valid linkage/metric pairs × nine k), nine K-Means k values, and
eight standardized-embedding DBSCAN settings. Total: 1,426 configurations,
7,130 selection-date fits over seeds 42–46. PCA seed replicates are deterministic
and are not misrepresented as additional independent uncertainty.

The first date alone enters candidate ranking. Freeze its imputation, clipping
and MinMax exactly as before. All observations, including RNI and noise-labelled
members, stay in outputs. Expected local execution is minutes; no expansion or
automatic adaptive continuation of the grid is allowed. Any interrupted/failed
run is not a completed search and must not supply a winner.

After selection, refit only the three selected configurations and fixed baseline
at all three dates using the same five seeds (at most 60 follow-up fits, including
selection-date replays). Later dates are descriptive follow-ups, already examined
in earlier research, and are not claimed to be untouched validation or predictive
tests. All settings are selected on June 2025 scores; no cross-date best-of score.

## Joint selection and geometry

Report silhouette (higher better) and DB (lower better) in both the fitted
representation and the common June-scaled ten-feature space. Both use Euclidean
score geometry; the linkage metric remains separately labelled. DB uses Euclidean
centroids, not Manhattan linkage. PCA(95%) may retain more than two dimensions;
its embedding-score geometry is its full retained representation.

Candidates must have finite scores, 2–10 clusters and full population coverage
on every seed to be eligible for a winning whole-universe partition. DBSCAN is
still evaluated and its noise/coverage retained, even when this eligibility rule
excludes it. It is not forced into eight clusters, and noise is excluded from
quality calculations. Degenerate all-noise/one-cluster outcomes are recorded.

For each eligible cohort compute mean scores across five seeds. Rank mean
silhouette descending and mean DB ascending with average ranks; their equally
weighted rank sum is the declared joint criterion. Choose the smallest sum,
then higher mean pairwise seed ARI, higher feature-space silhouette and finally
candidate ID for deterministic ties. This equal-rank preference is a new explicit
implementation choice. Also export the two-objective Pareto frontier and the
individual silhouette/DB champions so trade-offs remain visible.

Selections: (1) paper-style embedding scores at k=8; (2) common-feature scores at
k=8; (3) common-feature scores allowing k=2–10. The first follows the manuscript's
score-space convention, the second checks the representation effect, and the
third keeps the historical k=8 assumption open. No sector ARI/NMI enters ranking.
No single lucky seed is selected; seed 42 is only the pre-existing representative
fit for plots, assignments and eight-class surrogate explanations.

"Best" means best under this finite grid, cohort, date and declared criterion.
It does not mean a universal optimum or economic usefulness. The paper's original
scores remain historical reported results and the reconstructed baseline remains
unchanged. See scikit-learn's [DB definition](https://scikit-learn.org/1.6/modules/generated/sklearn.metrics.davies_bouldin_score.html)
and [t-SNE settings](https://scikit-learn.org/1.6/modules/generated/sklearn.manifold.TSNE.html).
