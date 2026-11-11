import importlib.util
from pathlib import Path

import numpy as np
import pytest

from terra_prisca.haze_world import dormancy_cycle_closure as closure


@pytest.fixture(scope="module")
def analysis():
    path = Path(__file__).parents[1]/"models/haze_world/review/dormancy_cycle_closure_analysis.py"
    spec = importlib.util.spec_from_file_location("cycle_analysis", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_fixed_perturbations_leave_chemistry_other_guild_and_zero_banks_unchanged():
    root, p, _ = closure.mixed_root()
    assert np.max(abs(closure.model.fluxes(root, p)["net_growth_yr"])) < 1e-10
    assert np.count_nonzero(root[p.dormant_indices]) == 0
    for guild in (0, 1):
        for fraction in (-.1, -.001, .001, .1):
            state = closure.perturb(root, p, guild, fraction)
            changeable = p.biomass_indices[:, guild]
            fixed = np.setdiff1d(np.arange(p.state_size), changeable)
            np.testing.assert_array_equal(state[fixed], root[fixed])
            np.testing.assert_allclose(state[changeable], (1+fraction)*root[changeable], rtol=0., atol=0.)
    assert np.count_nonzero(root[p.dormant_indices]) == 0


def test_macro_control_rejects_negative_stocks_and_a_missing_guild():
    root, p, _ = closure.mixed_root()
    negative = root.copy()
    negative[p.dormant_indices[0, 0]] = -1e-300
    with pytest.raises(ValueError, match="nonnegative"):
        closure.macro_integrate(negative, p, 1.)
    missing = root.copy()
    missing[p.biomass_indices[:, 0]] = 0.
    with pytest.raises(ArithmeticError, match="rare-population"):
        closure.macro_integrate(missing, p, .01)


def test_mode_fit_recovers_damping_separately_from_persistent_recurrence(analysis):
    time = np.arange(0., 30001., 10.)
    period, damping = 119.569797, 4853.91
    wave = np.cos(2*np.pi*time/period)
    decaying = analysis.peak_mode(time, 281.+.01*np.exp(-time/damping)*wave, 281.)
    persistent = analysis.peak_mode(time, 281.+.01*wave, 281.)
    assert decaying["period_yr"] == pytest.approx(period, rel=2e-5)
    assert decaying["damping_time_yr"] == pytest.approx(damping, rel=2e-3)
    assert decaying["log_amplitude_fit_r_squared"] > .99999
    assert abs(persistent["log_amplitude_slope_yr"]) < 1e-8
    assert persistent["last_peak_amplitude_k"] == pytest.approx(persistent["first_peak_amplitude_k"], rel=.002)
