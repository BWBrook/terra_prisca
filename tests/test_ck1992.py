from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from terra_prisca.biosphere_lifespan import ck1992 as m
from terra_prisca.walker_hays_kasting import whk1981

PDF = Path("local/sources/biosphere_lifespan/caldeira_kasting1992.pdf")


def test_sun_and_present_climate():
    assert float(m.solar(0.0)) == m.S0
    assert float(m.solar(1.6)) / m.S0 == pytest.approx(1 / (1 - 0.38 * 1.6 / 4.55), rel=1e-12)
    assert m.temperature(m.S0, m.P0) == pytest.approx(287.8899, abs=1e-3)  # not 288.15: the fits' present
    assert float(m.albedo(288.0)) == pytest.approx(0.2995, abs=1e-3)


def test_climate_has_one_root_over_the_range_used():
    Ts = np.linspace(200.0, 500.0, 6001)
    for t in np.linspace(0.0, 1.6, 9):
        for p in (1e-8, 1e-6, 1e-5, 3.2e-4, 1e-2):
            r = m.climate_residual(Ts, float(m.solar(t)), p)
            assert np.count_nonzero(np.sign(r[1:]) != np.sign(r[:-1])) == 1, (t, p)


def test_weathering_balance_has_one_root():
    """F - F0 changes sign once in Patm between the floor and 1e-2 bar. F is not
    monotonic everywhere: late on, high CO2 warms T towards 50 C and Pi falls,
    but only where F is several times F0."""
    ps = np.geomspace(1e-6, 1e-2, 400)
    for r in (m.FAITHFUL, m.READINGS["so2_fitted"], m.C3, m.READINGS["chemistry_T"]):
        ref = m._ref(r)
        for t in np.arange(0.0, 1.3, 0.05):
            f = np.array([m.weathering(p, float(m.solar(t)), r, ref) for p in ps]) - 1.0
            n = np.count_nonzero(np.sign(f[1:]) != np.sign(f[:-1]))
            assert n == (1 if f[0] < 0 else 0), (r.name, t, n)


def test_present_day_closure():
    s = m.state(0.0)
    assert s["P_atm_ppm"] == pytest.approx(320.0, rel=1e-9)
    assert s["P_soil_ppm"] == pytest.approx(3200.0, rel=1e-9)
    assert s["Pi_ratio"] == pytest.approx(1.0, rel=1e-9)
    s = m.state(0.0, m.READINGS["t0_printed"])  # T0 = 15 C cannot close today with these fits
    assert s["P_atm_ppm"] == pytest.approx(335.40, abs=0.01) and s["Pi_ratio"] == pytest.approx(1.0171, abs=1e-4)


def test_half_saturation():
    assert m.p_half() * 1e6 == pytest.approx(205.5726, abs=1e-3)
    assert m.p_half(m.READINGS["t0_printed"]) * 1e6 == pytest.approx(210.8, abs=1e-9)
    assert m.p_half(m.READINGS["volk_p_half"]) * 1e6 == pytest.approx(310.0, abs=1e-9)
    assert m.p_half(m.C3) * 1e6 == pytest.approx(112.733, abs=1e-3)
    T0 = m.t0()
    assert m.productivity(T0, m.P0) == pytest.approx(1.0, rel=1e-12)
    assert m.productivity(T0, m.P_MIN_C4) == 0.0 and m.productivity(323.15, m.P0) == 0.0


def test_imports_from_whk():
    assert m.EFOLD_K == whk1981.FAITHFUL.efold_K == 13.7
    assert whk1981.FAITHFUL.co2_exponent / 0.5 == pytest.approx(0.6)  # C&K's "implied exponent of 0.6"
    r = m.CONTROLS["whk_weathering"]
    assert m.weathering(m.P0, m.S0, r) == pytest.approx(1.0, abs=1e-9)


def test_h_activity_limits():
    r = replace(m.FAITHFUL, so2_factor=0.0)
    for p in (3.2e-3, 3.2e-4):
        k = m.constants(298.15, r)
        assert m.h_activity(p, 298.15, r) == pytest.approx(np.sqrt(k["KH"] * k["K1"] * p), rel=2e-3)
    low = m.h_activity(1e-6, 298.15)
    assert low > 2 * m.h_activity(1e-6, 298.15, r)  # SO2 sets the floor at low soil CO2


def test_floor_is_held():
    ref = m._ref(m.FAITHFUL)
    for t in (1.0, 1.2, 1.5):
        assert m.co2(t, m.FAITHFUL, ref) == m.P_FLOOR
        assert m.weathering(m.P_FLOOR, float(m.solar(t)), m.FAITHFUL, ref) >= 1.0
    assert m.co2_time(m.P_FLOOR) == pytest.approx(0.93195, abs=1e-4)


