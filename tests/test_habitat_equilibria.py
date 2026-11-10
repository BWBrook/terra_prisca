from dataclasses import replace

import numpy as np
import pytest

from terra_prisca.haze_world import habitat_coupling as m
from terra_prisca.haze_world import habitat_equilibria as e
from terra_prisca.haze_world import population_coupling as single


def reference(d=.001, activity="fixed"):
    return m.Habitats(replace(single.reference(),activity_feedback=activity),
        (m.Patch("bulk",.96),m.Patch("warm",.02,"buffered",286.),m.Patch("cold",.02,"buffered",278.)),d)


@pytest.mark.parametrize("d",[0.,1e-9,.001,1.])
@pytest.mark.parametrize("guild",[0,1])
def test_conditional_starts_are_supported_positive_and_stationary(d,guild):
    p=reference(d)
    states=e.conditional_states(p,guild)
    stable=[s for s in states if s["stability"]=="stable"]
    assert stable
    for s in stable:
        assert np.all(s["y"][p.biomass_indices[:,guild]]>0)
        assert np.all(s["y"][p.biomass_indices[:,1-guild]]==0)
        assert s["max_scaled_residual"]<1e-8
        assert "unsupported" not in s["physiology_domains"]


def test_full_root_matches_independently_derived_three_patch_anchor():
    p=reference()
    anchor=np.array([22.486284925419913,.0005733289267584172,.0003387306888040407,.0008812708744682377,
        19.978022906024876,1.4574557068651612e-7,.0006324208729959125,1.8777211349836823e-7,
        27.616383756231844,.001256137259106304,1.324680283098673e-7,.001762627194022004,.19510686213952005])
    found=e.refine(anchor*1.001,p)
    assert found is not None and found["stability"]=="stable"
    assert np.allclose(found["y"],anchor,rtol=1e-7,atol=1e-13)
    assert abs(found["redox_residual"])<1e-15


def test_product_activities_are_solved_self_consistently():
    p=reference(activity="products")
    states=e.conditional_states(p,0)
    assert states and any(s["stability"]=="stable" for s in states)
    assert all(s["max_scaled_residual"]<1e-8 for s in states)


def test_one_patch_conditional_matches_existing_model():
    p=m.Habitats(single.reference(),(m.Patch("bulk",1.),),.1)
    for guild in (0,1):
        ours=e.conditional_states(p,guild)
        base=replace(p.base,enabled=(guild==0,guild==1))
        old=single.equilibrium_states(base,n_grid=121)
        for state in ours:
            assert any(np.allclose(state["y"],s["y"],rtol=1e-7,atol=1e-10) for s in old)
