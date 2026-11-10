from dataclasses import replace

import numpy as np
import pytest

from terra_prisca.haze_world import dormancy as d
from terra_prisca.haze_world import habitat_coupling as h
from terra_prisca.haze_world import population_coupling as c


def model():
    return d.Dormancy(h.Habitats(patches=(h.Patch("bulk",.96),h.Patch("warm",.02,"buffered",286.),
                                          h.Patch("cold",.02,"buffered",278.)),dispersal_yr=.001))


def test_zero_switching_and_empty_dormancy_recover_frozen_active_equations():
    p=replace(model(),switching_factor=0.)
    old=h.embed_single([30.,3e-4,4e-4,1e-4,.195],p.base)
    y=d.reference_state(old,p);derivative=d.rhs(y,p)
    assert np.array_equal(d.active_state(derivative,p),h.rhs(old,p.base))
    assert np.array_equal(derivative[p.dormant_indices],np.zeros((3,2)))


def test_conversion_conserves_biomass_and_dormant_stocks_add_no_metabolism():
    p=model();y=d.reference_state(h.embed_single([30.,3e-4,4e-4,1e-4,.195],p.base),p)
    y[p.dormant_indices]=[[1e-4,2e-4],[2e-4,3e-4],[3e-4,4e-4]]
    f=d.fluxes(y,p);dy=d.rhs(y,p)
    active=h.rhs(d.active_state(y,p),p.base)
    assert np.allclose(dy[p.biomass_indices]+dy[p.dormant_indices],
        active[p.base.biomass_indices]+f["dormant_exchange_gdw_l_yr"]-f["dormant_loss_yr"]*y[p.dormant_indices])
    assert d.active_state(dy,p)[-1]==active[-1]
    assert np.allclose(p.weights@f["dormant_exchange_gdw_l_yr"],0.,atol=1e-22)
    assert abs(d.redox_residual(y,p))<2e-17
    coefficients=np.array([c.ASSIMILATION_A,p.coupled.biology.assimilation_m])
    assert d.inventory(y,p)-h.inventory(d.active_state(y,p),p.base)==pytest.approx(
        p.weights@(y[p.dormant_indices]@coefficients))


def test_switching_is_continuous_and_only_one_direction_operates():
    p=model();y=d.reference_state(h.embed_single([30.,3e-4,4e-4,1e-4,.195],p.base),p)
    f=d.fluxes(y,p);g=f["net_growth_yr"]
    assert np.all(f["sigma_yr"][g>=0]==0)
    assert np.all(f["rho_yr"][g<=0]==0)
    assert np.all(f["sigma_yr"]*f["rho_yr"]==0)
    assert np.max(f["sigma_yr"])<=p.switching_factor*p.coupled.biology.loss_h*c.HOURS_PER_YEAR
    x=np.array([-1.,0.,.25,.5,.75,1.,2.])
    assert np.allclose(d.switching_response(x,"cubic"),[0.,0.,.15625,.5,.84375,1.,1.])
    assert np.allclose(d.switching_response(x,"linear"),np.clip(x,0.,1.))


def test_well_mixed_equilibria_embed_but_spatial_growth_need_not_equal_loss():
    base=h.Habitats();p=d.Dormancy(base)
    for state in c.equilibrium_states(base.base):
        if state["kind"]=="mixed" and state["stable"]:
            y=np.asarray(state["y"])
            derivative=d.rhs(d.reference_state(y,p),p)
            assert np.max(abs(d.active_state(derivative,p)-c.rhs(y,p.coupled)))<1e-15
            assert np.max(abs(derivative[p.dormant_indices]))<1e-15
            break
    else:raise AssertionError("Missing reference mixed equilibrium")
    spatial=model()
    anchor=np.array([22.486284925419913,.0005733289267584172,.0003387306888040407,.0008812708744682377,
        19.978022906024876,1.4574557068651612e-7,.0006324208729959125,1.8777211349836823e-7,
        27.616383756231844,.001256137259106304,1.324680283098673e-7,.001762627194022004,.19510686213952005])
    assert np.max(abs(h.rhs(anchor,spatial.base)))<1e-7
    embedded=d.reference_state(anchor,spatial)
    assert np.max(abs(d.rhs(embedded,spatial)[spatial.dormant_indices]))>1e-7
