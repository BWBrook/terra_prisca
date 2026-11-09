from dataclasses import replace

import numpy as np
import pytest

from terra_prisca.haze_world.competition_switches import (
    SUPPLY, cases, finite_crossings, scan_path, temperature_grid,
)
from terra_prisca.haze_world.two_guilds import Competition, delivery, equilibrium


def test_scan_retains_multiple_crossings_and_orientation():
    ts = temperature_grid(277.15, 290., 1.)
    function = lambda t: (t - 278.) * (t - 281.) * (t - 287.)
    events = finite_crossings(ts, [function(t) for t in ts], function)
    assert [e["lower_k"] for e in events] == pytest.approx([278., 281., 287.])
    assert [e["orientation"] for e in events] == [
        "acetogen_cold_methanogen_warm", "methanogen_cold_acetogen_warm",
        "acetogen_cold_methanogen_warm"]


def test_undefined_roots_do_not_generate_a_crossing():
    assert finite_crossings([277., 278., 279.], [-1., np.nan, 1.], lambda t: t - 278.) == []


def test_zero_run_is_a_tie_bracket_not_many_switches():
    function = lambda t: -1. if t < 278. else 1. if t > 279. else 0.
    events = finite_crossings([277., 278., 279., 280.], [-1., 0., 0., 1.], function)
    assert len(events) == 1
    assert events[0]["kind"] == "sampled_tie_interval"
    assert (events[0]["lower_k"], events[0]["upper_k"]) == (278., 279.)


def test_outlet_can_hide_an_intrinsic_competition_switch():
    config = Competition(threshold_shape="fixed_energy", exchange_mol_l_h_pa=SUPPLY / 300.)
    _, reachable, _ = scan_path(config)
    points, hidden, _ = scan_path(replace(config, exchange_mol_l_h_pa=SUPPLY))
    assert len(reachable) == len(hidden) == 1
    assert reachable[0]["lower_k"] == pytest.approx(hidden[0]["lower_k"], abs=1e-7)
    assert reachable[0]["actual_exchange"]
    assert not hidden[0]["reachable"] and not hidden[0]["actual_exchange"]
    assert {p["winner"] for p in points} == {"lifeless"}


def test_active_design_uses_positive_outlets_and_separate_continuations():
    configurations = list(cases())
    assert len(configurations) == 1620 + 972
    assert all(c.exchange_mol_l_h_pa > 0 and c.atmosphere_pa == 0 for _, _, _, c in configurations)
    assert all(c.low_temperature_variant == "none" for group, _, _, c in configurations if group == "base_grid")
    with pytest.raises(ValueError, match="positive resource outlet"):
        scan_path(Competition())


def test_assimilation_changes_methane_delivery_without_moving_rstar():
    config = Competition(threshold_shape="fixed_energy", exchange_mol_l_h_pa=SUPPLY / 300.)
    modified = replace(config, assimilation_m=.0824)
    first, second = equilibrium(15., config), equilibrium(15., modified)
    assert first["winner"] == second["winner"] == "methanogen"
    assert first["rstar_a_pa"] == second["rstar_a_pa"]
    assert first["rstar_m_pa"] == second["rstar_m_pa"]
    a = delivery(first["pressure_pa"], first["biomass_g_l"], 15., config)
    b = delivery(second["pressure_pa"], second["biomass_g_l"], 15., modified)
    expected = config.loss_h * first["biomass_g_l"][1] * .0824 / 4
    assert a["methane_mol_l_h"] - b["methane_mol_l_h"] == pytest.approx(expected)
