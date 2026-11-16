from pathlib import Path

import numpy as np
import pytest

from terra_prisca.biosphere_lifespan import lw1982 as m
from terra_prisca.walker_hays_kasting import whk1981

PDF = Path("local/sources/biosphere_lifespan/lovelock_whitfield1982.pdf")
TWO_POINT = ("faithful", "text_7000", "two_thirds", "linear_c")


def test_two_point_readings_pass_through_their_anchors():
    for key in TWO_POINT:
        r = m.READINGS[key]
        assert float(m.co2(m.T_PAST, r)) == pytest.approx(r.c_past, rel=1e-12)
        assert float(m.co2(0.0, r)) == pytest.approx(m.C_NOW, rel=1e-12)


def test_faithful_sqrt_co2_is_straight_in_time():
    t = np.linspace(-3500, 80, 50)
    assert np.allclose(np.diff(np.sqrt(m.co2(t)), 2), 0.0, atol=1e-9)


def test_lifespan_matches_closed_form():
    lp = 1.0 - float(m.luminosity(m.T_PAST))
    for key in TWO_POINT:
        r = m.READINGS[key]
        f = lambda c: c ** r.power
        dL = (f(m.C_NOW) - f(m.C_LIMIT)) / (f(r.c_past) - f(m.C_NOW)) * lp
        assert m.lifespan(r) == pytest.approx(dL / m.SUN_SLOPE_PER_GYR * 1000, rel=1e-9)
    assert m.lifespan() == pytest.approx(80.04, abs=0.01)
    assert m.lifespan(m.READINGS["text_7000"]) == pytest.approx(300.2, abs=0.1)


def test_straight_sun_slope_cancels_and_gough_reanchors():
    from dataclasses import replace

    for slope in (0.05556, 0.0733, 0.0851):
        assert m.lifespan(replace(m.FAITHFUL, sun_slope=slope)) == pytest.approx(80.036102, abs=1e-6)
    g = m.VARIANTS["gough_sun"]
    assert float(m.co2(m.T_PAST, g)) == pytest.approx(m.C_PAST) and float(m.co2(0.0, g)) == pytest.approx(m.C_NOW)
    assert m.lifespan(g) == pytest.approx(61.345204, abs=1e-6)


def test_rules_have_no_solution_beyond_their_domain():
    for key, r in {**m.READINGS, **m.VARIANTS}.items():
        end = m.domain_end(r)
        assert m.lifespan(r) < end, key
        if np.isfinite(end):
            assert np.isnan(float(m.co2(end + 1.0, r))), key
            assert np.isfinite(float(m.co2(end - 1.0, r))), key
    r = m.READINGS["whk_constant_T"]
    assert m.domain_end(r) == pytest.approx(502.9, abs=0.02)
    assert np.isnan(float(m.co2(1000.0, r)))
    for t in np.linspace(-3500, 500, 41):  # eq. (6) closes at dT = 0 throughout the domain
        dte = float(whk1981.dTe_from_luminosity(m.luminosity(t)))
        assert float(whk1981.surface_dT(dte, float(m.co2(t, r)) / m.C_NOW)) == pytest.approx(0.0, abs=1e-9)


def test_whk_readings_use_whk1981():
    for t in (-3000.0, -500.0, 100.0):
        dte = float(whk1981.dTe_from_luminosity(m.luminosity(t)))
        p = float(m.co2(t, m.READINGS["whk_constant_T"])) / m.C_NOW
        assert float(whk1981.surface_dT(dte, p)) == pytest.approx(0.0, abs=1e-9)
        p = float(m.co2(t, m.VARIANTS["whk_feedback"])) / m.C_NOW
        assert p == pytest.approx(whk1981.equilibrium(dte, 1.0)[1], rel=1e-12)


def test_gough_and_controls():
    assert float(m.gough_luminosity(-4700.0)) == pytest.approx(1 / 1.4)
    assert float(m.gough_luminosity(0.0)) == pytest.approx(1.0)
    r = m.CONTROLS["no_brightening"]
    assert m.lifespan(r) == float("inf")
    assert np.all(m.co2(np.array([-3000.0, 0.0, 500.0]), r) == m.C_NOW)


