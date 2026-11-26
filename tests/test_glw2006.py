import numpy as np
import pytest

from terra_prisca.goldblatt_lenton_watson import fidelity_glw2006 as F
from terra_prisca.goldblatt_lenton_watson import glw2006 as g
from terra_prisca.goldblatt_lenton_watson import vectors as V

P = g.READINGS["author_p"]


@pytest.fixture(scope="module")
def vec():
    return V.load()


@pytest.fixture(scope="module")
def frames():
    return F.frames()


@pytest.fixture(scope="module")
def si():
    return V.load(V.SI_OUT)


def test_reading_validation():
    with pytest.raises(ValueError):
        g.Reading("bad", coeffs=(1.0, 2.0))
    with pytest.raises(ValueError):
        g.Reading("bad", s=-1.0)


def test_steady_state_satisfies_full_equations():
    for o, _ in g.steady_states(g.N_MODERN, 3e11, P):
        y = (3e11 / P.s, o, P.beta * (g.N_MODERN + 3e11) / g.W)
        d = g.rhs(0, y, g.N_MODERN, 3e11, P)
        assert abs(d[0]) / (3e11) < 1e-9 and abs(d[1]) / (3e11) < 1e-9 and abs(d[2]) < 1e-3


def test_three_states_in_bistable_region_with_middle_unstable():
    ss = g.steady_states(g.N_MODERN, 3e11, P)
    assert [ok for _, ok in ss] == [True, False, True]
    assert ss[0][0] / P.pal_mol == pytest.approx(1.28e-6, rel=0.02)


def test_printed_coefficients_lose_low_branch_at_bif_reductant():
    ss = g.steady_states(g.N_MODERN, 3e11, g.READINGS["faithful"])
    assert len(ss) == 1 and ss[0][0] / P.pal_mol > 0.1


def test_steady_state_independent_of_beta():
    a = g.steady_states(g.N_MODERN, 3e11, P)
    b = g.steady_states(g.N_MODERN, 3e11, g.with_beta(P, 0.01, "x"))
    assert np.allclose([o for o, _ in a], [o for o, _ in b])


def test_r_of_o_and_n_of_o_invert_eq12():
    O = np.logspace(10, 19, 7)
    r = g.r_of_o(O, g.N_MODERN, P)
    assert np.allclose(g.steady_residual(O, g.N_MODERN, r, P) / g.N_MODERN, 0, atol=1e-10)
    N = g.n_of_o(O, 7.5e10, P)
    assert np.allclose(g.steady_residual(O, N, 7.5e10, P) / N, 0, atol=1e-10)


def test_branch_curve_requires_exactly_one_fixed():
    with pytest.raises(ValueError):
        g.branch_curve(P)
    with pytest.raises(ValueError):
        g.branch_curve(P, N=1.0, r=1.0)


def test_low_state_found_next_to_the_lower_fold():
    # Codex GLW-R7: just inside the lower fold the two low roots are 0.2% apart.
    ss = g.steady_states(g.N_MODERN, 1.336945416659e11, P)
    assert [ok for _, ok in ss] == [True, False, True]
    assert ss[0][0] / P.pal_mol == pytest.approx(1.9900415e-5, rel=1e-6)
    assert g.lowest_stable(g.N_MODERN, 1.336945416659e11, P) == ss[0][0]


def test_pair_found_next_to_the_upper_fold():
    O, free, _ = g.branch_curve(P, N=g.N_MODERN, n=8001)
    o_fold, r_fold = max(g.folds(O, free), key=lambda t: t[0])
    ss = g.steady_states(g.N_MODERN, r_fold * (1 - 1e-6), P)
    assert len(ss) == 3 and [ok for _, ok in ss] == [True, False, True]


def test_stability_matches_residual_slope():
    for r in (1.336945416659e11, 3e11, 5.5e11):
        for o, ok in g.steady_states(g.N_MODERN, r, P):
            d = g.steady_residual(o * (1 + 1e-7), g.N_MODERN, r, P) - g.steady_residual(o * (1 - 1e-7), g.N_MODERN, r, P)
            assert ok == (d < 0)


def test_solver_keeps_to_the_fit_domain():
    with pytest.raises(ValueError):
        g.steady_states(g.N_MODERN, 3e11, P, hi=1e21)
    with pytest.raises(ValueError):
        g.branch_curve(P, N=g.N_MODERN, o_mol=(1e7, 1e19))
    with pytest.raises(ValueError):
        g.steady_states(g.N_MODERN, 1e6, P, lo=1.7e20, hi=9e19)
    with pytest.raises(ValueError):
        g.branch_curve(P, r=7.5e10, o_mol=(1.7e20, 9e19))
    assert all(o <= g.O_VALID[1] for o, _ in g.steady_states(g.N_MODERN, 1e6, P))
    assert g.branch_curve(P, N=g.N_MODERN, o_mol=(1e7, 1e19), n=11, extrapolate=True)[0][0] == pytest.approx(1e7)


