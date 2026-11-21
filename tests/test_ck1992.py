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
    assert s["P_atm_ppm"] == pytest.approx(335.32, abs=0.01) and s["Pi_ratio"] == pytest.approx(1.0169, abs=1e-4)


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
        assert m.h_activity(p, 298.15, r) == pytest.approx(np.sqrt(m.CO2_KH[0] * m.CO2_K1[0] * p), rel=2e-3)
    low = m.h_activity(1e-6, 298.15)
    assert low > 2 * m.h_activity(1e-6, 298.15, r)  # SO2 sets the floor at low soil CO2


def test_floor_is_held():
    ref = m._ref(m.FAITHFUL)
    for t in (1.0, 1.2, 1.5):
        assert m.co2(t, m.FAITHFUL, ref) == m.P_FLOOR
        assert m.weathering(m.P_FLOOR, float(m.solar(t)), m.FAITHFUL, ref) >= 1.0
    assert m.co2_time(m.P_FLOOR) == pytest.approx(0.95675, abs=1e-4)


def test_lifespans():
    assert m.co2_time(m.P_MIN_C3, m.C3) == pytest.approx(0.44383, abs=1e-4)
    assert m.co2_time(m.P_MIN_C4) == pytest.approx(0.79347, abs=1e-4)
    fit = m.READINGS["so2_fitted"]
    assert m.co2_time(m.P_MIN_C4, fit) == pytest.approx(0.8634, abs=2e-4)
    assert m.co2_time(m.P_MIN_C3, replace(fit, p_min=m.P_MIN_C3)) == pytest.approx(0.48887, abs=1e-4)
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

    sc = s.load(PDF)
    for key, ax in sc.axes.items():
        assert ax.residual < 4.5, key
    for c in f.CURVES:  # a trace drops only at crossings, the label, the junction and frames
        tr = s.trace(sc, c)
        assert sum(v for k, v in tr.reasons.items() if k in ("none", "two strokes", "merged")) <= 6, (c, tr.reasons)

    assert f.fit_so2_factor(PDF) == pytest.approx(m.SO2_FIT_FACTOR, abs=2e-4)
    assert m.so2_share() == pytest.approx(0.0598, abs=1e-4)
    assert m.so2_share(m.READINGS["so2_fitted"]) == pytest.approx(0.0243, abs=1e-4)
    co = {r["base"]: r for r in f.coupled(PDF)}  # alternatives with the SO2 factor refitted under each
    px = "Pi_ratio median px"
    assert co["faithful"][px] < 2 and co["t0_printed"][px] > 3 * co["faithful"][px]
    assert co["volk_p_half"][px] > 20

    ev = {r["feature"]: r for r in f.events(PDF)}
    assert abs(ev["Pi_ratio at t=0"]["printed"] - 1.0) < 0.006   # rejects T0 = 15 C (1.017)
    assert abs(np.log10(ev["P_atm_ppm at t=0"]["printed"] / 320)) < abs(np.log10(ev["P_atm_ppm at t=0"]["printed"] / 335.3))
    for k in ("T reaches 323.15 K, t Gyr", "T reaches 353.15 K, t Gyr", "T reaches 370 K, t Gyr"):
        assert abs(ev[k]["printed"] - ev[k]["faithful"]) < 0.01, k  # hot phase, every reading
    for k in ("P_atm reaches 1 ppm, t Gyr", "T reaches 300 K, t Gyr", "Pi_ratio falls to 0.05, t Gyr"):
        assert abs(ev[k]["printed"] - ev[k]["so2_fitted"]) < 0.015, k  # not fitted: tests of the fit
        assert abs(ev[k]["printed"] - ev[k]["faithful"]) > abs(ev[k]["printed"] - ev[k]["so2_fitted"]), k

    tw = {(r["curve"], r["reading"]): r for r in f.two_way(PDF)}
    for c in f.CURVES:
        if c == "S_ratio":
            continue
        r = tw[(c, "so2_fitted")]
        assert r["model_to_trace_median_px"] < 3 and r["trace_to_model_median_px"] < 3, c
        assert r["max_model_spacing_px"] < 0.26
    assert tw[("merged", "faithful")]["model_to_trace_median_px"] > 20
    sun = tw[("S_ratio", "faithful")]["model_to_trace_median_px"]
    assert sun < 2 and tw[("S_ratio", "Gough (1981)")]["model_to_trace_median_px"] > 2.5 * sun
    assert tw[("S_ratio", "Lovelock & Whitfield straight line")]["model_to_trace_median_px"] > 20 * sun
    for null in ("constant_productivity", "fixed_co2", "whk_weathering"):
        for c in ("P_atm", "T_K"):
            assert tw[(c, null)]["model_to_trace_p95_px"] > 5 * tw[(c, "so2_fitted")]["model_to_trace_p95_px"], (c, null)

    f.main(PDF, tmp_path)
    for committed in sorted(Path("models/biosphere_lifespan/fidelity").glob("ck1992_*.csv")):
        assert (tmp_path / committed.name).read_bytes() == committed.read_bytes(), committed.name
