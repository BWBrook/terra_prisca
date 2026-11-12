from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest

from terra_prisca.haze_world import continuum_characteristic as check
from terra_prisca.haze_world import dynamic_core as production
from terra_prisca.haze_world import population_coupling as core


def reference(fraction=.5,chemistry='fixed'):
    base=replace(core.reference(),acetate_fraction=fraction)
    p=production.DynamicParams(base,chemistry)
    state=next(e['y'] for e in production.equilibrium_states(p) if e['kind']=='mixed')
    q=SimpleNamespace(base=base,chemistry=chemistry,offsets=np.zeros(1),weights=np.ones(1),
                      dispersal_yr=.001,slope_multiplier=1.)
    return p,q,state


@pytest.mark.parametrize('chemistry',['fixed','products','acetate_only','methane_only'])
def test_independent_block_assembly_reconstructs_reference_spectrum(chemistry):
    p,q,state=reference(chemistry=chemistry)
    blocks=check.assemble(q,state)
    own=np.linalg.eigvals(check.dense_matrix(blocks,3.))
    target=np.linalg.eigvals(production.thermal_matrix(state,p,3.))
    assert max(min(abs(v-target)) for v in own)<1e-7


def test_frequency_elimination_finds_reference_margin_with_backsubstitution():
    _,q,state=reference()
    blocks=check.assemble(q,state)
    result=check.critical_lags(blocks)
    assert result['critical_lag_yr']==pytest.approx(1.1027600781,rel=1e-7)
    first=result['crossings'][0]
    assert first['smallest_singular']<1e-10
    assert first['backsubstitution_residual']<1e-10
    assert first['local_pole_distance']>1e-6


def test_censoring_does_not_become_an_infinite_stability_theorem():
    _,q,state=reference(chemistry='products')
    result=check.critical_lags(check.assemble(q,state))
    assert result['status']=='not_detected_through_10000'
    assert result['critical_lag_yr'] is None
    assert 'finite frequency' in result['limitation']


def test_validation_rejects_a_nonsingular_frequency_point():
    _,q,state=reference()
    result=check.validate_root(check.assemble(q,state),.04j,3.)
    assert not result['accepted']


def test_unequal_weights_and_mean_injection_match_physical_finite_differences():
    _,q,state=reference(chemistry='products')
    q.weights=np.array([.2,.3,.5]);q.offsets=np.array([-.5,0.,.5])
    y=np.r_[np.tile(state[:4],3),state[-1]]
    blocks=check.assemble(q,y)
    temperature=float(core.temperature_k(y[-1],q.base.climate))
    initial=np.r_[y,temperature]
    scales=np.r_[blocks.local_scales.ravel(),blocks.global_scales[2:]]
    def rhs(z):
        stocks=z[:-2].reshape(3,4);ratio=z[-2];t=z[-1]
        mean=q.weights@stocks[:,1:3];rows=[];emissions=[]
        for x,offset in zip(stocks,q.offsets):
            local,emission=check._flows(x,ratio,t+offset,q)
            local[1:3]+=q.dispersal_yr*mean
            rows.extend(local);emissions.append(emission)
        rows.extend([q.weights@emissions-q.base.loss.rate(ratio),
                     (core.temperature_k(ratio,q.base.climate)-t)/3.])
        return np.array(rows)
    finite=np.zeros((14,14))
    for j,scale in enumerate(scales):
        delta=np.eye(14)[j]*scale*1e-5
        finite[:,j]=(rhs(initial-2*delta)-8*rhs(initial-delta)+8*rhs(initial+delta)-rhs(initial+2*delta))/(12e-5)*1/scales
    np.testing.assert_allclose(check.dense_matrix(blocks,3.),finite,rtol=1e-6,atol=1e-7)


def test_frozen_composition_slope_matches_finite_input_and_changes_gain_metric():
    _,q,state=reference(chemistry='products')
    report=check.homogeneous_frozen_gain(q,state)
    assert report['sc']==pytest.approx(-1.87756715,rel=1e-7)
    assert report['s0']==pytest.approx(-48.55497806,rel=1e-7)
    assert report['gain_local']==pytest.approx(.03866889095,rel=1e-7)
    assert report['frozen_leading_real_yr']<0
    for row in report['finite_perturbations'][-2:]:
        assert row['relative_difference']<2e-7
        assert row['maximum_root_residual']<1e-10
