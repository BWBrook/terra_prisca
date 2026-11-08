import numpy as np
import pytest

from terra_prisca.daisyworld.wl1983 import (
    EXPERIMENTS,
    Params,
    growth_rate,
    hysteresis_sweep,
    invasion_rates,
    lifeless_temperature,
    state,
    steady_state,
)

STEP = 0.002


@pytest.fixture(scope="module")
def sweeps():
    return {k: hysteresis_sweep(0.6, 1.7, STEP, p) for k, p in EXPERIMENTS.items()}


def test_coexistence_temperatures_eq14(sweeps):
    up, _ = sweeps["fig1d_both"]
    both = (up["a_w"] > 0) & (up["a_b"] > 0)
    assert both.sum() > 100
    q = Params().q_prime
    np.testing.assert_allclose(up["t_b"][both], 22.5 + 0.5 * q * 0.5, atol=1e-6)
    np.testing.assert_allclose(up["t_w"][both], 22.5 - 0.5 * q * 0.5, atol=1e-6)


def test_steady_state_condition_eq10(sweeps):
    p = Params()
    for name in ("fig1b_black", "fig1c_white", "fig1d_both"):
        up, _ = sweeps[name]
        for i in np.flatnonzero(up["a_w"] + up["a_b"] > 0):
            x = 1 - up["a_w"][i] - up["a_b"][i]
            for a, t in ((up["a_w"][i], up["t_w"][i]), (up["a_b"][i], up["t_b"][i])):
                if a > 0:
                    assert x * growth_rate(t, p) == pytest.approx(p.death_rate, abs=1e-7)


def test_neutral_daisies_occupy_analytic_window(sweeps):
    # Neutral daisies leave the albedo unchanged, so they live exactly where
    # beta(T_lifeless) > gamma: 22.5 +/- sqrt((1 - 0.3)/0.003265) deg C.
    p = EXPERIMENTS["fig1a_neutral"]
    half = np.sqrt((1 - p.death_rate) / p.growth_curvature)
    lums = np.linspace(0.6, 1.7, 110001)
    inside = np.abs(lifeless_temperature(lums, p) - p.t_opt) < half
    lo, hi = lums[inside][0], lums[inside][-1]
    up, _ = sweeps["fig1a_neutral"]
    alive = up["lum"][up["a_b"] > 0]
    assert alive.min() == pytest.approx(lo, abs=STEP)
    assert alive.max() == pytest.approx(hi, abs=STEP)
    assert (lo, hi) == pytest.approx((0.770, 1.144), abs=1e-3)


def test_temperature_falls_as_sun_brightens_with_both_species(sweeps):
    up, _ = sweeps["fig1d_both"]
    both = (up["a_w"] > 0) & (up["a_b"] > 0)
    assert np.all(np.diff(up["t_e"][both]) < 0)


def test_lifeless_branches_match_bare_planet(sweeps):
    up, down = sweeps["fig1c_white"]
    dead = up["a_w"] == 0
    np.testing.assert_allclose(up["t_e"][dead], lifeless_temperature(up["lum"][dead], Params()), atol=1e-9)


def test_cloud_variant_keeps_black_warmer_and_excludes_white(sweeps):
    up, _ = sweeps["fig2_cloud"]
    alive = up["a_b"] > 0
    assert np.all(up["a_w"] == 0)
    assert np.all(up["t_b"][alive] > up["t_w"][alive])
    s = state(0.0, 0.5, 1.0, EXPERIMENTS["fig2_cloud"])
    assert s["albedo"] == pytest.approx(0.5 * 0.5 + 0.5 * 0.8)


@pytest.mark.parametrize(
    "name,direction,expected",
    [
        ("fig1b_black", "up", (0.713, 1.069)),
        ("fig1c_white", "up", (0.827, 1.561)),
        ("fig1d_both", "up", (0.713, 1.561)),
        ("fig2_cloud", "up", (0.719, 1.493)),
        ("fig1c_white", "down", (0.827, 1.225)),
    ],
)
def test_threshold_regression(sweeps, name, direction, expected):
    up, down = sweeps[name]
    r = up if direction == "up" else down
    alive = r["lum"][r["a_w"] + r["a_b"] > 0]
    assert (alive.min(), alive.max()) == pytest.approx(expected, abs=2 * STEP)


def test_no_returned_state_is_open_to_invasion(sweeps):
    for name, (up, down) in sweeps.items():
        p = EXPERIMENTS[name]
        present = np.array([p.white, p.black])
        for r in (up, down):
            for i in range(len(r["lum"])):
                a = np.array([r["a_w"][i], r["a_b"][i]])
                open_to = present & (a == 0) & (invasion_rates(a, r["lum"][i], p) > 1e-9)
                assert not open_to.any(), (name, r["lum"][i], a)


def test_black_recovers_on_downsweep_at_1_224(sweeps):
    # Review 2026-11-08: black was lost here while white re-established, although
    # it could invade the returned environment (rate +0.101).
    _, down = sweeps["fig1d_both"]
    i = np.argmin(np.abs(down["lum"] - 1.224))
    assert (down["a_w"][i], down["a_b"][i]) == pytest.approx((0.59266, 0.08068), abs=1e-4)


def test_steady_state_converges_from_seed():
    a, ok = steady_state(np.array([0.01, 0.01]), 1.0, Params())
    assert ok and np.all(a > 0)
