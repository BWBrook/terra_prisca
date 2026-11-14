from pathlib import Path

import numpy as np
import pytest

from terra_prisca.budyko_sellers.budyko1969 import (
    CAL_MIN_TO_KCAL_MONTH,
    LAT,
    hemispheric_mean,
    model,
)
from terra_prisca.budyko_sellers.digitise import Axis, Frame, column_median


def test_mean_insolation_is_quarter_solar_constant():
    m = model()
    assert m.qp == pytest.approx(1.92 * CAL_MIN_TO_KCAL_MONTH / 4, rel=1e-4)


def test_fixed_albedo_sensitivity_text():
    # p. 613: 1 % less radiation with albedo 0.33 cools the Earth by 1.5 deg
    assert model().fixed_albedo_sensitivity(0.33) == pytest.approx(1.5, abs=0.07)


def test_transport_sums_to_zero_with_insolation_weighted_albedo():
    # Eq. (3) with A summing to zero: the area mean of eq. (4) is T_p of eq. (5)
    m = model(planetary_albedo="insolation")
    assert hemispheric_mean(m.profile(LAT)) == pytest.approx(m.tp_now, abs=1e-6)


def test_faithful_present_planetary_temperature():
    # Area-mean albedo of the stated profile gives the T_p printed in Fig. 5 (14.9 deg C)
    m = model()
    assert m.alpha_p_now == pytest.approx(0.3413, abs=2e-4)
    assert m.tp_now == pytest.approx(15.09, abs=0.02)


def test_eq6_matches_eq5_when_albedo_change_is_exact():
    # With a stepped present albedo and insolation weighting, eq. (6) is eq. (5) recomputed
    m = model(present_albedo="step", planetary_albedo="insolation")
    for eps, edge in ((-0.01, 60.0), (-0.015, 55.0), (0.0, 65.0)):
        alpha_p = hemispheric_mean(m.q * m.albedo(LAT, edge)) / m.qp
        assert m.tp_now + m.delta_tp(eps, edge) == pytest.approx(m.planetary_temperature(alpha_p, eps), abs=1e-3)


@pytest.mark.parametrize("eps", [-0.004, -0.01, -0.015])
def test_ice_edge_holds_boundary_temperature(eps):
    m = model()
    edge = m.stable_edge(eps)
    t = m.zonal_temperature(m.insolation(edge), m.p.albedo_edge, m.tp_now + m.delta_tp(eps, edge), eps)
    assert t == pytest.approx(m.t_edge, abs=1e-3)


def test_critical_point_and_runaway():
    m = model()
    c = m.critical()
    assert c["eps"] == pytest.approx(-0.0167, abs=2e-4)
    assert c["edge"] == pytest.approx(51.5, abs=0.3)
    assert m.stable_edge(c["eps"] - 1e-4) == 0.0
    assert m.eps_for_edge(72.0) == pytest.approx(0.0, abs=1e-9)


def test_rejected_readings_differ():
    assert model(s_area_factor=0.5).critical()["eps"] < -0.04
    assert model(ice_albedo="translate").critical()["eps"] > -0.01


def test_axis_and_column_median_on_synthetic_stroke():
    ax = Axis.from_ticks([(100, 0.0), (200, 10.0), (300, 20.0)])
    assert ax.value(250) == pytest.approx(15.0) and ax.residual < 1e-9
    fr = Frame(ax, Axis.from_ticks([(500, 0.0), (400, 10.0)]), (0, 600, 0, 600), (0, 0))
    xs = np.arange(120, 280)
    pix = np.array([(x, y) for x in xs for y in (449, 450, 451)], dtype=float)
    out = column_median(pix, fr)
    np.testing.assert_allclose(out[:, 1], 5.0)


PDF = Path("local/sources/budyko_sellers/budyko1969.pdf")


@pytest.mark.skipif(not PDF.exists(), reason="Budyko (1969) scan not present")
def test_fidelity_against_scan():
    from terra_prisca.budyko_sellers.fidelity_budyko1969 import model_curves, score
    from terra_prisca.budyko_sellers.scan_budyko1969 import load

    scan = load(PDF)
    rows = {(r["figure"], r["curve"]): r for r in score(scan, model_curves(model()), "faithful")}
    for key in [("fig4", "T0"), ("fig4", "T1.0"), ("fig4", "T1.5"), ("fig6", "T0"), ("fig6", "Tq"), ("fig5", "Tp")]:
        assert rows[key]["rmse"] < 1.0, key
    nulls = {(r["figure"], r["curve"]): r for r in score(scan, model_curves(model(), "no feedback"), "null")}
    for key in [("fig4", "T1.0"), ("fig4", "T1.5"), ("fig5", "Tp"), ("fig5", "phi0")]:
        assert nulls[key]["rmse"] > 2 * rows[key]["rmse"], key