def test_event_search_boundaries():
    assert m.co2_time(0.5e-6) == float("inf")  # below the floor: never reached
    assert m.co2_time(0.5e-6, m.READINGS["so2_fitted"]) == float("inf")
    assert m.co2_time(m.P0, m.CONTROLS["fixed_co2"]) == 0.0  # holds at t = 0
    assert m.co2_time(m.P0, m.CONTROLS["constant_sun"]) == 0.0  # solved, so equal only to solver accuracy
    assert m.co2_time(m.P0, t_max=0.0) == 0.0
    assert m.co2_time(300e-6, m.CONTROLS["constant_sun"]) == float("inf")  # genuinely never reached
    assert m.first_crossing(lambda t: 1.0, 1.0, t_max=0.0) == 0.0
    assert m.first_crossing(lambda t: 2.0, 1.0, t_max=0.0) == float("inf")
    assert m.first_crossing(lambda t: 1.0 - t, 0.5, t_max=0.5, step=0.5) == pytest.approx(0.5)


def test_constants_traced_to_the_sources():
    k = m.constants(298.15)
    assert -np.log10([k["KH"], k["K1"], k["K2"], k["KW"]]) == pytest.approx([1.47, 6.352, 10.329, 13.999])
    assert (k["HS"], k["S1"], k["S2"]) == (1.23, 1.7e-2, 6.3e-8)
    k15 = m.constants(288.15, m.READINGS["chemistry_T"])  # Butler's 15 C row
    assert -np.log10([k15["KH"], k15["K1"], k15["K2"]]) == pytest.approx([1.33, 6.419, 10.430])
    t = m.READINGS["textbook"]
    assert m.co2_time(m.P_MIN_C4, t) == pytest.approx(0.79347, abs=1e-4)


def test_lifespans():
    assert m.co2_time(m.P_MIN_C3, m.C3) == pytest.approx(0.42302, abs=1e-4)
    assert m.co2_time(m.P_MIN_C4) == pytest.approx(0.76697, abs=1e-4)
    fit = m.READINGS["so2_fitted"]
    assert m.co2_time(m.P_MIN_C4, fit) == pytest.approx(0.8634, abs=2e-4)
    assert m.co2_time(m.P_MIN_C3, replace(fit, p_min=m.P_MIN_C3)) == pytest.approx(0.48882, abs=1e-4)
    assert m.kink_acidity_ratio(0.863374) == pytest.approx(0.17233, abs=1e-5)  # chemistry-free
    assert m.floor_threshold_T(fit) == pytest.approx(300.25, abs=0.01)
    for level, t in ((323.15, 1.32432), (353.15, 1.46469), (373.15, 1.57097)):
        assert m.temperature_time(level) == pytest.approx(t, abs=1e-4)
        assert m.temperature_time(level, fit) == pytest.approx(t, abs=1e-4)  # the hot phase is climate only


def test_controls():
    for key in ("constant_sun", "fixed_co2"):
        r = m.CONTROLS[key]
        assert all(m.co2(t, r) == pytest.approx(m.P0, rel=1e-9) for t in (0.0, 0.5, 1.0))
    assert m.temperature_time(323.15, m.CONTROLS["fixed_co2"]) == pytest.approx(0.948, abs=1e-3)
    assert m.co2_time(m.P_MIN_C4, m.CONTROLS["constant_productivity"]) < m.co2_time(m.P_MIN_C4)


def test_figure_table_is_reproducible(tmp_path):
    from terra_prisca.biosphere_lifespan import figures_ck1992

    figures_ck1992.main(tmp_path)
    committed = Path("models/biosphere_lifespan/figures/ck1992_fig2.csv")
    assert (tmp_path / "ck1992_fig2.csv").read_bytes() == committed.read_bytes()


