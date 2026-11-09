"""Stage-3 fixed-temperature H2 competition, separate from climate feedback.

    uv run python -m terra_prisca.haze_world.two_guilds [output_directory]

Source ratios, transferred absolute scales and structural assumptions are
separate. Time is hours, biomass gDW/L, uptake mol H2/gDW/h and supply mol/L/h.
"""

from dataclasses import dataclass, replace
import csv
from functools import lru_cache
from hashlib import sha256
import itertools
import json
from pathlib import Path
import sys

import numpy as np
from scipy.integrate import solve_ivp

from .hydrogen_uptake import ACETOGEN, MSB, MSP, parameters
from .woodii1998 import (BIOMASS_ACETATE_EQUIVALENT, MAINTENANCE_H2,
                         Y_H2_REPORTED, inferred_reference_uptake)

BASE = Path(__file__).resolve().parents[3] / "models/haze_world"
TEMPERATURES_C = (4., 10., 15., 20., 25., 30.)
GAS_CONSTANT = 8.314
HENRY_30C_MOL_L_PA = 7.65e-9
FIRST_ORDER_LIMIT_MOL_L = 450e-6
ASSIMILATION_A = 4 * BIOMASS_ACETATE_EQUIVALENT


@dataclass(frozen=True)
class Competition:
    methanogen: str = MSB
    capacity_ratio: float = 0.74
    yield_m: float = 0.78
    maintenance_m30: float = 1e-3
    loss_h: float = 1e-3
    threshold_a30: float = 20.
    threshold_shape: str = "constant"
    msp_threshold_4c: float = 20.
    maintenance_energy_j: float = 69000.
    kinetics: str = "saturating"
    assimilation_m: float = 0.

    def __post_init__(self):
        if self.methanogen not in (MSB, MSP):
            raise ValueError("Methanogen must be MSB or MSP")
        if self.threshold_shape not in ("constant", "fixed_energy") or self.kinetics not in ("saturating", "first_order"):
            raise ValueError("Unknown structural scenario")
        values = (self.capacity_ratio, self.yield_m, self.maintenance_m30, self.loss_h,
                  self.threshold_a30, self.msp_threshold_4c, self.maintenance_energy_j,
                  self.assimilation_m)
        if not all(np.isfinite(v) and v >= 0 for v in values) or min(self.capacity_ratio, self.yield_m, self.loss_h, self.msp_threshold_4c) <= 0:
            raise ValueError("Parameters must be finite and nonnegative; capacity, yield, loss and MSP cold level positive")
        if self.assimilation_m * self.yield_m > 1:
            raise ValueError("Biomass synthesis cannot consume more H2 than uptake")


@dataclass(frozen=True)
class Guild:
    name: str
    rate_scale: float
    km_pa: float
    threshold_pa: float
    yield_g_mol: float
    maintenance: float
    assimilation_mol_g: float
    kinetics: str

    def uptake(self, pressure_pa):
        pressure = np.asarray(pressure_pa, dtype=float)
        available = np.maximum(pressure - self.threshold_pa, 0.)
        if self.kinetics == "saturating":
            return self.rate_scale * available / (self.km_pa + available)
        return self.rate_scale * available / self.km_pa

    def net_growth(self, pressure_pa, loss_h):
        return self.yield_g_mol * (self.uptake(pressure_pa) - self.maintenance) - loss_h

    def rstar(self, loss_h):
        required = self.maintenance + loss_h / self.yield_g_mol
        if self.kinetics == "first_order":
            return self.threshold_pa + self.km_pa * required / self.rate_scale
        if required >= self.rate_scale:
            return np.inf
        return self.threshold_pa + self.km_pa * required / (self.rate_scale - required)


@lru_cache(maxsize=None)
def shape(temperature_c, strain):
    if not np.isfinite(temperature_c) or not 4 <= temperature_c <= 30:
        raise ValueError("Only the measured 4–30 C range is supported")
    rows = [parameters(t, strain) for t in TEMPERATURES_C]
    relative = np.interp(temperature_c, TEMPERATURES_C, [p.vmax_nmol_h for p in rows]) / rows[-1].vmax_nmol_h
    km = np.interp(temperature_c, TEMPERATURES_C, [p.km_pa for p in rows])
    return float(relative), float(km)


def maintenance_factor(temperature_c, energy_j):
    return float(np.exp(-energy_j / GAS_CONSTANT * (1 / (temperature_c + 273.15) - 1 / 303.15)))


