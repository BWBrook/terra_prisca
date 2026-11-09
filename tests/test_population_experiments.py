import numpy as np
import pytest
from dataclasses import replace

from terra_prisca.haze_world.population_coupling import equilibrium_states, jacobian, reference, supply_h2
from terra_prisca.haze_world.population_experiments import at_potential, configurations


def test_supply_sweep_keeps_habitat_and_outlet_fixed():
    base = reference(.3)
    for potential in (.12, .3, .6):
        p = at_potential(base, potential)
        assert p.habitat_l_cm2 == base.habitat_l_cm2
        assert p.biology.exchange_mol_l_h_pa == base.biology.exchange_mol_l_h_pa
        assert supply_h2(p) == pytest.approx(1e-6 * potential / .3)
        assert p.climate.t_zero_k == 283.


def test_design_separates_consistent_methanogen_controls():
    design = list(configurations(reference(.3)))
    coupled = [(metadata, p) for metadata, p in design if metadata["group"] == "coupled"]
    controls = [(metadata, p) for metadata, p in design if metadata["group"] == "methanogen_only"]
    assert len(coupled) == 800 and len(controls) == 25
    assert len(design) == 840
    assert all(p.enabled == (True, True) for _, p in coupled)
    assert all(p.enabled == (False, True) for _, p in controls)
    assert len({p.habitat_l_cm2 for _, p in design}) == 1
    assert len({p.biology.exchange_mol_l_h_pa for _, p in coupled + controls}) == 1
    assert {metadata["recycling"] for metadata, _ in coupled} == {"constant", "cold_limited"}
    assert np.allclose([p.biology.assimilation_m for _, p in design], .0824)


@pytest.mark.parametrize("variant", ("constant", "cold_limited"))
def test_dense_lag_rescaling_matches_independent_equilibrium_search(variant):
    base = replace(reference(.3), recycling_variant=variant)
    state = next(e for e in equilibrium_states(base, n_grid=201) if e["kind"] == "mixed")
    for lag in (.01, 10000.):
        p = replace(base, acetate_lifetime_yr=lag)
        independent = next(e for e in equilibrium_states(p, n_grid=201) if e["kind"] == "mixed")
        scaled = state["y"].copy()
        scaled[3] *= lag / base.acetate_lifetime_yr
        np.testing.assert_allclose(scaled, independent["y"], rtol=1e-10, atol=1e-12)
        maximum = max(np.linalg.eigvals(jacobian(scaled, p)).real)
        assert maximum == pytest.approx(independent["max_real_yr"], rel=1e-7, abs=1e-10)
