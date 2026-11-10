from dataclasses import replace

import numpy as np
import pytest
from scipy.linalg import expm

from terra_prisca.haze_world import habitat_coupling as h
from terra_prisca.haze_world import branching as b


def test_no_births_integrates_time_dependent_death_and_retains_tiny_probabilities():
    times = np.array([0., 5., 10.])
    logu = b.backward_survival(times, np.zeros((3, 1)), np.array([[2.], [4.], [1.]]), np.zeros((1, 1)))
    assert logu[0] == pytest.approx(-27.5, abs=2e-7)
    tiny = b.backward_survival([0., 1000.], [[0.], [0.]], [[1.], [1.]], [[0.]])
    assert tiny[0] == pytest.approx(-1000., abs=1e-7)
    result = b.lineages([1000.], tiny)
    assert result["survival_probability"] == pytest.approx(1 - np.exp(-1.), abs=1e-7)


def test_critical_birth_death_matches_kendall_limit():
    value = b.backward_survival([0., 500.], [[8.77], [8.77]], [[8.77], [8.77]], [[0.]])
    assert np.exp(value[0]) == pytest.approx(1 / (1 + 8.77 * 500), rel=2e-8)
    changing = b.backward_survival([0., 2., 5.], [[1.], [3.], [2.]], [[1.], [3.], [2.]], [[0.]])
    assert np.exp(changing[0]) == pytest.approx(1 / (1 + 4 + 7.5), rel=2e-8)


def test_multitype_no_births_matches_forward_count_matrix_with_correct_orientation():
    migration = np.array([[0., .03], [2., 0.]])
    death = np.array([.2, 1.])
    generator = migration - np.diag(migration.sum(axis=1) + death)
    expected = expm(generator * 8.) @ np.ones(2)
    actual = b.backward_survival([0., 8.], np.zeros((2, 2)), np.tile(death, (2, 1)), migration)
    assert np.exp(actual) == pytest.approx(expected, rel=2e-8)


def test_migration_conserves_counts_and_has_area_weighted_stationary_distribution():
    p = h.Habitats(patches=(h.Patch("bulk", .98), h.Patch("warm", .02, "buffered", 286.)), dispersal_yr=.4)
    migration = b.migration_matrix(p)
    assert migration[0, 1] == pytest.approx(.008)
    assert migration[1, 0] == pytest.approx(.392)
    generator = migration.T - np.diag(migration.sum(axis=1))
    assert generator @ p.weights == pytest.approx([0., 0.], abs=1e-16)
    assert generator.sum(axis=0) == pytest.approx([0., 0.], abs=1e-16)
    logu = b.backward_survival([0., 3.], np.ones((2, 2)), np.ones((2, 2)), migration)
    assert np.exp(logu) == pytest.approx([.25, .25], rel=2e-8)


def test_rates_match_metabolic_net_growth_with_underflowed_physical_biomass():
    p = h.Habitats(patches=(h.Patch("bulk", .98), h.Patch("warm", .02, "buffered", 286.)))
    y = np.array([30., 0., 0., .001, 15., 0., 0., .002, .195])
    for guild in (0, 1):
        active, birth, death = b.per_cell_rates(y, p, guild)
        assert list(active) == [0, 1]
        assert np.all(birth >= 0) and np.all(death >= 0)
        net = [b.core.fluxes_at_temperature(h.local_state(y, j), p.base, h.temperatures(y, p)[j])["net_growth_yr"][guild] for j in active]
        assert birth - death == pytest.approx(net)
    with pytest.raises(ValueError, match="enabled"):
        b.per_cell_rates(y, replace(p, base=replace(p.base, enabled=(False, True))), 0)


def test_fixed_counts_and_poisson_counts_are_distinct():
    assert b.fixed_count_probability([2], np.log([.5])) == pytest.approx(.75)
    assert b.lineages(np.log([2]), np.log([.5]))["survival_probability"] == pytest.approx(1 - np.exp(-1))
    assert b.fixed_count_probability([0, 1], [-np.inf, 0.]) == 1.
    assert b.fixed_count_probability([0, 0], [0., 0.]) == 0.
    assert b.fixed_count_probability([10**12], [-100.]) == pytest.approx(10**12 * np.exp(-100), rel=1e-12)
    with pytest.raises(ValueError, match="integers"):
        b.fixed_count_probability([.5], [-1.])


def test_classification_scans_count_scale_and_handles_exact_absence():
    assert b.lineages([np.log(1e-9)], [0.])["classification"] == "robust_loss"
    assert b.lineages([np.log(1e6)], [0.])["classification"] == "robust_persistence"
    result = b.lineages([0.], [0.])
    assert result["classification"] == "contingent"
    assert result["scale_for_half_survival"] == pytest.approx(np.log(2))
    absent = b.lineages([-np.inf], [-1.])
    assert absent["survival_probability"] == 0
    assert absent["scale_for_half_survival"] == np.inf


def test_invalid_event_rates_and_probability_inputs_fail_visibly():
    with pytest.raises(ValueError, match="nonnegative"):
        b.backward_survival([0, 1], [[-1], [0]], [[0], [0]], [[0]])
    with pytest.raises(ValueError, match="zero diagonal"):
        b.backward_survival([0, 1], [[0], [0]], [[0], [0]], [[1]])
    with pytest.raises(ValueError, match="strictly increasing"):
        b.backward_survival([1, 0], [[0], [0]], [[0], [0]], [[0]])
    with pytest.raises(ValueError, match="Invalid"):
        b.lineages([0.], [.01])
