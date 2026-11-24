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

# Equilibrium constants (M atm-1 and M; bar is taken as atm). The paper takes
# the carbon system from Stumm & Morgan (1981, ref. 14) and the sulphur system
# from Chameides (1984, ref. 23), doi:10.1029/JD089iD03p04739. Neither is in
# hand; the faithful set is traced to them through later tables:
#   carbonate: Butler (1991), Carbon Dioxide Equilibria and Their
#     Applications, Table 2.2, p. 17 -- pK_H, pK1, pK2 "selected by Stumm,
#     W. and Morgan, J. J. 1981 ... pp. 204-206" (with the calcite pKs0, unused
#     here), 0-50 C and 100 C;
#   water: pKw from the same table, which Butler's footnote traces to Sillen &
#     Martell's compilation, not to Stumm & Morgan;
#   S(IV) dissociation: Sellegri et al. (2003), Atmos. Chem. Phys. 3, 1509,
#     Table 5, p. 1517 -- K1 = 1.7e-2 M (-dH/R 2090 K) and K2 = 6.3e-8 M
#     (1510 K), attributed to Chameides (1984);
#   SO2 Henry constant: 1.23 M atm-1, 3100 K -- Sander's compilation lists
#     Chameides' value as 1.2e-2 mol m-3 Pa-1 (1.216 M atm-1) and 3100 K, and
#     Sellegri et al. give 1.2-1.23 M atm-1.
# "textbook" is the set first used here (board message 3628), kept as a reading.
BUTLER_T_C = (0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 100.0)
BUTLER_PK = {  # pK_H, pK1, pK2, pKw
    "KH": (1.11, 1.19, 1.27, 1.33, 1.41, 1.47, 1.53, 1.59, 1.64, 1.68, 1.72, 1.99),
    "K1": (6.579, 6.517, 6.464, 6.419, 6.381, 6.352, 6.327, 6.309, 6.298, 6.290, 6.285, 6.45),
    "K2": (10.625, 10.557, 10.490, 10.430, 10.377, 10.329, 10.290, 10.250, 10.220, 10.195, 10.172, 10.16),
    "KW": (14.955, 14.734, 14.534, 14.337, 14.161, 13.999, 13.833, 13.676, 13.533, 13.394, 13.263, 12.27),
}
SULPHUR = {"HS": (1.23, 3100.0), "S1": (1.7e-2, 2090.0), "S2": (6.3e-8, 1510.0)}
TEXTBOOK = {"KH": (10 ** -1.47, 2420.0), "K1": (10 ** -6.35, -1000.0), "K2": (10 ** -10.33, -1760.0),
            "KW": (1.0e-14, -6716.0), "HS": (1.23, 3120.0), "S1": (1.23e-2, 2010.0), "S2": (6.61e-8, 1500.0)}

# The SO2 factor that puts the faithful model's 10 ppm kink at the printed kink
# of Fig. 2 (0.8634 Gyr; fidelity_ck1992.fit_so2_factor re-derives it from the
# scan). It is fitted to that one feature; the other printed features were left
# out of the fit, but the figure had already been examined when it was chosen.
SO2_FIT_FACTOR = 0.2831

# 0.2 p.p.b. read as a mass mixing ratio (ppbm) rather than by volume: the
# volume ratio is smaller by M_air / M_SO2 (Gemini's review, CK-A2).
SO2_MASS_RATIO_FACTOR = 28.97 / 64.06

OPTIONS = {"t0": ("model", "printed"), "chemistry_T": ("25C", "T"), "constants": ("sources", "textbook"),
           "p_half": ("ck", "volk"), "productivity": ("eq8", "constant", "none"), "weathering": ("ck", "whk"),
           "sun": ("eq1", "constant"), "equilibration": ("open", "sequential")}


