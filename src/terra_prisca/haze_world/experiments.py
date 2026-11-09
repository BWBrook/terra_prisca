"""First experiments with the methane-budget skeleton.

    uv run python -m terra_prisca.haze_world.experiments [outdir]

Writes budget_sweeps.csv, setpoint.csv, regimes.csv and budget_figures.png
(default outdir models/haze_world/figures).
"""

from __future__ import annotations

import csv
import sys
from dataclasses import replace
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .methane_budget import (
    Params,
    atmosphere,
    capture_efficiency,
    domain,
    equilibria,
    response,
    sweep,
    temperature_k,
    tendency,
)

R_POT = np.linspace(0.0, 0.4, 201)  # potential ratio: what the whole supply would sustain
HIGH_R_POT = 0.4


def flux_for_potential(r_pot: float | np.ndarray, p: Params) -> float | np.ndarray:
    return np.asarray(r_pot) / (p.lifetime_yr * atmosphere(p.case)["flux_to_ratio_per_yr"])


def cold_edge_k(p: Params) -> float:
    """Temperature below which methanogens cannot capture any supply (eta = 0)."""
    need = 1.0 + p.maintenance_flux / p.donor_flux
    return p.t_opt_k - p.t_halfwidth_k * np.sqrt(1.0 - need / p.growth_ratio_max)


def t_opt_for_edge(edge_k: float, p: Params) -> float:
    need = 1.0 + p.maintenance_flux / p.donor_flux
    return edge_k + p.t_halfwidth_k * np.sqrt(1.0 - need / p.growth_ratio_max)


def biotic_branch(p: Params) -> dict | None:
    alive = [e for e in equilibria(p) if e["stable"] and e["eta"] > 0]
    return alive[-1] if alive else None


def domain_invariant(p: Params) -> bool:
    """True if the flow points into Arney's extracted domain at both ends, so any
    trajectory started inside it stays there and no closure assumption is used."""
    lo, hi = response(p.case).ratios[[0, -1]]
    return bool(tendency(lo, p) > 0 and tendency(hi, p) < 0)


def run_sweeps(p: Params) -> list[dict]:
    rows = []
    for label, q in (("thermal", p), ("temperature-independent", replace(p, thermal=False))):
        fluxes = flux_for_potential(R_POT, q)
        up = sweep(fluxes, q, r0=0.0)
        down = sweep(fluxes[::-1], q, r0=HIGH_R_POT * 1.5)[::-1]
        for direction, run in (("up from lifeless", up), ("down from high supply", down)):
            for r_pot, e in zip(R_POT, run):
                rows.append({"methanogens": label, "direction": direction, "r_pot": round(float(r_pot), 4),
                             "donor_flux": f"{e['donor_flux']:.4e}", "r": round(e["r"], 6),
                             "t_k": round(e["t_k"], 3), "eta": round(e["eta"], 5), "domain": e["domain"]})
    return rows


def run_setpoint(p: Params) -> list[dict]:
    rows = []
    for case in "ABCD":
        q0 = replace(p, case=case)
        q0 = replace(q0, donor_flux=float(flux_for_potential(HIGH_R_POT * response(case).ratios[-1] / 0.2333, q0)))
        for edge in np.arange(250.0, 300.01, 1.0):
            q = replace(q0, t_opt_k=t_opt_for_edge(edge, q0))
            e = biotic_branch(q)
            rows.append({"case": case, "cold_edge_k": edge, "t_k": round(e["t_k"], 3) if e else "",
                         "r": round(e["r"], 6) if e else "", "domain": e["domain"] if e else "none",
                         "domain_invariant": domain_invariant(q)})
    return rows


