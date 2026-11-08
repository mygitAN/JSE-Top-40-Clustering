import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from tune_umap import ROOT,tune_umap,rank_results,metric_champions,hierarchy_matrix


class UserUmapTests(unittest.TestCase):
    def setUp(self):
        self.config=json.loads((ROOT/'configs/user_umap_grid.json').read_text())

    def test_grid_reuses_fits_and_sweeps_best_not_last_embedding(self):
        def embedding(x,neighbors,distance,config):
            return np.tile([neighbors,distance],(len(x),1))
        def scoring(x,z,k,config):
            score=1/z[0,0]-z[0,1]/10-k*.001
            return np.arange(len(x))%k,dict(Silhouette=score,Davies_Bouldin=1-score,
                silhouette_features=score,davies_bouldin_features=1-score,singleton_clusters=0)
        with (patch('tune_umap.fit_umap',side_effect=embedding) as fitting,
              patch('tune_umap.score_fit',side_effect=scoring)):
            result=tune_umap(np.ones((20,3)),self.config)
        self.assertEqual(fitting.call_count,9)
        self.assertEqual(len(result['grid_results']),36)
        self.assertEqual(len(result['cluster_sweep']),14)
        np.testing.assert_array_equal(result['embedding'],np.tile([3,.01],(20,1)))
        self.assertEqual(result['best_parameters']['n_clusters'],2)
        self.assertEqual(result['best_parameters']['linkage'],'average')

    def test_both_scores_print_separate_champions(self):
        import io
        from contextlib import redirect_stdout
        from tune_umap import print_results
        frame=pd.DataFrame([dict(n_neighbors=3,min_dist=.01,n_clusters=7,Silhouette=.9,Davies_Bouldin=2.),
                            dict(n_neighbors=5,min_dist=.04,n_clusters=10,Silhouette=.8,Davies_Bouldin=.1)])
        winners=metric_champions(frame)
        self.assertEqual(winners['highest_silhouette']['n_neighbors'],3)
        self.assertEqual(winners['lowest_db']['n_neighbors'],5)
        with redirect_stdout(io.StringIO()) as text:
            print_results(dict(grid_results=rank_results(frame),grid_champions=winners,sweep_champions=winners,
                               best_parameters={'n_neighbors':3,'min_dist':.01,'n_clusters':7}))
        self.assertIn('silhouette=',text.getvalue())
        self.assertIn('DB=',text.getvalue())
        self.assertIn('Final parameters',text.getvalue())

    def test_dendrogram_tree_matches_same_clustering_geometry(self):
        from scipy.cluster.hierarchy import is_valid_linkage,cut_tree
        from sklearn.cluster import AgglomerativeClustering
        from sklearn.metrics import adjusted_rand_score
        z=np.random.default_rng(42).normal(size=(20,2))
        matrix=hierarchy_matrix(z,self.config)
        self.assertTrue(is_valid_linkage(matrix))
        self.assertEqual(matrix[-1,3],20)
        y=AgglomerativeClustering(n_clusters=3,metric='manhattan',linkage='average').fit_predict(z)
        self.assertEqual(adjusted_rand_score(y,cut_tree(matrix,n_clusters=[3]).ravel()),1.)

    def test_invalid_input_fails_instead_of_skipping(self):
        with self.assertRaisesRegex(ValueError,'finite'):
            tune_umap(np.full((20,3),np.nan),self.config)
        with self.assertRaisesRegex(ValueError,'cluster counts'):
            tune_umap(np.ones((10,3)),self.config)

    def test_fixed_embedding_is_fit_once_and_prints_every_k(self):
        import io
        from contextlib import redirect_stdout
        from tune_umap import sweep_fixed_umap,print_results
        config=json.loads((ROOT/'configs/umap_fixed_001.json').read_text())
        z=np.random.default_rng(42).normal(size=(20,2))
        with patch('tune_umap.fit_umap',return_value=z) as fitting:
            result=sweep_fixed_umap(np.ones((20,3)),config)
        self.assertEqual(fitting.call_count,1)
        self.assertEqual(set(result['cluster_sweep'].n_clusters),set(range(2,13)))
        self.assertEqual(result['best_parameters']['min_dist'],.01)
        with redirect_stdout(io.StringIO()) as output:
            print_results(result)
        self.assertEqual(output.getvalue().count('For k='),11)
        self.assertIn('DB=',output.getvalue())

    def test_fixed_mode_rejects_ambiguous_grid(self):
        from tune_umap import sweep_fixed_umap
        with self.assertRaisesRegex(ValueError,'exactly one'):
            sweep_fixed_umap(np.ones((20,3)),self.config)
