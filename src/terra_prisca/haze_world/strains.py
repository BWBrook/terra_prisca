"""Haze-world stage 2: strain-resolved methanogens with mutation and explicit extinction.

    uv run python -m terra_prisca.haze_world.strains [outdir]

A named variant of darwinian.py. Methanogens occupy bins on a grid of thermal
optima theta_i (spacing dtheta). Each bin follows the stage-1 physiology and
shares the donor pool and the climate:

    U_i   = delta rho_i(T) B_i D / (K + D)
    dB_i  = (1 - 2m) U_i + m (U_{i-1} + U_{i+1}) - delta B_i     (mutation on births)
    dD    = c Phi(t) - k_D D - sum U_i
    dM    = sum U_i + c Phi_abiotic - L(M),    T = T(M)

Mutation moves a fraction m of births one bin either way (reflecting ends) and
does not change methane production. Demographic extinction is explicit: every
`check_yr` years any bin below B_min is set to zero. A bin can be repopulated
only by mutation from a living neighbour; extinction of all bins is absorbing
(no immigration). Supply Phi(t) is the experimental forcing. Time is in years
with the stage-1 biology (delta = 1 yr-1, k_D = 0.1 yr-1); mutation rates are
uncalibrated and swept.
"""

from __future__ import annotations

import csv
import sys
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp

from .darwinian import Constraint, Loss, evolved, peak_growth, reference, singular_theta
from .experiments import flux_for_potential
from .methane_budget import Params, atmosphere, temperature_k


@dataclass(frozen=True)
class Grid:
    theta_min_k: float = 245.0
    theta_max_k: float = 310.0
    step_k: float = 0.5

    @property
    def theta(self) -> np.ndarray:
        n = int(round((self.theta_max_k - self.theta_min_k) / self.step_k)) + 1
        return self.theta_min_k + self.step_k * np.arange(n)


@dataclass(frozen=True)
class Run:
    constraint: Constraint
    loss: Loss
    mutation: float = 1e-6  # fraction of births moved one bin each way
    b_min_rel: float = 1e-9  # extinction threshold relative to the initial total biomass B*
    t_zero_k: float = 265.0  # low-methane bridge endpoint
    k_donor: float = 0.1
    death: float = 1.0
    check_yr: float = 1.0


def supply_schedule(phi0: float, phi1: float, start_yr: float, duration_yr: float):
    def phi(t):
        if t <= start_yr:
            return phi0
        if t >= start_yr + duration_yr:
            return phi1
        return phi0 + (phi1 - phi0) * (t - start_yr) / duration_yr
    return phi


