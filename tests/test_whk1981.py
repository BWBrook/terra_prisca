from pathlib import Path

import numpy as np
import pytest

from terra_prisca.walker_hays_kasting import whk1981 as m

PDF = Path("local/sources/walker_hays_kasting/whk1981.pdf")
GRID = np.arange(-20.0, 6.01, 0.5)
V = (0.5, 1.0, 2.0, 4.0)


def test_eq2_is_eq1_balanced_against_the_source():
    for v in V:
        for dT in (-20.0, -5.0, 0.0, 8.0):
            p = m.co2_ratio(v, dT)
            assert m.weathering_ratio(p, dT) == pytest.approx(v, rel=1e-12)


def test_eq6_follows_from_eqs_3_to_5_and_closes_today():
    assert m.TE0 + 29.7 + 2.3 == pytest.approx(m.TS0, abs=1e-12)
    for dTe in (-18.0, 0.0, 4.0):
        for p in (0.1, 1.0, 80.0):
            # Ts = Te + 29.7 + 0.5 (Ts - 285) + 2.3 p^0.364, solved for Ts
            ts = (m.TE0 + dTe + 29.7 - 0.5 * m.TS0 + 2.3 * p ** 0.364) / 0.5
            assert m.surface_dT(dTe, p) == pytest.approx(ts - m.TS0, abs=1e-10)


def test_present_state_is_the_calibration_point():
    dT, p = m.equilibrium(0.0, 1.0)
    assert dT == pytest.approx(0.0, abs=1e-10) and p == pytest.approx(1.0, abs=1e-10)


def test_equilibrium_is_unique_and_solves_both_equations():
    dTs = np.linspace(-150, 150, 3001)
    for v in V:
        for dTe in GRID:
            g = dTs - m.surface_dT(dTe, m.co2_ratio(v, dTs))
            assert np.all(np.diff(g) > 0)
            dT, p = m.equilibrium(dTe, v)
            assert p == pytest.approx(m.co2_ratio(v, dT), rel=1e-12)
            assert dT == pytest.approx(float(m.surface_dT(dTe, p)), abs=1e-9)


def test_sensitivity_matches_finite_difference():
    for v in V:
        for dTe in (-15.0, 0.0, 5.0):
            h = 1e-4
            fd = (m.equilibrium(dTe + h, v)[0] - m.equilibrium(dTe - h, v)[0]) / (2 * h)
            assert m.sensitivity(dTe, v) == pytest.approx(fd, rel=1e-6)


def test_stated_numbers():
    assert m.arrhenius_efold() == pytest.approx(17.66, abs=0.005)        # text 17.7
    assert m.combined_efold(17.7, 60.0) == pytest.approx(13.67, abs=0.005)  # text 13.7
    assert m.doubling_warming() == pytest.approx(1.320, abs=0.001)       # text 1.3
    assert float(m.dTe_from_luminosity(0.75)) == pytest.approx(-17.56, abs=0.005)  # text -18
    dT, _ = m.equilibrium(-18.0, 1.0)
    assert dT == pytest.approx(-17.98, abs=0.005)                        # text -18
    assert m.TS0 + dT == pytest.approx(267.0, abs=0.05)                  # text 265: inconsistent


def test_qualitative_claims():
    p = {v: np.array([m.equilibrium(x, v)[1] for x in GRID]) for v in V}
    s = {v: np.array([m.sensitivity(x, v) for x in GRID]) for v in V}
    for a, b in zip(V, V[1:]):
        assert np.all(p[a] < p[b]) and np.all(s[a] > s[b])
    for v in V:
        assert np.all(np.diff(s[v]) > 0) and np.all(s[v] < 2.0)
    weak, faith = m.Reading(co2_exponent=0.2, p_efold_K=None, v_exponent=None), m.Reading(p_efold_K=None, v_exponent=None)
    assert all(m.sensitivity(x, 1.0, weak) < m.sensitivity(x, 1.0, faith) for x in (-15, -5, 3))


def test_controls():
    for dTe in (-15.0, 0.0, 4.0):
        assert m.equilibrium(dTe, 2.0, m.CONTROLS["thermostat"])[0] == pytest.approx(13.7 * np.log(2.0))
        assert m.equilibrium(dTe, 2.0, m.CONTROLS["no_feedback"]) == (pytest.approx(2 * dTe), 1.0)


def test_figure_table_is_reproducible(tmp_path):
    from terra_prisca.walker_hays_kasting import figures_whk1981

    figures_whk1981.main(tmp_path)
    committed = Path("models/walker_hays_kasting/figures/whk1981_fig2.csv")
    assert (tmp_path / "whk1981_fig2.csv").read_bytes() == committed.read_bytes()


@pytest.mark.skipif(not PDF.exists(), reason="source scan not present")
def test_fidelity_against_scan(tmp_path):
    from terra_prisca.walker_hays_kasting import fidelity_whk1981 as f
    from terra_prisca.walker_hays_kasting import scan_whk1981 as s

    sc = s.load(PDF)
    traces = f.printed(sc)
    rows = f.fig2_scores(sc, traces)
    faithful = {r["curve"]: r for r in rows if r["reading"] == "faithful"}
    assert len(faithful) == 9
    for name, r in faithful.items():
        assert r["columns_unsupported"] == 0 and r["columns"] > 150
        assert r["rmse"] < (0.25 if "2a" in name else 0.012)
    for r in rows:
        if r["reading"] in ("faithful", "unrounded"):
            continue
        assert r["rmse"] > 2.5 * r["faithful_rmse_same_columns"], (r["curve"], r["reading"])

    # Trace identity: each panel's traces lie nearest their own model curve.
    for p in "ab":
        for v, tr in ((v, traces[(p, v)]) for v in V):
            own = np.median(np.abs(f.predict("faithful", p, v, tr[:, 0]) - tr[:, 1]))
            for w in V:
                if w != v:
                    other = np.median(np.abs(f.predict("faithful", p, w, tr[:, 0]) - tr[:, 1]))
                    assert other > 5 * own, (p, v, w)

    bl = f.broken_line_fit(sc)
    assert bl["slope"] == pytest.approx(2.0, abs=0.05) and abs(bl["intercept"]) < 0.25
    lag = f.lagache_fit(sc)
    assert lag["efold_implied_K"] == pytest.approx(17.7, abs=0.5)

    segs, implied = f.fig1_table(sc)
    ends = sorted({round(x, -1) for sg in segs if sg["panel"] == "a" for x in (sg["x_start"], sg["x_end"])})
    for bound in (30, 120, 280, 630):  # Table 1's class limits, in mm/yr, on an axis labelled cm/yr
        assert min(abs(e - bound) for e in ends) <= 15
    outside = [(r["temperature_class"], r["runoff_class"]) for r in implied if not r["inside_class"]]
    assert outside == [(">20", "30-120")]

    f.main(PDF, tmp_path)
    for name in ("whk1981_fidelity.csv", "whk1981_numbers.csv", "whk1981_printed_curves.csv",
                 "whk1981_fig1_implied_runoff.csv", "whk1981_lines.csv"):
        committed = Path("models/walker_hays_kasting/fidelity") / name
        assert (tmp_path / name).read_bytes() == committed.read_bytes(), name