def thresholds(temperature_c, config):
    a, m = config.threshold_a30, 1.
    if config.threshold_shape == "fixed_energy":
        delta = 1 / (temperature_c + 273.15) - 1 / 303.15
        a *= np.exp((-270700. - (-24000.)) / (4 * GAS_CONSTANT) * delta)
        m *= np.exp((-253000. - (-28000.)) / (4 * GAS_CONSTANT) * delta)
    if config.methanogen == MSP:
        # Unmeasured cold anomaly: join a swept 4 C level to the 15 C baseline.
        cold_baseline = 1. if config.threshold_shape == "constant" else np.exp(
            (-253000. - (-28000.)) / (4 * GAS_CONSTANT) * (1 / 277.15 - 1 / 303.15))
        weight = np.clip((15 - temperature_c) / 11, 0., 1.)
        m *= (config.msp_threshold_4c / cold_baseline) ** weight
    return float(a), float(m)


def guilds(temperature_c, config=Competition()):
    relative_a, km_a = shape(temperature_c, ACETOGEN)
    relative_m, km_m = shape(temperature_c, config.methanogen)
    pa, pm = thresholds(temperature_c, config)
    factor = maintenance_factor(temperature_c, config.maintenance_energy_j)
    return (
        Guild("acetogen", inferred_reference_uptake() * relative_a, km_a, pa,
              Y_H2_REPORTED, MAINTENANCE_H2 * factor, ASSIMILATION_A, config.kinetics),
        Guild("methanogen", inferred_reference_uptake() * config.capacity_ratio * relative_m,
              km_m, pm, config.yield_m, config.maintenance_m30 * factor,
              config.assimilation_m, "saturating"),
    )


def equilibrium(temperature_c, config=Competition(), supply=1e-6):
    """Constant-input resource equilibrium; no resource washout or climate.

    No viable consumer means H2 accumulates, not a finite lifeless equilibrium.
    First-order equilibria beyond the explicit concentration limit are unresolved.
    """
    if not np.isfinite(supply) or supply <= 0:
        raise ValueError("Supply must be positive")
    pair = guilds(temperature_c, config)
    roots = np.array([g.rstar(config.loss_h) for g in pair])
    winner = int(np.argmin(roots))
    pressure = roots[winner]
    status = "living"
    if not np.isfinite(pressure):
        status = "no_consumer"
    elif config.kinetics == "first_order" and pressure * HENRY_30C_MOL_L_PA > FIRST_ORDER_LIMIT_MOL_L:
        status = "outside_first_order_domain"
    elif np.isclose(roots[0], roots[1], rtol=1e-10, atol=1e-10):
        status = "tie"
    biomass = np.zeros(2)
    invasion = None
    if status == "living":
        biomass[winner] = supply / float(pair[winner].uptake(pressure))
        invasion = float(pair[1 - winner].net_growth(pressure, config.loss_h))
    return dict(status=status, winner=pair[winner].name if status == "living" else status,
                pressure_pa=float(pressure), rstar_a_pa=float(roots[0]), rstar_m_pa=float(roots[1]),
                biomass_g_l=biomass, invader_growth_h=invasion)


def delivery(pressure_pa, biomass_g_l, temperature_c, config=Competition(), acetate_fraction=0.):
    """Instantaneous routing to external acetate sinks/recyclers, not explicit M.

    No acetate residence time or biomass recycling is included.
    """
    if not 0 <= acetate_fraction <= 1:
        raise ValueError("Acetate-to-methane fraction must lie in [0, 1]")
    biomass = np.asarray(biomass_g_l, dtype=float)
    if biomass.shape != (2,) or np.any(~np.isfinite(biomass)) or np.any(biomass < 0) or not np.isfinite(pressure_pa) or pressure_pa < 0:
        raise ValueError("Pressure and two biomasses must be finite and nonnegative")
    pair = guilds(temperature_c, config)
    uptake = np.array([g.uptake(pressure_pa) for g in pair]) * biomass
    synthesis = np.array([max(g.yield_g_mol * (g.uptake(pressure_pa) - g.maintenance), 0.) for g in pair]) * biomass
    assimilation = synthesis * np.array([g.assimilation_mol_g for g in pair])
    catabolic = uptake - assimilation
    methane = (catabolic[1] + acetate_fraction * catabolic[0]) / 4
    total = float(np.sum(catabolic))
    return dict(uptake_h2_mol_l_h=uptake, biomass_h2_mol_l_h=assimilation,
                catabolic_h2_mol_l_h=catabolic, methane_mol_l_h=float(methane),
                nonmethane_acetate_mol_l_h=float((1 - acetate_fraction) * catabolic[0] / 4),
                acetogen_catabolic_share=float(catabolic[0] / total) if total else np.nan,
                routing_factor=float(4 * methane / total) if total else np.nan)


