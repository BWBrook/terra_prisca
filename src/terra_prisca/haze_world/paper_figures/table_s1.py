"""Table S1 of the haze-world paper, built from the model's own parameter objects.

Reference values come from population_coupling.reference(), two_guilds, woodii1998,
methane_budget, the Kotsyurbenko et al. (2001) table, the Arney et al. (2016)
extraction and the sweep constants in the experiment modules. Code locations
are navigation hints, not value checks. Reported literal experiment settings
are separately checked against parsed source expressions. This is a scoped
record of the reference model and the paper's Stage B/B'/B'' designs, not an
inventory of every setting in earlier exploratory stages. Writes
models/haze_world/paper/esm/table_s1.{csv,md} and the
six-temperature table table_s1_kinetics.{csv,md}, then the other ESM tables
(esm_tables.py).
"""

import ast
import csv
import inspect
import itertools
import math
import re
from dataclasses import replace
from pathlib import Path

import numpy as np
from scipy.optimize import brentq

from .. import dynamic_realisation as b1
from .. import dynamic_core as dynamic
from .. import continuum_core as continuum
from .. import continuum_experiments as continuum_runs
from .. import dynamic_transients as transients
from .. import graded_dials as dials
from .. import methane_budget as budget
from .. import population_coupling as core
from .. import two_guilds as tg
from .. import woodii1998 as woodii
from .. import graded_spread as spread
from .. import graded_thresholds as thresholds
from ..finite_populations import CellProcess
from ..hydrogen_uptake import ACETOGEN, BIOMASS_MG_ML, MSB, VOLUME_ML, parameters

ROOT = Path(__file__).resolve().parents[4]
PKG = ROOT / "src/terra_prisca"
ESM = ROOT / "models/haze_world/paper/esm"
COLUMNS = ("symbol", "meaning", "value", "units", "basis", "source", "code location")
K2001 = "Kotsyurbenko et al. 2001"
P1998 = "Peters et al. 1998"
T1993 = "Tijhuis et al. 1993"
A2016 = "Arney et al. 2016"
ASSUMED = "assumption"
NUMERICAL = "numerical choice"
KINETICS_NOTE = "table_s1_kinetics"


def loc(file, pattern):
    """First line of a source file matching a pattern, as file:line."""
    path = PKG / file
    for number, line in enumerate(path.read_text().splitlines(), 1):
        if re.search(pattern, line):
            return f"{file.split('/')[-1]}:{number}"
    raise ValueError(f"{pattern!r} not found in {file}")


def checked_loc(file, *expressions):
    """Require exact parsed expressions/statements for reported literal settings."""
    path = ROOT / file if file.startswith("models/") else PKG / file
    nodes = list(ast.walk(ast.parse(path.read_text())))
    first = None
    for expression in expressions:
        wanted = ast.parse(expression).body[0]
        if isinstance(wanted, ast.Expr):
            wanted = wanted.value
        matches = [node for node in nodes if ast.dump(node) == ast.dump(wanted)]
        if not matches:
            raise ValueError(f"Reported Table S1 setting changed in {file}: {expression}")
        first = first or matches[0].lineno
    shown = file if file.startswith("models/") else file.split("/")[-1]
    return f"{shown}:{first} (parsed setting checked)"


def num(x, sig=9):
    if isinstance(x, str):
        return x
    if isinstance(x, (list, tuple, np.ndarray)):
        return ", ".join(num(v, sig) for v in x)
    if isinstance(x, (int, np.integer)):
        return str(int(x))
    return f"{float(x):.{sig}g}"


