from pathlib import Path

import numpy as np
import pytest

from terra_prisca.budyko_sellers.sellers1969 import (AREA, BELT_ALPHA_D, BELT_B, BELT_QS, NB, Scenario,
                                                     model, radiative_equilibrium)


@pytest.fixture(scope="module")
def m():
    return model()


def test_tables_are_internally_consistent():
    # Table 2's Q_s averages to S/4 for S = 2.00 ly/min; Table 1 has b - alpha_d = 2.548 in every belt
    assert np.sum(BELT_QS * AREA) / np.sum(AREA) == pytest.approx(2.00 * 1440 * 365.25 / 4 / 1000, rel=1e-3)
    np.testing.assert_allclose(BELT_B - BELT_ALPHA_D, 2.548, atol=1e-9)


def test_present_state(m):
    p = m.present()
    assert p["ok"]
    assert p["Tbar"] == pytest.approx(14.0, abs=0.1)  # p. 397: "about 14.0C"
    # Fig. 4 circles: polar albedos; Fig. 5 inset: the untreated Arctic when the Antarctic is set to 0.50
    assert p["albedo"][[0, 1, 16, 17]] == pytest.approx([0.65, 0.61, 0.80, 0.84], abs=0.01)
    case3 = m.solve(Scenario(fixed_albedo={16: 0.50, 17: 0.50}))
    assert case3["albedo"][[0, 1]] == pytest.approx([0.61, 0.58], abs=0.015)


def test_energy_is_conserved(m):
    p = m.present()
    assert np.sum(p["Rs"] * AREA) / np.sum(AREA) == pytest.approx(0.0, abs=1e-12)


def test_sellers_march_reproduces_the_solution(m):
    p = m.present()
    dt = p["T"][:-1] - p["T"][1:]
    t, res = m.march(p["T"][0], m.grad_mean(dt))
    np.testing.assert_allclose(t, p["T"], atol=1e-6)
    assert abs(res) < 1e-6


def test_ice_age_threshold(m):
    # p. 398: about 2% less sunlight gives an ice age; beyond it the earth ices over near -100C
    warm = m.solve(Scenario(s=1.96))
    ice = m.solve(Scenario(s=1.955), warm["T"])
    assert warm["Tbar"] > 0 and ice["Tbar"] < -95


def test_curve_i_has_three_equilibria(m):
    sc = Scenario(s=1.94, k_mult=2.0)
    warm = m.solve(sc)
    cold = m.solve(sc, np.full(NB, 250.0))
    ice = m.solve(sc, np.full(NB, 175.0))
    assert warm["ok"] and cold["ok"] and ice["ok"]
    assert warm["Tbar"] - cold["Tbar"] > 8 and ice["Tbar"] < -95
    p = m.present()
    assert p["Tc"][8] - cold["Tc"][8] == pytest.approx(16, abs=1)  # p. 398: equator "about 16C lower"
    # with equal heat capacities the plotted (middle) root is unstable; the other two are stable
    assert m.growth_rates(cold["T"], sc)[0].real > 0.5
    assert m.growth_rates(warm["T"], sc)[0].real < 0 and m.growth_rates(ice["T"], sc)[0].real < 0
    assert m.growth_rates(p["T"])[0].real < 0


def test_table3_heating(m):
    from terra_prisca.budyko_sellers.fidelity_sellers1969 import TABLE3_DT1, experiments

    ex = experiments(m)
    dt1 = ex["table3"][0]["Tc"] - ex["present"]["Tc"]
    assert np.max(np.abs(dt1 - TABLE3_DT1)) < 0.5


def test_rejected_readings_and_null_differ(m):
    p = m.present()
    celsius = model(vt_kelvin=False).present()
    assert np.max(np.abs(celsius["Tc"] - p["Tc"])) > 10
    assert np.max(np.abs(radiative_equilibrium(m)["Tc"] - p["Tc"])) > 50


PDF = Path("local/sources/budyko_sellers/sellers1969.pdf")


@pytest.mark.skipif(not PDF.exists(), reason="Sellers (1969) scan not present")
def test_fidelity_against_scan(m):
    from terra_prisca.budyko_sellers.fidelity_sellers1969 import experiments, null_rows, scan_targets, summarise
    from terra_prisca.budyko_sellers.scan_sellers1969 import load

    scan = load(PDF)
    ex = experiments(m)
    rows = {(r["figure"], r["curve"]): r["rmse"] for r in summarise(scan_targets(scan, ex), "faithful")}
    assert rows[("fig4", "T")] < 1.0 and rows[("fig4", "albedo")] < 0.01
    assert rows[("fig3", "P")] < 6.0 and rows[("fig2", "Rs")] < 1.5
    assert rows[("fig5", "6")] < 0.5 and rows[("fig6", "0.009")] < 1.5 and rows[("fig6", "0.005")] < 1.5
    assert rows[("fig7", "i")] < 1.5 and rows[("fig7", "g")] < 1.0 and rows[("fig7", "h")] < 2.0
    # curve identity where g and h run close to other curves: g's flat crest lies below the circled
    # a (~26.1 C at 0 deg), and h's crest dashes lie above the solid f (~16 C)
    for name, lat, lo, hi in (("g", 0.0, 24.0, 25.5), ("h", 15.0, 22.5, 25.0)):
        d = scan.traces[("fig7", name)][1]
        near = np.abs(d[:, 0] - lat) < 1.5
        assert near.any() and lo < np.median(d[near, 1]) < hi, name
    nulls = {(r["reading"], r["figure"], r["curve"]): r["rmse"] for r in null_rows(scan, ex)}
    # the observed line of Fig. 4 offered as the solution ties with the model: the present-state
    # T score cannot separate the reconstruction from Sellers' calibration target
    assert abs(nulls[("observed T offered as the solution", "fig4", "T")] - rows[("fig4", "T")]) < 0.2
    assert nulls[("no transport", "fig4", "T")] > 20 * rows[("fig4", "T")]
    assert nulls[("no change", "fig5", "6")] > 10 * rows[("fig5", "6")]
    assert nulls[("fixed albedo", "fig6", "0.009")] > 10 * rows[("fig6", "0.009")]
