"""Sellers (1969): a global climatic model based on the energy balance of the
earth-atmosphere system. J. Appl. Meteorol. 8, 392-400.
doi:10.1175/1520-0450(1969)008<0392:AGCMBO>2.0.CO;2

Eighteen 10-degree belts from 90N to 90S. In each belt the absorbed solar
radiation minus the infrared emission (eqs 4-6) is balanced by the divergence
of the poleward transport of latent heat, atmospheric sensible heat and ocean
heat across the 17 bounding latitude circles (eqs 1-2, 7-13). The inputs are
the paper's Tables 1 and 2. Interpretive choices are named in `Reading` and
documented in models/budyko_sellers/README.md.

Units follow the paper: cgs, calories, temperatures in K inside the model.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path

import numpy as np
from scipy.optimize import brentq, root

# --- Table 1 and Table 2, transcribed from the scan (belts 80-90N .. 80-90S) ---
BELT_B = np.array([2.924, 2.927, 2.878, 2.891, 2.908, 2.870, 2.826, 2.809, 2.808,
                   2.801, 2.798, 2.815, 2.865, 2.922, 2.937, 2.989, 2.992, 2.900])
BELT_Z = np.array([137, 220, 202, 296, 382, 496, 366, 146, 158,
                   154, 121, 156, 106, 5, 5, 388, 1420, 2272], dtype=float)
BELT_ALPHA_D = np.array([0.376, 0.379, 0.330, 0.343, 0.360, 0.322, 0.278, 0.261, 0.260,
                         0.253, 0.250, 0.267, 0.317, 0.374, 0.389, 0.441, 0.444, 0.352])
BELT_QS = np.array([135.7, 145.1, 167.3, 202.2, 237.7, 269.0, 293.9, 311.1, 319.8,
                    319.8, 311.1, 293.9, 269.0, 237.7, 202.2, 167.3, 145.1, 135.7])  # kly/yr
# circles 80N .. 80S
CIRC_DP = np.array([709, 710, 713, 750, 800, 833, 880, 904, 906,
                    904, 880, 833, 800, 750, 713, 710, 709], dtype=float)  # mb
CIRC_DZ = np.array([2, 1, 2, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 3, 0], dtype=float)  # km
CIRC_KH = np.array([1.9, 1.2, 1.7, 1.5, 0.9, 1.3, 10.3, 133.2, 68.2,
                    30.8, 8.5, 2.3, 2.3, 1.9, 1.4, 1.0, 0.5]) * 1e10  # cm2/s
CIRC_KW = np.array([4.6, 2.0, 2.5, 5.9, 5.1, 2.9, 2.2, 34.4, 16.3,
                    0.6, 0.8, 4.3, 11.9, 12.8, 8.2, 7.4, 6.3]) * 1e9
CIRC_K0 = np.array([0.7, 6.6, 6.9, 7.6, 5.3, 9.6, 13.3, 59.9, 7.0,
                    19.0, 9.5, 5.1, 2.9, 1.8, 0.5, 0.2, 0.0]) * 1e6
CIRC_A = np.array([0.5, 1.0, 1.0, 1.0, 1.0, 2.0, 3.0, 3.0, 3.0,
                   3.0, 3.0, 2.0, 1.0, 1.0, 1.0, 0.5, 0.5])  # cm/s/K

BELT_EDGES = np.arange(90.0, -91.0, -10.0)
BELT_LAT = 0.5 * (BELT_EDGES[:-1] + BELT_EDGES[1:])
CIRC_LAT = BELT_EDGES[1:-1]
NB, NC = 18, 17

YEAR_S = 365.25 * 86400.0
KLY_YR = 1000.0 / YEAR_S  # kly/yr -> cal cm-2 s-1
SIGMA = 1.356e-12  # ly s-1 K-4
L_COND = 590.0  # cal/g
EPS = 0.622
P_SURF = 1000.0  # mb
R_D = 6.8579e-2  # cal g-1 K-1
CP = 0.24
DY = 1.11e8  # cm
R_EARTH = 6.371e8  # cm
T_THRESH = 283.16
ALPHA_MAX = 0.85
S_NOW = 2.00
ICE_GUESS = 175.0  # K; fallback start for the ice-covered branch

_DATA = Path(__file__).with_name("data") / "ocean_fraction.csv"


def _ocean(kind: str) -> np.ndarray:
    tab = np.genfromtxt(_DATA, delimiter=",", names=True)
    return np.asarray(tab["ocean_" + kind], dtype=float)


AREA = 2 * np.pi * R_EARTH**2 * np.abs(np.diff(np.sin(np.radians(BELT_EDGES))))
LEN = 2 * np.pi * R_EARTH * np.cos(np.radians(CIRC_LAT))
HEMI = np.where(CIRC_LAT > 5.0, 1.0, -1.0)  # eq. (8a) north of 5N, (8b) otherwise


@dataclass(frozen=True)
class Reading:
    """Choices the paper leaves open. Defaults are the faithful reading."""

    ocean: str = "circle"  # l'/l1 at the circle itself, or "band" (+-5 deg mean)
    vapour: str = "cc"  # Clausius-Clapeyron with Sellers' L, eps, R_d; or "tetens"
    vt_kelvin: bool = True  # T in v*T0 of eq. (12) in K; False for deg C
    grad_mean: str = "global"  # |dT| mean over all circles, or "hemisphere"


@dataclass(frozen=True)
class Scenario:
    """An experiment: solar constant, transport multipliers, albedo law."""

    s: float = S_NOW
    k_mult: float = 1.0  # multiplies a, K_h, K_w and K_0 together
    m: float = 0.5
    law: str = "0.009"  # "0.009", "0.005", "0.005-anchored", "fixed"
    fixed_albedo: dict = field(default_factory=dict)  # belt index -> albedo held fixed
    heat: np.ndarray | None = None  # added heating per belt, cal cm-2 s-1 of belt area
    dqs: np.ndarray | None = None  # reduction of incoming solar per belt, cal cm-2 s-1


class Sellers1969:
    def __init__(self, reading: Reading = Reading()):
        self.r = reading
        self.ocean = _ocean(reading.ocean)
        self._present = None

    # --- radiation, eqs (4)-(6) ---
    def sat_vapour(self, t):
        if self.r.vapour == "tetens":
            return 6.1078 * np.exp(17.27 * (t - 273.16) / (t - 35.86))
        return 6.11 * np.exp(EPS * L_COND / R_D * (1.0 / 273.16 - 1.0 / t))

    def emission(self, t, m=0.5):
        return SIGMA * t**4 * (1.0 - m * np.tanh(19.0 * t**6 * 1e-16))

    def albedo(self, t, sc: Scenario):
        tg = t - 0.0065 * BELT_Z
        if sc.law == "fixed":
            a = self.present_albedo().copy()
        elif sc.law == "0.009":
            # eqs (5a, 5b). Table 1 gives b - alpha_d = 2.548 where 0.009 * 283.16 = 2.54844; taking the
            # larger of the two keeps the law continuous (the switch moves by 0.05 K).
            a = np.maximum(BELT_B - 0.009 * tg, BELT_ALPHA_D)
        elif sc.law == "0.005":
            a = np.where(tg < T_THRESH, BELT_ALPHA_D + 0.005 * (T_THRESH - tg), BELT_ALPHA_D)
        elif sc.law == "0.005-anchored":
            a0, tg0 = self.present_albedo(), self.present()["T"] - 0.0065 * BELT_Z
            b5 = np.where(tg0 < T_THRESH, a0 + 0.005 * tg0, BELT_ALPHA_D + 0.005 * T_THRESH)
            a = np.where(tg < T_THRESH, b5 - 0.005 * tg, BELT_ALPHA_D)
        else:
            raise ValueError(sc.law)
        a = np.minimum(a, ALPHA_MAX)
        for i, v in sc.fixed_albedo.items():
            a[i] = v
        return a

    def absorbed(self, t, sc: Scenario):
        q = BELT_QS * KLY_YR * sc.s / S_NOW
        if sc.dqs is not None:
            q = q - sc.dqs
        return q * (1.0 - self.albedo(t, sc))

    def net_radiation(self, t, sc: Scenario):
        rs = self.absorbed(t, sc) - self.emission(t, sc.m)
        if sc.heat is not None:
            rs = rs + sc.heat
        return rs

    # --- transport, eqs (7)-(13) ---
    def grad_mean(self, dt):
        w = LEN
        if self.r.grad_mean == "global":
            return np.full(NC, np.sum(np.abs(dt) * w) / np.sum(w))
        north = HEMI > 0
        gn = np.sum(np.abs(dt[north]) * w[north]) / np.sum(w[north])
        gs = np.sum(np.abs(dt[~north]) * w[~north]) / np.sum(w[~north])
        return np.where(north, gn, gs)

    def transport(self, t_north, dt, g, sc: Scenario):
        """Northward transports per unit length of circle (cal cm-1 s-1):
        latent Lc, sensible C, ocean F, and the wind v (cm/s)."""
        km = sc.k_mult
        k = EPS * L_COND / (R_D * t_north**2)
        e = self.sat_vapour(t_north) * (1.0 - 0.5 * k * dt)
        q = EPS * e / P_SURF
        dq = EPS * k * e * dt / P_SURF
        v = -km * CIRC_A * (dt + HEMI * g)
        lc = L_COND * (v * q - km * CIRC_KW * dq / DY) * CIRC_DP
        tv = t_north if self.r.vt_kelvin else t_north - 273.16
        c = (v * tv - km * CIRC_KH * dt / DY) * CP * CIRC_DP
        f = -km * CIRC_K0 * CIRC_DZ * 1e5 * self.ocean * dt / DY
        return {"Lc": lc, "C": c, "F": f, "P": lc + c + f, "v": v}

    def fluxes(self, t, sc: Scenario):
        dt = t[:-1] - t[1:]
        return self.transport(t[:-1], dt, self.grad_mean(dt), sc)

    def residual(self, t, sc: Scenario):
        """Belt energy balance, eq. (2), in kly/yr per unit belt area."""
        return self.net_radiation(t, sc) / KLY_YR - self.export(self.fluxes(t, sc)["P"])

    @staticmethod
    def export(p):
        """Net export from each belt (kly/yr per unit belt area) of a northward
        transport p per unit length: out across the north circle minus in from the south."""
        pl = p * LEN
        return (np.r_[0.0, pl] - np.r_[pl, 0.0]) / AREA / KLY_YR

    # --- solution ---
    def solve(self, sc: Scenario = Scenario(), guess=None):
        if guess is None:
            guess = self.present()["T"] if self._present is not None else 300.0 - 50.0 * np.sin(np.radians(BELT_LAT)) ** 2
        g0 = np.asarray(guess, dtype=float)
        # The albedo law has a kink at 283.16 K, where hybr can stall; retry with
        # Levenberg-Marquardt, then from colder starts (other branches).
        tries = [(g0, "hybr"), (g0, "lm"), (g0 + 0.3, "hybr"), (g0 - 10.0, "hybr"), (g0 - 25.0, "hybr"),
                 (g0 - 50.0, "hybr"), (np.full(NB, ICE_GUESS), "hybr")]
        for g, method in tries:
            opts = {"xtol": 1e-11} if method == "hybr" else {"xtol": 1e-12, "ftol": 1e-14}
            sol = root(self.residual, g, args=(sc,), method=method, options=opts)
            ok = np.all(np.isfinite(sol.x)) and np.max(np.abs(self.residual(sol.x, sc))) < 1e-6
            if ok:
                break
        return self._state(sol.x, sc, ok)

    def growth_rates(self, t, sc: Scenario = Scenario(), dt: float = 1e-3) -> np.ndarray:
        """Eigenvalues of the Jacobian of the belt balances at state t, largest real part first.

        Sellers solves for steady states only. With equal, positive heat capacity in
        every belt, dT/dt is proportional to the residual, so a positive real part
        marks an equilibrium that thermal relaxation would leave. Central differences."""
        t = np.asarray(t, dtype=float)
        jac = np.empty((NB, NB))
        for j in range(NB):
            e = np.zeros(NB)
            e[j] = dt
            jac[:, j] = (self.residual(t + e, sc) - self.residual(t - e, sc)) / (2 * dt)
        ev = np.linalg.eigvals(jac)
        return ev[np.argsort(-ev.real)]

    def _state(self, t, sc, ok=True):
        fl = self.fluxes(t, sc)
        return {"T": t, "Tc": t - 273.16, "albedo": self.albedo(t, sc), "Rs": self.net_radiation(t, sc),
                "Tbar": float(np.sum((t - 273.16) * AREA) / np.sum(AREA)), "ok": ok, **fl}

    def present(self):
        if self._present is None:
            self._present = self.solve(Scenario(), guess=300.0 - 50.0 * np.sin(np.radians(BELT_LAT)) ** 2)
            if not self._present["ok"]:
                raise RuntimeError("present state did not converge")
        return self._present

    def present_albedo(self):
        return self.present()["albedo"]

    def continuation(self, values, make, start=None):
        """Solve a sequence of scenarios, each from the previous solution."""
        guess = self.present()["T"] if start is None else start
        out = []
        for x in values:
            st = self.solve(make(x), guess)
            out.append(st)
            if st["ok"]:
                guess = st["T"]
        return out

    def belt_divergence(self, st):
        """Fig. 2's dC, L dc and dF: net export from each belt, kly/yr."""
        return {key: self.export(st[key]) for key in ("C", "Lc", "F")}

    # --- Sellers' own procedure: shoot from the north pole ---
    def march(self, t0, g, sc: Scenario = Scenario()):
        """March from 80-90N with the physical root of the quadratic in dT.
        Returns the belt temperatures and the eq. (3) residual at 80S."""
        t = np.full(NB, np.nan)
        t[0] = t0
        p_prev_len = 0.0
        gv = np.full(NC, g) if np.ndim(g) == 0 else g
        for j in range(NC):
            target = (p_prev_len - self.net_radiation(np.full(NB, t[j]), sc)[j] * AREA[j]) / LEN[j]
            f = lambda d: self.transport(np.full(NC, t[j]), np.full(NC, d), gv, sc)["P"][j] - target
            c0, c1, c2 = f(0.0), (f(1.0) - f(-1.0)) / 2.0, (f(1.0) + f(-1.0)) / 2.0 - f(0.0)
            disc = c1 * c1 - 4.0 * c2 * c0
            if disc < 0:
                return t, np.nan
            d = 2.0 * c0 / (-c1 + np.sqrt(disc)) if c1 < 0 else (-c1 - np.sqrt(disc)) / (2 * c2)
            t[j + 1] = t[j] - d
            p_prev_len = target * LEN[j]
        last = self.net_radiation(np.full(NB, t[-1]), sc)[-1] * AREA[-1]
        return t, (last - p_prev_len) / AREA[-1] / KLY_YR


def radiative_equilibrium(model: Sellers1969, sc: Scenario = Scenario()):
    """Null: each belt in local balance with no transport (warmest root)."""
    t = np.empty(NB)
    for i in range(NB):
        def f(x):
            full = np.full(NB, x)
            return model.net_radiation(full, sc)[i]
        grid = np.arange(400.0, 50.0, -0.5)
        vals = np.array([f(x) for x in grid])
        k = np.nonzero(np.sign(vals[:-1]) != np.sign(vals[1:]))[0][0]
        t[i] = brentq(f, grid[k + 1], grid[k])
    return model._state(t, sc)


def model(**reading) -> Sellers1969:
    return Sellers1969(replace(Reading(), **reading))
