import sys
import unittest
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from study_enrichment import membership_matrices, enrich_model, descriptive_screens
from paper_longitudinal import aligned_histories


class EnrichmentTests(unittest.TestCase):
    def test_jaccard_is_ratio_not_count(self):
        old=pd.Series([0,0,1],index=['A','B','C'])
        new=pd.Series([7,8,8],index=['A','B','C'])
        counts,jaccard,n=membership_matrices(old,new)
        self.assertEqual(n,3)
        self.assertEqual(counts.loc[0,8],1)
        self.assertAlmostEqual(jaccard.loc[0,8],1/3)
        self.assertAlmostEqual(jaccard.loc[0,7],.5)
        self.assertAlmostEqual(jaccard.loc[1,8],.5)

    def test_entries_exits_do_not_lower_continuing_similarity(self):
        old=pd.Series([0,0],index=['A','EXIT'])
        new=pd.Series([4,4],index=['A','ENTRY'])
        counts,jaccard,n=membership_matrices(old,new)
        self.assertEqual(n,1);self.assertEqual(counts.loc[0,4],1)
        self.assertEqual(jaccard.loc[0,4],1)

    def test_empty_unions_are_undefined(self):
        old=pd.Series([0,1],index=['A','EXIT'])
        new=pd.Series([3,4],index=['A','ENTRY'])
        _,jaccard,_=membership_matrices(old,new)
        self.assertTrue(np.isnan(jaccard.loc[1,4]))
        self.assertEqual(jaccard.loc[0,4],0)

    def test_duplicate_instruments_are_rejected(self):
        with self.assertRaises(ValueError):
            membership_matrices(pd.Series([0,1],index=['A','A']),pd.Series([2],index=['A']))

    def test_permuted_labels_and_membership_gaps_remain_separate(self):
        dates=['a','b','c']
        frames={d:pd.DataFrame(dict(ticker=['A','B',extra],cluster=labels))
                for d,extra,labels in [('a','X',[0,0,1]),('b','Y',[4,4,7]),('c','Y',[8,8,6])]}
        aligned,maps,events,histories,sensitivity=aligned_histories(frames,dates)
        self.assertTrue(events.loc[events.membership_event!='continuing','cluster_changed'].isna().all())
        self.assertTrue((histories.set_index('ticker').loc[['A','B'],'stability_status']=='stable all three').all())
        self.assertEqual(int(histories.observed_all_three.sum()),2)
        _,similarity,_=membership_matrices(aligned['a'],aligned['b'])
        self.assertEqual(similarity.loc[0,0],1)

    def test_screens_align_tickers_and_keep_singular_as_missing(self):
        frame=pd.DataFrame(dict(ticker=['A','B','C','D'],cluster=[0,0,1,1],sector_label=['X','X','Y','Y']))
        with tempfile.TemporaryDirectory() as temporary:
            folder=Path(temporary);(folder/'d').mkdir()
            for seed in range(42,47):
                np.savez(folder/'d'/f'seed_{seed}_arrays.npz',tickers=np.array(['D','C','B','A']),embedding=np.array([[4,8],[3,6],[2,4],[1,2]]))
            result=descriptive_screens({'d':frame},folder,['d'],42,5)
            self.assertTrue(result.screen_flag.isna().all())
            self.assertTrue(result.multi_seed_supported.isna().all())
            self.assertEqual(result.estimable_seeds.sum(),0)

    def test_missing_date_fails_without_fitting(self):
        frame=pd.DataFrame(dict(decision_date=['a'],ticker=['A'],cluster=[0]))
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError,'Missing study date'):
                enrich_model(frame,Path(temporary),['a','b','c'],Path(temporary)/'out','test')


if __name__=='__main__':unittest.main()
