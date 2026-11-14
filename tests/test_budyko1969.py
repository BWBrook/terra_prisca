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


def test_faithful_transport_sums_to_zero():
    # p. 614: eqs (4)-(5) follow from A = 0 over the Earth, so the area mean of eq. (4) is T_p of eq. (5)
    m = model()
    assert hemispheric_mean(m.profile(LAT)) == pytest.approx(m.tp_now, abs=1e-6)
    assert hemispheric_mean(model(planetary_albedo="area").profile(LAT)) - model(planetary_albedo="area").tp_now > 0.5


def test_faithful_present_planetary_temperature():
    # Insolation-weighted albedo with a 30-day month gives the T_p printed in Fig. 5 (14.9 deg C)
    m = model()
    assert m.alpha_p_now == pytest.approx(0.3319, abs=2e-4)
    assert m.tp_now == pytest.approx(15.03, abs=0.02)
    assert model(month_days=365.25 / 12).tp_now > 17


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
    # the public profile uses the boundary albedo 0.50 at the edge and 0.62 just poleward
    assert m.profile([edge], eps)[0] == pytest.approx(m.t_edge, abs=0.01)
    assert m.albedo([edge, edge + 0.01], edge) == pytest.approx([0.50, 0.62])


def test_critical_point_and_runaway():
    m = model()
    c = m.critical()
    assert c["eps"] == pytest.approx(-0.0165, abs=2e-4)
    assert c["edge"] == pytest.approx(51.5, abs=0.3)
    assert m.stable_edge(c["eps"] - 1e-4) == 0.0
    assert m.eps_for_edge(72.0) == pytest.approx(0.0, abs=1e-9)


def test_rejected_readings_differ():
    assert model(s_area_factor=0.5).critical()["eps"] < -0.04
    assert model(ice_albedo="translate").critical()["eps"] > -0.01
    # ice threshold from the present profile's own T0 at 72 deg (albedo 0.524) instead of the boundary albedo 0.50
    assert model(t_edge=float(model().profile(72.0))).critical()["eps"] < -0.02


def test_no_equilibrium_is_invented_off_the_branch():
    # this threshold puts eps(72 deg) at -0.67%: nearer the present there is no computed equilibrium
    alt = model(t_edge=float(model().profile(72.0)))
    top = alt.eps_for_edge(72.0)
    assert top < -0.006
    assert np.isnan(alt.stable_edge(-0.001)) and np.isnan(alt.stable_edge(top / 2))
    assert alt.stable_edge(top - 1e-4) < 72.0
    assert model().stable_edge(0.0) == pytest.approx(72.0, abs=0.05)  # eps(edge) wobbles by ~1e-5 within 0.03 deg of 72


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
    from terra_prisca.budyko_sellers.fidelity_budyko1969 import column_errors, model_curves, score
    from terra_prisca.budyko_sellers.scan_budyko1969 import load

    scan = load(PDF)
    rows = {(r["figure"], r["curve"]): r for r in score(scan, model_curves(model()), "faithful")}
    for key in [("fig4", "T0"), ("fig4", "T1.0"), ("fig4", "T1.5"), ("fig6", "T0"), ("fig5", "Tp")]:
        assert rows[key]["rmse"] < 1.0, key
    assert rows[("fig6", "Tq")]["rmse"] < 1.2
    # the minus sign of the -0.01 tick label is not part of the traced ice edge
    phi = scan.curves[("fig5", "phi0")]
    assert not np.any((phi[:, 0] < 1443) & (phi[:, 1] > 2190) & (phi[:, 1] < 2205))
    nulls = {(r["figure"], r["curve"]): r for r in score(scan, model_curves(model(), "no feedback"), "null")}
    for key in [("fig4", "T1.0"), ("fig4", "T1.5"), ("fig5", "Tp"), ("fig5", "phi0")]:
        assert nulls[key]["rmse"] > 2 * rows[key]["rmse"], key
    # scores never extend a model curve past its computed range: the off-branch columns are counted, not clamped
    assert all(r["columns_unsupported"] == 0 for r in rows.values())
    base = {k: column_errors(scan, k, mc)[1] for k, mc in model_curves(model()).items() if k in scan.curves}
    alt = {(r["figure"], r["curve"]): r for r in
           score(scan, model_curves(model(t_edge=float(model().profile(72.0)))), "alt", baseline=base)}
    tp = alt[("fig5", "Tp")]
    assert tp["columns_unsupported"] > 100 and tp["columns"] + tp["columns_unsupported"] == rows[("fig5", "Tp")]["columns"]
    assert tp["faithful_rmse_same_columns"] < tp["rmse"] / 2