@dataclass(frozen=True)
class Reading:
    """One reading of the model. The default is the faithful one.

    t0: "printed" uses T0 = 15 C in eqs (6) and (8); "model" uses the
        present-day temperature of eqs (1)-(5) at 320 ppm, so that F = F0,
        Pi = Pi0 and Patm = 320 ppm hold together at t = 0.
    chemistry_T: "25C" holds the equilibrium constants at 25 C; "T" lets them
        follow the global mean temperature (Butler's table, interpolated, for
        carbonate; van 't Hoff for sulphur).
    constants: "sources" (traced to the paper's refs 14 and 23, above) or
        "textbook".
    so2_factor: multiplies the SO2 term (Henry constant x first dissociation).
    p_half: "ck" forces eq. (8) through Pi0 at (T0, Patm0), temperature factor
        included; "volk" is Volk's eq. (13), (Pi_max/Pi0 - 1)(Patm0 - Pmin).
    productivity: "eq8"; "constant" holds Pi at Pi0 (Volk's case W3); "none"
        removes the soil pump (Psoil = Patm, aH normalised at 320 ppm today).
    equilibration: "open" equilibrates soil water with Psoil and atmospheric
        SO2 together; "sequential" equilibrates rain with Patm and SO2 first,
        then closes it to SO2 and opens it to Psoil, holding total S(IV).
    """

    name: str = "faithful"
    t0: str = "model"
    chemistry_T: str = "25C"
    constants: str = "sources"
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
    equilibration: str = "open"

    def __post_init__(self):
        for field, allowed in OPTIONS.items():
            if getattr(self, field) not in allowed:
                raise ValueError(f"unknown {field} {getattr(self, field)!r}; expected one of {allowed}")


FAITHFUL = Reading()


def solar(t, r: Reading = FAITHFUL):
    """Eq. (1): insolation at Earth, W m-2."""
    t = np.asarray(t, float)
    if r.sun == "constant":
        return np.full_like(t, S0)
    d = 1.0 - SUN_COEFF * t / TAU0_GYR  # pole at 11.97 Gyr; the fit is stated for -4.5 < t < 4.77
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(d > 0, S0 / d, np.nan)


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


def constants(T: float, r: Reading = FAITHFUL) -> dict[str, float]:
    """Equilibrium constants at T (K), or at 25 C under chemistry_T = "25C"."""
    Tk = 298.15 if r.chemistry_T == "25C" else float(T)
    vh = lambda k, b: k * np.exp(b * (1.0 / Tk - 1.0 / 298.15))
    if r.constants == "textbook":
        return {k: vh(*v) for k, v in TEXTBOOK.items()}
    out = {k: 10.0 ** -float(np.interp(Tk - 273.15, BUTLER_T_C, pk)) for k, pk in BUTLER_PK.items()}
    out.update({k: vh(*v) for k, v in SULPHUR.items()})
    return out


def _open_h(c: float, s: float, k: dict) -> float:
    def bal(lh):
        h = 10.0 ** lh
        return h - (k["K1"] * c / h * (1 + 2 * k["K2"] / h) + k["S1"] * s / h * (1 + 2 * k["S2"] / h) + k["KW"] / h)

    return 10.0 ** brentq(bal, -12.0, 0.0, xtol=1e-13)


def h_activity(p_soil: float, T: float, r: Reading = FAITHFUL, p_atm: float | None = None) -> float:
    """H+ activity (M) of soil water, from the charge balance
    [H+] = [HCO3-] + 2[CO3--] + [HSO3-] + 2[SO3--] + [OH-].

    "open": in equilibrium with soil CO2 p_soil (bar) and atmospheric SO2.
    "sequential": rain first equilibrates with p_atm and SO2, fixing total
    S(IV); in the soil it is open to p_soil and closed to SO2."""
    k = constants(T, r)
    c = k["KH"] * p_soil
    s = k["HS"] * SO2 * r.so2_factor
    if r.equilibration == "open":
        return _open_h(c, s, k)
    if p_atm is None:
        raise ValueError("sequential equilibration needs p_atm")
    hr = _open_h(k["KH"] * p_atm, s, k)
    s_total = s * (1 + k["S1"] / hr + k["S1"] * k["S2"] / hr ** 2)

    def bal(lh):
        h = 10.0 ** lh
        d = 1 + k["S1"] / h + k["S1"] * k["S2"] / h ** 2
        return h - (k["K1"] * c / h * (1 + 2 * k["K2"] / h) + s_total * (k["S1"] / h + 2 * k["S1"] * k["S2"] / h ** 2) / d + k["KW"] / h)

    return 10.0 ** brentq(bal, -12.0, 0.0, xtol=1e-13)


