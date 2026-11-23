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
    life = {tuple(r[f"{k}_from"] for k in sw.INGREDIENTS): r["time_to_limit_Myr"] for r in cells}
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
    fitted = {(r["sun_from"], r["co2_from"], r["plants_from"]): r["time_to_limit_Myr"] for r in sw.factorial("so2_fitted")}
    assert fitted[("C&K",) * 3] == pytest.approx(ck.co2_time(ck.P_MIN_C4, ck.READINGS["so2_fitted"]) * 1e3, abs=1e-6)
    assert sum(r["share_of_ln_change"] for r in sw.shapley(sw.factorial("so2_fitted"))) == pytest.approx(1.0, abs=1e-12)


def test_fixed_lw_line_changes_only_the_future_clock():
    """SW-R1: keeping the sqrt(CO2)-luminosity line fitted under L&W's own Sun
    moves only the two L&W-rule cells under eq. (1); the ranking survives."""
    rec = {(r["sun_from"], r["co2_from"], r["plants_from"]): r["time_to_limit_Myr"] for r in sw.factorial()}
    fix = {(r["sun_from"], r["co2_from"], r["plants_from"]): r["time_to_limit_Myr"] for r in sw.factorial("lw_line_fixed")}
    moved = {k for k in rec if rec[k] != fix[k]}
    assert moved == {("C&K", "L&W", "L&W"), ("C&K", "L&W", "C&K")}
    assert fix[("C&K", "L&W", "L&W")] == pytest.approx(69.836, abs=1e-3)
    assert fix[("C&K", "L&W", "C&K")] == pytest.approx(180.612, abs=1e-3)
    by = {r["ingredient"]: r["shapley_factor"] for r in sw.shapley(sw.factorial("lw_line_fixed"))}
    assert (by["co2"], by["plants"], by["sun"]) == pytest.approx((5.167, 2.183, 0.850), abs=1e-3)


def test_closure_and_pump_act_together():
    """SW-R4: after the greenhouse, neither the closure (weathering balance, T
    free) nor the responsive pump does much alone; together they do."""
    steps = {(r["plants"][:2], r["step"]): r for r in sw.co2_steps()}
    for p in ("C3", "C4"):
        t = {k: steps[(p, k)]["time_to_limit_Myr"] for k in sw.CO2_STEPS}
        assert t["ck_constant_T_pump_responsive"] == t["ck_constant_T_pump_held"]  # pump alone: no change
        assert 1.0 < t["ck_pump_held"] / t["ck_constant_T_pump_held"] < 1.06       # closure alone: small
        assert t["ck_biology"] / t["ck_constant_T_pump_responsive"] > 1.5          # both: large
        assert steps[(p, "lw_rule")]["T_minus_T0_K"] == 0.0
        assert steps[(p, "ck_pump_held")]["F_over_F0"] == pytest.approx(1.0, abs=1e-7)
        assert steps[(p, "ck_biology")]["F_over_F0"] == pytest.approx(1.0, abs=1e-7)
        assert 0 < steps[(p, "ck_pump_held")]["T_minus_T0_K"] < 0.5
        assert steps[(p, "ck_biology")]["T_minus_T0_K"] > 7
    assert steps[("C3", "ck_constant_T_pump_responsive")]["F_over_F0"] == pytest.approx(0.597, abs=1e-3)
    assert steps[("C4", "ck_constant_T_pump_responsive")]["F_over_F0"] == pytest.approx(0.544, abs=1e-3)
    # the warming builds while productivity declines, not only after it stops
    w = {(r["plants"], r["P_atm_ppm"]): r for r in sw.warming()}
    assert w[("C4", 20.0)]["T_minus_T0_K"] == pytest.approx(6.197, abs=1e-3)
    assert w[("C4", 20.0)]["Pi_ratio"] == pytest.approx(0.0903, abs=1e-4)
    assert w[("C4", 10.0)]["T_minus_T0_K"] == pytest.approx(8.346, abs=1e-3)


def test_threshold_override_domain():
    """SW-R5: an already-met threshold is reached today; zero and levels below
    C&K's fit range are rejected; a level C&K's weathering never reaches is inf."""
    for law in ("lw_rule", "ck_constant_T", "ck_biology"):
        for sun in sw.SUNS:
            assert sw.lifespan_myr(law, "C3", sun, threshold_ppm=400.0) == 0.0
            assert sw.lifespan_myr(law, "C3", sun, threshold_ppm=320.0) == 0.0
            with pytest.raises(ValueError):
                sw.lifespan_myr(law, "C3", sun, threshold_ppm=0.0)
    assert lw.lifespan(replace(lw.FAITHFUL, c_limit=400.0)) == 0.0
    with pytest.raises(ValueError):
        sw.lifespan_myr("ck_constant_T", "C4", "straight", threshold_ppm=0.005)
    assert sw.lifespan_myr("ck_biology", "C4", "eq1", threshold_ppm=0.5) == float("inf")  # below the 1 ppm floor


def test_unknown_names_are_rejected():
    """SW-R6: a misspelt setting must not fall through to another model."""
    for args in (("lw_rul", "C3", "eq1"), ("lw_rule", "C3", "straght"), ("lw_rule", "C5", "eq1")):
        with pytest.raises(ValueError, match="unknown"):
            sw.lifespan_myr(*args)
    with pytest.raises(ValueError, match="unknown"):
        sw.lifespan_myr("lw_rule", "C3", "eq1", lw_line="fixd")
    with pytest.raises(ValueError, match="unknown"):
        sw.factorial("so2_fited")


def test_threshold_at_compensation_point_ignores_the_productivity_curve():
    """At a threshold equal to Pmin, Pi = 0: the time depends on the soil pump
    being off, not on the shape of eq. (8). In the C3-only run it is the
    atmosphere that reaches 10 ppm, long after C3 productivity has stopped."""
    assert ck.co2_time(ck.P_MIN_C4, ck.C3) == pytest.approx(ck.co2_time(ck.P_MIN_C4), abs=1e-9)
    volk = ck.READINGS["volk_p_half"]
    assert ck.co2_time(ck.P_MIN_C4, volk) == pytest.approx(ck.co2_time(ck.P_MIN_C4), abs=1e-9)
    assert ck.co2_time(ck.P_MIN_C3, replace(volk, p_min=ck.P_MIN_C3)) == pytest.approx(
        ck.co2_time(ck.P_MIN_C3, ck.C3), abs=1e-9)


def test_outputs_reproduce(tmp_path):
    sw.main(tmp_path)
    for f in ("cells", "shapley", "co2_steps", "warming", "side"):
        name = f"ingredient_swap_{f}.csv"
        assert (tmp_path / name).read_bytes() == (sw.Path("models/biosphere_lifespan/swap") / name).read_bytes(), name
