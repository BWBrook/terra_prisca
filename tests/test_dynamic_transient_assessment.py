import numpy as np

from terra_prisca.haze_world.dynamic_transient_assessment import first_episode,score_first


def test_first_episode_cannot_be_replaced_by_later_deeper_global_minimum():
    log_counts=np.array([45.,40.,30.,10.,-5.,15.,40.,45.,30.,-200.,-10.,40.])
    got=first_episode(log_counts,np.ones(log_counts.size)*1e-12)
    lo,hi,_=got['window']
    assert hi<8
    assert np.min(log_counts[lo:hi+1])==-5.


def test_rarity_refinement_stays_inside_first_episode_or_becomes_unassessed():
    log_counts=np.array([45.,40.,30.,20.,30.,40.,45.,20.,-200.,40.])
    fractions=np.array([1e-5]*6+[1e-20]*4)
    got=first_episode(log_counts,fractions)
    assert got['status']=='first_episode_not_locally_linear'
    assert got['window'] is None


def test_other_loss_inside_window_invalidates_assembly_without_zeroing_conditional_math():
    t=np.arange(21.,dtype=float)
    logs=np.array([40.-t*3.,np.ones(21)*50.])
    result=dict(t=t,log_biomass=logs,global_log_cell_conversion=0.,
                uptake_fraction=np.ones((2,21))*1e-12,birth_yr=np.ones((2,21)),
                death_yr=np.ones((2,21))*4.,first_below_cell_yr=[40/3,10.])
    got=score_first(result,0)
    assert got['assembly_status']=='unassessed_other_guild_loss'
    assert got['other_loss_before_end']
    assert 0<got['survival_probability']<1
    assert np.isfinite(got['log_survival_probability'])
