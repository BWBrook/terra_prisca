"""Goldblatt, Lenton & Watson (2006), Nature 443, 683-686, doi:10.1038/nature05169.

Three reservoirs: methane M and oxygen O (mol) in the atmosphere and ocean mixed
layer, and organic carbon C (mol) in the crust. Equations (1)-(3) of the
Supplementary Information (SI pp. 8-9), which the article's Methods repeat:

    dM/dt = 1/2 Om (N + r) - s M - 1/2 Psi M^0.7 - 1/2 Om (beta (N + r) - w C)
    dO/dt = Om N - (1 - Om) r - s M - Psi M^0.7 + (1 - Om)(beta (N + r) - w C)
    dC/dt = beta (N + r) - w C

with Om = (1 - gamma)(1 - delta), gamma = O/(d_gamma + O), delta = O/(d_delta + O),
and Psi = 10^(a1 psi^4 + a2 psi^3 + a3 psi^2 + a4 psi + a5), psi = log10 O.

In steady state M = r/s, C = beta (N + r)/w, and O solves
Om N + (Om - 2) r - Psi (r/s)^0.7 = 0 (SI eq. 12), independent of beta.

Readings (each a fixed set of source values, none tuned to a figure):

  faithful          the printed coefficients (four decimals) and s = 2.03e-5 /yr
  author_p          Goldblatt's full-precision coefficients, printed s
  author_corrected  both corrections on Goldblatt's publications page: the
                    full-precision coefficients and s = 3.7e-5 /yr

Interpretive choices shared by every reading:

  PAL     0.2095 mu = 3.714e19 mol. The source never states PAL in moles; mu is
          "the number of moles in the present atmosphere" and O2 is 20.95% of it.
  beta    1e13 / (N_MODERN + R_TODAY) = 2.667e-3. The SI gives beta (N + r) =
          1e13 mol/yr today with C = 1.66e21 mol (hence w = 6e-9 /yr) but never
          beta itself; today's r is the caption's 7.5e10. Steady states do not
          depend on beta; the transients do.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq, minimize_scalar

MU = 1.773e20                 # mol, moles in the present atmosphere (Methods)
O2_FRACTION = 0.2095          # interpretive: PAL = O2_FRACTION * MU
ALPHA = 0.0013                # M, O2 solubility (Methods)
D_GAMMA = 1.36e19             # mol, heterotrophic respiration half-saturation (Methods, SI p. 4)
D_DELTA = 2.73e17             # mol, methanotrophy half-saturation (Methods, SI p. 4)
W = 6e-9                      # /yr, weathering rate constant (SI p. 6)
C_TODAY = 1.66e21             # mol, crustal organic carbon today (SI p. 6)
BURIAL_TODAY = 1e13           # mol/yr, beta (N + r) today (SI p. 6)
N_MODERN = 3.75e15            # mol O2/yr, modern marine net primary productivity (Fig. 2a)
R_TODAY = 7.5e10              # mol O2 equiv./yr, present hydrothermal Fe input (Fig. 2a)
O_VALID = (1e8, 1e20)         # mol, stated validity of the oxidation polynomial
METHANE_EXPONENT = 0.7

COEFFS_PRINTED = (0.0030, -0.1655, 3.2305, -25.8343, 71.5398)
COEFFS_AUTHOR = (0.0030084, -0.1655405, 3.2305351, -25.8343054, 71.5397861)
S_PRINTED = 2.03e-5
S_AUTHOR = 3.7e-5
BETA_SI = BURIAL_TODAY / (N_MODERN + R_TODAY)


@dataclass(frozen=True)
class Reading:
    name: str
    coeffs: tuple[float, ...] = COEFFS_PRINTED
    s: float = S_PRINTED
    beta: float = BETA_SI
    pal_mol: float = O2_FRACTION * MU

    def __post_init__(self):
        if len(self.coeffs) != 5:
            raise ValueError("the oxidation polynomial has five coefficients")
        if not (self.s > 0 and self.beta > 0 and self.pal_mol > 0):
            raise ValueError("s, beta and PAL must be positive")


READINGS = {
    "faithful": Reading("faithful"),
    "author_p": Reading("author_p", coeffs=COEFFS_AUTHOR),
    "author_corrected": Reading("author_corrected", coeffs=COEFFS_AUTHOR, s=S_AUTHOR),
}


def with_beta(reading: Reading, beta: float, suffix: str) -> Reading:
    return replace(reading, name=f"{reading.name}+{suffix}", beta=beta)


def omega(O):
    O = np.asarray(O, dtype=float)
    return (D_GAMMA / (D_GAMMA + O)) * (D_DELTA / (D_DELTA + O))


def psi(O, rd: Reading):
    return 10.0 ** np.polyval(rd.coeffs, np.log10(np.asarray(O, dtype=float)))


def steady_residual(O, N, r, rd: Reading):
    """SI eq. 12: zero at a steady state."""
    om = omega(O)
    return om * N + (om - 2.0) * r - psi(O, rd) * (r / rd.s) ** METHANE_EXPONENT


def n_of_o(O, r, rd: Reading):
    """N that makes O a steady state at fixed r (eq. 12 is linear in N)."""
    om = omega(O)
    return ((2.0 - om) * r + psi(O, rd) * (r / rd.s) ** METHANE_EXPONENT) / om


def r_of_o(O, N, rd: Reading):
    """r that makes O a steady state at fixed N. Eq. 12 falls monotonically in r
    from Om N > 0 at r = 0, so the root is unique."""
    O = np.atleast_1d(np.asarray(O, dtype=float))
    out = np.empty_like(O)
    for i, o in enumerate(O):
        om, ps = float(omega(o)), float(psi(o, rd))
        f = lambda lr: om * N + (om - 2.0) * 10**lr - ps * (10**lr / rd.s) ** METHANE_EXPONENT
        out[i] = 10 ** brentq(f, -10.0, 30.0, xtol=1e-13)
    return out


def rhs(t, y, N, r, rd: Reading):
    M, O, C = y
    om = omega(O)
    ox = psi(O, rd) * max(M, 0.0) ** METHANE_EXPONENT
    x = rd.beta * (N + r) - W * C
    dM = 0.5 * om * (N + r) - rd.s * M - 0.5 * ox - 0.5 * om * x
    dO = om * N - (1.0 - om) * r - rd.s * M - ox + (1.0 - om) * x
    dC = x
    return np.array([dM, dO, dC])


def _log_rhs(t, z, N, r, rd):
    M, O = np.exp(z[0]), np.exp(z[1])
    d = rhs(t, (M, O, z[2]), N, r, rd)
    return np.array([d[0] / M, d[1] / O, d[2]])


def jacobian(y, N, r, rd: Reading):
    """Exact Jacobian of the log-transformed system (log M, log O, C) at a
    steady state, where each f_i/y_i term vanishes. Written analytically
    because central differences of the cancelling fluxes (~4e15 mol/yr) can
    invert the stability of a root very close to a fold."""
    M, O, C = (float(v) for v in y)
    om = float(omega(O))
    dom = -om * (1.0 / (D_GAMMA + O) + 1.0 / (D_DELTA + O))
    ox = float(psi(O, rd)) * M**METHANE_EXPONENT
    dox_dO = ox * float(np.polyval(np.polyder(rd.coeffs), np.log10(O))) / O
    dox_dM = METHANE_EXPONENT * ox / M
    x = rd.beta * (N + r) - W * C
    a = np.array([
        [-rd.s - 0.5 * dox_dM, 0.5 * dom * (N + r) - 0.5 * dox_dO - 0.5 * dom * x, 0.5 * om * W],
        [-rd.s - dox_dM, dom * (N + r) - dox_dO - dom * x, -(1.0 - om) * W],
        [0.0, 0.0, -W],
    ])
    scale = np.array([M, O, 1.0])
    J = a * scale[None, :] / scale[:, None]
    return J


def is_stable(O, N, r, rd: Reading) -> bool:
    y = (r / rd.s, O, rd.beta * (N + r) / W)
    return bool(np.all(np.linalg.eigvals(jacobian(y, N, r, rd)).real < 0))


def _check_domain(lo, hi, extrapolate):
    if not lo < hi:
        raise ValueError(f"O range must ascend: got {lo:.3g} to {hi:.3g} mol")
    if not extrapolate and (lo < O_VALID[0] * (1 - 1e-12) or hi > O_VALID[1] * (1 + 1e-12)):
        raise ValueError(f"O range {lo:.3g}-{hi:.3g} mol leaves the oxidation fit's stated "
                         f"domain {O_VALID[0]:.0e}-{O_VALID[1]:.0e} mol; pass extrapolate=True")


def steady_states(N, r, rd: Reading, lo=O_VALID[0], hi=O_VALID[1], n=6001, extrapolate=False):
    """All roots of eq. 12 in O, ascending, each with its stability.

    The residual is bracketed between its own turning points (grid extrema
    refined by bounded minimisation), so a pair of roots closer together than
    the grid spacing near a fold is still found. By default the search keeps to
    the polynomial's stated domain; outside it the extrapolated quartic is not
    the source's model and can create spurious roots."""
    _check_domain(lo, hi, extrapolate)
    q = np.linspace(np.log10(lo), np.log10(hi), n)
    f = lambda x: float(steady_residual(10.0**x, N, r, rd))
    fq = steady_residual(10.0**q, N, r, rd)
    d = np.diff(fq)
    breaks = [q[0]]
    for i in np.where(np.sign(d[:-1]) != np.sign(d[1:]))[0] + 1:
        sgn = 1.0 if (d[i - 1] < 0 or d[i] > 0) else -1.0   # +1 at a minimum, -1 at a maximum
        res = minimize_scalar(lambda x: sgn * f(x), bounds=(q[i - 1], q[i + 1]), method="bounded",
                              options={"xatol": 1e-13})
        breaks.append(float(res.x))
    breaks.append(q[-1])
    roots = []
    for a, b in zip(breaks[:-1], breaks[1:]):
        fa, fb = f(a), f(b)
        if fa == 0.0:
            roots.append(a)
        elif np.sign(fa) != np.sign(fb) and fb != 0.0:
            roots.append(brentq(f, a, b, xtol=1e-15))
    if f(breaks[-1]) == 0.0:
        roots.append(breaks[-1])
    roots = sorted(roots)
    roots = [x for i, x in enumerate(roots) if i == 0 or x - roots[i - 1] > 1e-12]
    return [(10.0**x, is_stable(10.0**x, N, r, rd)) for x in roots]


