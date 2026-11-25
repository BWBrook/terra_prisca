import numpy as np
import pytest

from terra_prisca.goldblatt_lenton_watson import fidelity_glw2006 as F
from terra_prisca.goldblatt_lenton_watson import glw2006 as g
from terra_prisca.goldblatt_lenton_watson import vectors as V

P = g.READINGS["author_p"]


@pytest.fixture(scope="module")
def vec():
    return V.load()


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


def test_author_p_reproduces_fig2(vec):
    for (panel, curve), (fixed, value) in F.FIG2_CASES.items():
        val = F.CAPTION_R_TENFOLD if (panel, curve) == ("b", "dashed") else value
        m, _, _ = F.model2(P, fixed, val, panel, n=1501)
        assert F.two_way(F.printed2(vec, panel, curve), m, F.SCALE2)[0] < 0.15


def test_fig2b_dashed_is_not_r_3e10(vec):
    m, _, _ = F.model2(P, "r", 3e10, "b", n=1501)
    assert F.two_way(F.printed2(vec, "b", "dashed"), m, F.SCALE2)[0] > 5


def test_faithful_misses_fig2(vec):
    m, _, _ = F.model2(g.READINGS["faithful"], "N", g.N_MODERN, "a", n=1501)
    assert F.two_way(F.printed2(vec, "a", "solid"), m, F.SCALE2)[0] > 5


def test_beta_from_fig3d(vec):
    assert F.beta_from_fig3d(vec) == pytest.approx(2.0e-3, rel=0.03)


def test_delta13c_arithmetic():
    f1 = 0.2 * 1.03
    assert (-6 + f1 * 30) / (1 - f1) == pytest.approx(0.2267, abs=1e-4)


def test_fig3d_beta_also_fits_fig3c_oxygen(vec):
    from dataclasses import replace

    p = vec[("3", "c", "oxygen", "trace")]
    sc = np.array(F.SCALE3["c"])

    def score(beta):
        rd = replace(P, beta=beta)
        run = F.run_case(rd, "c", 4e8)
        m = F._clip(F.model3(rd, run, "oxygen", "c", "PAL"), "c")
        return F.two_way(p, F.densify(m * sc, 0.01) / sc, F.SCALE3["c"])[0]

    assert score(F.beta_from_fig3d(vec)) < 0.1
    assert score(g.BETA_SI) > 0.3