def integrate(temperature_c, config, pressure_pa, biomass_g_l, duration_h, *, supply=1e-6,
              storage_mol_l_pa=HENRY_30C_MOL_L_PA):
    """Integrate pressure and log biomasses, retaining arbitrarily rare strains.

    storage * dp/dt = supply - sum(q X) closes the pressure/inventory units.
    Storage is fixed at the 30 C Henry reference, an explicit dynamic assumption.
    """
    biomass = np.asarray(biomass_g_l, dtype=float)
    if biomass.shape != (2,) or np.any(biomass <= 0) or np.any(~np.isfinite(biomass)):
        raise ValueError("Both starting biomasses must be positive; no extinction threshold is imposed")
    if not all(np.isfinite(v) and v > 0 for v in (pressure_pa, duration_h, supply, storage_mol_l_pa)):
        raise ValueError("Initial pressure, duration, supply and storage must be positive")
    pair = guilds(temperature_c, config)

    def rhs(_, state):
        p, *logs = state
        populations = np.exp(logs)
        uptake = np.array([g.uptake(p) for g in pair])
        return np.r_[(supply - uptake @ populations) / storage_mol_l_pa,
                     [g.yield_g_mol * (q - g.maintenance) - config.loss_h for g, q in zip(pair, uptake)]]

    result = solve_ivp(rhs, (0., duration_h), np.r_[pressure_pa, np.log(biomass)],
                       method="Radau", rtol=1e-8, atol=1e-10, dense_output=True)
    if not result.success:
        raise RuntimeError(result.message)
    if config.kinetics == "first_order" and np.max(result.y[0]) * HENRY_30C_MOL_L_PA > FIRST_ORDER_LIMIT_MOL_L:
        raise ValueError("First-order trajectory left its declared concentration domain")
    return result


def parameter_grid(methanogen):
    for values in itertools.product((.38, .74, 1.5), (.4, .78, 1.7), (.3e-3, 1e-3, 2.3e-3),
                                    (1e-4, 1e-3, 1e-2), (5., 20., 95.)):
        yield Competition(methanogen=methanogen, capacity_ratio=values[0], yield_m=values[1],
                          maintenance_m30=values[2], loss_h=values[3], threshold_a30=values[4])


def counts(rows):
    return {w: sum(r["winner"] == w for r in rows) for w in (
        "acetogen", "methanogen", "no_consumer", "outside_first_order_domain", "tie")}