def branch_curve(rd: Reading, *, N=None, r=None, o_mol=O_VALID, n=4001, extrapolate=False):
    """Steady-state curve traced parametrically in O (mol): returns O, the free
    parameter (r if N is fixed, N if r is fixed), and stability at each point.
    The default O range is the oxidation fit's stated domain."""
    if (N is None) == (r is None):
        raise ValueError("fix exactly one of N and r")
    _check_domain(*o_mol, extrapolate)
    O = np.logspace(np.log10(o_mol[0]), np.log10(o_mol[1]), n)
    if N is not None:
        free = r_of_o(O, N, rd)
        stable = np.array([is_stable(o, N, x, rd) for o, x in zip(O, free)])
    else:
        free = n_of_o(O, r, rd)
        stable = np.array([is_stable(o, x, r, rd) for o, x in zip(O, free)])
    return O, free, stable


def folds(O, free):
    """Interior extrema of the free parameter along the curve: (O, value) pairs."""
    lf = np.log10(free)
    d = np.diff(lf)
    idx = np.where(np.sign(d[:-1]) != np.sign(d[1:]))[0] + 1
    return [(float(O[i]), float(free[i])) for i in idx]


def lowest_stable(N, r, rd: Reading) -> float:
    st = [o for o, ok in steady_states(N, r, rd) if ok]
    if not st:
        raise ValueError("no stable steady state")
    return st[0]