def so2_share(r: Reading = FAITHFUL) -> float:
    """Fraction of today's soil-water H+ balanced by sulphur anions, ([HSO3-] +
    2[SO3--]) / [H+], at Psoil0 and T0. What the printed kink fixes is an
    acidity ratio across time (kink_acidity_ratio); this share is its
    translation into today's chemistry, and depends on the chemistry model."""
    T = t0(r)
    k = constants(T, r)
    if r.equilibration != "open":
        raise ValueError("so2_share is defined for open equilibration")
    h = h_activity(PSOIL0, T, r)
    s = k["HS"] * SO2 * r.so2_factor
    return k["S1"] * s / h * (1 + 2 * k["S2"] / h) / h


def kink_acidity_ratio(t_kink: float, r: Reading = FAITHFUL) -> float:
    """aH(kink)/aH(today) required by eq. (6) with F = F0 when Patm = Psoil =
    Pmin (Pi = 0) at time t_kink: exp(-2 (T_kink - T0)/13.7 K). Independent of
    the chemistry; only the climate equations and T0 enter."""
    T = temperature(float(solar(t_kink, r)), r.p_min, r)
    return float(np.exp(-2.0 * (T - t0(r)) / EFOLD_K))


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
    if r.productivity == "none":
        return 0.0
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
    ps = P0 if r.productivity == "none" else PSOIL0
    return _Ref(T, h_activity(ps, T, r, P0), p_half(r))


def weathering(p: float, s: float, r: Reading = FAITHFUL, ref: _Ref | None = None) -> float:
    """F/F0 at atmospheric CO2 p (bar) and insolation s, with T from eqs (2)-(5)."""
    ref = _ref(r) if ref is None else ref
    T = temperature(s, p, r)
    if r.weathering == "whk":
        return float(whk1981.weathering_ratio(p / P0, T - ref.T0))
    ps = soil_co2(productivity(T, p, r, ref.ph), p)
    return (h_activity(ps, T, r, p) / ref.aH0) ** 0.5 * np.exp((T - ref.T0) / EFOLD_K)


CO2_XTOL_DECADES = 1e-12
CO2_TOL_DECADES = 10 * CO2_XTOL_DECADES


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
                          np.log10(r.p_floor), np.log10(P_FIT[1]), xtol=CO2_XTOL_DECADES)


def state(t: float, r: Reading = FAITHFUL, ref: _Ref | None = None) -> dict[str, float]:
    ref = _ref(r) if ref is None else ref
    s = float(solar(t, r))
    p = co2(t, r, ref)
    T = temperature(s, p, r)
    pi = productivity(T, p, r, ref.ph)
    ps = soil_co2(pi, p) if r.weathering == "ck" else np.nan
    in_fit = T_FIT[0] <= T <= T_FIT[1] and P_FIT[0] <= p <= P_FIT[1]
    return {"t_Gyr": float(t), "S_ratio": s / S0, "P_atm_ppm": p * 1e6, "P_soil_ppm": ps * 1e6,
            "Pi_ratio": pi, "T_K": T, "in_fit": bool(in_fit)}


def trajectory(times, r: Reading = FAITHFUL) -> dict[str, np.ndarray]:
    ref = _ref(r)
    rows = [state(float(t), r, ref) for t in np.asarray(times, float)]
    return {k: np.array([row[k] for row in rows]) for k in rows[0]}


def first_crossing(f, level: float, t_max: float = 2.0, step: float = 0.01, tol: float = 0.0) -> float:
    """First t in [0, t_max] at which f(t) reaches level (to within tol): 0 if
    it holds at t = 0, otherwise the first sign change of f - level on the
    grid, refined by brentq; inf if none."""
    g0 = f(0.0) - level
    if abs(g0) <= tol:
        return 0.0
    t = np.append(np.arange(0.0, t_max, step), t_max)
    for a, b in zip(t[:-1], t[1:]):
        if b <= a:
            continue
        gb = f(b) - level
        if abs(gb) <= tol:
            return float(b)
        if np.sign(gb) != np.sign(g0):
            return brentq(lambda x: f(x) - level, a, b, xtol=1e-9)
        g0 = gb
    return float("inf")


