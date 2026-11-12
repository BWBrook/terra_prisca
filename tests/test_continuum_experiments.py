import numpy as np
import pytest

from terra_prisca.haze_world import continuum_experiments as runs


def test_local_gain_is_a_different_counterfactual_from_matched_world():
    p0=runs.b1.parameters('products',.5,.001,.3)
    y=next(r['y'] for r in runs.legacy.equilibrium_states(p0) if r['kind']=='mixed')
    p=runs.model.WeightedParams(p0.base,'products')
    value=runs.gain_check(y,p)
    assert value['status']=='defined'
    assert value['Sc']==pytest.approx(-1.87756715156,rel=1e-7)
    assert value['S0']==pytest.approx(-48.55497806357,rel=1e-7)
    assert value['G_loc']<.05
    assert value['frozen_fd_agrees']
    assert value['frozen_leading_real']<0


def test_static_doubling_does_not_substitute_for_spectral_agreement():
    a=dict(Sc=-2.,S0=-50.,lag=dict(status='finite_crossing',tau_c=10.))
    b=dict(Sc=-2.0001,S0=-50.001,lag=dict(status='finite_crossing',tau_c=100.))
    assert runs.slopes_agree(a,b)
    assert not runs.lag_agrees(a['lag'],b['lag'])
    assert not runs.lag_agrees(dict(status='spectrum_unresolved',tau_c=None),dict(status='spectrum_unresolved',tau_c=None))


def test_finite_input_table_reports_the_perturbation_that_was_qualified():
    record=dict(gain=dict(S0_finite_difference=-69.,S0_finite_difference_fine=-71.,frozen_fd_agrees=True))
    exported=runs.flat(record)
    assert exported['S0_finite_difference']==-71.
    assert exported['S0_finite_difference_step']==1e-5
    assert exported['S0_finite_difference_coarse']==-69.


def test_primary_dense_weighted_operator_recovers_homogeneous_delay_loss():
    p0=runs.b1.parameters('fixed',.5,.001,.3)
    y=next(r['y'] for r in runs.legacy.equilibrium_states(p0) if r['kind']=='mixed')
    p=runs.model.WeightedParams(p0.base,'fixed')
    assert runs.spectrum(y,p,1.)['leading_real']<0
    assert runs.spectrum(y,p,3.)['leading_real']>0
    loss=runs.lag_check(y,p)
    assert loss['tau_c']==pytest.approx(1.102760078,rel=1e-6)