class StrainModel:
    def __init__(self, p: Params, run: Run, grid: Grid = Grid()):
        self.p = replace(p, thermal=True, t_zero_k=run.t_zero_k)
        self.run, self.theta = run, grid.theta
        keep = self.theta >= run.constraint.floor_k
        self.theta = self.theta[keep]
        self.rho_peak = peak_growth(self.theta, run.constraint)
        self.c = atmosphere(p.case)["flux_to_ratio_per_yr"]
        self.half_sat = self.c * p.maintenance_flux / run.k_donor

    def rho(self, t_k: float) -> np.ndarray:
        return self.rho_peak * np.maximum(0.0, 1.0 - ((t_k - self.theta) / self.p.t_halfwidth_k) ** 2)

    def rhs(self, t, y, phi):
        r, m = self.run, self.run.mutation
        d, meth, b = max(y[0], 0.0), max(y[1], 0.0), np.maximum(y[2:], 0.0)
        u = r.death * self.rho(float(temperature_k(meth, self.p))) * b * d / (self.half_sat + d)
        births = (1 - 2 * m) * u
        births[1:] += m * u[:-1]
        births[:-1] += m * u[1:]
        births[0] += m * u[0]
        births[-1] += m * u[-1]
        total = u.sum()
        return np.r_[self.c * phi(t) - r.k_donor * d - total,
                     total + self.c * self.p.abiotic_flux - float(r.loss.rate(meth)),
                     births - r.death * b]

    def resident_state(self, phi: float) -> tuple[np.ndarray, dict]:
        """Monomorphic stage-1 equilibrium at supply phi, placed in the nearest bin."""
        q = replace(self.p, donor_flux=phi)
        e = evolved(q, self.run.constraint, self.run.loss)
        i = int(np.argmin(abs(self.theta - e["theta_k"])))
        rho = float(self.rho(e["t_k"])[i])
        d = self.half_sat / (rho - 1.0)
        b = np.zeros(self.theta.size)
        b[i] = (self.c * phi - self.run.k_donor * d) / self.run.death
        return np.r_[d, e["r"], b], e

    def integrate(self, y0: np.ndarray, phi, years: float, b_min: float, record_every_yr: float = 10.0) -> dict:
        y, t, rows = y0.copy(), 0.0, []
        atol = np.r_[1e-12, 1e-12, np.full(self.theta.size, max(1e-3 * b_min, 1e-300))]
        next_record, extinct_at, min_total = 0.0, None, float(y[2:].sum())
        while t < years:
            t1 = min(t + self.run.check_yr, years)
            sol = solve_ivp(self.rhs, (t, t1), y, method="LSODA", rtol=1e-7, atol=atol, args=(phi,))
            if not sol.success:
                raise RuntimeError(sol.message)
            y, t = np.maximum(sol.y[:, -1], 0.0), t1
            y[2:][y[2:] < b_min] = 0.0
            total = float(y[2:].sum())
            min_total = min(min_total, total)
            if total == 0.0 and extinct_at is None:
                extinct_at = t
            if t >= next_record or t >= years:
                rows.append(self.snapshot(t, y, phi))
                next_record += record_every_yr
        return {"y": y, "series": rows, "extinct_at_yr": extinct_at, "min_total_biomass": min_total}

    def snapshot(self, t: float, y: np.ndarray, phi) -> dict:
        b = y[2:]
        total = float(b.sum())
        t_k = float(temperature_k(y[1], self.p))
        mean_theta = float((b * self.theta).sum() / total) if total > 0 else np.nan
        target = singular_theta(t_k, self.run.constraint)
        return {"t_yr": round(t, 3), "potential_ratio": phi(t) * self.run.loss.lifetime_yr * self.c,
                "r": float(y[1]), "t_k": t_k, "total_biomass": total, "mean_theta_k": mean_theta,
                "singular_theta_k": target, "lag_k": mean_theta - target if total > 0 else np.nan,
                "living_bins": int((b > 0).sum())}


def rescue(p: Params, run: Run, r_pot0=0.22, r_pot1=0.02, decline_yr=1e4, spinup_yr=2e3, after_yr=2e3) -> dict:
    """Spin up at r_pot0, then decline supply linearly to r_pot1 and hold."""
    model = StrainModel(p, run)
    phi0, phi1 = float(flux_for_potential(r_pot0, p)), float(flux_for_potential(r_pot1, p))
    y0, e0 = model.resident_state(phi0)
    b_min = run.b_min_rel * float(y0[2:].sum())
    phi = supply_schedule(phi0, phi1, spinup_yr, decline_yr)
    out = model.integrate(y0, phi, spinup_yr + decline_yr + after_yr, b_min,
                          record_every_yr=max(10.0, (spinup_yr + decline_yr + after_yr) / 400))
    final = out["series"][-1]
    survivors_lag = [s["lag_k"] for s in out["series"] if np.isfinite(s["lag_k"])]
    return {"constraint": run.constraint.label, "loss": run.loss.label, "mutation": run.mutation,
            "b_min_rel": run.b_min_rel, "t_zero_k": run.t_zero_k, "decline_yr": decline_yr,
            "survived": out["extinct_at_yr"] is None, "extinct_at_yr": out["extinct_at_yr"] or "",
            "min_total_rel": out["min_total_biomass"] / float(y0[2:].sum()),
            "final_t_k": round(final["t_k"], 3), "final_r": final["r"],
            "final_mean_theta_k": round(final["mean_theta_k"], 3) if final["total_biomass"] > 0 else "",
            "max_abs_lag_k": round(max(abs(x) for x in survivors_lag), 3) if survivors_lag else "",
            "series": out["series"]}