def test_figure_table_is_reproducible(tmp_path):
    from terra_prisca.biosphere_lifespan import figures_lw1982

    figures_lw1982.main(tmp_path)
    committed = Path("models/biosphere_lifespan/figures/lw1982_fig2.csv")
    assert (tmp_path / "lw1982_fig2.csv").read_bytes() == committed.read_bytes()


@pytest.mark.skipif(not PDF.exists(), reason="source scan not present")
def test_fidelity_against_scan(tmp_path):
    from terra_prisca.biosphere_lifespan import fidelity_lw1982 as f
    from terra_prisca.biosphere_lifespan import scan_lw1982 as s

    sc = s.load(PDF)
    for ax in (sc.time, sc.lum, sc.sqrtc):
        assert ax.residual < 1.0
    for y, v in s.TEMP_LABEL_ROWS:  # labels sit on the frame-calibrated scale
        assert abs(float(sc.temp.value(y)) - v) < 1.0

    rows = {(r["curve"].split()[0], r["reading"]): r for r in f.scores(sc)}
    sun = {k[1]: v for k, v in rows.items() if k[0] == "Sun"}
    faithful_sun = sun.pop("faithful (straight, 0.0733/Gyr)")
    assert faithful_sun["rmse_px"] < 1.5
    assert all(v["rmse_px"] > 5 * faithful_sun["rmse_px"] for v in sun.values())
    co2 = {k[1]: v for k, v in rows.items() if k[0] == "CO2"}
    faithful = co2.pop("faithful")
    assert faithful["rmse_px"] < 5
    assert all(v["rmse_px"] > 2.5 * faithful["rmse_px"] for v in co2.values())

    ln = {r["line"]: r for r in f.lines(sc)}
    assert 260 < ln["co2"]["value_at_start"] < 280          # about 70,000 ppm, not 7,000
    assert abs(ln["co2"]["value_at_t0"] - np.sqrt(320)) < 1.5
    assert abs(ln["sun"]["slope_per_Myr"] * 1000 - m.SUN_SLOPE_PER_GYR) < 0.001
    x = f.crossing(sc)
    assert 80 < x["co2_meets_limit_Myr"] < 130 and 80 < x["co2_tail_meets_limit_Myr"] < 130
    # The stroke beyond t = 0 is the same line: same slope, stable to the window.
    assert abs(x["co2_tail_slope_px_per_px"] / x["co2_slope_px_per_px"] - 1) < 0.02
    for half in (1, 2, 3):
        tail = s.trace(sc, "co2_tail", half)
        assert abs(np.polyfit(tail[:, 0], tail[:, 1], 1)[0] / x["co2_slope_px_per_px"] - 1) < 0.02, half
        assert not np.any((tail[:, 0] >= 615) & (tail[:, 0] <= 625))
    for key in ("sun", "co2"):  # main lines are stable from +-2 to +-8 px
        k = [np.polyfit(*s.trace(sc, key, h).T, 1)[0] for h in (2, 4, 6, 8)]
        assert np.ptp(k) < 2e-4, key

    tw = {(r["curve"], r["reading"]): r for r in f.two_way(sc)}
    for curve, lim in (("Sun line", 2.0), ("CO2 line", 6.0)):
        best = tw[(curve, "faithful")]
        assert best["model_to_ink_p95_px"] < lim and best["ink_to_model_p95_px"] < lim, curve
        assert best["max_sample_spacing_px"] < 0.5
        for (c, name), r in tw.items():
            if c == curve and name != "faithful":
                assert r["model_to_ink_median_px"] > 2 * best["model_to_ink_median_px"], (c, name)
                assert r["ink_to_model_median_px"] > 2 * best["ink_to_model_median_px"], (c, name)
    assert abs(np.sqrt(x["limit_ppm"]) - np.sqrt(150)) < 1.5

    for r in f.band(sc):
        if r["feature"] == "glaciation minimum":
            assert 3.5 < r["printed_C"] < 5.0
        else:
            assert abs(r["printed_C"] - r["text_value_C"]) < 0.5

    f.main(PDF, tmp_path)
    for committed in sorted(Path("models/biosphere_lifespan/fidelity").glob("lw1982_*.csv")):
        assert (tmp_path / committed.name).read_bytes() == committed.read_bytes(), committed.name