def test_budget_closes_on_o_minus_2m():
    run = g.step(P, N0=g.N_MODERN, r0=3e11, N1=g.N_MODERN, r1=7.5e10, t_end=2e6)
    net = g.budget(run, P)["net"]
    change = (run.O[-1] - 2 * run.M[-1]) - (run.O[0] - 2 * run.M[0])
    assert np.trapezoid(net, run.t) == pytest.approx(change, rel=1e-3)


def test_vectors_counted_once(vec):
    counts = {k: len(v) for k, v in vec.items() if k[0] == "2"}
    assert counts[("2", "a", "solid", "lower")] == 441
    assert counts[("2", "b", "dashed", "unstable")] == 44
    assert len(counts) == 12


def test_author_p_reproduces_fig2(vec, frames):
    for (panel, curve), (fixed, value) in F.FIG2_CASES.items():
        val = F.CAPTION_R_TENFOLD if (panel, curve) == ("b", "dashed") else value
        fr = frames[("2", panel)]
        runs = F.model2(P, fixed, val, fr, n=1501)[0]
        sc = F.score(F.printed2(vec, panel, curve), runs, F.scale(fr), 1)
        assert sc["printed_to_model_pt"] < 0.05 and sc["model_to_printed_pt"] < 0.05


def test_fig2b_dashed_is_not_r_3e10(vec, frames):
    fr = frames[("2", "b")]
    runs = F.model2(P, "r", 3e10, fr, n=1501)[0]
    assert F.score(F.printed2(vec, "b", "dashed"), runs, F.scale(fr), 1)["printed_to_model_pt"] > 5


def test_faithful_misses_fig2(vec, frames):
    fr = frames[("2", "a")]
    runs = F.model2(g.READINGS["faithful"], "N", g.N_MODERN, fr, n=1501)[0]
    assert F.score(F.printed2(vec, "a", "solid"), runs, F.scale(fr), 1)["printed_to_model_pt"] > 5


def test_clip_splits_a_curve_that_leaves_the_frame():
    p = np.array([[0.0, 0.0], [2.0, 2.0], [4.0, 0.0]])
    runs = F.clip_runs(p, (0.0, 4.0, 0.0, 1.0))
    assert len(runs) == 2
    assert np.allclose(runs[0], [[0, 0], [1, 1]]) and np.allclose(runs[1], [[3, 1], [4, 0]])


def test_score_does_not_join_separate_branches():
    a, b = np.array([[0.0, 0.0], [1.0, 0.0]]), np.array([[0.0, 5.0], [1.0, 5.0]])
    joined = [np.vstack([a, b])]
    assert F.score([a, b], [a, b], (10, 10), None)["printed_to_model_pt"] == pytest.approx(0, abs=1e-12)
    assert F.score(joined, [a, b], (10, 10), None)["printed_to_model_pt"] > 1


def test_score_excludes_a_gap_in_the_model_from_both_directions():
    printed = [np.array([[0.0, 0.0], [10.0, 0.0]])]
    model = [np.array([[0.0, 0.0], [4.0, 0.0]]), np.array([[6.0, 1.0], [10.0, 1.0]])]
    sc = F.score(printed, model, (1, 1), 0)
    assert sc["printed_unmatched_pt"] == pytest.approx(2.0, abs=0.02)
    assert sc["printed_to_model_pt"] == pytest.approx(np.sqrt(0.5), rel=1e-3)


def test_out_of_frame_excursion_counts_as_unmatched(vec, frames):
    # Codex GLW-R3: author_corrected escape leaves the Fig. 3d zoom frame.
    rd = F.replace(g.READINGS["author_corrected"], beta=F.beta_from_fig3d(vec))
    fr = frames[("3", "d_zoom")]
    m = F.clip_runs(F.model3(rd, F.run_case(rd, "c", 1e6), "escape", fr), F.box(fr))
    sc = F.score([vec[("3", "d_zoom", "escape", "trace")]], m, F.scale(fr), 0)
    assert len(m) == 2 and sc["printed_unmatched_pt"] > 25


def test_fig2_branches_scored_separately(vec, frames):
    fr = frames[("2", "b")]
    br = F.model2_branches(F.model2_points(P, "r", 7.5e10)[0])
    parts = dict(zip(F.FIG2_PARTS, F.printed2(vec, "b", "solid")))
    for part in F.FIG2_PARTS:
        sc = F.score([parts[part]], F.clip_runs(br[part], F.box(fr)), F.scale(fr), 1)
        assert sc["printed_to_model_pt"] < 0.06 and sc["model_to_printed_pt"] < 0.06


def test_si_fig_s2_triangles_read_at_their_data_points(si):
    assert si[("S2", "", "1 PAL", "markers")][0] == pytest.approx([14.47723, 13.70683], abs=2e-5)