def run_regimes(p: Params) -> list[dict]:
    q0 = replace(p, donor_flux=float(flux_for_potential(0.3, p)))
    rows = []
    for t0 in np.arange(250.0, 292.01, 1.0):
        for edge in np.arange(250.0, 300.01, 1.0):
            q = replace(q0, t_zero_k=t0, t_opt_k=t_opt_for_edge(edge, q0))
            stable = [e for e in equilibria(q) if e["stable"]]
            lifeless = any(e["eta"] == 0 for e in stable)
            biotic = any(e["eta"] > 0 for e in stable)
            rows.append({"t_zero_k": t0, "cold_edge_k": edge,
                         "regime": {(True, False): "lifeless only", (False, True): "biotic only",
                                    (True, True): "bistable"}[(lifeless, biotic)]})
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def plot(p: Params, sweeps: list[dict], setpoint: list[dict], regimes: list[dict], out: Path) -> None:
    fig, axs = plt.subplots(2, 2, figsize=(11, 8.5))
    resp = response(p.case)
    edge = cold_edge_k(replace(p, donor_flux=float(flux_for_potential(0.3, p))))

    ax = axs[0, 0]
    r = np.linspace(0.0, 0.3, 1201)
    for t0, ls in ((255.0, ":"), (p.t_zero_k, "-"), (280.0, "--")):
        q = replace(p, t_zero_k=t0)
        m = domain(r, q) == "bridge"
        ax.plot(r[m], temperature_k(r[m], q), ls, color="0.5", lw=1, label=f"bridge, T0 = {t0:.0f} K")
    ax.plot(resp.ratios, resp.temperatures_k, "k-", lw=2, label=f"Arney et al. (2016) case {p.case}")
    ax.plot([resp.ratios[-1], 0.3], [resp.temperatures_k[-1]] * 2, color="0.5", lw=1, ls="-.", label="plateau")
    ax.axhspan(edge, 320, color="tab:green", alpha=0.08, label=f"methanogens viable (T > {edge:.0f} K)")
    ax.set(xlabel="surface CH$_4$/CO$_2$", ylabel="surface temperature (K)", ylim=(250, 300),
           title="(a) climate closure")
    ax.legend(fontsize=7, loc="lower right")

    ax = axs[0, 1]
    for label, color in (("thermal", "tab:red"), ("temperature-independent", "tab:blue")):
        for direction, ls in (("up from lifeless", "-"), ("down from high supply", "--")):
            rows = [s for s in sweeps if s["methanogens"] == label and s["direction"] == direction]
            ax.plot([s["r_pot"] for s in rows], [s["t_k"] for s in rows], ls, color=color, lw=1.4,
                    label=f"{label}, {direction}")
    for r_pot in R_POT[::4]:
        q = replace(p, donor_flux=float(flux_for_potential(r_pot, p)))
        for e in equilibria(q):
            if not e["stable"]:
                ax.plot(r_pot, e["t_k"], ".", color="0.6", ms=3)
    ax.plot([], [], ".", color="0.6", label="unstable equilibria (thermal)")
    ax.axhline(edge, color="tab:green", lw=0.8, ls=":")
    ax.set(xlabel=r"potential CH$_4$/CO$_2$ = $\tau c \Phi$ (0.1 $\approx$ 1.25$\times$10$^{11}$ cm$^{-2}$ s$^{-1}$ at $\tau$ = 10 kyr)",
           ylabel="equilibrium temperature (K)", title=f"(b) case {p.case}: equilibria as donor supply rises and falls")
    ax.legend(fontsize=6.5, loc="lower right")

    ax = axs[1, 0]
    for case, color in zip("ABCD", ("tab:blue", "tab:red", "tab:purple", "tab:orange")):
        rows = [s for s in setpoint if s["case"] == case and s["t_k"] != ""]
        x = np.array([s["cold_edge_k"] for s in rows])
        y = np.array([s["t_k"] for s in rows])
        inv = np.array([s["domain_invariant"] for s in rows])
        ax.plot(x, y, "-", color=color, lw=1, label=f"case {case}")
        ax.plot(x[inv], y[inv], "o", color=color, ms=3)
    ax.plot([250, 300], [250, 300], "k:", lw=0.8, label="T = cold edge")
    ax.set(xlabel="methanogens' cold edge (K)", ylabel="biotic equilibrium temperature (K)",
           title="(c) high supply: set point vs thermal tolerance\n(dots: Arney domain is invariant, no closure assumption used)")
    ax.legend(fontsize=7)

    ax = axs[1, 1]
    names = ["lifeless only", "bistable", "biotic only"]
    t0s = sorted({s["t_zero_k"] for s in regimes})
    edges = sorted({s["cold_edge_k"] for s in regimes})
    grid = np.full((len(edges), len(t0s)), np.nan)
    for s in regimes:
        grid[edges.index(s["cold_edge_k"]), t0s.index(s["t_zero_k"])] = names.index(s["regime"])
    cmap = matplotlib.colors.ListedColormap(["#cfd8dc", "#ffcc80", "#a5d6a7"])
    ax.pcolormesh(t0s, edges, grid, cmap=cmap, vmin=-0.5, vmax=2.5, shading="nearest")
    for i, n in enumerate(names):
        ax.plot([], [], "s", color=cmap(i), label=n)
    ax.plot([250, 292], [250, 292], "k:", lw=0.8)
    ax.set(xlabel="zero-methane temperature T0 (bridge assumption, K)", ylabel="methanogens' cold edge (K)",
           title=f"(d) case {p.case}, potential ratio 0.3: stable states")
    ax.legend(fontsize=7, loc="upper left")

    fig.tight_layout()
    fig.savefig(out, dpi=130)


def main(outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    p = Params()
    sweeps, setpoint, regimes = run_sweeps(p), run_setpoint(p), run_regimes(p)
    write_csv(outdir / "budget_sweeps.csv", sweeps)
    write_csv(outdir / "setpoint.csv", setpoint)
    write_csv(outdir / "regimes.csv", regimes)
    plot(p, sweeps, setpoint, regimes, outdir / "budget_figures.png")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("models/haze_world/figures"))
