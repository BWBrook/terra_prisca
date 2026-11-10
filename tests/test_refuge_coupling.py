from dataclasses import replace

import numpy as np
import pytest

from terra_prisca.haze_world import population_coupling as single
from terra_prisca.haze_world import refuge_coupling as refuge


@pytest.mark.parametrize("warm_fraction", (0., .1, .5, .9, 1.))
def test_identical_patch_rhs_matches_single_habitat(warm_fraction):
    p = refuge.Refuge(warm_fraction=warm_fraction, dispersal_yr=1.)
    y = np.array([30., .0003, .0008, .001, .195])
    together = refuge.embed_single(y, p)
    actual, expected = refuge.rhs(together, p), single.rhs(y, p.base)
    for j, w in enumerate(p.weights):
        assert actual[4*j:4*j+4] == pytest.approx(expected[:4] if w > 0 else np.zeros(4))
    assert actual[8] == pytest.approx(expected[4], rel=2e-15)


def test_area_mean_temperature_and_dispersal_are_conservative():
    p = refuge.Refuge(warm_fraction=.3, contrast_k=6., dispersal_yr=.2)
    y = np.array([28., .0002, .001, .001, 35., .0009, .0001, .003, .195])
    f = refuge.fluxes(y, p)
    assert np.dot(p.weights, f["temperatures_k"]) == pytest.approx(f["global_temperature_k"], abs=1e-12)
    assert p.weights @ f["exchange_gdw_l_yr"] == pytest.approx([0., 0.], abs=1e-20)
    no_exchange = refuge.rhs(y, replace(p, dispersal_yr=0.))
    difference = refuge.rhs(y, p) - no_exchange
    assert difference[refuge.BIOMASS_INDICES] == pytest.approx(f["exchange_gdw_l_yr"], abs=1e-18)
    assert difference[[0, 3, 4, 7, 8]] == pytest.approx(np.zeros(5), abs=1e-18)
    assert abs(refuge.redox_residual(y, p)) < 1e-14


@pytest.mark.parametrize("activity", ("fixed", "products"))
def test_local_product_budget_and_abiotic_methane_are_counted_once(activity):
    p = refuge.Refuge(base=replace(single.reference(), activity_feedback=activity,
                                 recycling_variant="cold_limited"),
                      warm_fraction=.4, contrast_k=5., dispersal_yr=.001)
    y = np.array([25., .0004, .0001, .0005, 35., .0001, .0007, .002, .195])
    f = refuge.fluxes(y, p)
    expected = single.inventory_to_ratio(p.base) * sum(
        w * local["methane_local_mol_l_yr"] for w, local in zip(p.weights, f["local"])) + f["abiotic_ratio_yr"]
    assert f["methane_source_ratio_yr"] == pytest.approx(expected)
    assert abs(refuge.redox_residual(y, p)) < 1e-14
    assert f["local"][0]["temperature_k"] != f["local"][1]["temperature_k"]


def test_one_habitat_ignores_inactive_patch_temperature_and_stocks():
    p = refuge.Refuge(warm_fraction=0., contrast_k=100., dispersal_yr=12.)
    y = refuge.embed_single([30., .0003, .0008, .001, .195], p)
    assert refuge.temperature_flags(y, p) == ["measured", "inactive"]
    assert len(refuge.active_indices(p)) == 5
    assert refuge.jacobian(y, p).shape == (5, 5)
    assert abs(refuge.redox_residual(y, p)) < 1e-14


def test_supported_temperature_flags_and_numerical_extension_are_explicit():
    p = refuge.Refuge(warm_fraction=.5, contrast_k=20.)
    y = refuge.embed_single([30., .001, .001, .001, .195], p)
    assert refuge.temperature_flags(y, p)[0] == "unsupported"
    with pytest.raises(ValueError):
        refuge.rhs(y, p)
    assert np.all(np.isfinite(refuge.rhs(y, p, trial_extension=True)))


def test_homogeneous_biomass_does_not_replace_two_temperatures_by_the_mean():
    p = refuge.Refuge(contrast_k=6., dispersal_yr=1000.)
    y = refuge.embed_single([30., .0003, .0008, .001, .195], p)
    local = refuge.fluxes(y, p)
    averaged_growth = sum(w * f["net_growth_yr"] for w, f in zip(p.weights, local["local"]))
    mean_growth = single.fluxes(refuge.local_state(y, 0), p.base)["net_growth_yr"]
    assert np.max(abs(averaged_growth - mean_growth)) > .01
    assert local["exchange_gdw_l_yr"] == pytest.approx(np.zeros((2, 2)))


def test_invalid_geometry_and_exchange_are_rejected():
    with pytest.raises(ValueError):
        refuge.Refuge(warm_fraction=1.1)
    with pytest.raises(ValueError):
        refuge.Refuge(contrast_k=-1.)
