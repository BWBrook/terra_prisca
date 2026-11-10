import numpy as np
import pytest

from terra_prisca.haze_world import turnover as t
from terra_prisca.haze_world import population_coupling as core


def test_thermal_switch_is_separate_from_planetary_mixed_state():
    assert np.isfinite(t.switch_at(2.3e-4))
    assert t.switch_at(2.3e-4) < 273.39
    assert not any(s["kind"]=="mixed" for s in t.equilibria(0.,2.3e-4))


def test_small_radiative_upturn_creates_low_turnover_bistability():
    states=t.equilibria(0.,2.3713737056616554e-4,verify=True)
    stable={s["kind"] for s in states if s["stable"]}
    assert stable=={"mixed","methanogen"}
    assert any(s["kind"]=="mixed" and not s["stable"] for s in states)


def test_extended_turnover_grid_includes_lifeless_high_loss_state():
    states=t.equilibria(.5,.01)
    assert [(s["kind"],s["stable"]) for s in states]==[("lifeless",True)]


def test_direct_resident_balance_matches_full_physical_model():
    for fraction,index,ratio in ((.5,0,.10),(0.,1,.20)):
        loss=t._resident_loss(ratio,fraction,index)
        assert np.isfinite(loss)
        p=t.params(fraction,loss);state=core._resident(ratio,p,index)
        assert abs(t._pure_balance(ratio,loss,fraction,index)) < 1e-13
        assert core.rhs(state,p)[-1]==pytest.approx(t._pure_balance(ratio,loss,fraction,index),abs=1e-15)


def test_exact_plateau_crossing_has_a_family_not_an_isolated_mixed_root():
    roots=t._log_roots(lambda L:t._difference(274.002,L))
    assert len(roots)==1
    family=t.plateau_family(0.,roots[0])
    assert family is not None
    assert family["ratio_interval"][0]==pytest.approx(.2333365)
    assert family["ratio_interval"][1]>.27


@pytest.mark.parametrize("fraction,loss,expected", [
    (.9,.003011,["acetogen","acetogen"]),
    (0.,.004,["acetogen","methanogen"]),
    (.5,.009245,["acetogen","lifeless"]),
])
def test_root_resolved_narrow_windows_include_all_stable_branches(fraction,loss,expected):
    states=t.equilibria(fraction,loss,verify=True)
    assert sorted(s["kind"] for s in states if s["stable"])==expected


def test_near_vertex_stability_does_not_mix_two_radiative_slopes():
    below,above=.0030123,.0030124
    for loss,sign in ((below,1),(above,-1)):
        p=t.params(.9,loss)
        state=next(s for s in t.equilibria(.9,loss) if s["kind"]=="mixed")
        values=[max(t.stability_spectrum(state["y"],p,step)[0].real) for step in (1e-4,1e-5,1e-6)]
        assert all(sign*value>0 for value in values)
        assert max(values)-min(values)<1e-10
