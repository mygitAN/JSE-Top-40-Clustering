import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from review_cluster_suitability import shortlist,size_profile


class SuitabilityReviewTests(unittest.TestCase):
    def test_better_scoring_singleton_or_wrong_k_cannot_enter_review_shortlist(self):
        rows=[]
        for cid,singletons,k,eligible in [('usable',0,8,True),('singleton',1,8,True),
                                         ('wrong_k',0,7,True),('partial',0,8,False)]:
            rows.append(dict(candidate_id=cid,singleton_clusters_max=singletons,n_clusters_min=k,n_clusters_max=k,
                eligible_all_seeds=eligible,silhouette_features_mean=.1 if cid=='usable' else .9,
                davies_bouldin_features_mean=1. if cid=='usable' else .1,seed_ari_mean=.8))
        self.assertEqual(shortlist(pd.DataFrame(rows)).candidate_id.tolist(),['usable'])

    def test_size_profile_does_not_treat_noise_as_a_peer_group(self):
        result=size_profile(np.array([0,0,1,-1,-1]))
        self.assertEqual(result['largest_cluster'],2)
        self.assertEqual(result['smallest_cluster'],1)
        self.assertEqual(result['singleton_clusters'],1)
        self.assertEqual(result['largest_fraction'],.4)
