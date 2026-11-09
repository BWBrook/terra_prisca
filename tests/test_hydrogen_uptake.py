import numpy as np
import pytest

from terra_prisca.haze_world.hydrogen_uptake import (
    ACETOGEN, MSB, MSP, competition_bounds, competitiveness, parameters, rate_bounds, uptake,
)


def test_shifted_half_saturation_and_cessation():
    p = parameters(30, ACETOGEN)
    assert uptake(200 + p.km_pa, p, 200, basis="culture") == pytest.approx(p.vmax_nmol_h / 2)
    assert np.array_equal(uptake([0, 100, 200], p, 200, basis="culture"), [0, 0, 0])


def test_source_culture_to_specific_mass_conversion():
    p = parameters(30, ACETOGEN)
    assert p.mass_mg == pytest.approx(3.6)
    assert uptake(520, p, 0, basis="culture") == pytest.approx(380)
    assert uptake(520, p, 0, basis="dry_mass") == pytest.approx(380 / 3.6)
    with pytest.raises(ValueError):
        parameters(12, ACETOGEN)


def test_competition_does_not_score_both_inactive_as_a_tie():
    assert np.isnan(competitiveness(0, 0))
    assert competitiveness(1, 0) == 1
    assert competitiveness(0, 1) == -1


def test_normalization_changes_central_parameter_prediction():
    a, b = parameters(30, ACETOGEN), parameters(30, MSB)
    culture = competition_bounds(500, a, b, basis="culture")
    specific = competition_bounds(500, a, b, basis="dry_mass")
    assert culture[1] < 0 and specific[0] > 0
    for ta in (0, 100, 200):
        for tb in (0, 1, 2):
            value = competitiveness(uptake(500, a, ta, basis="dry_mass"), uptake(500, b, tb, basis="dry_mass"))
            assert specific[0] <= value <= specific[1]


def test_missing_cold_msp_threshold_remains_unbounded():
    p = parameters(4, MSP)
    low, high = rate_bounds(100, p, basis="culture")
    assert low == 0 and high > 0