def test_flat_trace_scores_zero_against_its_own_null(vec, frames):
    fr = frames[("3", "d")]
    p = vec[("3", "d", "input", "trace")]
    flat = np.array([[fr["x_left"], p[0, 1]], [fr["x_right"], p[0, 1]]])
    sc = F.score([p], F.clip_runs(flat, F.box(fr)), F.scale(fr), 0)
    assert sc["printed_to_model_pt"] < 1e-9 and sc["model_to_printed_pt"] < 1e-9


def test_right_axis_is_close_to_partial_pressure(frames):
    for pn in ("a", "a_zoom", "c", "c_zoom"):
        assert 0.18 < 10 ** frames[("3", pn)]["right_at_left_zero"] < 0.21
        assert frames[("3", pn)]["right_per_left"] == pytest.approx(1.0, abs=0.002)


def test_beta_from_fig3d(vec):
    assert F.beta_from_fig3d(vec) == pytest.approx(2.0e-3, rel=0.03)


def test_delta13c_arithmetic():
    f1 = 0.2 * 1.03
    assert (-6 + f1 * 30) / (1 - f1) == pytest.approx(0.2267, abs=1e-4)


def test_fig3d_beta_also_fits_fig3c_oxygen(vec, frames):
    from dataclasses import replace

    p = vec[("3", "c", "oxygen", "trace")]
    fr = frames[("3", "c")]

    def score(beta):
        rd = replace(P, beta=beta)
        run = F.run_case(rd, "c", 4e8)
        m = F.clip_runs(F.model3(rd, run, "oxygen", fr), F.box(fr))
        return F.score([p], m, F.scale(fr), 0)["printed_to_model_pt"]

    assert score(F.beta_from_fig3d(vec)) < 0.1
    assert score(g.BETA_SI) > 0.3


def test_si_fig_s2_slopes_recover_stated_exponents(si):
    for level, n in (("1 PAL", 0.58), ("0.1 PAL", 0.75), ("0.01 PAL", 0.70)):
        v = si[("S2", "", level, "markers")]
        assert np.polyfit(v[:, 0], v[:, 1], 1)[0] == pytest.approx(n, abs=0.005)


def test_si_fig_s3_line_is_half_of_psi(si):
    line = si[("S3", "", "fit", "line")]
    d = line[:, 1] - np.polyval(g.COEFFS_AUTHOR, line[:, 0])
    assert d.mean() == pytest.approx(-np.log10(2), abs=0.005) and d.std() < 0.005


def test_si_only_quartic_recovers_bistable_range(si):
    folds = []
    for rd in (P, F.si_reading(si)):
        O, free, _ = g.branch_curve(rd, N=g.N_MODERN, n=4001)
        folds.append(sorted(r for _, r in g.folds(O, free)))
    assert np.allclose(folds[0], folds[1], rtol=0.01)


def test_catling_escape_coefficient():
    assert F.catling_s() == pytest.approx(3.7e-5, rel=0.02)


def test_kasting_fit_transcription():
    # Kasting et al. (2001), p. 273: above 1e-4 CH4, Ts can exceed freezing at today's pCO2.
    assert 273 < F.kasting_ts(1e-4, 3.5e-4) < 277


def test_methane_falls_about_twofold_at_the_oxygen_crossing():
    rd = g.with_beta(P, 2.0e-3, "fig3d")
    ev = F.methane_events(F.run_case(rd, "a", 4e8), F.run_case(rd, "a", 1e6), rd)
    assert ev["fall_cross"] == pytest.approx(2.138, abs=0.01)
    assert ev["t_cross"] == pytest.approx(1.26e5, rel=0.02)


def test_stability_exact_just_inside_lower_fold():
    # Gemini GLW-G2: finite differences inverted the low pair here.
    ss = g.steady_states(g.N_MODERN, 1.336945282964e11 * (1 + 2e-12), P)
    assert [ok for _, ok in ss] == [True, False, True]
    assert ss[0][0] / P.pal_mol == pytest.approx(1.992e-5, rel=1e-3)


def test_analytic_jacobian_matches_differences():
    r = 3e11
    for o, _ in g.steady_states(g.N_MODERN, r, P):
        y = (r / P.s, o, P.beta * (g.N_MODERN + r) / g.W)
        z = np.array([np.log(y[0]), np.log(y[1]), y[2]])
        fd = np.empty((3, 3))
        for j in range(3):
            dz = np.zeros(3)
            dz[j] = 1e-5 if j < 2 else 1e-5 * abs(z[2])
            fd[:, j] = (g._log_rhs(0, z + dz, g.N_MODERN, r, P) - g._log_rhs(0, z - dz, g.N_MODERN, r, P)) / (2 * dz[j])
        assert np.allclose(g.jacobian(y, g.N_MODERN, r, P), fd, rtol=1e-6, atol=1e-12)
