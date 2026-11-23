import math
from dataclasses import replace

import pytest

from terra_prisca.biosphere_lifespan import ck1992 as ck
from terra_prisca.biosphere_lifespan import ingredient_swap as sw
from terra_prisca.biosphere_lifespan import lw1982 as lw


def test_sun_laws_invert():
    for sun in sw.SUNS:
        for t in (0.0, 0.3, 1.2):
            assert sw.time_to(sw.brightness(t, sun), sun) == pytest.approx(t, abs=1e-12)


def test_endpoints_are_the_faithful_models():
    assert sw.lifespan_myr("lw_rule", "C3", "straight") == pytest.approx(lw.lifespan(), abs=1e-6)
    assert sw.lifespan_myr("ck_biology", "C4", "eq1") == pytest.approx(ck.co2_time(ck.P_MIN_C4) * 1e3, abs=1e-6)
    assert sw.lifespan_myr("ck_biology", "C3", "eq1") == pytest.approx(ck.co2_time(ck.P_MIN_C3, ck.C3) * 1e3, abs=1e-6)
    # the re-anchored rule matches lw1982's own re-anchoring under another Sun law
    gough = lw.VARIANTS["gough_sun"]
    l_star = sw.lw_rule_s_star(150.0, lw.gough_luminosity)
    assert float(lw.gough_luminosity(lw.lifespan(gough))) == pytest.approx(l_star, abs=1e-12)
    assert sw.lw_rule_s_star(10.0, lw.luminosity) == pytest.approx(
        float(lw.luminosity(lw.lifespan(replace(lw.FAITHFUL, c_limit=10.0)))), abs=1e-12)


def test_ck_cells_balance_weathering():
    for law in ("ck_pump_held", "ck_biology"):
        for plants, (_, thr, _) in sw.PLANTS.items():
            r = sw._reading(law, plants)
            s = sw.s_star(law, plants) * ck.S0
            assert ck.weathering(thr * sw.PPM, s, r) == pytest.approx(1.0, abs=1e-7), (law, plants)
    for plants, (_, thr, _) in sw.PLANTS.items():
        s = sw.s_star("ck_constant_T", plants) * ck.S0
        assert ck.temperature(s, thr * sw.PPM) == pytest.approx(ck.t0(), abs=1e-7)
    # C&K's laws depend on time only through S: the straight Sun reaches the same S*
    t = sw.lifespan_myr("ck_biology", "C4", "straight") / 1e3
    assert float(lw.luminosity(t * 1e3)) == pytest.approx(sw.s_star("ck_biology", "C4"), abs=1e-12)


def test_shapley_telescopes():
    cells = sw.factorial()
    sh = sw.shapley(cells)
    life = {tuple(r[f"{k}_from"] for k in sw.INGREDIENTS): r["lifespan_Myr"] for r in cells}
    lw_end, ck_end = life[("L&W",) * 3], life[("C&K",) * 3]
    assert sum(r["shapley_ln"] for r in sh) == pytest.approx(math.log(ck_end / lw_end), abs=1e-12)
    assert sum(r["shapley_Myr"] for r in sh) == pytest.approx(ck_end - lw_end, abs=1e-9)
    assert sum(r["share_of_ln_change"] for r in sh) == pytest.approx(1.0, abs=1e-12)
    by = {r["ingredient"]: r for r in sh}
    assert by["co2"]["shapley_factor"] == pytest.approx(5.4985, abs=1e-3)
    assert by["plants"]["shapley_factor"] == pytest.approx(2.1836, abs=1e-3)
    assert by["sun"]["shapley_factor"] == pytest.approx(0.7981, abs=1e-3)
    for r in sh:
        assert r["factor_min"] <= r["shapley_factor"] <= r["factor_max"]
    fitted = {(r["sun_from"], r["co2_from"], r["plants_from"]): r["lifespan_Myr"] for r in sw.factorial("so2_fitted")}
    assert fitted[("C&K",) * 3] == pytest.approx(ck.co2_time(ck.P_MIN_C4, ck.READINGS["so2_fitted"]) * 1e3, abs=1e-6)
    assert sum(r["share_of_ln_change"] for r in sw.shapley(sw.factorial("so2_fitted"))) == pytest.approx(1.0, abs=1e-12)
    steps = sw.co2_steps()
    held = [r for r in steps if r["step"] == sw.LAWS["ck_pump_held"]]
    full = [r for r in steps if r["step"] == sw.LAWS["ck_biology"]]
    assert all(0 < r["T_minus_T0_K"] < 0.5 for r in held)  # pump held: nearly a perfect thermostat
    assert all(r["T_minus_T0_K"] > 7 for r in full)          # pump off at the threshold: the Earth warms
    for lab in (p[0] for p in sw.PLANTS.values()):
        s = [r for r in steps if r["plants"] == lab]
        assert math.prod(r["factor"] for r in s[1:]) == pytest.approx(s[-1]["lifespan_Myr"] / s[0]["lifespan_Myr"])


def test_threshold_at_compensation_point_ignores_the_productivity_curve():
    """At a threshold equal to Pmin, Pi = 0: the lifespan depends on the soil
    pump being off, not on the shape of eq. (8)."""
    assert ck.co2_time(ck.P_MIN_C4, ck.C3) == pytest.approx(ck.co2_time(ck.P_MIN_C4), abs=1e-9)
    volk = ck.READINGS["volk_p_half"]
    assert ck.co2_time(ck.P_MIN_C4, volk) == pytest.approx(ck.co2_time(ck.P_MIN_C4), abs=1e-9)
    assert ck.co2_time(ck.P_MIN_C3, replace(volk, p_min=ck.P_MIN_C3)) == pytest.approx(
        ck.co2_time(ck.P_MIN_C3, ck.C3), abs=1e-9)


def test_outputs_reproduce(tmp_path):
    sw.main(tmp_path)
    for f in ("cells", "shapley", "co2_steps", "side"):
        name = f"ingredient_swap_{f}.csv"
        assert (tmp_path / name).read_bytes() == (sw.Path("models/biosphere_lifespan/swap") / name).read_bytes(), name