def build_rows():
    ref = core.reference()
    bio, clim, loss = ref.biology, ref.climate, ref.loss
    a30, m30 = tg.guilds(30., bio)
    tc = tg.TEMPERATURES_C
    ka = [parameters(t, ACETOGEN) for t in tc]
    km = [parameters(t, MSB) for t in tc]
    atm = budget.atmosphere(clim.case)
    resp = budget.response(clim.case)
    cases = {r["case"]: r for r in csv.DictReader((budget.ARNEY_DIR / "cases.csv").open())}[clim.case]
    ell = bio.loss_h
    n_co2 = atm["column"] * atm["f_co2"]
    volume = ref.habitat_l_cm2
    process = CellProcess()
    if (process.census_yr, process.minimum_cells, process.immigration_cells_yr) != (10., 1., (0., 0.)):
        raise ValueError("B3's fixed ten-year, one-cell, no-immigration protocol differs from CellProcess defaults")
    checked_loc("haze_world/dynamic_transients.py", "next_census=10.", "next_census+=10.", "next_census=t+10.",
                "floor_z=positive._inverse(np.exp(-conversion)/positive.SCALE)",
                "coords.present[0,i] and cl[0,i]+conversion < -1e-12")
    seed = 1e-12
    v_global = process.surface_cm2 * volume
    design = transients.design()
    n_b3 = sum(c.stage == "B3" for c in design)
    b3_protocol = {(c.direction, c.chemistry, c.fraction, c.tau_yr, c.years)
                   for c in design if c.stage == "B3"}
    if b3_protocol != set(itertools.product(("A_into_M", "M_into_A"), ("fixed", "products"),
                                           (0., .5), (0., 3., 30.), (100000.,))):
        raise ValueError("B3 design differs from the protocol reported in Table S1")
    b2 = [c for c in design if c.stage == "B2"]
    lag_sig = inspect.signature(transients.integrate).parameters

    def switch(loss_h):
        cfg = replace(bio, loss_h=loss_h)
        def gap(t):
            a, m = tg.guilds(t - 273.15, cfg)
            return a.rstar(loss_h) - m.rstar(loss_h)
        return brentq(gap, 276., 290., xtol=1e-12)

    t_sw = switch(ell)
    ra, rm = (g.rstar(ell) for g in tg.guilds(t_sw - 273.15, bio))
    a_sw, m_sw = tg.guilds(t_sw - 273.15, bio)
    eta = [1 - g.assimilation_mol_g * ell / (g.maintenance + ell / g.yield_g_mol) for g in (a_sw, m_sw)]
    state = next(s for s in core.equilibrium_states(ref) if s["kind"] == "mixed" and s["stable"])
    r_sw = float(state["r"])
    seg = int(np.searchsorted(resp.ratios, r_sw, side="right")) - 1
    slope = float((resp.temperatures_k[seg + 1] - resp.temperatures_k[seg]) / (resp.ratios[seg + 1] - resp.ratios[seg]))
    e_alt = [tg.GAS_CONSTANT * math.log(p[1].vmax_nmol_h / p[0].vmax_nmol_h) / (1 / 277.15 - 1 / 283.15)
             for p in (ka, km)]
    t_loss = [switch(x) for x in (.0005, .001, .002)]
    if abs(tg.maintenance_factor(30., bio.maintenance_energy_j) - 1) > 1e-12:
        raise ValueError("Maintenance reference temperature is no longer 303.15 K")
    a_thr = tg.thresholds(30., replace(bio))
    if abs(a_thr[0] - bio.threshold_a30) > 1e-12 or abs(a_thr[1] - bio.threshold_m30) > 1e-12:
        raise ValueError("Thresholds are not anchored at 303.15 K")
    for tcel, (pa, pm) in ((10., tg.thresholds(10., bio)),):
        dh = (1 / (tcel + 273.15) - 1 / 303.15)
        want = (bio.threshold_a30 * math.exp((-270700. - bio.cessation_energy_a_j) / (4 * tg.GAS_CONSTANT) * dh),
                bio.threshold_m30 * math.exp((-253000. - bio.cessation_energy_m_j) / (4 * tg.GAS_CONSTANT) * dh))
        if abs(pa - want[0]) > 1e-9 * want[0] or abs(pm - want[1]) > 1e-9 * want[1]:
            raise ValueError("Reaction enthalpies in Table S1 no longer match two_guilds.thresholds")

    rows = []

    def add(group, symbol, meaning, value, units, basis, source, where):
        rows.append(dict(group=group, symbol=symbol, meaning=meaning, value=num(value), units=units,
                         basis=basis, source=source, **{"code location": where or "computed in table_s1.py"}))

    G = "Units and state"
    add(G, "H", "Hours per model year (seconds per year / 3600)", core.HOURS_PER_YEAR, "h yr⁻¹", "derived",
        "3.15576e7 s yr⁻¹", loc("haze_world/population_coupling.py", r"^HOURS_PER_YEAR"))
    add(G, "T range", "Temperature interval over which physiology is defined", "273 to 303.15", "K", ASSUMED,
        "assays span 277.15 to 303.15 K; the 273 K floor is chosen here",
        checked_loc("haze_world/dynamic_core.py", 'low = 277.15 if p.base.biology.low_temperature_variant == "none" else 273.',
                    'valid = bool(np.all((support >= low-1e-10) & (support <= 303.15+1e-10)))'))

    G = "Uptake kinetics (equation 2.1)"
    add(G, "T_C", "Assay temperatures", list(tc), "°C", "source", K2001,
        loc("haze_world/two_guilds.py", r"^TEMPERATURES_C"))
    add(G, "V_A(T_C)", "Acetogen (A. bakii) uptake capacity per 20-mL culture", [p.vmax_nmol_h for p in ka],
        "nmol H₂ h⁻¹", "transferred", K2001, "models/haze_world/evidence/kotsyurbenko2001_table2.csv, via hydrogen_uptake.parameters")
    add(G, "K_A(T_C)", "Acetogen half-saturation pressure", [p.km_pa for p in ka], "Pa", "transferred", K2001,
        "models/haze_world/evidence/kotsyurbenko2001_table2.csv, via hydrogen_uptake.parameters")
    add(G, "V_M(T_C)", "Methanogen (strain MSB) uptake capacity per 20-mL culture", [p.vmax_nmol_h for p in km],
        "nmol H₂ h⁻¹", "transferred", K2001, "models/haze_world/evidence/kotsyurbenko2001_table2.csv, via hydrogen_uptake.parameters")
    add(G, "K_M(T_C)", "Methanogen half-saturation pressure", [p.km_pa for p in km], "Pa", "transferred", K2001,
        "models/haze_world/evidence/kotsyurbenko2001_table2.csv, via hydrogen_uptake.parameters")
    add(G, "interpolation", "V and K interpolated linearly in T between the six assays, independently; capacity relative to V(30 °C)",
        "linear", "", ASSUMED, ASSUMED, loc("haze_world/two_guilds.py", r"relative = np\.interp"))
    add(G, "s_A30", "Acetogen capacity at 303.15 K: mu_max/Y_A + m_A30", a30.rate_scale, "mol H₂ gDW⁻¹ h⁻¹",
        "derived", P1998 + " (mu_max, Y_A, m_A30)", loc("haze_world/woodii1998.py", r"def inferred_reference_uptake"))
    add(G, "mu_max", "A. woodii maximum biomass-synthesis rate used to close s_A30", woodii.MU_MAX, "h⁻¹",
        "transferred", P1998, loc("haze_world/woodii1998.py", r"^MU_MAX"))
    add(G, "gamma", "Methanogen / acetogen capacity ratio at 303.15 K (source culture ratio V_M/V_A at 30 °C = "
        f"{km[-1].vmax_nmol_h / ka[-1].vmax_nmol_h:.4f}; dry-mass ratio = "
        f"{(km[-1].vmax_nmol_h / (VOLUME_ML * BIOMASS_MG_ML[MSB])) / (ka[-1].vmax_nmol_h / (VOLUME_ML * BIOMASS_MG_ML[ACETOGEN])):.4f})",
        bio.capacity_ratio, "", ASSUMED, ASSUMED + "; " + K2001 + " culture ratio",
        loc("haze_world/two_guilds.py", r"capacity_ratio: float"))
    add(G, "s_M30", "Methanogen capacity at 303.15 K: gamma s_A30", m30.rate_scale, "mol H₂ gDW⁻¹ h⁻¹", "derived",
        "gamma, s_A30", loc("haze_world/two_guilds.py", r"inferred_reference_uptake\(\) \* config\.capacity_ratio"))
    add(G, "kinetics", "Uptake law", bio.kinetics, "", ASSUMED, K2001 + " (Michaelis-Menten fit)",
        loc("haze_world/two_guilds.py", r"kinetics: str"))
    add(G, "T_min,assay", "Lowest uptake assay", 277.15, "K", "source", K2001,
        loc("haze_world/two_guilds.py", r"minimum = 4\."))
    add(G, "continuation", "Below 277.15 K: capacity and half-saturation held at their 277.15 K values; "
        "maintenance and thresholds keep their laws", bio.low_temperature_variant, "", ASSUMED, ASSUMED,
        loc("haze_world/population_coupling.py", r'low_temperature_variant="constant_shape"'))
    add(G, "E_A, E_M (alternative)", "Arrhenius energies for the alternative continuation: R ln[V(10 °C)/V(4 °C)] / (1/277.15 - 1/283.15); "
        "half-saturation stays frozen", e_alt, "J mol⁻¹", "derived", K2001 + "; alternative, not in the reference",
        loc("haze_world/two_guilds.py", r"energy = GAS_CONSTANT"))

    G = "Yields, maintenance, loss (equation 2.2)"
    add(G, "Y_A", "Acetogen true yield (maintenance-corrected, per mol H₂)", woodii.Y_H2_REPORTED, "gDW mol⁻¹ H₂",
        "transferred", P1998, loc("haze_world/woodii1998.py", r"^Y_H2_REPORTED"))
    add(G, "Y_A (not used)", "Yield recomputed from acetate yield and biomass composition: 1/[4(1/7.7 + 0.0206)]",
        woodii.hydrogen_yield_from_assimilation(), "gDW mol⁻¹ H₂", "derived", P1998,
        loc("haze_world/woodii1998.py", r"def hydrogen_yield_from_assimilation"))
    add(G, "Y_M", "Methanogen true yield (scenario anchor)", bio.yield_m, "gDW mol⁻¹ H₂", ASSUMED, "no derivation recorded for this exact value; warm-strain transfer range in evidence/methanogen-growth-parameters.csv; no matched cold-strain calibration",
        loc("haze_world/two_guilds.py", r"yield_m: float"))
    add(G, "m_A30", "Acetogen maintenance at 303.15 K: 4 x 0.40 mmol acetate gDW⁻¹ h⁻¹", woodii.MAINTENANCE_H2,
        "mol H₂ gDW⁻¹ h⁻¹", "derived", P1998, loc("haze_world/woodii1998.py", r"^MAINTENANCE_H2"))
    add(G, "m_M30", "Methanogen maintenance at 303.15 K", bio.maintenance_m30, "mol H₂ gDW⁻¹ h⁻¹", ASSUMED,
        ASSUMED + " (no matched cold-strain calibration recovered)", loc("haze_world/two_guilds.py", r"maintenance_m30: float"))
    add(G, "E_m", "Arrhenius activation energy of maintenance, shared; m_i(T) = m_i30 exp[-E_m/R (1/T - 1/303.15)]",
        bio.maintenance_energy_j, "J mol⁻¹", "transferred", T1993, loc("haze_world/two_guilds.py", r"maintenance_energy_j: float"))
    add(G, "T_ref", "Reference temperature of the maintenance and threshold laws", 303.15, "K", ASSUMED,
        "30 °C assay", loc("haze_world/two_guilds.py", r"def maintenance_factor"))
    add(G, "R", "Gas constant as implemented", tg.GAS_CONSTANT, "J mol⁻¹ K⁻¹", "source", "standard value",
        loc("haze_world/two_guilds.py", r"^GAS_CONSTANT"))
    add(G, "ell", "Demographic loss rate, common to both groups (reference)", ell, "h⁻¹", "swept (reference value assumed)",
        ASSUMED, loc("haze_world/two_guilds.py", r"loss_h: float"))
    add(G, "ell scan", "Loss rates in the homogeneous map", list(b1.LOSSES), "h⁻¹", "swept", ASSUMED,
        loc("haze_world/dynamic_realisation.py", r"^LOSSES"))
    add(G, "T* vs ell", "Set temperature at ell = 0.0005, 0.001, 0.002 h⁻¹ (switch of equation 2.3)", t_loss, "K", "derived",
        "R*_A(T) = R*_M(T)", "solved in table_s1.py with two_guilds.guilds")
    add(G, "ell half-life", "ln 2 / ell, excluding growth and maintenance", math.log(2) / ell / 24, "days", "derived", "ell", "")
    add(G, "a_A", "Hydrogen equivalents retained per unit new acetogen biomass: 4 x 0.0206", tg.ASSIMILATION_A,
        "mol H₂ gDW⁻¹", "derived", P1998, loc("haze_world/two_guilds.py", r"^ASSIMILATION_A"))
    add(G, "a_M", "Same biomass coefficient imposed on the methanogen", bio.assimilation_m, "mol H₂ gDW⁻¹", ASSUMED, ASSUMED,
        loc("haze_world/population_coupling.py", r"assimilation_m=ASSIMILATION_A"))
    add(G, "Y_acetate, m_acetate, a_acetate", "Source inputs to the three rows above: true yield per mol acetate; maintenance per gDW per h; mol acetate-equivalent per gDW",
        [woodii.Y_ACETATE_REPORTED, woodii.MAINTENANCE_ACETATE, woodii.BIOMASS_ACETATE_EQUIVALENT],
        "gDW mol⁻¹; mol gDW⁻¹ h⁻¹; mol gDW⁻¹", "source", P1998, loc("haze_world/woodii1998.py", r"^Y_ACETATE_REPORTED"))

    G = "Thermodynamic inputs to the cessation thresholds"
    add(G, "p*_A30, p*_M30", "Cessation pressures at 303.15 K", [bio.threshold_a30, bio.threshold_m30], "Pa", ASSUMED,
        ASSUMED + "; " + K2001 + " bounds (upper limits 200 and 2 Pa)", loc("haze_world/two_guilds.py", r"threshold_a30: float"))
    add(G, "shape", "p*_i(T) = p*_i30 exp{[(DeltaH_i - DeltaG_c,i)/(4R)] (1/T - 1/303.15)}", bio.threshold_shape, "", ASSUMED,
        K2001, loc("haze_world/two_guilds.py", r"if config\.threshold_shape == \"fixed_energy\":"))
    add(G, "DeltaH_A, DeltaH_M", "Reaction enthalpies (acetogenesis, methanogenesis), per four-H₂ reaction", [-270700., -253000.],
        "J mol⁻¹", "source", K2001, loc("haze_world/two_guilds.py", r"-270700\."))
    add(G, "DeltaG_c,A, DeltaG_c,M", "Cessation energies, per four-H₂ reaction; source ranges are -5 to -7 and -6 to -8 kJ per mol H₂, "
        "that is -20 to -28 and -24 to -32 kJ per reaction",
        [bio.cessation_energy_a_j, bio.cessation_energy_m_j], "J mol⁻¹", ASSUMED, K2001 + " (ranges); chosen within them",
        loc("haze_world/two_guilds.py", r"cessation_energy_a_j: float"))

    G = "Switch"
    add(G, "T*", "Temperature at which R*_A = R*_M (reference)", t_sw, "K", "derived", "equation 2.3",
        "solved in table_s1.py with two_guilds.guilds")
    add(G, "R*(T*)", "Hydrogen requirement at the switch", ra, "Pa", "derived", "equation 2.3", "")
    add(G, "R*_A, R*_M at 278 K", "Requirements at 278 K", [g.rstar(ell) for g in tg.guilds(278. - 273.15, bio)], "Pa", "derived",
        "equation 2.3", "")
    add(G, "R*_A, R*_M at 283 K", "Requirements at 283 K", [g.rstar(ell) for g in tg.guilds(283. - 273.15, bio)], "Pa", "derived",
        "equation 2.3", "")

    G = "Hydrogen budget (equation 2.4)"
    add(G, "K_H", "Dissolved-H₂ storage coefficient (30 °C assay)", tg.HENRY_30C_MOL_L_PA, "mol L⁻¹ Pa⁻¹", "transferred",
        K2001 + " (section 2.3)", loc("haze_world/two_guilds.py", r"^HENRY_30C_MOL_L_PA"))
    add(G, "J", "Hydrogen input at the reference supply: 4 Phi (3600) / (N_A V)", core.supply_h2(ref), "mol H₂ L⁻¹ h⁻¹",
        ASSUMED, "habitat volume V is set so that J = 1e-6 at P = 0.30", loc("haze_world/population_coupling.py", r"^def supply_h2"))
    add(G, "k_ex", "Hydrogen exchange conductance", bio.exchange_mol_l_h_pa, "mol H₂ L⁻¹ h⁻¹ Pa⁻¹", ASSUMED, ASSUMED,
        loc("haze_world/population_coupling.py", r"exchange_mol_l_h_pa=1e-6 / 300"))
    add(G, "p_atm", "Atmospheric H₂ reservoir pressure (reference; atmospheric-hydrogen check in S7)", bio.atmosphere_pa, "Pa",
        "swept", ASSUMED, loc("haze_world/two_guilds.py", r"atmosphere_pa: float"))
    add(G, "p_atm sweep", "Reservoir pressures checked (C59)", [0, 1, 3, 10, 30, 100, 200], "Pa", "swept", ASSUMED,
        checked_loc("models/haze_world/review/check_atmospheric_h2.py", "PRESSURES = (0., 1., 3., 10., 30., 100., 200.)"))
    add(G, "p_0", "Lifeless hydrogen pressure p_atm + J/k_ex", bio.atmosphere_pa + core.supply_h2(ref) / bio.exchange_mol_l_h_pa,
        "Pa", "derived", "J, k_ex, p_atm", loc("haze_world/two_guilds.py", r"lifeless = config\.atmosphere_pa"))
    add(G, "P", "Supply potential: nominal donor supply scaled so that P = 0.30 gives the reference input; the reference is 0.30",
        list(b1.SUPPLIES), "", "swept", ASSUMED, loc("haze_world/dynamic_realisation.py", r"^SUPPLIES"))
    add(G, "Phi", "Donor supply as CH₄-equivalent flux, at P = 0.24, 0.30, 0.36",
        [core.reference(p).climate.donor_flux for p in b1.SUPPLIES], "molecules cm⁻² s⁻¹", "swept", ASSUMED,
        loc("haze_world/population_coupling.py", r"donor_flux=float\(potential"))
    add(G, "V", "Effective habitat volume per surface area, from J = 1e-6 at P = 0.30", volume, "L cm⁻²", ASSUMED, ASSUMED,
        loc("haze_world/population_coupling.py", r"volume = 4 \* flux_ref"))

    G = "Acetate fate (equation 2.5) and biomass export"
    add(G, "t_A", "Acetate removal time", ref.acetate_lifetime_yr, "yr", ASSUMED, ASSUMED,
        loc("haze_world/population_coupling.py", r"acetate_lifetime_yr: float"))
    add(G, "f", "Fraction of acetate removal routed to methane (reference, and the three values of the homogeneous map)",
        [ref.acetate_fraction, 0., .5, .9], "", "swept", ASSUMED,
        checked_loc("haze_world/dynamic_realisation.py", "itertools.product(model.CHEMISTRIES, (0., .5, .9), LOSSES, SUPPLIES)"))
    add(G, "k_rec, k_other", "Recycling and other removal: f/t_A and (1 - f)/t_A", "f/t_A, (1-f)/t_A", "yr⁻¹", "derived", "f, t_A",
        loc("haze_world/population_coupling.py", r"^def recycling_rates"))
    add(G, "recycling", "Recycling is constant (temperature-independent)", ref.recycling_variant, "", ASSUMED, ASSUMED,
        loc("haze_world/population_coupling.py", r"recycling_variant: str"))
    add(G, "eta_A, eta_M", "Catabolised fraction of uptake at coexistence, 1 - a_i ell/(m_i + ell/Y_i), at T*", eta, "", "derived",
        "a_i, ell, m_i, Y_i", "solved in table_s1.py")
    add(G, "yield per H₂", "Steady methane per H₂ taken up: f eta_A/4 and eta_M/4 (f = 0.5)", [.5 * eta[0] / 4, eta[1] / 4],
        "mol CH₄ mol⁻¹ H₂", "derived", "eta_i, f", "")
    add(G, "biomass export", "Lost biomass leaves with its retained hydrogen equivalents a_i (ell + max(-mu_i, 0)); it is not recycled to methane",
        "implemented", "", ASSUMED, ASSUMED, loc("haze_world/population_coupling.py", r"biomass_export_h2_mol_l_yr"))

    G = "Methane budget and column (equation 2.6)"
    add(G, "t_CH4", "Atmospheric methane lifetime", clim.lifetime_yr, "yr", ASSUMED, ASSUMED,
        loc("haze_world/methane_budget.py", r"lifetime_yr: float"))
    add(G, "Phi_abiotic", "Abiotic methane source (Earth-mass serpentinisation estimate)", clim.abiotic_flux, "molecules cm⁻² s⁻¹",
        "source", A2016, loc("haze_world/methane_budget.py", r"abiotic_flux: float"))
    add(G, "p_s", "Surface pressure, case B", float(cases["surface_pressure_bar"]) * 1e5, "Pa", "source", A2016,
        "models/haze_response/arney2016/cases.csv")
    add(G, "p_CO2", "CO₂ pressure, case B", float(cases["p_co2_bar"]) * 1e5, "Pa", "source", A2016,
        "models/haze_response/arney2016/cases.csv")
    add(G, "M_air, g", "Mean molar mass of air and gravity used for the column", [budget.AIR_MOLAR_MASS, budget.GRAVITY],
        "kg mol⁻¹; m s⁻²", ASSUMED, ASSUMED + " (N₂-dominated background)", loc("haze_world/methane_budget.py", r"^GRAVITY"))
    add(G, "N_A, s yr⁻¹", "Avogadro constant; seconds per year", [budget.AVOGADRO, budget.SECONDS_PER_YEAR], "mol⁻¹; s yr⁻¹",
        "source", "standard values", loc("haze_world/methane_budget.py", r"^SECONDS_PER_YEAR"))
    add(G, "N_air", "Air column p_s N_A/(M_air g 10⁴)", atm["column"], "molecules cm⁻²", "derived", "p_s, M_air, g",
        loc("haze_world/methane_budget.py", r"column = pressure_bar"))
    add(G, "N_CO2", "CO₂ column f_CO2 N_air", n_co2, "molecules cm⁻²", "derived", "N_air, p_CO2/p_s", "")
    add(G, "c", "Column conversion (seconds per year)/N_CO2, for the abiotic and supply terms of (2.6)", atm["flux_to_ratio_per_yr"],
        "ratio yr⁻¹ per molecules cm⁻² s⁻¹", "derived", "N_CO2", loc("haze_world/methane_budget.py", r"flux_to_ratio_per_yr"))
    add(G, "chi", "Habitat conversion V N_A/N_CO2", core.inventory_to_ratio(ref), "ratio per mol L⁻¹", "derived", "V, N_A, N_CO2",
        loc("haze_world/population_coupling.py", r"^def inventory_to_ratio"))
    add(G, "loss law", "Methane removal rate r/t_CH4 (power law with elasticity 1)", f"{loss.kind}, elasticity {loss.elasticity:g}", "",
        ASSUMED, ASSUMED, loc("haze_world/population_coupling.py", r"Loss\(\.3, q\.lifetime_yr\)"))

    G = "Climate response (equation 2.7)"
    add(G, "case", "Arney et al. case B: surface pressure, CO₂, S/S0, epoch, surface albedo",
        [float(cases["surface_pressure_bar"]), float(cases["p_co2_bar"]), float(cases["solar_fraction"]),
         float(cases["epoch_ga"]), float(cases["surface_albedo"])], "bar; bar; ; Ga; ", "source", A2016,
        "models/haze_response/arney2016/cases.csv")
    add(G, "vertices r", "CH₄/CO₂ ratios of the ten extracted case-B vertices", list(resp.ratios), "", "source", A2016 + " fig. 4 (extracted)",
        "models/haze_response/arney2016/figure4.csv")
    add(G, "vertices T", "Temperatures at those vertices", list(resp.temperatures_k), "K", "source", A2016 + " fig. 4 (extracted)",
        "models/haze_response/arney2016/figure4.csv")
    add(G, "T_0", "Methane-free bridge temperature (bridge T_clim = T_0 + (T_first - T_0) ln(1 + r/s)/ln(1 + r_0/s) below r_0 = first vertex)",
        clim.t_zero_k, "K", ASSUMED, ASSUMED, loc("haze_world/population_coupling.py", r"Params\(t_zero_k=283"))
    add(G, "s", "Bridge scale", clim.bridge_scale, "ratio", ASSUMED, ASSUMED, loc("haze_world/methane_budget.py", r"bridge_scale: float"))
    add(G, "plateau", "Above the last vertex T_clim = T_last", float(resp.temperatures_k[-1]), "K", ASSUMED, ASSUMED,
        loc("haze_world/methane_budget.py", r"t\[r > hi\]"))
    add(G, "r at switch", "Methane ratio at the reference mixed state", r_sw, "", "derived", "equilibrium", "")
    add(G, "dT_clim/dr", f"Climate slope at the switch (between extracted vertices {seg + 1} and {seg + 2}, counted from 1)", slope, "K per unit ratio", "derived",
        A2016, "")
    add(G, "tau", "Thermal response time (equation 2.7); tau = 0 is instantaneous", "0 to 10000", "yr", "swept", ASSUMED,
        loc("haze_world/dynamic_realisation.py", r"^LAGS"))
    add(G, "tau grid", "Lag grid of the spectral maps", list(b1.LAGS), "yr", "swept", ASSUMED, loc("haze_world/dynamic_realisation.py", r"^LAGS"))

    G = "B4 sensitivity and two-layer check"
    add(G, "t_CH4 (B4)", "Methane-lifetime sensitivity at fixed/products chemistry, f = 0 or 0.5, and all listed ell and P values",
        [6000., 10000., 19000.], "yr", "swept", ASSUMED,
        checked_loc("haze_world/dynamic_realisation.py", "itertools.product(('fixed', 'products'), (0., .5), LOSSES, SUPPLIES, (6000., 10000., 19000.))"))
    add(G, "climate slope (B4)", "Multiplier on the local climate derivative for each lifetime-sensitivity state; equilibrium climate unchanged",
        [.5, 1., 2.], "", "swept", ASSUMED,
        checked_loc("haze_world/dynamic_realisation.py", "(.5, 1., 2.)"))
    add(G, "two-layer constants", "Implemented deep/surface heat-capacity ratio; exchange/feedback coefficient ratio. Surface: (T_clim - 2T_surface + T_deep)/tau; deep: (T_surface - T_deep)/(100 tau)",
        [100., 1.], "ratio; ratio", ASSUMED, "dimensionless check, not an ocean calibration",
        checked_loc("haze_world/dynamic_realisation.py", "out[n, n] = -2/tau", "out[n, n+1] = 1/tau",
                    "out[n+1, n] = 1/(100*tau)", "out[n+1, n+1] = -1/(100*tau)"))
    add(G, "two-layer subset", "Source-state selectors; earlier finite-grid sigma = 3 K cases remain unresolved and are not continuum-habitat evidence",
        "fixed/products; f = 0.5; ell = 0.001 h^-1; sigma = 0 or 3 K; n = 1 or 33; all P", "", "design choice", ASSUMED,
        checked_loc("haze_world/dynamic_realisation.py", "item['chemistry'] not in ('fixed', 'products') or item['fraction'] != .5 or item['loss_h'] != .001",
                    "item['sigma_k'] not in (0., 3.) or item['n_habitats'] not in (1, 33)"))

    G = "Product feedback and dials (equation 2.8, 2.9)"
    add(G, "C_ref", "Acetate reference activity", ref.acetate_reference_mol_l, "mol L⁻¹", ASSUMED, ASSUMED,
        loc("haze_world/population_coupling.py", r"acetate_reference_mol_l: float"))
    add(G, "p_CH4,ref", "Methane reference activity", ref.methane_reference_pa, "Pa", ASSUMED, ASSUMED,
        loc("haze_world/population_coupling.py", r"methane_reference_pa: float"))
    add(G, "feedback form", "Threshold multipliers (C/C_ref)^(a/4) and (r p_CO2/p_CH4,ref)^(m/4); chemistries (a, m) = (0,0), (0,1), (1,0), (1,1)",
        "fixed, methane_only, acetate_only, products", "", ASSUMED, ASSUMED, loc("haze_world/dynamic_core.py", r"def local_guilds"))
    add(G, "kappa (D1)", "Acetate-exponent dial, a = kappa, m = 0", list(dials.KAPPAS), "", "swept", ASSUMED,
        loc("haze_world/graded_dials.py", r"^KAPPAS"))
    add(G, "f (D1)", "Recycling fractions on D1", [value for stage, value in dials.BRANCHES if stage == "D1"], "", "swept", ASSUMED, loc("haze_world/graded_dials.py", r"^BRANCHES"))
    add(G, "sigma (D2)", "Habitat half-width of the uniform temperature spread", list(dials.SIGMAS), "K", "swept", ASSUMED,
        loc("haze_world/graded_dials.py", r"^SIGMAS"))
    add(G, "d (D2)", "Cell exchange rate on D2", [dials.BRANCHES[2][1], dials.BRANCHES[3][1]], "yr⁻¹", "swept", ASSUMED,
        loc("haze_world/graded_dials.py", r"^BRANCHES"))
    add(G, "C1 map", "Resolved habitat map: sigma (K); d (yr⁻¹); chemistry; f; P", "1, 3, 6; 1e-4, 1e-3, 1e-2, 1e-1; fixed, products; 0, 0.5; 0.30 (sigma = 3 K also 0.24, 0.36)",
        "", "swept", ASSUMED, checked_loc("haze_world/continuum_experiments.py",
            "itertools.product(('fixed','products'),(0.,.5),(1.,3.,6.),(1e-4,1e-3,1e-2,1e-1),(.3,))",
            "itertools.product(('fixed','products'),(0.,.5),(3.,),(1e-4,1e-3,1e-2,1e-1),(.24,.36))"))
    add(G, "B1 map spreads", "Equal-weight grid spreads of the earlier stage", list(b1.SPREADS), "K", "swept", ASSUMED,
        loc("haze_world/dynamic_realisation.py", r"^SPREADS"))

    G = "Invasions and the one-cell rule"
    add(G, "X_seed", f"Invader dose (about {seed * v_global / process.cell_mass_gdw:.3e} global cells)", seed, "gDW L⁻¹", ASSUMED, ASSUMED,
        checked_loc("haze_world/finite_experiments.py", 'state[1 if case.direction == "A_into_M" else 2] = 1e-12'))
    add(G, "m_cell", "Dry mass per cell, both groups", process.cell_mass_gdw, "gDW cell⁻¹", ASSUMED, ASSUMED,
        loc("haze_world/finite_populations.py", r"cell_mass_gdw: float"))
    add(G, "A_eff", "Effective habitat area", process.surface_cm2, "cm²", ASSUMED, ASSUMED,
        loc("haze_world/finite_populations.py", r"surface_cm2: float"))
    add(G, "V_global", "Global habitat volume A_eff V", v_global, "L", "derived", "A_eff, V", "")
    add(G, "census interval", "Scheduled census; a group with fewer than the minimum cells is removed", process.census_yr, "yr", ASSUMED,
        ASSUMED + " (motivated by Mollison 1991)", loc("haze_world/finite_populations.py", r"census_yr: float"))
    add(G, "minimum cells", "Census floor (equivalent to m_cell/V_global gDW L⁻¹)", process.minimum_cells, "cells", ASSUMED, ASSUMED,
        loc("haze_world/finite_populations.py", r"minimum_cells: float"))
    add(G, "floor", "Census floor in biomass concentration", process.minimum_cells * process.cell_mass_gdw / v_global, "gDW L⁻¹", "derived",
        "m_cell, V_global", "")
    add(G, "immigration", "Cell immigration after the invader dose", 0, "cells yr⁻¹", ASSUMED, ASSUMED,
        loc("haze_world/dynamic_transients.py", r"class Coordinates"))
    add(G, "B3 design", "Invasions: 2 directions x 2 chemistries (fixed, products) x f in {0, 0.5} x tau in {0, 3, 30} yr", n_b3, "runs",
        "swept", ASSUMED, loc("haze_world/dynamic_transients.py", r"^def design"))
    add(G, "B3 duration", "Invasion run length", [c.years for c in design if c.stage == "B3"][0], "yr", ASSUMED, ASSUMED,
        loc("haze_world/dynamic_transients.py", r"years: float = 100000"))
    add(G, "B2 design", "Kicked runs (f, tau): " + "; ".join(f"({c.fraction:g}, {c.tau_yr:g})" for c in b2) + f"; {b2[0].years:g} yr each",
        len(b2), "runs", "swept", ASSUMED, loc("haze_world/dynamic_transients.py", r"for f, tau in \(\(0\.,1\.\)"))
    add(G, "kick", "Log kick to acetogen biomass at the mixed state", .001, "ln units", ASSUMED, ASSUMED,
        loc("haze_world/dynamic_transients.py", r"y\[1\]\*=np\.exp\(\.001\)"))

    G = "Numerical tolerances"
    add(G, "root grid", "Initial ratio-grid points of the homogeneous root search", inspect.signature(dynamic.single_equilibria).parameters["n_grid"].default, "points", NUMERICAL, "algorithm setting",
        loc("haze_world/dynamic_core.py", r"def single_equilibria"))
    add(G, "root bracketing", "Brent tolerance on the methane ratio", 1e-13, "", NUMERICAL, "algorithm setting",
        checked_loc("haze_world/dynamic_core.py", "brentq(fun, a, b, xtol=1e-13)"))
    add(G, "root acceptance", "State-scaled residual of the full balance, and per-capita residual of the biomass equations",
        [1e-6, 1e-7], "(scaled); yr⁻¹", NUMERICAL, "algorithm setting", checked_loc("haze_world/dynamic_core.py", 'residual < 1e-6', 'percapita > 1e-7'))
    add(G, "exact pinning", "|S| below which a state is classed as exactly pinned", 1e-6, "K per e-fold", NUMERICAL, "classification threshold",
        checked_loc("models/haze_world/review/check_frontier_envelope.py", 'abs(r["Sc"]) < 1e-6'))
    add(G, "temperature step", "Step of the five-point temperature derivative in the Jacobian", inspect.signature(dynamic.jacobian_blocks).parameters["temperature_step"].default, "K", NUMERICAL, "algorithm setting",
        loc("haze_world/dynamic_core.py", r"temperature_step=1e-4"))
    add(G, "zero-lag spectrum", "Real part separating stable, neutral and unstable at tau = 0", 1e-9, "yr⁻¹", NUMERICAL, "algorithm setting",
        checked_loc("haze_world/dynamic_realisation.py", "value(0.) >= -1e-9", "value(0.) > 1e-9"))
    add(G, "critical-lag search", "Homogeneous: lag grid plus 29 log-spaced points from 0.001 to 1e4 yr; Brent tolerance 1e-8 yr. "
        "Resolved habitats: grid plus 22 log-spaced points; Brent tolerance 1e-7 yr. Censoring at 1e4 yr",
        "29, 22 points", "", NUMERICAL, "algorithm setting", checked_loc("haze_world/dynamic_realisation.py", "np.geomspace(.001, 1e4, 29)", "brentq(value, left, float(right), xtol=1e-8)")
        + "; " + checked_loc("haze_world/continuum_experiments.py", "np.geomspace(.001,1e4,22)", "brentq(scalar,left,float(right),xtol=1e-7)"))
    add(G, "quadrature", "Gauss-Legendre nodes per panel; initial panels; panel refinement when the acetogen-share logit changes by more than 1; node cap",
        [inspect.signature(continuum.gauss_mesh).parameters["order"].default, 4,
         inspect.signature(continuum.refine_panels).parameters["max_logit_change"].default,
         inspect.signature(continuum.adaptive_equilibrium).parameters["max_nodes"].default], "", NUMERICAL, "algorithm setting",
        checked_loc("haze_world/continuum_core.py", "edges = np.linspace(-sigma, sigma, 5) if panels is None else np.asarray(panels)")
        + "; function defaults: gauss_mesh.order, refine_panels.max_logit_change, adaptive_equilibrium.max_nodes")
    add(G, "doubling test", "Supply slopes within max(0.001 K, 2%); finite margins within 2%; censoring classes agree; frozen-composition slope agrees with a finite supply difference",
        [1e-3, .02], "K; relative", NUMERICAL, "algorithm setting", checked_loc("haze_world/continuum_experiments.py", "abs(a[k]-b[k])<=max(.001,.02*abs(b[k]))", "abs(a['tau_c']-b['tau_c'])<=.02*abs(b['tau_c'])"))
    add(G, "habitat Newton", "Equilibrium tolerance and maximum steps of the weighted-habitat solver", [inspect.signature(continuum.equilibrium).parameters[key].default for key in ("tolerance", "max_steps")], "", NUMERICAL, "algorithm setting",
        loc("haze_world/continuum_core.py", r"def equilibrium\(seed,p,tolerance"))
    add(G, "sparse spectrum", "Shift-invert eigensolver shifts and relative tolerance (used above 2048 states)",
        ", ".join(f"{v.imag:g}i" if np.imag(v) else f"{np.real(v):g}" for v in continuum_runs.SHIFTS) + "; 1e-10",
        "yr⁻¹ (shifts); dimensionless (tolerance)", NUMERICAL, "algorithm setting", checked_loc("haze_world/continuum_experiments.py", "size<=2048", "model.spectrum(y,p,tau,blocks=blocks,shifts=SHIFTS,tolerance=1e-10)"))
    add(G, "trajectory solver", "LSODA in positive coordinates: relative tolerance, maximum step, sample interval",
        [lag_sig["rtol"].default, lag_sig["max_step"].default, lag_sig["sample_step"].default], "dimensionless; yr; yr", NUMERICAL, "algorithm setting",
        loc("haze_world/dynamic_transients.py", r"^def integrate"))
    add(G, "trajectory atol", "Absolute tolerances in order p, X_A, X_M, C, r (then T when tau > 0)", "1e-9, 1e-9, 1e-9, 1e-10, 1e-12 (1e-8)",
        "solver-coordinate units (K)", NUMERICAL, "algorithm setting", checked_loc("haze_world/dynamic_transients.py", "np.r_[[1e-9,1e-9,1e-9,1e-10,1e-12],1e-8] if tau else [1e-9,1e-9,1e-9,1e-10,1e-12]"))
    add(G, "tight controls", "Cases B2_f0_tau1, B2_f0_tau100, B3_fixed_f0.5_tau3_A_into_M and B3_products_f0.5_tau3_M_into_A rerun with rtol 2e-9, maximum step 2 yr, sample 0.5 yr", [2e-9, 2., .5], "dimensionless; yr; yr", NUMERICAL,
        "algorithm setting", checked_loc("haze_world/dynamic_transient_assessment.py", "pool.submit(runs.run_case,c,raw,2e-9,2.,.5)", "requested={'B2_f0_tau1','B2_f0_tau100','B3_fixed_f0.5_tau3_A_into_M','B3_products_f0.5_tau3_M_into_A'}"))
    add(G, "threshold refinement", "Bisection of the dial for the 30-yr margin: target; maximum iterations; stop when the price brackets agree within max(0.001, 2%) and the margins within 2% of the target",
        [inspect.signature(thresholds.refine).parameters["target"].default, 24], "yr; iterations", NUMERICAL, "algorithm setting", checked_loc("haze_world/graded_thresholds.py", "range(24)", "price_error<=max(.001,.02*abs(hi['Sc'])) and finite and lag_value(hi)-lag_value(lo)<=.02*target"))
    add(G, "dial continuation", "Maximum bisection depth when a continuation step fails: D1; D2", [16, inspect.signature(spread._advance).parameters["max_depth"].default], "", NUMERICAL, "algorithm setting",
        checked_loc("haze_world/graded_dials.py", "depth>=16"))
    return rows


