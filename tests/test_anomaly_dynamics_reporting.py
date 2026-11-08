import json
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from report_anomaly_dynamics import classify_pattern,signal_histories,sensitivity_summary
from optimize_models import quality


class ReportingAmendmentTests(unittest.TestCase):
    def setUp(self):
        self.patterns=json.loads((Path(__file__).resolve().parents[1]/'configs/anomaly_dynamics_reporting_v2.json').read_text())['patterns']

    def test_taxonomy_distinguishes_resolved_resolving_and_sustained(self):
        self.assertEqual(classify_pattern([1,0,0],self.patterns),'resolved')
        self.assertEqual(classify_pattern([1,1,0],self.patterns),'resolving')
        self.assertEqual(classify_pattern([0,1,1],self.patterns),'emerging and sustained')
        self.assertEqual(classify_pattern([1,0,1],self.patterns),'recurring')

    def test_missing_observation_is_not_resolution(self):
        for values in [[True,None,False],[True,np.nan,False],[False,pd.NA,False]]:
            self.assertTrue(classify_pattern(values,self.patterns).startswith('not eligible'))

    def test_geometric_sector_and_joint_histories_are_separate(self):
        cases=pd.DataFrame(dict(ticker=['A']*3,decision_date=['a','b','c'],screen_flag=[False,True,True],
            sector_divergence=[True,True,None]))
        result=signal_histories(cases,['a','b','c'],self.patterns).set_index('channel')
        self.assertEqual(result.loc['geometric_screen','classification'],'emerging and sustained')
        self.assertTrue(result.loc['sector_divergence','classification'].startswith('not eligible'))
        self.assertTrue(result.loc['joint_agreement','classification'].startswith('not eligible'))
        self.assertFalse(bool(result.loc['joint_agreement','a']))

    def test_k12_remains_eligible_in_declared_2_to_12_sensitivity(self):
        x=np.random.default_rng(5).normal(size=(24,3));y=np.repeat(np.arange(12),2)
        metrics=[dict(candidate_id='k12',seed=seed,**quality(x,x,y)) for seed in [42,43]]
        stability=pd.DataFrame([dict(candidate_id='k12',seed_a=42,seed_b=43,ari=1.,nmi=1.)])
        result=sensitivity_summary(metrics,stability,dict(seeds=[42,43]))
        self.assertTrue(bool(result.eligible_all_seeds.iloc[0]))