def seed_escape(p: Params, run: Run, seed_theta_k: float, seed_rel: float = 1e-3, r_pot=0.22,
                years=2e4) -> dict:
    """Seed a lifeless planet at constant supply with one strain; does mutation find a viable optimum?"""
    model = StrainModel(p, run)
    phi = float(flux_for_potential(r_pot, p))
    ref, _ = model.resident_state(phi)
    b_star = float(ref[2:].sum())
    r_a = float(run.loss.inverse(model.c * p.abiotic_flux))
    b = np.zeros(model.theta.size)
    b[int(np.argmin(abs(model.theta - seed_theta_k)))] = seed_rel * b_star
    y0 = np.r_[model.c * phi / run.k_donor, r_a, b]
    out = model.integrate(y0, lambda t: phi, years, run.b_min_rel * b_star, record_every_yr=5.0)
    t_a = float(temperature_k(r_a, model.p))
    viable = model.theta[model.rho(t_a) > 1.0 + p.maintenance_flux / phi]
    nearest = float(abs(viable - seed_theta_k).min()) if viable.size else np.nan
    return {"t_zero_k": run.t_zero_k, "mutation": run.mutation, "b_min_rel": run.b_min_rel,
            "seed_theta_k": seed_theta_k, "abiotic_t_k": round(t_a, 3),
            "check_yr": run.check_yr, "years": years,
            "initial_net_growth_per_yr": float(run.death * (model.rho(t_a)[int(np.argmin(abs(model.theta - seed_theta_k)))]
                                                * y0[0] / (model.half_sat + y0[0]) - 1.0)),
            "steps_to_viable": int(round(nearest / Grid().step_k)) if viable.size else "",
            "alive_at_end": out["extinct_at_yr"] is None, "extinct_at_yr": out["extinct_at_yr"] or "",
            "final_total_rel": out["series"][-1]["total_biomass"] / b_star,
            "final_t_k": round(out["series"][-1]["t_k"], 3)}


def required_potential(r, theta, p: Params, constraint: Constraint, loss: Loss) -> np.ndarray:
    """Supply potential tau c Phi needed for a positive stationary state at methane ratio r with
    optimum theta (linear loss): r - r_a + P_K / (rho(T(r), theta) - 1), infinite where rho <= 1."""
    c = atmosphere(p.case)["flux_to_ratio_per_yr"]
    tau = loss.lifetime_yr
    r = np.asarray(r, dtype=float)
    t = np.asarray(temperature_k(r, p), dtype=float)
    theta = np.broadcast_to(np.asarray(theta, dtype=float), t.shape)
    rho = peak_growth(theta, constraint) * np.maximum(0.0, 1.0 - ((t - theta) / p.t_halfwidth_k) ** 2)
    with np.errstate(divide="ignore"):
        extra = np.where(rho > 1.0, tau * c * p.maintenance_flux / (rho - 1.0), np.inf)
    return r - tau * c * p.abiotic_flux + extra


def viability_threshold(p: Params, constraint: Constraint, loss: Loss, theta: float | None = None) -> dict:
    """Least supply potential admitting a positive stationary state, for a fixed optimum theta or,
    with theta None, for the best-growth envelope (theta singular at each temperature).
    No stationary community can capture more than this envelope allows."""
    if loss.kind != "power" or loss.elasticity != 1.0:
        raise ValueError("required_potential assumes linear loss")
    r_a = loss.lifetime_yr * atmosphere(p.case)["flux_to_ratio_per_yr"] * p.abiotic_flux
    r = r_a + np.geomspace(1e-9, 0.5, 20001)
    t = np.asarray(temperature_k(r, p), dtype=float)
    th = np.array([singular_theta(x, constraint) for x in t]) if theta is None else np.full(r.shape, theta)
    need = required_potential(r, th, p, constraint, loss)
    i = int(np.argmin(need))
    return {"potential": float(need[i]), "r": float(r[i]), "t_k": float(t[i]), "theta_k": float(th[i])}