def kinetics_table():
    bio = core.reference().biology
    out = []
    for tcel in tg.TEMPERATURES_C:
        ka, km = parameters(tcel, ACETOGEN), parameters(tcel, MSB)
        a, m = tg.guilds(tcel, bio)
        out.append({
            "T_C": num(tcel), "T_K": num(tcel + 273.15),
            "V_A": num(ka.vmax_nmol_h), "V_A 95% half-width": num(ka.vmax_ci), "K_A": num(ka.km_pa), "K_A 95% half-width": num(ka.km_ci),
            "V_M": num(km.vmax_nmol_h), "V_M 95% half-width": num(km.vmax_ci), "K_M": num(km.km_pa), "K_M 95% half-width": num(km.km_ci),
            "s_A": num(a.rate_scale, 6), "s_M": num(m.rate_scale, 6),
            "m_A": num(a.maintenance, 6), "m_M": num(m.maintenance, 6),
            "p*_A": num(a.threshold_pa, 6), "p*_M": num(m.threshold_pa, 6),
            "R*_A": num(a.rstar(bio.loss_h), 6), "R*_M": num(m.rstar(bio.loss_h), 6)})
    return out


KINETICS_UNITS = ("V in nmol H₂ h⁻¹ per 20-mL culture and K in Pa (source, with 95% half-widths from the paper); "
                  "s in mol H₂ gDW⁻¹ h⁻¹; m in mol H₂ gDW⁻¹ h⁻¹; p* and R* in Pa. "
                  "s, m, p* and R* are computed by two_guilds.guilds for the reference configuration at ell = 0.001 h⁻¹, fixed products.")