def co2_time(level: float, r: Reading = FAITHFUL, t_max: float = 2.0) -> float:
    """Gyr until Patm first falls to `level` (bar); inf for a level below the
    floor, which Patm never goes beneath. The floor itself is reached when Patm
    comes within 1e-9 decades of it; any other level when Patm comes within
    CO2_TOL_DECADES, ten times the accuracy of the CO2 solve. A level at or
    above today's is reached at t = 0."""
    ref = _ref(r)
    if level < r.p_floor:
        return float("inf")
    if np.log10(level) >= np.log10(co2(0.0, r, ref)) - CO2_TOL_DECADES:
        return 0.0
    if level == r.p_floor:
        f = lambda t: float(np.log10(co2(t, r, ref) / r.p_floor) > 1e-9)
        return first_crossing(f, 0.5, t_max) if f(0.0) else 0.0
    return first_crossing(lambda t: np.log10(co2(t, r, ref)), np.log10(level), t_max, tol=CO2_TOL_DECADES)


T_TOL_K = 1e-9


def temperature_time(level_K: float, r: Reading = FAITHFUL, t_max: float = 2.0) -> float:
    """Gyr until T first reaches level_K, which must lie in the climate fits'
    range T_FIT; 0 for a level at or below today's temperature."""
    if not T_FIT[0] <= level_K <= T_FIT[1]:
        raise ValueError(f"{level_K} K is outside the climate fits' range {T_FIT}")
    ref = _ref(r)
    f = lambda t: temperature(float(solar(t, r)), co2(t, r, ref), r)
    if level_K <= f(0.0) + T_TOL_K:
        return 0.0
    return first_crossing(f, level_K, t_max)


def floor_threshold_T(r: Reading = FAITHFUL) -> float:
    """Temperature at which weathering with Patm = Psoil = floor equals F0
    (the text's "above 300 K, silicate dissolution may proceed more rapidly
    than CO2 ... supplied")."""
    ref = _ref(r)

    def f(T):
        return (h_activity(r.p_floor, T, r, r.p_floor) / ref.aH0) ** 0.5 * np.exp((T - ref.T0) / EFOLD_K) - 1.0

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
    "textbook": Reading(name="textbook constants (first build)", constants="textbook"),
    "so2_fitted": Reading(name=f"SO2 term x {SO2_FIT_FACTOR} (fitted to the printed kink)", so2_factor=SO2_FIT_FACTOR),
}

# Readings of Box 1's SO2 equilibration with no fitted parameter, suggested in
# Gemini's review (CK-A2). Two binary choices crossed with the chemistry
# temperature give eight combinations; all eight are scored (fidelity_ck1992
# .so2_readings), so the best of them is a selection among eight, not a
# prediction. None replaces the faithful reading without Chameides (1984).
SO2_READINGS = {
    f"{eq}_{basis}_{chem}": Reading(name=f"{eq} equilibration, 0.2 ppb by {basis}, constants at {chem}",
                                    equilibration=eq, chemistry_T=chem,
                                    so2_factor=SO2_MASS_RATIO_FACTOR if basis == "mass" else 1.0)
    for eq in ("open", "sequential") for basis in ("volume", "mass") for chem in ("25C", "T")
}

C3 = replace(FAITHFUL, name="C3 world (Pmin = 150 ppm, P_half recalibrated)", p_min=P_MIN_C3)

CONTROLS = {
    "no_so2": Reading(name="null: no SO2", so2_factor=0.0),
    "constant_productivity": Reading(name="null: Pi held at Pi0 (Volk W3)", productivity="constant"),
    "whk_weathering": Reading(name="null: WHK weathering on Patm", weathering="whk"),
    "fixed_co2": Reading(name="null: Patm held at 320 ppm", fixed_co2=True),
    "constant_sun": Reading(name="null: constant Sun", sun="constant"),
}
