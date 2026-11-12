from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest

from terra_prisca.haze_world import dynamic_transients as runs


def test_explicit_temperature_rates_are_not_instantaneous_climate_rates():
    p=runs.core.reference()
    y=next(e['y'] for e in runs.core.equilibrium_states(p) if e['kind']=='mixed').copy()
    coordinates=runs.Coordinates(y,p,3.,285.)
    internal=coordinates.encode(y,285.)
    got=coordinates.derivative(0.,internal)
    expected=runs.core.fluxes_at_temperature(y,p,285.)['net_growth_yr']
    for i in range(2):
        z=internal[i+1]
        factor=np.logaddexp(0.,z)/runs.expit(z)
        assert got[i+1]==pytest.approx(expected[i]*factor)
    assert got[-1]==pytest.approx((runs.core.temperature_k(y[4],p.climate)-285.)/3.)
    assert max(abs(expected))>.01


def test_underflowed_biomass_keeps_finite_log_and_growth_coordinate():
    p=runs.core.reference()
    y=next(e['y'] for e in runs.core.equilibrium_states(p) if e['kind']=='mixed').copy()
    coordinates=runs.Coordinates(y,p,3.,285.)
    internal=coordinates.encode(y,285.);internal[1]=-10000.
    physical,logs=coordinates.decode(internal)
    assert physical[1]==0.
    assert logs[0,0]==pytest.approx(np.log(runs.positive.SCALE)-10000.)
    got=coordinates.derivative(0.,internal)
    expected=runs.core.fluxes_at_temperature(physical,p,285.)['net_growth_yr'][0]
    assert got[1]==pytest.approx(expected)


def test_checked_dense_polynomial_locates_interior_log_population_minimum():
    p=runs.core.reference()
    y=next(e['y'] for e in runs.core.equilibrium_states(p) if e['kind']=='mixed').copy()
    coordinates=runs.Coordinates(y,p,0.,281.5)
    state=coordinates.encode(y)
    coefficients=np.zeros((5,3));coefficients[:,0]=state
    coefficients[1]=[-99.75,1.,1.]
    dense=SimpleNamespace(t=1.,h=1.,yh=coefficients)
    lo=coefficients@np.array([1.,-1.,1.])
    values,times=runs.positive._dense_minima(dense,0.,1.,coordinates,lo)
    assert times[0,0]==pytest.approx(.5)
    assert values[0,0]==pytest.approx(np.log(runs.positive.SCALE)-100.)


def test_zero_lag_recovers_focal_c07_census():
    case=runs.Case('test','B3','fixed',.5,0.,'A_into_M',30.)
    y,t=runs.initial(case);p=runs.parameters(case)
    result=runs.integrate(y,p,30.,census=True,max_step=1.)
    assert result['events'][0]['guild']==1
    assert result['events'][0]['time_yr']==20.
    assert result['y'][2,-1]==0.
    assert result['temperature_k'][20]==pytest.approx(273.525251377,abs=2e-6)


def test_terminal_rare_window_is_horizon_conditional_not_forced_zero(monkeypatch):
    t=np.arange(21.,dtype=float)
    p=runs.core.reference()
    result=dict(t=t,log_biomass=np.array([10.-t,np.ones(t.size)*20.]),
                min_log_biomass=np.array([-10.,20.]),global_log_cell_conversion=0.,
                first_below_cell_yr=[10.,None])
    monkeypatch.setattr(runs,'rates',lambda result,p,g:(np.ones(t.size),np.ones(t.size)*2.,np.ones(t.size)*1e-12))
    got=runs.first_window(result,p,0)
    assert got['status']=='terminal_window_censored'
    assert 0<got['survival_probability']<1
    assert np.isfinite(got['log_survival_probability'])


def test_design_preserves_five_b2_and_twenty_four_homogeneous_invasions():
    cases=runs.design()
    assert len([c for c in cases if c.stage=='B2'])==5
    assert len([c for c in cases if c.stage=='B3'])==24
    assert all(c.chemistry=='fixed' for c in cases if c.stage=='B2')


@pytest.mark.parametrize('chemistry',['fixed','products'])
@pytest.mark.parametrize('tau',[0.,3.])
def test_analytic_coordinate_jacobian_matches_physical_finite_differences(chemistry,tau):
    p=replace(runs.core.reference(),activity_feedback=chemistry)
    y=next(e['y'] for e in runs.core.equilibrium_states(p) if e['kind']=='mixed' and e['stable']).copy()
    coords=runs.Coordinates(y,p,tau,285.)
    state=coords.encode(y,285.);expected=coords.jacobian(0.,state)
    actual=np.zeros_like(expected)
    steps=np.r_[[1e-5,1e-5,1e-5,1e-5,1e-7],1e-4] if tau else [1e-5,1e-5,1e-5,1e-5,1e-7]
    for j,h in enumerate(steps):
        d=np.eye(len(state))[j]*h
        actual[:,j]=(coords.derivative(0.,state+d)-coords.derivative(0.,state-d))/(2*h)
    np.testing.assert_allclose(expected,actual,rtol=3e-5,atol=2e-4)


def test_unsafe_chemical_trial_extension_cannot_be_accepted(monkeypatch):
    p=runs.core.reference()
    y=next(e['y'] for e in runs.core.equilibrium_states(p) if e['kind']=='mixed').copy()
    coords=runs.Coordinates(y,p,3.,285.);state=coords.encode(y,285.)
    state[3]=-1e6
    assert coords.source_log(state)>100
    assert np.all(np.isfinite(coords.derivative(0.,state)))
    monkeypatch.setattr(runs.Coordinates,'source_log',lambda *args:101.)
    with pytest.raises(ArithmeticError,match='accepted state'):
        runs.integrate(y,p,.01,3.,285.)


def test_interval_source_certificate_bounds_interior_coordinate_extrema():
    p=runs.core.reference()
    y=next(e['y'] for e in runs.core.equilibrium_states(p) if e['kind']=='mixed').copy()
    coords=runs.Coordinates(y,p,3.,285.);state=coords.encode(y,285.)
    coefficients=np.zeros((6,3));coefficients[:,0]=state
    coefficients[1]+=[0.,-1.,-1.]
    coefficients[3]+=[0.,1.,1.]
    dense=SimpleNamespace(t=1.,h=1.,yh=coefficients)
    bound=coords.interval_source_bound(dense,0.,1.)
    sampled=max(coords.source_log(coefficients@np.array([1.,x,x*x])) for x in np.linspace(-1.,0.,101))
    assert bound>=sampled
    assert bound<100
