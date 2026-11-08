# Three Cross Sections: reporting additions

Use `notebooks/three_cross_section_study.ipynb` for the complete fixed-model workflow. Its t-SNE baseline, UMAP sensitivity, preprocessing, seeds, cluster count, feature profiles, dendrograms, SHAP and original comparisons remain unchanged. New reports are generated during the temporal-comparison stage and required before completion.

Open `reports/three_cross_section_enriched_review.ipynb` for an already executed read-only review: nine code cells and pre-rendered figures, no model fitting. It uses the verified completed `three-cross-section-population-clarified-02` run and separate derived artifacts in `reports/three_cross_section_enriched_20261108`.

The additions include Jaccard-aligned instrument histories, stable/shifted lists, true 0-1 Jaccard heatmaps, separate instrument-movement counts, membership entries/exits, alignment-objective sensitivity and descriptive sector/geometric screens. The existing population/sector plot is retained. Jaccard uses continuing instruments; it is not a transition probability and empty unions remain undefined. No PCA-selected model replaces the original models.

The baseline has 21 stable and 18 shifted instruments among 39 observed at all dates; the fixed UMAP sensitivity has 20 stable and 19 shifted. Each adjacent pair has 40 continuing instruments. Geometric flags are descriptive references, not confirmed outliers. No new temporal-outlier taxonomy or distance-SHAP explanation is claimed.

Verification: seven new focused tests and seven existing study tests pass. The read-only review executes without errors. Completion validation passes with 111 required artifacts and rejects a missing Jaccard CSV. All 289 source-run artifacts verify unchanged. The manifest and derived artifact hashes record source identity. No exhaustive search, model refit, archive overwrite or repository push occurred.

To derive another separate saved-model report, run:

```powershell
.venv\Scripts\python.exe -B scripts/enrich_saved_study.py --source experiments/runs/<completed-study-id> --output reports/<new-report-folder>
```

The output directory must be new and outside the completed source run. Source checksums and completion are verified before and after. Paper Experiments remains available as a separate experiment record; its search and selected results are not rewritten.

The baseline and UMAP Jaccard heatmaps now have separate visible output cells immediately after setup, ahead of EDA/model/SHAP output. Their full-size PNGs are linked above each plot.

Cluster histories now use coloured instrument-flow diagrams instead of numbered heatmap cells. The self-contained history cell in the main notebook explicitly displays inline PNGs; numeric tables are off by default and remain available through `history_tables`. Both the main notebook and enriched review contain rendered flow previews from saved assignments. The standalone `reports/three_cross_section_history_flows_review.ipynb` records exact agreement with the previous aligned labels and zero refits.