@dataclass(frozen=True)
class Run:
    t: np.ndarray          # yr after the step
    M: np.ndarray
    O: np.ndarray
    C: np.ndarray
    N: float
    r: float


def step(rd: Reading, *, N0, r0, N1, r1, t_end=4e8, t_eval=None, rtol=1e-10, atol=1e-12) -> Run:
    """Start at the lowest stable steady state of (N0, r0), with C in balance,
    and integrate after a step to (N1, r1) at t = 0."""
    O0 = lowest_stable(N0, r0, rd)
    y0 = np.array([np.log(r0 / rd.s), np.log(O0), rd.beta * (N0 + r0) / W])
    if t_eval is None:
        t_eval = np.concatenate([[0.0], np.logspace(-3, np.log10(t_end), 3000)])
    t_eval = np.clip(t_eval, 0.0, t_end)
    sol = solve_ivp(_log_rhs, (0.0, t_end), y0, args=(N1, r1, rd), method="Radau",
                    t_eval=t_eval, rtol=rtol, atol=atol)
    if not sol.success:
        raise RuntimeError(sol.message)
    return Run(sol.t, np.exp(sol.y[0]), np.exp(sol.y[1]), sol.y[2], N1, r1)


def budget(run: Run, rd: Reading) -> dict[str, np.ndarray]:
    """Redox budget of the surface system in mol O2 equiv./yr (Fig. 3b, d):
    d(O - 2M)/dt = s M + (beta (N + r) - w C) - r."""
    escape = rd.s * run.M
    burial = rd.beta * (run.N + run.r) - W * run.C
    inp = -run.r * np.ones_like(run.t)
    return {"escape": escape, "burial": burial, "input": inp, "net": escape + burial + inp}
