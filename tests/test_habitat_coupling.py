from dataclasses import replace

import numpy as np
import pytest

from terra_prisca.haze_world import habitat_coupling as model
from terra_prisca.haze_world import population_coupling as core
from terra_prisca.haze_world import refuge_coupling as legacy


def reference(activity="fixed", dispersal=.001):
    return model.Habitats(replace(core.reference(), activity_feedback=activity),
                          (model.Patch("bulk", .96), model.Patch("warm", .02, "buffered", 286.),
                           model.Patch("cold", .02, "buffered", 278.)), dispersal)


@pytest.mark.parametrize("activity", ("fixed", "products"))
def test_two_tracking_patches_reproduce_legacy_rhs_exactly(activity):
    base = replace(core.reference(), activity_feedback=activity)
    y = np.array([28., .0002, .001, .001, 35., .0009, .0001, .003, .195])
    for warm in (.1, .37, .9):
        for dispersal in (0., 1e-6, .1, 1.):
            old = legacy.Refuge(base, warm, 2., dispersal)
            p = model.Habitats(base, (model.Patch("cold", 1-warm, value=-warm*2),
                                     model.Patch("warm", warm, value=(1-warm)*2)), dispersal)
            assert np.array_equal(model.rhs(y, p), legacy.rhs(y, old))
            assert np.array_equal(model.temperatures(y, p), legacy.temperatures(y, old))
            assert model.inventory(y, p) == pytest.approx(legacy.inventory(y, old), rel=2e-15)


@pytest.mark.parametrize("weights", ((1.,), (.2, .3, .5), (1., 0., 0.)))
def test_identical_or_zero_area_habitats_recover_single_model(weights):
    patches = tuple(model.Patch(str(j), w, "tracking" if w else "buffered", 0. if w else 1000.)
                    for j, w in enumerate(weights))
    p = model.Habitats(patches=patches, dispersal_yr=12.)
    y = np.array([30., .0003, .0008, .001, .195])
    together = model.embed_single(y, p)
    actual, expected = model.rhs(together, p), core.rhs(y, p.base)
    for j, weight in enumerate(weights):
        assert actual[4*j:4*j+4] == pytest.approx(expected[:4] if weight else np.zeros(4), rel=2e-15)
    assert actual[-1] == pytest.approx(expected[-1], rel=2e-15)
    assert abs(model.redox_residual(together, p)) < 1e-14


@pytest.mark.parametrize("activity", ("fixed", "products"))
def test_three_patch_exchange_and_redox_are_conservative(activity):
    p = reference(activity, .2)
    y = np.array([28., .0002, .001, .001, 35., .0009, .0001, .003,
                  24., .0006, .0004, .0008, .195])
    f = model.fluxes(y, p)
    assert p.weights @ f["exchange_gdw_l_yr"] == pytest.approx([0., 0.], abs=1e-20)
    difference = model.rhs(y, p)-model.rhs(y, replace(p, dispersal_yr=0.))
    assert difference[p.biomass_indices] == pytest.approx(f["exchange_gdw_l_yr"], abs=1e-18)
    assert difference[[0, 3, 4, 7, 8, 11, 12]] == pytest.approx(np.zeros(7), abs=1e-18)
    assert abs(model.redox_residual(y, p)) < 1e-14
    expected = core.inventory_to_ratio(p.base) * sum(w*local["methane_local_mol_l_yr"]
                    for w, local in zip(p.weights, f["local"])) + f["abiotic_ratio_yr"]
    assert f["methane_source_ratio_yr"] == expected
    assert f["mean_habitat_temperature_k"] == pytest.approx(p.weights @ f["temperatures_k"])


def test_buffered_temperatures_have_no_radiative_derivative_in_rhs_or_jacobian():
    p = reference()
    y = model.embed_single([30., .0003, .0008, .001, .195], p)
    changed = y.copy(); changed[-1] = .20
    assert np.array_equal(model.temperatures(y, p)[1:], model.temperatures(changed, p)[1:])
    assert model.temperatures(y, p)[0] != model.temperatures(changed, p)[0]
    assert np.array_equal(model.rhs(y, p)[4:12], model.rhs(changed, p)[4:12])
    matrix = model.jacobian(y, p)
    assert np.array_equal(matrix[4:12, -1], np.zeros(8))
    assert max(abs(matrix[:4, -1])) > 0


def test_buffered_product_chemistry_still_responds_to_shared_methane():
    p = reference("products")
    y = model.embed_single([30., .0003, .0008, .001, .195], p)
    changed = y.copy(); changed[-1] = .20
    assert np.array_equal(model.temperatures(y, p)[1:], model.temperatures(changed, p)[1:])
    assert np.max(abs(model.rhs(y, p)[4:12]-model.rhs(changed, p)[4:12])) > 0
    assert max(abs(model.jacobian(y, p)[4:12, -1])) > 0


def test_supported_ratio_intervals_follow_tracking_bounds_and_ignore_inactive_rules():
    p = reference()
    assert model.supported_ratio_intervals(p) == [[0., np.inf]]
    tracking = model.Habitats(p.base, (model.Patch("cold", .5, value=-10.),
                                      model.Patch("warm", .5, value=10.)))
    intervals = model.supported_ratio_intervals(tracking)
    contains = lambda r: any(a <= r <= b for a, b in intervals)
    assert contains(0.) and contains(.1) and contains(.18)
    assert not contains(.166) and not contains(.195)
    invalid = replace(p, patches=(model.Patch("bulk", 1., "buffered", 270.),))
    assert model.supported_ratio_intervals(invalid) == []
    with pytest.raises(ValueError):
        model.rhs(model.embed_single([30., .001, .001, .001, .195], invalid), invalid)
    inactive = replace(p, patches=(model.Patch("bulk", 1.), model.Patch("unused", 0., "buffered", 1000.)))
    assert model.supported_ratio_intervals(inactive) == [[0., np.inf]]
    assert model.temperature_flags(model.embed_single([30., .001, .001, .001, .195], inactive), inactive)[1] == "inactive"
    assert model.jacobian(model.embed_single([30., .001, .001, .001, .195], inactive), inactive).shape == (5, 5)


def test_invalid_patch_geometries_are_rejected():
    for kwargs in (dict(name="", weight=1.), dict(name="x", weight=-1.),
                   dict(name="x", weight=1., rule="other"), dict(name="x", weight=1., value=np.inf)):
        with pytest.raises(ValueError):
            model.Patch(**kwargs)
    for patches in ((), (model.Patch("x", .5),), (model.Patch("x", .5), model.Patch("x", .5))):
        with pytest.raises(ValueError):
            model.Habitats(patches=patches)
    with pytest.raises(ValueError):
        model.Habitats(dispersal_yr=-1.)


def test_interval_membership_matches_direct_flags_across_nonmonotone_climate():
    for offsets in ((-12., 6.), (-5., 4.)):
        p = model.Habitats(patches=(model.Patch("a", .4, value=offsets[0]),
                                    model.Patch("b", .6, value=offsets[1])))
        intervals = model.supported_ratio_intervals(p)
        for ratio in np.linspace(0., .3, 301):
            y = model.embed_single([30., .001, .001, .001, ratio], p)
            actual = "unsupported" not in model.temperature_flags(y, p)
            assert actual == any(a <= ratio <= b for a, b in intervals)
