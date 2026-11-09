from dataclasses import replace

import numpy as np
import pytest

from terra_prisca.haze_world.darwinian import fixed_equilibria, reference
from terra_prisca.haze_world.methane_budget import temperature_k
from terra_prisca.haze_world.switch_coupling import Switch, integrate, mixed_states, states, tendency

P, LOSSES = reference()
LINEAR = LOSSES[2]


def test_complete_recycling_or_a_cold_switch_reproduces_the_methanogen_only_haze_world():
    expected = [(e["r"], e["stable"]) for e in fixed_equilibria(P, LINEAR)]
    for sw in (Switch(281.5, 1.0), Switch(250.0, 0.0)):
        got = [(e["r"], e["stable"]) for e in states(P, LINEAR, sw)]
        assert len(got) == len(expected)
        for (r, s), (r0, s0) in zip(got, expected):
            assert r == pytest.approx(r0, rel=1e-9) and s == s0


@pytest.mark.parametrize("t_sw,f_ac", [(281.5, 0.0), (282.8, 0.5)])
def test_mixed_state_is_pinned_at_the_switch_and_stable_only_on_the_haze_branch(t_sw, f_ac):
    sw = Switch(t_sw, f_ac)
    mixed = mixed_states(P, LINEAR, sw)
    assert mixed
    for e in mixed:
        assert float(temperature_k(e["r"], P)) == pytest.approx(t_sw, abs=1e-8)
        assert abs(float(tendency(np.array([e["r"]]), e["s"], P, LINEAR, sw)[0])) < 1e-12
        haze = all(side["t_r"] < 0 for side in e["sides"])
        assert e["stable"] == haze
        if not haze:
            assert all(side["det"] < 0 for side in e["sides"])
    assert any(e["stable"] for e in mixed)


def test_stable_mixed_state_is_reached_whatever_the_selection_rate():
    sw = Switch(282.8, 0.5)
    target = [e for e in mixed_states(P, LINEAR, sw) if e["stable"]][0]
    for g in (0.1, 10.0):
        end = integrate(P, LINEAR, replace(sw, selection_per_k_yr=g), r0=0.1953, s0=0.01)
        assert end["t_k"] == pytest.approx(282.8, abs=1e-6)
        assert end["s"] == pytest.approx(target["s"], rel=1e-5)


def test_mixed_temperature_is_independent_of_supply_within_its_band():
    from terra_prisca.haze_world.experiments import flux_for_potential
    sw = Switch(281.5, 0.0)
    shares = []
    for pot in (0.25, 0.4, 0.55):
        q = replace(P, donor_flux=float(flux_for_potential(pot, P)))
        e = [x for x in mixed_states(q, LINEAR, sw) if x["stable"]][0]
        assert e["t_k"] == 281.5
        shares.append(e["s"])
    assert np.all(np.diff(shares) > 0)