@pytest.mark.skipif(not PDF.exists(), reason="source scan not present")
def test_fidelity_against_scan(tmp_path):
    from terra_prisca.biosphere_lifespan import fidelity_ck1992 as f
    from terra_prisca.biosphere_lifespan import scan_ck1992 as s
    from scipy.spatial import cKDTree

    sc = s.load(PDF)
    for key, ax in sc.axes.items():
        assert ax.residual < 4.5, key
    for c in f.CURVES:  # a trace drops only at crossings, the label, the junction and frames
        tr = s.trace(sc, c)
        assert sum(v for k, v in tr.reasons.items() if k in ("none", "two strokes", "merged")) <= 6, (c, tr.reasons)

    assert f.fit_so2_factor(PDF) == pytest.approx(m.SO2_FIT_FACTOR, abs=2e-4)
    assert m.so2_share() == pytest.approx(0.0811, abs=1e-4)
    assert m.so2_share(m.READINGS["so2_fitted"]) == pytest.approx(0.0244, abs=1e-4)
    co = {r["base"]: r for r in f.coupled(PDF)}  # alternatives with the SO2 factor refitted under each
    px = "Pi_ratio model_to_trace median px"
    assert co["faithful"][px] < 2 and co["t0_printed"][px] > 3 * co["faithful"][px]
    assert co["volk_p_half"][px] > 20
    for k in ("faithful", "chemistry_T", "textbook", "textbook_chemistry_T"):  # one ratio, several shares
        assert co[k]["aH_kink_over_aH_today"] == pytest.approx(0.17233, abs=1e-5)
    assert co["chemistry_T"]["so2_share_today"] > 2 * co["faithful"]["so2_share_today"]

    ev = {r["feature"]: r for r in f.events(PDF)}
    assert abs(ev["Pi_ratio at t=0"]["printed"] - 1.0) < 0.006   # rejects T0 = 15 C (1.017)
    for k in ("T reaches 323.15 K, t Gyr", "T reaches 353.15 K, t Gyr", "T reaches 370 K, t Gyr"):
        assert abs(ev[k]["printed"] - ev[k]["faithful"]) < 0.01, k  # hot phase, every reading
    for k, tol in (("P_atm reaches 1 ppm, t Gyr", 0.002), ("Pi_ratio falls to 0.05, t Gyr", 0.011), ("T at 0.9 Gyr, K", 0.2)):
        assert abs(ev[k]["printed"] - ev[k]["so2_fitted"]) < tol, k  # left out of the one-parameter fit
        assert abs(ev[k]["printed"] - ev[k]["faithful"]) > 3 * abs(ev[k]["printed"] - ev[k]["so2_fitted"]), k
    # the printed T curve is nearly flat at 300 K: the axis residual alone moves its crossing by >0.1 Gyr
    lo, hi = (ev[k]["printed"] for k in ev if "axis residual" in k)
    assert hi - lo > 0.1

    tw = {(r["curve"], r["reading"]): r for r in f.two_way(PDF)}
    for c in f.CURVES:
        if c == "S_ratio":
            continue
        r = tw[(c, "so2_fitted")]
        assert r["model_to_trace_median_px"] < 3 and r["trace_to_model_median_px"] < 3, c
        assert r["max_model_spacing_px"] < 0.26
    assert tw[("merged", "faithful")]["model_to_trace_median_px"] > 20
    # paired coverage: a reading is scored only where it has values, and so is its comparator
    fx = tw[("T_K", "fixed_co2")]
    assert fx["trace_points_without_value"] == 112 and fx["trace_points_used"] == 654
    assert fx["trace_to_model_p95_px"] > 5 * fx["faithful_trace_to_model_p95_px_same_points"]
    assert tw[("T_K", "dT_plus_0.5")]["trace_points_without_value"] == 68
    # model-to-trace measures against the same 698 supported centres, not all 766 (Codex CK-R5 follow-up)
    sc, tr = f._traces(PDF)
    ink, t_ink = tr["T_K"].centres, f.traced(sc, tr)["T_K"][:, 0]
    hot = f.SENSITIVITY["dT_plus_0.5"]
    sup = np.isfinite(f._model_values("T_K", t_ink, hot))
    mp = f._model_px(sc, "T_K", hot, t_ink[sup].min(), t_ink[sup].max())
    mp = mp[[s._excluded(x, y, sc, s.CURVE_AXES["T_K"][0]) is None for x, y in mp]]
    to_all = np.percentile(cKDTree(ink).query(mp)[0], 95)
    to_sup = np.percentile(cKDTree(ink[sup]).query(mp)[0], 95)
    assert tw[("T_K", "dT_plus_0.5")]["model_to_trace_p95_px"] == pytest.approx(to_sup) and to_sup > to_all + 10
    for r in (m.FAITHFUL, f.gough_ratio):  # tabulated and callable readings share exact endpoints
        e = sc.to_data("S_ratio", f._model_px(sc, "S_ratio", r, 0.05, 1.5)[[0, -1]])[:, 0]
        assert e == pytest.approx([0.05, 1.5], abs=1e-9)
    joint = tw[("T_K", "dT_plus_0.5_albedo_plus_0.005708")]  # greenhouse and albedo trade off
    assert abs(joint["model_to_trace_median_px"] - tw[("T_K", "faithful")]["model_to_trace_median_px"]) < 0.5
    sco = {(r["curve"], r["reading"]): r for r in f.scores(PDF)}
    assert sco[("T_K", "fixed_co2")]["used"] < sco[("T_K", "faithful")]["used"]
    assert sco[("T_K", "fixed_co2")]["rmse"] > 20 * sco[("T_K", "fixed_co2")]["faithful_rmse_same_points"] / 2
    sun = tw[("S_ratio", "faithful")]["model_to_trace_median_px"]
    assert sun < 2 and tw[("S_ratio", "Gough (1981)")]["model_to_trace_median_px"] > 2.5 * sun
    assert tw[("S_ratio", "Lovelock & Whitfield straight line")]["model_to_trace_median_px"] > 20 * sun
    for null in ("constant_productivity", "fixed_co2", "whk_weathering"):
        for c in ("P_atm", "T_K"):
            assert tw[(c, null)]["model_to_trace_p95_px"] > 5 * tw[(c, "so2_fitted")]["model_to_trace_p95_px"], (c, null)

    f.main(PDF, tmp_path)
    for committed in sorted(Path("models/biosphere_lifespan/fidelity").glob("ck1992_*.csv")):
        assert (tmp_path / committed.name).read_bytes() == committed.read_bytes(), committed.name