def _rescue_job(args):
    constraint, m, census, t0, final = args
    p, losses = reference()
    run = Run(constraint, losses[2], mutation=m, b_min_rel=1e-6, t_zero_k=t0, check_yr=census)
    out = rescue(p, run, r_pot1=final, decline_yr=1e3, after_yr=2e5)
    q = replace(p, t_zero_k=t0)
    model = StrainModel(p, run)
    theta0 = float(model.theta[int(np.argmax(model.resident_state(float(flux_for_potential(0.22, p)))[0][2:]))])
    frozen = viability_threshold(q, constraint, losses[2], theta0)["potential"]
    best = viability_threshold(q, constraint, losses[2])["potential"]
    tail = [s for s in out["series"] if s["t_yr"] >= out["series"][-1]["t_yr"] - 2e4]
    tb = [s["total_biomass"] for s in tail]
    settled = bool(out["survived"] and max(tb) - min(tb) < 0.01 * tb[-1])
    return {**{k: v for k, v in out.items() if k != "series"}, "census_yr": census, "final_potential": final,
            "initial_theta_k": theta0, "frozen_threshold": round(frozen, 6), "best_threshold": round(best, 6),
            "frozen_viable": final > frozen, "best_viable": final > best, "settled_last_20kyr": settled,
            "extinct_after_decline_yr": (out["extinct_at_yr"] - 2e3) if out["extinct_at_yr"] else "",
            "series": out["series"]}


RESCUE_GRID = {"constraint": (Constraint(), Constraint(energy_ev=0.65)), "mutation": (0.0, 1e-8, 1e-6, 1e-4),
               "census_yr": (10.0, 30.0, 100.0), "t_zero_k": (265.0, 283.0), "final_potential": (0.02, 0.03, 0.08)}


def run_rescue(processes: int = 9) -> list[dict]:
    from multiprocessing import Pool

    g = RESCUE_GRID
    jobs = [(c, m, n, t0, f) for c in g["constraint"] for t0 in g["t_zero_k"] for f in g["final_potential"]
            for n in g["census_yr"] for m in g["mutation"]]
    jobs.sort(key=lambda j: j[2])  # shortest censuses first: they are the slowest
    with Pool(processes) as pool:
        return pool.map(_rescue_job, jobs, chunksize=1)


def _seed_job(args):
    m, theta = args
    p, losses = reference()
    return seed_escape(p, Run(Constraint(), losses[2], mutation=m, b_min_rel=1e-9, check_yr=1.0), theta)


def run_seed(processes: int = 9) -> list[dict]:
    from multiprocessing import Pool

    jobs = [(m, th) for m in (0.0, 1e-4, 1e-2) for th in np.arange(284.0, 287.01, 0.5)]
    with Pool(processes) as pool:
        return pool.map(_seed_job, jobs, chunksize=1)


