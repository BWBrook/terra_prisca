"""Caldeira & Kasting (1992): the life span of the biosphere revisited.

Nature 360, 721-723, doi:10.1038/360721a0. All equations are in the paper's
Box 1:

  (1)  S(t) = S0 / (1 - 0.38 t/tau0),  tau0 = 4.55 Gyr, S0 = 1368 W m-2
  (2)  (1 - a) S/4 = sigma Teff^4
  (3)  T = Teff + dT
  (4)  dT(T, psi), psi = log10 P_atm (bar)        greenhouse fit
  (5)  a(T)                                       albedo fit
  (6)  F/F0 = (aH/aH0)^0.5 exp((T - T0)/13.7 K)   silicate weathering
  (7)  Psoil/Psoil0 = (Pi/Pi0)(1 - Patm0/Psoil0) + Patm/Psoil0   (Volk 1987)
  (8)  Pi/Pi_max = (1 - ((T - 25 C)/25 C)^2) (Patm - Pmin)/(P_half + Patm - Pmin)

with Pi_max = 2 Pi0, Pmin = 10 ppm, Psoil0 = 10 Patm0, Patm0 = 320 ppm,
T0 = 15 C, and P_half fixed by Pi = Pi0 at (T0, Patm0). aH is the H+ activity
of rain water equilibrated with soil CO2 and 0.2 ppb atmospheric SO2. "The
model is solved by setting F = F0 until Patm = 1 ppm; thereafter, Patm is
maintained at this value."

Time t is in Gyr from the present; pressures in bar; temperatures in K.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
from scipy.optimize import brentq

from terra_prisca.walker_hays_kasting import whk1981

S0 = 1368.0            # W m-2 (Box 1)
TAU0_GYR = 4.55        # Box 1
SUN_COEFF = 0.38       # Box 1, eq. (1)
SIGMA = 5.670e-8       # W m-2 K-4; not stated in the paper
T0_PRINTED = 288.15    # K, "T0 (= 15 C)"
P0 = 320e-6            # bar, "Patm,0 (= 320 p.p.m.)"
PSOIL0 = 10 * P0       # "Psoil,0 = 10 Patm,0" (after Volk 1987)
PI_MAX = 2.0           # Pi_max / Pi0 (after Volk 1987)
P_MIN_C4 = 10e-6       # bar
P_MIN_C3 = 150e-6      # bar, Lovelock & Whitfield's limit
P_FLOOR = 1e-6         # bar
SO2 = 0.2e-9           # bar, "0.2 p.p.b."
EFOLD_K = whk1981.FAITHFUL.efold_K  # 13.7 K, taken from Walker, Hays & Kasting (1981)
T_FIT = (273.15, 373.15)            # range of the 143 climate-model runs behind eqs (4)-(5)
P_FIT = (1e-8, 1e-2)                # bar

# Equilibrium constants at 298.15 K, with van 't Hoff coefficients -dH/R (K)
# for the temperature-dependent reading. Units M atm-1 and M; bar is taken as
# atm. Carbonate: Stumm & Morgan (1981). Sulphur: Chameides (1984),
# doi:10.1029/JD089iD03p04739. PROVISIONAL until checked against Chameides'
# table: these are the values widely quoted from it, not yet read from it.
CO2_KH, CO2_K1, CO2_K2 = (10 ** -1.47, 2420.0), (10 ** -6.35, -1000.0), (10 ** -10.33, -1760.0)
SO2_KH, SO2_K1, SO2_K2 = (1.23, 3120.0), (1.23e-2, 2010.0), (6.61e-8, 1500.0)
KW = (1.0e-14, -6716.0)

# The SO2 factor that puts the faithful model's 10 ppm kink at the printed kink
# of Fig. 2 (0.8634 Gyr; fidelity_ck1992.fit_so2_factor re-derives it from the
# scan). Fitted to that one feature only; every other printed feature is a test.
SO2_FIT_FACTOR = 0.3914


@dataclass(frozen=True)
class Reading:
    """One reading of the model. The default is the faithful one.

    t0: "printed" uses T0 = 15 C in eqs (6) and (8); "model" uses the
        present-day temperature of eqs (1)-(5) at 320 ppm, so that F = F0,
        Pi = Pi0 and Patm = 320 ppm hold together at t = 0.
    chemistry_T: "25C" holds the equilibrium constants at 25 C; "T" lets them
        follow the global mean temperature.
    so2_factor: multiplies the SO2 term (Henry constant x first dissociation).
    p_half: "ck" forces eq. (8) through Pi0 at (T0, Patm0), temperature factor
        included; "volk" is Volk's eq. (13), (Pi_max/Pi0 - 1)(Patm0 - Pmin).
    """

    name: str = "faithful"
    t0: str = "model"
    chemistry_T: str = "25C"
    so2_factor: float = 1.0
    p_half: str = "ck"
    p_min: float = P_MIN_C4
    p_floor: float = P_FLOOR
    dT_offset: float = 0.0       # K added to eq. (4); sensitivity only
    albedo_offset: float = 0.0   # added to eq. (5); sensitivity only
    productivity: str = "eq8"    # control "constant": Pi = Pi0 (Volk's case W3)
    weathering: str = "ck"       # control "whk": WHK eq. (1) on atmospheric CO2
    fixed_co2: bool = False      # control: Patm held at 320 ppm
    sun: str = "eq1"             # control "constant"


FAITHFUL = Reading()


def solar(t, r: Reading = FAITHFUL):
    """Eq. (1): insolation at Earth, W m-2."""
    t = np.asarray(t, float)
    return np.full_like(t, S0) if r.sun == "constant" else S0 / (1.0 - SUN_COEFF * t / TAU0_GYR)


def albedo(T, r: Reading = FAITHFUL):
    T = np.asarray(T, float)
    return 1.4891 - 0.0065979 * T + 8.567e-6 * T ** 2 + r.albedo_offset


def greenhouse(T, p, r: Reading = FAITHFUL):
    """Eq. (4): dT (K) for surface temperature T (K) and CO2 p (bar)."""
    T, psi = np.asarray(T, float), np.log10(np.asarray(p, float))
    return (815.17 + 4.895e7 / T ** 2 - 3.9787e5 / T
            - 6.7084 / psi ** 2 + 73.221 / psi - 30882.0 / (T * psi) + r.dT_offset)


def climate_residual(T, s, p, r: Reading = FAITHFUL):
    """Teff(T) + dT(T, p) - T; zero at the surface temperature."""
    teff = ((1.0 - albedo(T, r)) * s / (4.0 * SIGMA)) ** 0.25
    return teff + greenhouse(T, p, r) - T


def temperature(s: float, p: float, r: Reading = FAITHFUL) -> float:
    """Eqs (2)-(5) solved for T. The residual has one root in 200-500 K over
    the range used here (tests scan for others)."""
    return brentq(lambda T: climate_residual(T, s, p, r), 200.0, 500.0, xtol=1e-10)


def _k(pair, T, r: Reading):
    k, b = pair
    return k if r.chemistry_T == "25C" else k * np.exp(b * (1.0 / T - 1.0 / 298.15))


def h_activity(p_soil: float, T: float, r: Reading = FAITHFUL) -> float:
    """H+ activity (M) of rain water in equilibrium with soil CO2 p_soil (bar)
    and atmospheric SO2, from the charge balance
    [H+] = [HCO3-] + 2[CO3--] + [HSO3-] + 2[SO3--] + [OH-]."""
    c = _k(CO2_KH, T, r) * p_soil
    k1, k2 = _k(CO2_K1, T, r), _k(CO2_K2, T, r)
    s = _k(SO2_KH, T, r) * SO2 * r.so2_factor
    s1, s2, kw = _k(SO2_K1, T, r), _k(SO2_K2, T, r), _k(KW, T, r)

    def bal(lh):
        h = 10.0 ** lh
        return h - (k1 * c / h * (1 + 2 * k2 / h) + s1 * s / h * (1 + 2 * s2 / h) + kw / h)

    return 10.0 ** brentq(bal, -12.0, 0.0, xtol=1e-13)


def t0(r: Reading = FAITHFUL) -> float:
    return T0_PRINTED if r.t0 == "printed" else temperature(S0, P0, replace(r, sun="eq1"))


def p_half(r: Reading = FAITHFUL) -> float:
    """Half-saturation of eq. (8), bar."""
    excess = P0 - r.p_min
    if r.p_half == "volk":
        return (PI_MAX - 1.0) * excess
    g0 = 1.0 - ((t0(r) - 298.15) / 25.0) ** 2
    return PI_MAX * g0 * excess - excess


def productivity(T: float, p: float, r: Reading = FAITHFUL, ph: float | None = None) -> float:
    """Eq. (8) as Pi/Pi0, held at zero where either factor would go negative
    (below Pmin, or outside 0-50 C)."""
    if r.productivity == "constant":
        return 1.0
    ph = p_half(r) if ph is None else ph
    g = max(0.0, 1.0 - ((T - 298.15) / 25.0) ** 2)
    x = max(0.0, p - r.p_min)
    return PI_MAX * g * x / (ph + x)


def soil_co2(pi: float, p: float) -> float:
    """Eq. (7), bar."""
    return pi * (PSOIL0 - P0) + p


@dataclass(frozen=True)
class _Ref:
    T0: float
    aH0: float
    ph: float


def _ref(r: Reading) -> _Ref:
    T = t0(r)
    return _Ref(T, h_activity(PSOIL0, T, r), p_half(r))


def weathering(p: float, s: float, r: Reading = FAITHFUL, ref: _Ref | None = None) -> float:
    """F/F0 at atmospheric CO2 p (bar) and insolation s, with T from eqs (2)-(5)."""
    ref = _ref(r) if ref is None else ref
    T = temperature(s, p, r)
    if r.weathering == "whk":
        return float(whk1981.weathering_ratio(p / P0, T - ref.T0))
    ps = soil_co2(productivity(T, p, r, ref.ph), p)
    return (h_activity(ps, T, r) / ref.aH0) ** 0.5 * np.exp((T - ref.T0) / EFOLD_K)


def co2(t: float, r: Reading = FAITHFUL, ref: _Ref | None = None) -> float:
    """Patm (bar) at time t: the root of F = F0, or the floor once F at the
    floor reaches F0. F - F0 changes sign once between the floor and 1e-2 bar
    (tested), so the root is unique."""
    if r.fixed_co2:
        return P0
    ref = _ref(r) if ref is None else ref
    s = float(solar(t, r))
    if weathering(r.p_floor, s, r, ref) >= 1.0:
        return r.p_floor
    return 10.0 ** brentq(lambda lp: weathering(10.0 ** lp, s, r, ref) - 1.0,
                          np.log10(r.p_floor), np.log10(P_FIT[1]), xtol=1e-12)


def state(t: float, r: Reading = FAITHFUL, ref: _Ref | None = None) -> dict[str, float]:
    ref = _ref(r) if ref is None else ref
    s = float(solar(t, r))
    p = co2(t, r, ref)
    T = temperature(s, p, r)
    pi = productivity(T, p, r, ref.ph)
    ps = soil_co2(pi, p) if r.weathering == "ck" else np.nan
    return {"t_Gyr": float(t), "S_ratio": s / S0, "P_atm_ppm": p * 1e6, "P_soil_ppm": ps * 1e6,
            "Pi_ratio": pi, "T_K": T, "in_fit": bool(T_FIT[0] <= T <= T_FIT[1])}


def trajectory(times, r: Reading = FAITHFUL) -> dict[str, np.ndarray]:
    ref = _ref(r)
    rows = [state(float(t), r, ref) for t in np.asarray(times, float)]
    return {k: np.array([row[k] for row in rows]) for k in rows[0]}


def first_crossing(f, level: float, t_max: float = 2.0, step: float = 0.01) -> float:
    """First t in [0, t_max] at which f(t) - level changes sign, refined by
    brentq on the bracketing step; inf if none."""
    t = np.append(np.arange(0.0, t_max, step), t_max)
    g0 = f(0.0) - level
    for a, b in zip(t[:-1], t[1:]):
        gb = f(b) - level
        if gb == 0.0:
            return float(b)
        if np.sign(gb) != np.sign(g0):
            return brentq(lambda x: f(x) - level, a, b, xtol=1e-9)
        g0 = gb
    return float("inf")


def co2_time(level: float, r: Reading = FAITHFUL, t_max: float = 2.0) -> float:
    """Gyr until Patm first falls to `level` (bar); compared in log10, so the
    floor itself is reached when Patm comes within 1e-9 decades of it."""
    ref = _ref(r)
    if level <= r.p_floor:
        f = lambda t: float(np.log10(co2(t, r, ref) / r.p_floor) > 1e-9)
        return first_crossing(f, 0.5, t_max)
    return first_crossing(lambda t: np.log10(co2(t, r, ref)), np.log10(level), t_max)


def temperature_time(level_K: float, r: Reading = FAITHFUL, t_max: float = 2.0) -> float:
    ref = _ref(r)
    return first_crossing(lambda t: temperature(float(solar(t, r)), co2(t, r, ref), r), level_K, t_max)


def floor_threshold_T(r: Reading = FAITHFUL) -> float:
    """Temperature at which weathering with Patm = Psoil = floor equals F0
    (the text's "above 300 K, silicate dissolution may proceed more rapidly
    than CO2 ... supplied")."""
    ref = _ref(r)

    def f(T):
        return (h_activity(r.p_floor, T, r) / ref.aH0) ** 0.5 * np.exp((T - ref.T0) / EFOLD_K) - 1.0

    return brentq(f, 250.0, 400.0, xtol=1e-9)


def constant_T_time(level: float, r: Reading = FAITHFUL, t_max: float = 3.0) -> float:
    """The text's "constant temperature" sentence read literally: the time at
    which CO2 must fall to `level` (bar) to hold T at T0 with eqs (1)-(5)."""
    T = t0(r)
    return brentq(lambda t: temperature(float(solar(t, r)), level, r) - T, 0.0, t_max, xtol=1e-9)


READINGS = {
    "faithful": FAITHFUL,
    "t0_printed": Reading(name="T0 = 15 C as printed", t0="printed"),
    "chemistry_T": Reading(name="equilibrium constants follow T", chemistry_T="T"),
    "so2_half": Reading(name="SO2 term x 0.5", so2_factor=0.5),
    "so2_double": Reading(name="SO2 term x 2", so2_factor=2.0),
    "volk_p_half": Reading(name="Volk eq. (13) P_half", p_half="volk"),
    "so2_fitted": Reading(name=f"SO2 term x {SO2_FIT_FACTOR} (fitted to the printed kink)", so2_factor=SO2_FIT_FACTOR),
}

C3 = replace(FAITHFUL, name="C3 world (Pmin = 150 ppm, P_half recalibrated)", p_min=P_MIN_C3)

CONTROLS = {
    "no_so2": Reading(name="null: no SO2", so2_factor=0.0),
    "constant_productivity": Reading(name="null: Pi held at Pi0 (Volk W3)", productivity="constant"),
    "whk_weathering": Reading(name="null: WHK weathering on Patm", weathering="whk"),
    "fixed_co2": Reading(name="null: Patm held at 320 ppm", fixed_co2=True),
    "constant_sun": Reading(name="null: constant Sun", sun="constant"),
}
