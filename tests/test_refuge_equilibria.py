from dataclasses import replace

import numpy as np
import pytest

from terra_prisca.haze_world import population_coupling as core
from terra_prisca.haze_world.refuge_coupling import Refuge, rhs, temperatures
from terra_prisca.haze_world.refuge_equilibria import equilibrium_states, search_coverage


@pytest.mark.parametrize("fraction,weight,contrast,expected", [
    (0., .74, 1., 281.7926410225), (.5, .51, 8., 282.0023037937),
])
def test_protected_partitions_solve_shared_methane_and_full_local_budgets(fraction, weight, contrast, expected):
    p = Refuge(replace(core.reference(), acetate_fraction=fraction), weight, contrast, 0.)
    row = next(e for e in equilibrium_states(p, n_grid=101) if e["kind"] == "pure_partition" and e["stable"])
    assert row["global_temperature_k"] == pytest.approx(expected, abs=1e-7)
    assert row["measured"]
    switch = core.switch_temperatures(p.base.biology)[0]
    assert row["temperatures_k"][0] < switch < row["temperatures_k"][1]
    assert row["max_scaled_residual"] < 1e-10
    assert abs(row["redox_residual"]) < 1e-14
    assert np.max(abs(rhs(row["y"], p)[[1, 2, 3, 5, 6, 7, 8]])) < 1e-10


def test_algebraic_partition_existence_does_not_imply_invasion_protection():
    p = Refuge()
    rows = equilibrium_states(p, n_grid=101)
    partition = next(e for e in rows if e["kind"] == "pure_partition")
    assert partition["stability"] == "unstable"
    assert np.all(partition["temperatures_k"] > core.switch_temperatures(p.base.biology)[0])
    mixed = [e for e in rows if e["nonisolated"]]
    assert mixed and all(e["stability"] == "marginal" for e in mixed)
    assert all(min(abs(e["eigenvalues"])) < 1e-7 for e in mixed)


def test_positive_exchange_has_sink_stocks_and_closes_each_population_equation():
    p = Refuge(replace(core.reference(), acetate_fraction=0.), .74, 1., .001)
    row = next(e for e in equilibrium_states(p, n_grid=101) if e["stable"])
    assert row["kind"] == "partition_with_sinks"
    assert np.all(row["y"][[1, 2, 5, 6]] > 0)
    assert row["y"][2] < row["y"][6] and row["y"][5] < row["y"][1]
    assert row["max_scaled_residual"] < 1e-8
    assert abs(row["redox_residual"]) < 1e-14


def test_identical_habitats_and_the_one_habitat_limit_recover_scalar_roots():
    base = core.reference()
    scalar = core.equilibrium_states(base)
    p = Refuge(base, .3, 0., .001)
    target = next(e for e in scalar if e["kind"] == "mixed")
    mixed = next(e for e in equilibrium_states(p, n_grid=101) if e["stable"])
    assert mixed["y"][:4] == pytest.approx(target["y"][:4], rel=1e-7)
    assert mixed["y"][4:8] == pytest.approx(target["y"][:4], rel=1e-7)
    assert mixed["r"] == pytest.approx(target["r"], abs=1e-10)
    edge = equilibrium_states(Refuge(base, 0., 15., 1.), n_grid=101)
    assert sorted(e["r"] for e in edge) == pytest.approx(sorted(e["r"] for e in scalar), abs=1e-10)
    assert all(np.all(e["y"][4:8] == 0) for e in edge)


def test_fast_exchange_does_not_replace_heterogeneous_response_by_mean_temperature():
    p = Refuge(core.reference(), .51, 8., 1000.)
    row = next(e for e in equilibrium_states(p, n_grid=101) if e["stable"])
    assert row["global_temperature_k"] == pytest.approx(282.336920296, abs=1e-6)
    assert abs(row["global_temperature_k"] - core.switch_temperatures(p.base.biology)[0]) > .5
    assert row["y"][[1, 2]] == pytest.approx(row["y"][[5, 6]], rel=.01)
    assert np.diff(temperatures(row["y"], p))[0] == pytest.approx(8.)


def test_supported_search_interval_is_distinct_from_finding_a_supported_start():
    p = Refuge(replace(core.reference(), enabled=(False, True)), .5, 5., .001)
    assert search_coverage(p, 101)["status"] == "supported_search_interval"
    assert not any(e["stable"] for e in equilibrium_states(p, n_grid=101))
    impossible = replace(p, contrast_k=40.)
    assert search_coverage(impossible, 101)["status"] == "no_supported_ratio_interval"
    assert equilibrium_states(impossible, n_grid=101) == []


def test_product_feedback_solves_local_inventories_and_changes_degenerate_family():
    p = Refuge(replace(core.reference(), activity_feedback="products"), .5, 0., 0.)
    row = next(e for e in equilibrium_states(p, n_grid=101) if e["stable"])
    assert row["global_temperature_k"] == pytest.approx(281.28482672, abs=1e-6)
    assert not row["nonisolated"]
    patch = Refuge(p.base, .51, 8., .001)
    row = next(e for e in equilibrium_states(patch, n_grid=101) if e["stable"])
    assert row["kind"] == "partition_with_sinks"
    assert row["max_scaled_residual"] < 1e-8
    assert row["measured"]


def test_mixed_patch_root_on_climate_vertex_retains_both_one_sided_spectra():
    base = core.reference()
    switch = core.switch_temperatures(base.biology)[0]
    p = Refuge(base, .5, 2 * (282.005 - switch), 0.)
    rows = equilibrium_states(p, n_grid=101)
    candidates = [e for e in rows if e["kind"] == "locally_mixed" and abs(e["r"] - .19445499) < 1e-8]
    assert candidates
    assert all(len(e["eigenvalues"]) == 18 for e in candidates)
    assert all(e["max_scaled_residual"] < 1e-8 for e in candidates)
