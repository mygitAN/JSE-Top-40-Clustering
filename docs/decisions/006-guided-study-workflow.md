# Guided three-cross-section workflow

The user clarified that the objective is to strengthen the original single-window
SACJ paper with three cross-sections for submission elsewhere, and asks for easy
code starting with EDA, followed by modelling, plots and SHAP.

This follow-up adds a clean, ordered notebook and a command-line entry point
using the same stage functions. It does not create a second independent set of
financial definitions. The existing validation/preprocessing, baseline model,
surrogate SHAP and temporal joins are reused.

EDA is completed before fitting models: population, raw/model missingness,
imputations, evidence counts, distributions, correlations and sector context.
The frozen June MinMax is used for comparable distribution plots; raw descriptive
statistics are also retained. No automatic feature removal or future-date tuning.

The recovered t-SNE k=8 baseline retains all nine comparison families per date.
The user's fixed UMAP neighbours=3/min_dist=0.01/k=8 is included as a separately
labelled sensitivity. Both roles use fixed settings across all three dates and
five seeds. The user clarified that k must equal eight, following the original
sector-count design. Both surrogates therefore have eight classes. Other k values
remain diagnostics, not selected paper specifications. DBSCAN reports its natural
cluster/noise count and is not forced into an eight-cluster solution. Legacy sector
labels remain contextual evidence, not independently certified historical ICB.
Baseline result promotion remains unchanged.

Development runs `three-cross-section-study-01` and `-02` preceded this clarification
and retain their original k=5 UMAP outputs for provenance. Their configuration
is superseded for the paper walkthrough by the explicitly constrained k=8 run.

SHAP runs as its own stage after modelling. Both score geometries, fidelity,
class mapping/additivity, univariate comparisons and singleton qualifications
remain explicit. Temporal comparisons retain continuing members separately from
entries/exits. The workflow supplies no new anomaly threshold or taxonomy.

The outer tracked run stays running until every required EDA/model/SHAP/temporal
artifact is validated. Phase errors are recorded as failed; incomplete notebooks
do not produce a completion marker. Source snapshots now include the notebook
and notebook requirements. Executed notebook outputs are saved separately from
the immutable run so post-execution notebook saving cannot invalidate its hashes.

Three cross-sections strengthen descriptive scope but do not guarantee journal
acceptance or resolve archived source evidence. The reviewer feedback is the
user's stated motivation; no rejection letter or journal decision was fabricated.
