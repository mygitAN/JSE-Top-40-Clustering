# Print the best UMAP results and parameters

Corrected executable: `scripts/tune_umap.py`. Completed run: `user-umap-grid-01`.

Print the saved winners, scores, parameters and top ten rows without fitting:

```bash
python scripts/tune_umap.py --print-run user-umap-grid-01
```

Run the grid again in a new immutable run:

```bash
python scripts/tune_umap.py
```

For a notebook running from the repository root:

```python
import sys
sys.path.insert(0, "scripts")
from tune_umap import tune_umap, print_results

result = tune_umap(scaled_data)
print_results(result)
best_parameters = result["best_parameters"]
best_umap_data = result["embedding"]
best_labels = result["labels"]
```

## Actual June 2025 output (seed 42)

| Stage | n_neighbors | min_dist | n_clusters | Silhouette | Davies-Bouldin |
| --- | ---: | ---: | ---: | ---: | ---: |
| Best of the supplied 36 combinations | 3 | 0.1 | 7 | 0.748599 | 0.259814 |
| Best k=2–15 on that winning embedding | 3 | 0.1 | 4 | 0.876566 | 0.143483 |

In this run, the highest-silhouette, lowest-DB and joint-score choices agree at
each stage. Both scores are still printed separately; the code does not assume
that they always share a winner. Higher silhouette and lower DB are better.

Final parameters:

```json
{
  "n_neighbors": 3,
  "min_dist": 0.1,
  "n_components": 2,
  "umap_metric": "euclidean",
  "n_clusters": 4,
  "clustering_metric": "manhattan",
  "linkage": "average",
  "random_state": 42,
  "n_jobs": 1
}
```

## Repairs and saved artifacts

- Fixed the missing closing bracket in `[7, 10, 11, 12]`.
- Defined clustering metric/linkage consistently and imported plotting dependencies.
- Fit UMAP nine times, once per parameter pair, rather than refitting it for each k.
- Selected the best grid embedding before the k sweep, replacing the loop's last embedding.
- Recorded every combination; a failed fit fails the tracked run with diagnostics instead of being silently skipped.
- Built the dendrogram linkage matrix from a full scikit-learn tree fitted on the
  selected embedding with the same average/Manhattan geometry. Its cut reference
  lies between the merge heights for the selected k, with tied-height accounting.
- Replaced the unrelated "Stores" label with instruments and retained legacy sector
  context plus imputation markers in the dendrogram labels.

The run stores `grid_results.csv`, `cluster_count_scores.csv`, `best_parameters.json`,
`metric_champions.json`, `selected_arrays.npz`, `linkage_matrix.npy`,
`cluster_count_scores.png`, `dendrogram.png`, and assignments at all three dates.
It also stores its code/configuration snapshot, log, status and checksum manifest.
The CLI print-only mode was executed successfully against the saved bundle.
All 40 tests pass locally, including fit reuse, selection of the correct embedding,
printing both champions, input failures and exact hierarchy/partition agreement.

## Scope

This follows the supplied two-stage search: 36 initial combinations, then k=2–15
on one selected embedding. It is not an exhaustive 9×14 grid. The seed is 42;
these are single-seed exploratory scores, not five-seed means or stability evidence.
Selection uses June 2025 only, June-fitted preprocessing, and all 41 instruments.
Later dates refit the frozen chosen parameters descriptively. Baseline promotion
and source data are unchanged.

Both headline metrics above are calculated in Euclidean UMAP embedding geometry;
hierarchical fitting itself uses average linkage and Manhattan distance. The June
four-cluster solution's common-feature silhouette/DB are 0.174717/1.219883, so the
strong embedding separation does not carry over to the same degree in financial
feature space. Full follow-up metrics are in `frozen_followup_scores.csv`.