def write_csv(path: Path, rows: list[dict]) -> None:
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def plot(rescues: list[dict], seeds: list[dict], out: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    g = RESCUE_GRID
    fig, axs = plt.subplots(2, 2, figsize=(14, 10))

    ax = axs[0, 0]
    for m, color in zip(g["mutation"], ("k", "tab:red", "tab:orange", "tab:green")):
        r = next(x for x in rescues if x["constraint"] == "H E=0.65" and x["t_zero_k"] == 265.0
                 and x["final_potential"] == 0.03 and x["census_yr"] == 10.0 and x["mutation"] == m)
        s = [x for x in r["series"] if x["t_yr"] <= 1.2e5]
        t = [(x["t_yr"] - 2e3) / 1e3 for x in s]
        ax.plot(t, [x["t_k"] for x in s], "-", color=color, lw=1.3, label=f"climate, m = {m:g}")
        ax.plot(t, [x["mean_theta_k"] for x in s], "--", color=color, lw=0.9)
    ax.plot([], [], "k--", lw=0.9, label="dashed: mean optimum")
    ax.set(xlabel="kyr since supply decline began (0.22 → 0.03 over 1 kyr)", ylabel="K",
           title="(a) H, T0 = 265 K, final 0.03 (viable), 10-yr census")
    ax.legend(fontsize=7)

    ax = axs[0, 1]
    rows = [(c.label, t0, f) for c in g["constraint"] for t0 in g["t_zero_k"] for f in g["final_potential"]]
    cols = [(n, m) for n in g["census_yr"] for m in g["mutation"]]
    grid = np.zeros((len(rows), len(cols)))
    labels = []
    for i, (c, t0, f) in enumerate(rows):
        for j, (n, m) in enumerate(cols):
            x = next(r for r in rescues if r["constraint"] == c and r["t_zero_k"] == t0
                     and r["final_potential"] == f and r["census_yr"] == n and r["mutation"] == m)
            grid[i, j] = 0 if not x["survived"] else (2 if x["settled_last_20kyr"] else 1)
            txt = f"{x['extinct_after_decline_yr'] / 1e3:.0f}k" if not x["survived"] else f"{x['final_t_k']:.0f}"
            ax.text(j, i, txt, ha="center", va="center", fontsize=6)
        ref = x
        labels.append(f"{c}, T0 {t0:g}, final {f:g}" + ("" if ref["best_viable"] else " (no living state)"))
    ax.imshow(grid, cmap=matplotlib.colors.ListedColormap(["#ef9a9a", "#fff59d", "#a5d6a7"]), aspect="auto",
              vmin=0, vmax=2)
    ax.set_yticks(range(len(rows)), labels, fontsize=6.5)
    ax.set_xticks(range(len(cols)), [f"Δt {n:g}\nm {m:g}" for n, m in cols], fontsize=6)
    ax.set_title("(b) after 200 kyr at final supply: extinct (red, kyr after decline),\n"
                 "alive and settled (green) or still changing (yellow); numbers: final climate (K)", fontsize=9)

    ax = axs[1, 0]
    p, losses = reference()
    for t0, ls in ((265.0, "-"), (283.0, "--")):
        q = replace(p, t_zero_k=t0)
        r_a = losses[2].lifetime_yr * atmosphere(p.case)["flux_to_ratio_per_yr"] * p.abiotic_flux
        r = r_a + np.geomspace(1e-6, 0.3, 1500)
        c = Constraint(energy_ev=0.65)
        t = np.asarray(temperature_k(r, q))
        best = required_potential(r, [singular_theta(x, c) for x in t], q, c, losses[2])
        ax.semilogx(r, best, ls, color="tab:red", lw=1.3, label=f"H best-growth envelope, T0 {t0:g} K")
        ax.semilogx(r, required_potential(r, 285.5, q, c, losses[2]), ls, color="tab:blue", lw=1,
                    label=f"H frozen at 285.5 K, T0 {t0:g} K")
    for f in g["final_potential"]:
        ax.axhline(f, color="0.5", lw=0.7, ls=":")
    ax.set(xlabel="methane ratio r", ylabel="supply potential needed for a living steady state",
           ylim=(0, 0.12), title="(c) which final supplies admit a living H state")
    ax.legend(fontsize=7)

    ax = axs[1, 1]
    for m, color in zip((0.0, 1e-4, 1e-2), ("k", "tab:orange", "tab:green")):
        pts = [x for x in seeds if x["mutation"] == m]
        ax.semilogy([x["seed_theta_k"] for x in pts], [max(x["final_total_rel"], 1e-12) for x in pts], "o-", ms=4,
                    color=color, label=f"m = {m:g}")
    t_a = seeds[0]["abiotic_t_k"]
    ax.axvline(t_a + 18.93, color="0.3", lw=0.8, ls="--", label="net growth positive below here")
    ax.axvline(t_a + 20.0, color="0.3", lw=0.8, ls=":", label="no division (no mutants) above here")
    ax.set(xlabel="optimum of the single seed strain (K)", ylabel="biomass after 20 kyr / B* (1e-12 = extinct)",
           title=f"(d) seeding a lifeless planet at {t_a:.1f} K (T0 = 265 K), 1-yr census")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(out, dpi=130)


def main(outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    rescues, seeds = run_rescue(), run_seed()
    write_csv(outdir / "strains_rescue.csv", [{k: v for k, v in r.items() if k != "series"} for r in rescues])
    write_csv(outdir / "strains_seed.csv", seeds)
    example = [dict(constraint=r["constraint"], t_zero_k=r["t_zero_k"], final_potential=r["final_potential"],
                    census_yr=r["census_yr"], mutation=r["mutation"], **s)
               for r in rescues if r["t_zero_k"] == 265.0 and r["census_yr"] == 10.0 and r["final_potential"] == 0.03
               for s in r["series"]]
    write_csv(outdir / "strains_series.csv", example)
    plot(rescues, seeds, outdir / "strains_figures.png")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("models/haze_world/figures"))