def run(output):
    output.mkdir(parents=True, exist_ok=True)
    summary = []
    # The 243 sets per structure use a shared capacity-ratio sensitivity for
    # comparison; MSP's source-normalization ratios differ and are noted below.
    for strain, form, threshold_shape in itertools.product((MSB, MSP), ("saturating", "first_order"), ("constant", "fixed_energy")):
        cold_levels = (20.,) if strain == MSB else (2., 20., 200.)
        for cold in cold_levels:
            configs = [replace(c, kinetics=form, threshold_shape=threshold_shape, msp_threshold_4c=cold)
                       for c in parameter_grid(strain)]
            all_cold = [equilibrium(4, c) for c in configs]
            match30 = [equilibrium(30, c)["winner"] == "methanogen" for c in configs]
            match20_30 = [ok and equilibrium(20, c)["winner"] == "methanogen" for c, ok in zip(configs, match30)]
            for label, keep in (("all", [True] * len(configs)), ("M_wins_30C", match30), ("M_wins_20_and_30C", match20_30)):
                rows = [r for r, ok in zip(all_cold, keep) if ok]
                summary.append(dict(strain=strain, kinetics=form, threshold_shape=threshold_shape,
                                    msp_threshold_4c_pa=cold if strain == MSP else None,
                                    condition=label, retained=len(rows), cold_4c=counts(rows),
                                    by_loss_h={str(d): counts([r for c, r, ok in zip(configs, all_cold, keep) if ok and c.loss_h == d])
                                               for d in (1e-4, 1e-3, 1e-2)}))
    status = dict(climate_coupled=False, summary=summary,
                  kinetics_variants={"saturating": "Both guilds saturating", "first_order": "Acetogen low-pressure-slope matched first order; methanogen stays saturating"},
                  source_capacity_ratios_30C={"MSB_dry_mass": (560 / 7) / (760 / 3.6),
                                             "MSB_culture": 560 / 760,
                                             "MSP_dry_mass": (360 / 6.6) / (760 / 3.6),
                                             "MSP_culture": 360 / 760},
                  maintenance_energy_j=69000., supply_mol_l_h=1e-6,
                  threshold_energy_assumptions_j_reaction={"acetogen": -24000, "methanogen": -28000},
                  first_order_limit_mol_l=FIRST_ORDER_LIMIT_MOL_L,
                  input_sha256={name: sha256((BASE / "evidence" / name).read_bytes()).hexdigest()
                                for name in ("peters1998_chemostat.csv", "kotsyurbenko2001_table2.csv")},
                  msb_scoping_grid_size=243, caveat="Counts are sensitivity-grid outcomes, not probabilities or a calibration")
    (output / "two_guilds_summary.json").write_text(json.dumps(status, indent=2) + "\n")
    slices = []
    for strain, form, d in itertools.product((MSB, MSP), ("saturating", "first_order"), (1e-4, 1e-3, 1e-2)):
        c = Competition(methanogen=strain, kinetics=form, loss_h=d)
        for t in np.linspace(4, 30, 131):
            eq = equilibrium(float(t), c)
            row = dict(strain=strain, kinetics=form, loss_h=d, temperature_c=float(t),
                       winner=eq["winner"], pressure_pa=eq["pressure_pa"] if np.isfinite(eq["pressure_pa"]) else None)
            for fac in (0., .5, 1.):
                if eq["status"] == "living":
                    routed = delivery(eq["pressure_pa"], eq["biomass_g_l"], float(t), c, fac)
                    row[f"routing_factor_fac_{fac:g}"] = routed["routing_factor"]
                    row[f"feed_conversion_fac_{fac:g}"] = 4 * routed["methane_mol_l_h"] / 1e-6
                else:
                    row[f"routing_factor_fac_{fac:g}"] = None
                    row[f"feed_conversion_fac_{fac:g}"] = None
            slices.append(row)
    with (output / "two_guilds_reference_slices.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(slices[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(slices)
    plot(output)
    print(json.dumps({"structural_scenarios": len(summary) // 3, "reference": summary[1]}, indent=2))


def plot(output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap, BoundaryNorm

    ts = np.linspace(4, 30, 131)
    ds = np.geomspace(1e-4, 1e-2, 91)
    fig, axes = plt.subplots(2, 2, figsize=(11, 8), constrained_layout=True)
    color = ListedColormap(["#9b661e", "#347b91", "#dddddd", "#ad70aa"])
    norm = BoundaryNorm(np.arange(-.5, 4.5), color.N)
    codes = {"acetogen": 0, "methanogen": 1, "no_consumer": 2, "outside_first_order_domain": 3, "tie": 3}
    for ax, (strain, form) in zip(axes.flat, itertools.product((MSB, MSP), ("saturating", "first_order"))):
        grid = [[codes[equilibrium(float(t), Competition(methanogen=strain, kinetics=form, loss_h=float(d)))["winner"]]
                 for t in ts] for d in ds]
        mesh = ax.pcolormesh(ts, ds, grid, cmap=color, norm=norm, shading="nearest", rasterized=True)
        ax.set(xlabel="Temperature (°C)", ylabel="Demographic loss (h⁻¹)", yscale="log",
               title=f"{strain.rsplit(' ', 1)[-1]} · {'Ac first order' if form == 'first_order' else 'both saturating'}")
    bar = fig.colorbar(mesh, ax=axes, ticks=range(4), shrink=.85)
    bar.ax.set_yticklabels(["Acetogen", "Methanogen", "No consumer", "Outside domain / tie"])
    fig.suptitle("Illustrative competition: γ=0.74, Yₘ=0.78, mₘ(30)=1 mmol g⁻¹ h⁻¹\nConstant p*ₐ=20 Pa; MSP p*(4)=20 Pa; not a fitted Archean ecosystem", fontsize=12)
    fig.savefig(output / "two_guilds_competition.png", dpi=150)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4), constrained_layout=True)
    for fac in (0., .5, 1.):
        values = [[], []]
        for t in ts:
            c = Competition(methanogen=MSP, loss_h=1e-3)
            eq = equilibrium(float(t), c)
            routed = delivery(eq["pressure_pa"], eq["biomass_g_l"], float(t), c, fac)
            values[0].append(routed["routing_factor"])
            values[1].append(4 * routed["methane_mol_l_h"] / 1e-6)
        for ax, curve in zip(axes, values):
            ax.plot(ts, curve, label=f"Acetate converted to methane: {fac:g}")
    axes[0].set(xlabel="Temperature (°C)", ylabel="4 CH₄ / catabolic H₂", ylim=(-.03, 1.05), title="Product routing")
    axes[1].set(xlabel="Temperature (°C)", ylabel="4 CH₄ / H₂ input", ylim=(-.03, 1.05), title="Routing plus biomass demand")
    axes[0].legend(fontsize=8)
    fig.suptitle("MSP illustrative slice; instantaneous acetate fate, no climate coupling")
    fig.savefig(output / "two_guilds_delivery.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    run(Path(sys.argv[1]) if len(sys.argv) > 1 else BASE / "figures/two_guilds")
