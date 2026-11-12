import numpy as np
import pytest

from terra_prisca.haze_world import continuum_core as weighted
from terra_prisca.haze_world import graded_dials as dials


def test_partial_exponent_spectra_never_call_full_strength_block_builder(monkeypatch):
    def wrong_builder(*args,**kwargs):
        raise AssertionError('Old full-strength blocks used for a partial exponent')
    monkeypatch.setattr(weighted,'local_blocks',wrong_builder)
    record=dials.d1_point(.01,.5)
    assert record['status']=='accepted'
    assert record['gain']['frozen_fd_agrees']
    assert record['supply_check']['status']=='passed'
    pair=record['zero_lag_modes']['selected_pair']
    assert pair['damping_time_yr']>0
    assert pair['eigenpair_residual']<1e-10
    assert record['weak_mode_tau_yr']==pytest.approx(2*(-pair['real_yr'])/pair['omega_yr']**2)


def test_modal_summary_keeps_dominant_real_mode_separate(monkeypatch):
    p=dials.acetate.parameters(0.,.5)
    y=np.ones(5)
    b=weighted.Blocks(np.zeros((1,4,4)),np.zeros((1,4,2)),np.zeros((1,4)),
        np.zeros((1,4)),np.zeros((1,4)),0.,0.,np.zeros((2,4)),np.ones(1),0.)
    matrix=np.array([[-.01,0,0,0,0],[0,-.2,-2,0,0],[0,2,-.2,0,0],
                     [0,0,0,-1,0],[0,0,0,0,-3]])
    monkeypatch.setattr(weighted,'dense_matrix',lambda *a,**k:matrix)
    monkeypatch.setattr(weighted,'operator_scales',lambda *a,**k:np.ones(5))
    result=dials.modal_record(y,p,b)
    assert result['leading_real_yr']==pytest.approx(-.01)
    assert result['leading_imag_yr']==0
    assert result['selected_pair']['real_yr']==pytest.approx(-.2)
    assert result['selected_pair']['period_yr']==pytest.approx(np.pi)