def write_csv(path, rows, columns):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def md_table(rows, columns):
    esc = lambda s: str(s).replace("|", "\\|")
    lines = ["| " + " | ".join(columns) + " |", "|" + "|".join("---" for _ in columns) + "|"]
    lines += ["| " + " | ".join(esc(r.get(c, "")) for c in columns) + " |" for r in rows]
    return "\n".join(lines)


def write_s1(rows):
    write_csv(ESM / "table_s1.csv", rows, COLUMNS)
    parts = ["# Table S1. Parameters of the haze-world model", "",
             "Generated by `uv run python -m terra_prisca.haze_world.paper_figures table_s1`. "
             "Scope: the reference coupled model and the paper's Stage B/B′/B″ designs, including B4 sensitivity settings; earlier exploratory stages are not inventoried. "
             "Values are read from parameter objects, source data and function defaults, or computed from them. "
             "Reported literal design settings have explicit parsed-source checks. These checks cover the recorded expressions, not every possible model change. "
             "Basis: source = quoted from a publication; transferred = a measurement applied beyond its original system; "
             "assumption = chosen here; derived = computed from other rows; swept = varied over the listed values; numerical choice = an algorithm or classification setting; design choice = a selected subset. "
             "Unmarked code locations are navigation hints, not value checks, in `src/terra_prisca/haze_world/`; full repository paths identify external check scripts. "
             "This table describes current source values; archived-result provenance remains in each producer's manifests and source epochs. "
             f"The six-temperature kinetic values with derived s, m, p* and R* are in `{KINETICS_NOTE}.md`.", ""]
    group = None
    buffer = []
    for row in rows + [dict(group=None)]:
        if row["group"] != group:
            if buffer:
                parts += [f"## {group}", "", md_table(buffer, COLUMNS), ""]
            group, buffer = row["group"], []
        if row["group"] is not None:
            buffer.append(row)
    (ESM / "table_s1.md").write_text("\n".join(parts))
    kin = kinetics_table()
    write_csv(ESM / f"{KINETICS_NOTE}.csv", kin, list(kin[0]))
    (ESM / f"{KINETICS_NOTE}.md").write_text(
        "# Table S1 (continued). Six-temperature kinetics and derived temperature laws\n\n" + KINETICS_UNITS + "\n\n"
        + md_table(kin, list(kin[0])) + "\n")


def main():
    ESM.mkdir(parents=True, exist_ok=True)
    rows = build_rows()
    write_s1(rows)
    from . import esm_tables
    extra = esm_tables.main()
    return f"{len(rows)} parameter rows, 6 temperatures; {extra}"
