import unittest
import numpy as np
import pandas as pd
from top40.explanation_report import transition_tables

class ExplanationTests(unittest.TestCase):
    def fixture(self):
        rows=[]
        # A stays with B despite a local label renumbering; C joins, X exits.
        for date,listing in [('d1',[('A',0,2,1.),('B',0,2,2.),('X',1,3,3.)]),
                             ('d2',[('A',5,2,2.),('B',5,2,4.),('C',6,3,8.)])]:
            for ticker,raw,aligned,value in listing:
                rows.append(dict(study_model='m',decision_date=date,ticker=ticker,company=ticker,
                    feature='f',feature_label='Feature',raw_cluster=raw,aligned_cluster=aligned,
                    raw_value=value,scaled_value=value,own_class_shap=.2,
                    destination_minus_source_shap=.1,surrogate_oof_accuracy=.8))
        members=pd.DataFrame(rows)
        profiles=pd.DataFrame([dict(study_model='m',decision_date=d,cluster=c,feature='f',deviation_scaled=.5)
                               for d in ['d1','d2'] for c in [2,3]])
        return transition_tables(members,profiles)

    def test_raw_renumbering_is_not_a_move(self):
        transitions,_,_,_=self.fixture()
        self.assertFalse(transitions.aligned_move.any())
        self.assertEqual(transitions.loc[transitions.ticker=='A','to_raw_cluster'].iloc[0],5)

    def test_entries_and_exits_are_separate(self):
        transitions,_,evolution,_=self.fixture()
        self.assertEqual(set(transitions.ticker),{'A','B'})
        group=evolution[evolution.aligned_cluster==3].iloc[0]
        self.assertEqual((group.index_entries,group.index_exits),('C','X'))
        self.assertEqual(group.joined_from_other_clusters,'')

    def test_peer_medians_exclude_focal_name(self):
        _,features,_,_=self.fixture()
        a=features[features.ticker=='A'].iloc[0]
        self.assertEqual(a.destination_peers_median_after,4.)
        self.assertEqual(a.original_peers_median_after,4.)
        self.assertEqual(a.scaled_change,1.)
        self.assertTrue(np.isnan(a.same_date_destination_minus_source_shap))

if __name__=='__main__':unittest.main()
