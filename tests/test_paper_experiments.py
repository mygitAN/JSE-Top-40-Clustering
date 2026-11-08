import json
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from paper_search import grid
from paper_longitudinal import hotelling_screen,screen_history,sector_context,aligned_histories,contrast_change


class PaperExperimentTests(unittest.TestCase):
    def test_declared_grid_complete_unique_and_invalid_ward_excluded(self):
        config=json.loads((Path(__file__).resolve().parents[1]/'configs/paper_experiments.json').read_text())
        reps,pool,invalid=grid(config)
        self.assertEqual((len(reps),len(pool),len(pool)*len(config['seeds'])),(86,3268,16340))
        self.assertEqual(len({c['candidate_id'] for c in pool}),3268)
        self.assertEqual(len(invalid),3)
        self.assertEqual({c['clustering']['params']['n_clusters'] for c in pool if c['clustering']['algorithm']!='dbscan'},{8})
        self.assertTrue(all(c['clustering']['params']['metric']=='euclidean' for c in pool if c['clustering']['params'].get('linkage')=='ward'))

    def test_individual_distance_no_n_multiplier_and_affine_invariance(self):
        rng=np.random.default_rng(7);z=rng.normal(size=(41,2))
        d,meta=hotelling_screen(z)
        self.assertAlmostEqual(float(d.sum()),2*(len(z)-1))
        transformed,_=hotelling_screen(z@np.array([[2.,.5],[0.,3.]])+[15,-7])
        np.testing.assert_allclose(d,transformed,atol=1e-10)
        self.assertIn('no calibrated',meta['status'])

    def test_f_reference_formula_is_saved_without_claiming_individual_test(self):
        from scipy.stats import f
        _,meta=hotelling_screen(np.random.default_rng(2).normal(size=(41,2)))
        self.assertAlmostEqual(meta['f_reference'],2*40/39*f.ppf(.95,2,39))
        self.assertIn('internal_beta_reference',meta)

    def test_singular_screen_unestimable_not_zero_distance(self):
        d,meta=hotelling_screen(np.column_stack([np.arange(41),2*np.arange(41)]))
        self.assertTrue(np.isnan(d).all());self.assertIn('not estimable',meta['status'])

    def test_screen_taxonomy_requires_observation_and_handles_recurrence(self):
        self.assertEqual(screen_history([True,None,False]),'not eligible: missing observation/screen')
        self.assertEqual(screen_history([False,True,False]),'transient')
        self.assertEqual(screen_history([True,True,False]),'resolving')
        self.assertEqual(screen_history([True,False,True]),'recurring')
        self.assertEqual(screen_history([False,True,True]),'emerging')

    def test_sector_context_does_not_label_singletons_or_ties_as_divergent(self):
        frame=pd.DataFrame(dict(ticker=['A','B','C','D'],cluster=[0,0,0,1],sector_label=['X','Y','Z','X']))
        result=sector_context(frame).set_index('ticker')
        self.assertTrue(result.sector_divergence.isna().all())
        self.assertIn('singleton',result.loc['D','sector_status'])
        frame.loc[1:2,'sector_label']='Y'
        self.assertTrue(sector_context(frame).set_index('ticker').loc['A','sector_divergence'])

    def test_permuted_clusters_stable_entries_not_shifts(self):
        dates=['a','b','c']
        snapshots={
            'a':pd.DataFrame(dict(ticker=['A','B','C','X'],cluster=[0,0,1,1])),
            'b':pd.DataFrame(dict(ticker=['A','B','C','Y'],cluster=[9,9,3,3])),
            'c':pd.DataFrame(dict(ticker=['A','B','C','Y'],cluster=[5,5,8,8]))}
        aligned,maps,events,histories,objective=aligned_histories(snapshots,dates)
        self.assertTrue((histories.set_index('ticker').loc[['A','B','C'],'stability_status']=='stable all three').all())
        self.assertTrue(events.loc[events.membership_event!='continuing','cluster_changed'].isna().all())
        self.assertFalse(bool(histories.set_index('ticker').loc['Y','observed_all_three']))

    def test_frozen_contrast_attributions_sum_to_same_model_margin_change(self):
        a=np.array([[1.,2.],[3.,5.],[-1.,4.]])
        b=np.array([[3.,1.],[6.,2.],[-2.,7.]])
        delta=contrast_change(a,b,0,1)
        self.assertAlmostEqual(delta.sum(),(b[:,1].sum()-b[:,0].sum())-(a[:,1].sum()-a[:,0].sum()))
        np.testing.assert_array_equal(contrast_change(a,b,0,0),np.zeros(3))

    def test_screen_rejects_missing_or_non_2d_input(self):
        with self.assertRaises(ValueError):hotelling_screen(np.ones((5,1)))
        with self.assertRaises(ValueError):hotelling_screen(np.array([[np.nan,1],[2,3],[4,5],[6,7]]))

    def test_saved_notebook_replay_is_read_only(self):
        import tempfile
        from unittest.mock import patch
        from tracking import Run,digest
        from paper_experiments import SavedPaperExperiment
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            with Run(root/'experiments',{},'fixture','read-only replay fixture','saved') as run:
                (run.out/'paper_manifest.json').write_text(json.dumps(dict(config={'k':8},selected_roles={'baseline':'example'})))
                for name in ['eda/population.csv','search/candidate_summary.csv','search/best_parameters.csv',
                             'representative_scores.csv','longitudinal_summary.csv']:
                    p=run.out/name;p.parent.mkdir(exist_ok=True);p.write_text('value\n1\n')
            before={p.relative_to(root):digest(p) for p in root.rglob('*') if p.is_file()}
            with patch('paper_experiments.ROOT',root):
                view=SavedPaperExperiment('saved')
                for method in [view.explore,view.experiment,view.select_models,view.fit_results,view.longitudinal_review]:
                    self.assertEqual(method().value.tolist(),[1])
                self.assertEqual(view.finish(),run.out)
            after={p.relative_to(root):digest(p) for p in root.rglob('*') if p.is_file()}
            self.assertEqual(before,after)

    def test_saved_replay_rejects_unfinished_runs_and_path_ids(self):
        import tempfile
        from unittest.mock import patch
        from paper_experiments import SavedPaperExperiment
        with tempfile.TemporaryDirectory() as temporary:
            with patch('paper_experiments.ROOT',Path(temporary)):
                with self.assertRaises((ValueError,FileNotFoundError)):SavedPaperExperiment('unfinished')
                with self.assertRaises(ValueError):SavedPaperExperiment('../elsewhere')
