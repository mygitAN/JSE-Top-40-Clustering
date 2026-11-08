import json
import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from optimize_models import candidates,representations,baseline_candidate,quality,select,pareto,fit_cluster


class OptimizationTests(unittest.TestCase):
    def test_exact_budget_and_preserved_baseline(self):
        config=json.loads((Path(__file__).resolve().parents[1]/'configs/optimization.json').read_text())
        pool=candidates(config)
        self.assertEqual(len(representations(config)),23)
        self.assertEqual(len(pool),1426)
        self.assertEqual(len({c['candidate_id'] for c in pool}),1426)
        self.assertEqual(baseline_candidate(pool)['clustering']['params'],
                         {'n_clusters':8,'linkage':'average','metric':'manhattan'})
        self.assertTrue(all(c['clustering']['params']['metric']=='euclidean' for c in pool
                            if c['clustering']['params'].get('linkage')=='ward'))

    def test_both_metrics_and_noise_accounting(self):
        from sklearn.metrics import davies_bouldin_score,silhouette_score
        x=np.array([[0,0],[0,1],[9,9],[9,10],[100,100]],dtype=float)
        y=np.array([0,0,1,1,-1])
        score=quality(x,x,y)
        self.assertEqual(score['noise_count'],1)
        self.assertEqual(score['coverage'],.8)
        self.assertAlmostEqual(score['davies_bouldin_features'],davies_bouldin_score(x[:4],y[:4]))
        self.assertAlmostEqual(score['silhouette_embedding'],silhouette_score(x[:4],y[:4]))
        for labels in [np.full(5,-1),np.zeros(5,dtype=int)]:
            result=quality(x,x,labels)
            self.assertIsNone(result['davies_bouldin_embedding'])
            self.assertIsNone(result['silhouette_features'])

    def test_joint_selection_filters_population_and_uses_db(self):
        rows=[]
        for cid,s,d,eligible in [('a',.9,9,True),('b',.8,.1,True),('c',.7,.2,True),('fake',1.,0.,False)]:
            rows.append(dict(candidate_id=cid,silhouette_embedding_mean=s,davies_bouldin_embedding_mean=d,
                             silhouette_features_mean=s,seed_ari_mean=1.,eligible_all_seeds=eligible,
                             n_clusters_min=8,n_clusters_max=8))
        result=select(pd.DataFrame(rows),'embedding',8)
        self.assertEqual(result.iloc[0].candidate_id,'b')
        self.assertNotIn('fake',set(result.candidate_id))
        changed=pd.DataFrame(rows);changed['sector_ari']=range(4)
        pd.testing.assert_series_equal(result.candidate_id,select(changed,'embedding',8).candidate_id)

    def test_pareto_and_deterministic_hierarchical_fit(self):
        frame=pd.DataFrame({'sil':[.8,.7,.6,.8],'db':[.2,.1,.3,.2]})
        np.testing.assert_array_equal(pareto(frame,'sil','db'),[True,True,False,True])
        data=np.array([[0,0],[0,.1],[10,10],[10,10.1]],dtype=float)
        spec={'algorithm':'hierarchical','params':{'n_clusters':2,'linkage':'average','metric':'manhattan'}}
        np.testing.assert_array_equal(fit_cluster(data,spec,42),fit_cluster(data,spec,43))

    def test_dbscan_stability_excludes_noise_and_reports_common_coverage(self):
        from summarize_optimization import nonnoise_agreement
        a=np.array([0,0,1,-1]);b=np.array([2,2,3,3])
        result=nonnoise_agreement(a,b)
        self.assertEqual(result['common_nonnoise_members'],3)
        self.assertEqual(result['common_coverage'],.75)
        self.assertEqual(result['ari'],1.)
        self.assertIsNone(nonnoise_agreement(np.full(4,-1),b)['ari'])
        self.assertIsNone(nonnoise_agreement(np.zeros(4),np.zeros(4))['nmi'])
