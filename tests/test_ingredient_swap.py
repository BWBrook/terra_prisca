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
    w = {(r["plants"], r["P_atm_ppm"]): r for r in sw.warming() if r["reading"] == "faithful"}
    assert w[("C4", 20.0)]["T_minus_T0_K"] == pytest.approx(6.197, abs=1e-3)
    assert w[("C4", 20.0)]["Pi_ratio"] == pytest.approx(0.0903, abs=1e-4)
    assert w[("C4", 10.0)]["T_minus_T0_K"] == pytest.approx(8.346, abs=1e-3)
    fit = {(r["plants"], r["P_atm_ppm"]): r for r in sw.warming() if r["reading"] == "so2_fitted"}
    assert fit[("C3", 150.0)]["T_minus_T0_K"] == pytest.approx(9.036, abs=1e-3)
    assert fit[("C4", 10.0)]["T_minus_T0_K"] == pytest.approx(12.045, abs=1e-3)
    # the constant-T steps hold T at T0 exactly (closed form)
    for p in ("C3", "C4"):
        thr = sw.PLANTS[p][1] * sw.PPM
        assert ck.temperature(sw.constant_T_s_star(thr) * ck.S0, thr) == pytest.approx(ck.t0(), abs=1e-8)
        assert steps[(p, "ck_constant_T_pump_held")]["T_minus_T0_K"] == 0.0


def test_abiotic_baseline():
    """IS-A2: with no soil pump (Psoil = Patm), C&K's chemistry reaches the
    limits sooner and warms less; the responsive pump adds about 6 K."""
    side = {(r["so2"], r["plants"][:2]): r for r in sw.side_branches()
            if r["branch"] == sw.SIDE["ck_no_pump"] and r["sun"] == sw.SUNS["eq1"]}
    assert side[("faithful", "C3")]["time_to_limit_Myr"] == pytest.approx(189.069, abs=1e-3)
    assert side[("faithful", "C4")]["time_to_limit_Myr"] == pytest.approx(575.939, abs=1e-3)
    assert side[("no_so2", "C4")]["time_to_limit_Myr"] == pytest.approx(853.942, abs=1e-3)
    assert side[("faithful", "C4")]["T_minus_T0_K"] == pytest.approx(2.378, abs=1e-3)
    r = sw._reading("ck_no_pump", "C4")
    assert ck.weathering(ck.P0, ck.S0, r) == pytest.approx(1.0, abs=1e-9)  # normalised today
    assert sw.lifespan_myr("ck_biology", "C3", "eq1") / side[("faithful", "C3")]["time_to_limit_Myr"] == pytest.approx(2.237, abs=1e-3)


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
    assert sw.lw_rule_s_star(400.0, lw.luminosity) == 1.0
    with pytest.raises(ValueError):
        sw.lw_rule_s_star(0.0, lw.luminosity)
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
    # a side-row label is not a law
    with pytest.raises(ValueError, match="unknown"):
        sw.lifespan_myr("c4_productivity_at_150", "C4", "eq1")
    side = [r for r in sw.side_branches() if r["branch"] == sw.SIDE["c4_productivity_at_150"] and r["sun"] == sw.SUNS["eq1"]]
    assert side[0]["time_to_limit_Myr"] == pytest.approx(sw.lifespan_myr("ck_biology", "C4", "eq1", threshold_ppm=150.0))
    assert side[0]["time_to_limit_Myr"] == pytest.approx(192.878, abs=1e-3)


def test_threshold_at_compensation_point_ignores_the_productivity_curve():
    """At a threshold equal to Pmin, Pi = 0: the time depends on the soil pump
    being off, not on the shape of eq. (8). In the C3-only run it is the
    atmosphere that reaches 10 ppm, long after C3 productivity has stopped."""
    assert ck.co2_time(ck.P_MIN_C4, ck.C3) == pytest.approx(ck.co2_time(ck.P_MIN_C4), abs=1e-9)
    volk = ck.READINGS["volk_p_half"]
    assert ck.co2_time(ck.P_MIN_C4, volk) == pytest.approx(ck.co2_time(ck.P_MIN_C4), abs=1e-9)
    assert ck.co2_time(ck.P_MIN_C3, replace(volk, p_min=ck.P_MIN_C3)) == pytest.approx(
        ck.co2_time(ck.P_MIN_C3, ck.C3), abs=1e-9)
    # below Pmin too: Pi stays 0, so the C3 run reaches 100 ppm at one time under both curves
    assert ck.co2_time(100e-6, replace(volk, p_min=ck.P_MIN_C3)) == pytest.approx(ck.co2_time(100e-6, ck.C3), abs=1e-9)
    assert ck.co2_time(100e-6, ck.C3) * 1e3 == pytest.approx(494.160, abs=1e-3)


def test_outputs_reproduce(tmp_path):
    sw.main(tmp_path)
    for f in ("cells", "shapley", "co2_steps", "warming", "side"):
        name = f"ingredient_swap_{f}.csv"
        assert (tmp_path / name).read_bytes() == (sw.Path("models/biosphere_lifespan/swap") / name).read_bytes(), name


def test_sun_effect_on_the_lw_face_is_mostly_past_curvature():
    """GA-R4: continuing eq. (1) along its present tangent isolates the
    refitted past; the curvature ahead adds a little more."""
    eq1 = lambda t_myr: sw.brightness(t_myr / 1000.0, "eq1")
    slope = 0.38 / 4.55
    for plants, past, ahead in (("C3", 0.77381, 0.99485), ("C4", 0.77381, 0.98668)):
        thr = sw.PLANTS[plants][1]
        s = sw.lw_rule_s_star(thr, eq1)
        tangent = (s - 1.0) / slope * 1000.0
        assert tangent / sw.lifespan_myr("lw_rule", plants, "straight") == pytest.approx(past, abs=1e-5)
        assert sw.lifespan_myr("lw_rule", plants, "eq1") / tangent == pytest.approx(ahead, abs=1e-5)
