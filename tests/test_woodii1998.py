import numpy as np
import pytest

from terra_prisca.haze_world.woodii1998 import (
    BIOMASS_ACETATE_EQUIVALENT, MAINTENANCE_ACETATE, MAINTENANCE_H2, MU_MAX,
    Y_H2_REPORTED, acetate_production, fidelity_rows, fit_rounded_means,
    hydrogen_yield_from_assimilation, inferred_reference_uptake, observations,
    observed_yield,
)


def test_assimilation_reconciles_hydrogen_and_acetate_mass_balances():
    growth = np.array([0, 0.007, 0.012, 0.020, MU_MAX])
    total_h2 = 4 * (acetate_production(growth) + BIOMASS_ACETATE_EQUIVALENT * growth)
    converted_h2 = MAINTENANCE_H2 + growth / hydrogen_yield_from_assimilation()
    assert total_h2 == pytest.approx(converted_h2)
    assert hydrogen_yield_from_assimilation() == pytest.approx(1.6614593222972156)
    assert hydrogen_yield_from_assimilation() != pytest.approx(7.7 / 4)
    assert total_h2[0] == pytest.approx(0.0016)


def test_inferred_rate_uses_reported_yield_and_returns_source_growth():
    reference = inferred_reference_uptake()
    assert reference == pytest.approx(0.01571764705882353)
    assert Y_H2_REPORTED * (reference - MAINTENANCE_H2) == pytest.approx(MU_MAX)
    exact_assimilation_rate = MU_MAX / hydrogen_yield_from_assimilation() + MAINTENANCE_H2
    assert exact_assimilation_rate == pytest.approx(0.016045132467532468)
    assert reference != pytest.approx(exact_assimilation_rate)


def test_fit_to_rounded_means_reconstructs_source_with_finite_residuals():
    fit = fit_rounded_means()
    assert fit.true_yield_acetate == pytest.approx(7.622, abs=0.001)
    assert fit.maintenance_acetate == pytest.approx(0.000355, abs=1e-6)
    rows = observations()
    growth = np.array([r.growth_h for r in rows])
    residual = acetate_production(growth, true_yield=fit.true_yield_acetate,
                                  maintenance=fit.maintenance_acetate)
    residual -= np.array([r.q_acetate for r in rows])
    assert abs(np.sum(residual)) < 1e-17
    assert abs(np.dot(growth, residual)) < 1e-18
    source_residual = np.array([r["table2_q_residual_mol_gdw_h"] for r in fidelity_rows()])
    assert 0 < fit.production_rmse < np.sqrt(np.mean(source_residual ** 2))
    assert fit.maintenance_acetate < MAINTENANCE_ACETATE
    assert max(abs(r["table2_yield_residual_gdw_mol"]) for r in fidelity_rows()) < 0.2


def test_observed_yield_keeps_maintenance_distinct_from_true_yield():
    assert acetate_production(0) == MAINTENANCE_ACETATE
    assert observed_yield(0) == 0
    assert observed_yield(0.007) < observed_yield(0.020) < 7.7
    assert observed_yield(1e6) == pytest.approx(7.7, rel=1e-8)
    assert np.isnan(observed_yield(0, maintenance=0))
    with pytest.raises(ValueError):
        acetate_production(-0.01)
    with pytest.raises(ValueError):
        acetate_production(0.01, true_yield=0)
    with pytest.raises(ValueError):
        observed_yield(np.nan)
