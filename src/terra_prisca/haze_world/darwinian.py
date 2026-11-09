"""Haze-world with an evolving thermal optimum: a named variant of methane_budget.

    uv run python -m terra_prisca.haze_world.darwinian [outdir]

Monomorphic adaptive dynamics on the methanogens' thermal optimum theta, with
the methane budget of methane_budget.py and three constraint scenarios:

    U  unconstrained: fixed peak growth rho_max = 10 (E = 0), no floor
    F  hard floor theta >= floor, otherwise as U
    H  hotter-is-better: rho_max(theta) = 10 exp[(E/k)(1/300 K - 1/theta)]

A rare mutant at the resident equilibrium invades when rho_m(T*) > rho_r(T*)
(common donor half-saturation K), so the selection gradient is
g = d ln rho(T*; theta)/d theta = E/(k theta^2) - 2x/(w^2 - x^2), x = theta - T*.
It depends on the resident only through T*, so the singular optimum is an
explicit function of temperature and the evolved equilibrium solves one
methane balance. Methane loss is a swept family anchored on the
temperature-independent rho = 10 control, so the control climate is the same
under every loss shape. See models/haze_world/README.md for the scope.
"""

from __future__ import annotations

import csv
import sys
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
from scipy.optimize import brentq

from .experiments import cold_edge_k, flux_for_potential, t_opt_for_edge
from .methane_budget import (
    Params,
    atmosphere,
    capture_efficiency,
    domain,
    equilibria,
    growth_ratio,
    response,
    temperature_k,
)

KB_EV = 8.617333e-5  # Boltzmann constant, eV K-1
RHO_REF = 10.0
T_REF_K = 300.0


@dataclass(frozen=True)
class Loss:
    """Methane loss in ratio units per year, anchored so that loss(anchor) = anchor / tau.

    power: (anchor/tau) (r/anchor)^n, constant elasticity n (n = 1 is the first-order draft)
    log:   (anchor/tau) ln(1 + r/s) / ln(1 + anchor/s)
    These are sensitivity shapes, not recovered photochemistry.
    """

    anchor_ratio: float
    lifetime_yr: float = 1.0e4
    kind: str = "power"
    elasticity: float = 1.0
    log_scale: float = 1.0e-3

    def rate(self, r):
        r = np.maximum(np.asarray(r, dtype=float), 0.0)
        a = self.anchor_ratio
        if self.kind == "power":
            shape = (r / a) ** self.elasticity
        else:
            shape = np.log1p(r / self.log_scale) / np.log1p(a / self.log_scale)
        return a / self.lifetime_yr * shape

    def inverse(self, rate: float) -> float:
        a, x = self.anchor_ratio, rate * self.lifetime_yr / self.anchor_ratio
        if self.kind == "power":
            return a * x ** (1.0 / self.elasticity)
        return self.log_scale * np.expm1(x * np.log1p(a / self.log_scale))

    @property
    def label(self) -> str:
        return f"power n={self.elasticity:g}" if self.kind == "power" else f"log s={self.log_scale:g}"


@dataclass(frozen=True)
class Constraint:
    energy_ev: float = 0.0  # hotter-is-better activation energy E; 0 is scenario U
    floor_k: float = -np.inf  # hard floor on theta; -inf is no floor

    @property
    def label(self) -> str:
        if np.isfinite(self.floor_k):
            return f"F floor={self.floor_k:g}"
        return "U" if self.energy_ev == 0 else f"H E={self.energy_ev:g}"


def peak_growth(theta, c: Constraint):
    return RHO_REF * np.exp(c.energy_ev / KB_EV * (1.0 / T_REF_K - 1.0 / np.asarray(theta, dtype=float)))


def strain(p: Params, theta: float, c: Constraint) -> Params:
    """Params for a thermal strain with optimum theta under constraint c."""
    return replace(p, thermal=True, t_opt_k=float(theta), growth_ratio_max=float(peak_growth(theta, c)))


def gradient(t_k, theta, c: Constraint, w: float = 20.0):
    """Selection gradient d ln rho(T; theta) / d theta at resident temperature T."""
    x = np.asarray(theta) - np.asarray(t_k)
    return c.energy_ev / (KB_EV * np.asarray(theta) ** 2) - 2 * x / (w**2 - x**2)


def singular_theta(t_k: float, c: Constraint, w: float = 20.0) -> float:
    """Evolutionarily singular optimum at temperature T, then the hard floor."""
    theta = t_k if c.energy_ev == 0 else brentq(lambda th: gradient(t_k, th, c, w), t_k, t_k + w * (1 - 1e-9))
    return max(theta, c.floor_k)


def control_params(p: Params, rho: float = RHO_REF) -> Params:
    return replace(p, thermal=False, growth_ratio_max=float(rho))


def tendency(r, q: Params, loss: Loss):
    cr = atmosphere(q.case)["flux_to_ratio_per_yr"]
    eta = capture_efficiency(temperature_k(r, q), q)
    return cr * (eta * q.donor_flux + q.abiotic_flux) - loss.rate(r)


def _roots(f, q: Params, loss: Loss, n_grid: int = 4001) -> list[tuple[float, bool]]:
    cr = atmosphere(q.case)["flux_to_ratio_per_yr"]
    r_hi = 1.01 * loss.inverse(cr * (q.donor_flux + q.abiotic_flux))
    resp = response(q.case)
    grid = np.unique(np.r_[np.linspace(0.0, r_hi, n_grid), np.geomspace(1e-12, r_hi, n_grid // 2),
                           resp.ratios[resp.ratios < r_hi]])
    v = f(grid)
    out = []
    for i in np.flatnonzero(np.sign(v[:-1]) * np.sign(v[1:]) < 0):
        out.append((brentq(lambda x: float(f(np.array([x]))[0]), grid[i], grid[i + 1], xtol=1e-14, rtol=1e-13),
                    bool(v[i] > 0)))
    return out


def fixed_equilibria(q: Params, loss: Loss) -> list[dict]:
    """Equilibria of the reduced model for fixed traits under a general loss law."""
    out = []
    for r, stable in _roots(lambda x: tendency(x, q, loss), q, loss):
        t = float(temperature_k(r, q))
        out.append({"r": r, "stable": stable, "t_k": t, "eta": float(capture_efficiency(t, q)),
                    "domain": str(domain(r, q))})
    return out


def biotic(q: Params, loss: Loss) -> dict | None:
    alive = [e for e in fixed_equilibria(q, loss) if e["stable"] and e["eta"] > 0]
    return alive[-1] if alive else None


def evolved(p: Params, c: Constraint, loss: Loss) -> dict | None:
    """Warmest feasible equilibrium at which the resident sits at its singular (or floor) optimum."""

    def balance(rs):
        out = np.empty_like(rs)
        for i, r in enumerate(rs):
            t = float(temperature_k(r, p))
            out[i] = float(tendency(r, strain(p, singular_theta(t, c), c), loss))
        return out

    roots = [(r, s) for r, s in _roots(balance, p, loss, n_grid=1201)]
    feasible = []
    for r, _ in roots:
        t = float(temperature_k(r, p))
        theta = singular_theta(t, c)
        q = strain(p, theta, c)
        eta = float(capture_efficiency(t, q))
        if eta > 0:
            feasible.append({"r": r, "t_k": t, "theta_k": theta, "eta": eta, "domain": str(domain(r, p)),
                             "rho_peak": float(q.growth_ratio_max), "rho_realized": float(growth_ratio(t, q)),
                             "at_floor": bool(theta == c.floor_k)})
    return feasible[-1] if feasible else None


def convergence_slope(p: Params, c: Constraint, loss: Loss, theta: float, h: float = 0.05) -> float:
    """d/dtheta of the selection gradient along the resident's own equilibrium."""
    g = []
    for th in (theta - h, theta + h):
        e = biotic(strain(p, th, c), loss)
        g.append(np.nan if e is None else float(gradient(e["t_k"], th, c)))
    return (g[1] - g[0]) / (2 * h)


def full_rhs(y, q: Params, loss: Loss, k_donor: float = 0.1, death: float = 1.0):
    d, b, m = y
    cr = atmosphere(q.case)["flux_to_ratio_per_yr"]
    half_sat = cr * q.maintenance_flux / k_donor
    uptake = death * growth_ratio(temperature_k(max(m, 0.0), q), q) * b * d / (half_sat + d)
    return np.array([cr * q.donor_flux - k_donor * d - uptake, uptake - death * b,
                     uptake + cr * q.abiotic_flux - float(loss.rate(m))])


def full_max_real_eigenvalue(q: Params, loss: Loss, e: dict, k_donor: float = 0.1, death: float = 1.0) -> float:
    """Largest real part of the full (D, B, M) Jacobian at the positive equilibrium (yr-1)."""
    cr = atmosphere(q.case)["flux_to_ratio_per_yr"]
    half_sat = cr * q.maintenance_flux / k_donor
    rho = float(growth_ratio(e["t_k"], q))
    d = half_sat / (rho - 1)
    y = np.array([d, (cr * q.donor_flux - k_donor * d) / death, e["r"]])
    jac = np.empty((3, 3))
    for j in range(3):
        h = 1e-7 * max(abs(y[j]), 1e-12)
        dy = np.zeros(3)
        dy[j] = h
        jac[:, j] = (full_rhs(y + dy, q, loss, k_donor, death) - full_rhs(y - dy, q, loss, k_donor, death)) / (2 * h)
    return float(np.max(np.linalg.eigvals(jac).real))


def invades_lifeless(q: Params, loss: Loss, t_zero_k: float) -> bool:
    """Whether a rare strain grows at the abiotic-only equilibrium under bridge endpoint T0."""
    qq = replace(q, t_zero_k=t_zero_k)
    r_abiotic = loss.inverse(atmosphere(q.case)["flux_to_ratio_per_yr"] * q.abiotic_flux)
    return bool(capture_efficiency(temperature_k(r_abiotic, qq), qq) > 0)


def supply_sensitivity(p: Params, c: Constraint, loss: Loss, e: dict, eps: float = 0.005) -> dict:
    """dT/d ln(supply) with the trait fixed (ecological), re-evolved (evolutionary), and for a
    temperature-independent control with the same realized growth at the base equilibrium."""
    res = {}
    fixed = strain(p, e["theta_k"], c)
    matched = control_params(p, e["rho_realized"])
    for name, solve in (("ecological", lambda q: biotic(replace(fixed, donor_flux=q.donor_flux), loss)),
                        ("evolutionary", lambda q: evolved(q, c, loss)),
                        ("matched_control", lambda q: biotic(replace(matched, donor_flux=q.donor_flux), loss))):
        ts = []
        for f in (1 - eps, 1 + eps):
            s = solve(replace(p, donor_flux=p.donor_flux * f))
            ts.append(np.nan if s is None else s["t_k"])
        res[name] = (ts[1] - ts[0]) / (np.log(1 + eps) - np.log(1 - eps))
    return res


def scenario_row(p: Params, c: Constraint, loss: Loss, t_zero_refs=(265.0, 283.0)) -> dict:
    e = evolved(p, c, loss)
    row = {"constraint": c.label, "energy_ev": c.energy_ev,
           "floor_k": c.floor_k if np.isfinite(c.floor_k) else "", "loss": loss.label}
    if e is None:
        return {**row, "persists": False}
    q = strain(p, e["theta_k"], c)
    c10 = biotic(control_params(p), loss)
    cpeak = biotic(control_params(p, e["rho_peak"]), loss)
    sens = supply_sensitivity(p, c, loss, e)
    row.update({
        "theta_k": round(e["theta_k"], 4), "t_k": round(e["t_k"], 4), "r": round(e["r"], 7),
        "domain": e["domain"], "eta": round(e["eta"], 6), "at_floor": e["at_floor"],
        "rho_peak": round(e["rho_peak"], 4), "rho_realized": round(e["rho_realized"], 4),
        "t_minus_control10_k": round(e["t_k"] - c10["t_k"], 4),
        "t_minus_matched_peak_k": round(e["t_k"] - cpeak["t_k"], 4) if cpeak else "",
        "dT_dlnS_ecological": round(sens["ecological"], 4),
        "dT_dlnS_evolutionary": round(sens["evolutionary"], 4),
        "dT_dlnS_matched_control": round(sens["matched_control"], 4),
        "regulation_ecological": round(sens["ecological"] / sens["matched_control"], 4),
        "regulation_evolutionary": round(sens["evolutionary"] / sens["matched_control"], 4),
        "cold_edge_k": round(float(cold_edge_k(q)), 4),
        "convergence_slope": round(convergence_slope(p, c, loss, e["theta_k"]), 5) if not e["at_floor"] else "",
        "floor_gradient": round(float(gradient(e["t_k"], e["theta_k"], c)), 5) if e["at_floor"] else "",
        "full_max_real_eig_per_yr": round(full_max_real_eigenvalue(q, loss, e), 6),
        "persists": full_max_real_eigenvalue(q, loss, e) < 0,
    })
    for t0 in t_zero_refs:
        row[f"invades_lifeless_T0_{t0:g}"] = invades_lifeless(q, loss, t0)
    return row


def reference(potential_ratio: float = 0.22) -> tuple[Params, list[Loss]]:
    p0 = Params()
    p = replace(p0, donor_flux=float(flux_for_potential(potential_ratio, p0)))
    anchor = [e for e in equilibria(control_params(p)) if e["stable"]][-1]["r"]
    losses = [Loss(anchor, kind="power", elasticity=n) for n in (0.2, 0.5, 1.0, 2.0)]
    losses.append(Loss(anchor, kind="log"))
    return p, losses


def trait_path(p: Params, c: Constraint, loss: Loss, start_edge_k: float = 281.0, n: int = 121) -> list[dict]:
    """Resident equilibrium along the monotone trait path from a 281-K cold edge to the endpoint.
    Plotted against theta (trait change), not time; mutation supply is uncalibrated."""
    e = evolved(p, c, loss)
    theta0 = t_opt_for_edge(start_edge_k, p)
    out = []
    for th in np.linspace(theta0, e["theta_k"], n):
        b = biotic(strain(p, th, c), loss)
        if b:
            out.append({"constraint": c.label, "loss": loss.label, "theta_k": round(float(th), 4),
                        "t_k": round(b["t_k"], 4), "eta": round(b["eta"], 6), "domain": b["domain"]})
    return out


def plot(p: Params, rows: list[dict], paths: list[dict], out: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    t_c10 = [r for r in rows if r["constraint"] == "U"][0]["t_k"]
    losses = list(dict.fromkeys(r["loss"] for r in rows))
    colors = dict(zip(losses, ("tab:purple", "tab:blue", "k", "tab:green", "tab:red")))
    h = [r for r in rows if r["constraint"] == "U" or r["constraint"].startswith("H")]
    f = [r for r in rows if r["constraint"].startswith("F")]
    fig, axs = plt.subplots(2, 3, figsize=(15, 8.6))

    ax = axs[0, 0]
    styles = {"U": "k", "H E=0.32": "tab:orange", "H E=0.65": "tab:red", "F floor=290": "tab:blue"}
    for (c, loss), ls in (((c, l), "-" if l == "power n=1" else "--") for c in styles for l in ("power n=1", "power n=0.2")):
        pts = [x for x in paths if x["constraint"] == c and x["loss"] == loss]
        if pts:
            ax.plot([x["theta_k"] for x in pts], [x["t_k"] for x in pts], ls, color=styles[c], lw=1.4,
                    label=f"{c}, {loss}")
            ax.plot(pts[-1]["theta_k"], pts[-1]["t_k"], "o", color=styles[c], ms=4)
    ax.axhline(t_c10, color="0.5", lw=0.8, ls=":", label="temperature-independent control")
    ax.invert_xaxis()
    ax.set(xlabel="resident thermal optimum θ (K), evolving left to right",
           ylabel="equilibrium temperature (K)", title="(a) case B, potential 0.22: climate along the trait path")
    ax.legend(fontsize=6.5)

    for ax, key, ttl in ((axs[0, 1], "t_minus_control10_k", "(b) H: evolved climate minus ρ = 10 control"),
                         (axs[1, 1], "regulation_ecological", "(e) H: supply sensitivity / matched control")):
        for loss in losses:
            pts = [r for r in h if r["loss"] == loss and r.get("persists")]
            x = [r["energy_ev"] for r in pts]
            ax.plot(x, [r[key] for r in pts], "-o", ms=2.5, color=colors[loss], lw=1.2, label=loss)
            if key == "t_minus_control10_k":
                ax.plot(x, [r["t_minus_matched_peak_k"] for r in pts], ":", color=colors[loss], lw=1)
        ax.set(xlabel="hotter-is-better activation energy E (eV)", title=ttl)
    axs[0, 1].plot([], [], "k:", label="dotted: minus matched-peak control")
    axs[0, 1].set_ylabel("temperature difference (K)")
    axs[1, 1].set_ylabel("dT/d ln supply, ratio to matched control")
    axs[1, 1].axhline(1, color="0.5", lw=0.8, ls=":")
    axs[0, 1].legend(fontsize=7)

    ax = axs[0, 2]
    for loss in losses:
        pts = [r for r in f if r["loss"] == loss and r.get("persists")]
        ax.plot([r["floor_k"] for r in pts], [r["t_k"] for r in pts], "-", color=colors[loss], lw=1.2, label=loss)
    pts = [r for r in f if r["loss"] == "power n=1" and r.get("persists")]
    ax.plot([r["floor_k"] for r in pts], [r["cold_edge_k"] for r in pts], "--", color="tab:green", lw=1,
            label="resident cold edge (linear loss)")
    ax.axhline(t_c10, color="0.5", lw=0.8, ls=":")
    ax.set(xlabel="hard floor on θ (K)", ylabel="evolved equilibrium temperature (K)", title="(c) F: climate against the floor")
    ax.legend(fontsize=7)

    ax = axs[1, 2]
    for loss in losses:
        pts = [r for r in f if r["loss"] == loss and r.get("persists")]
        ax.semilogy([r["floor_k"] for r in pts], [r["regulation_ecological"] for r in pts], "-", color=colors[loss],
                    lw=1.2, label=loss)
    ax.axhline(1, color="0.5", lw=0.8, ls=":")
    ax.set(xlabel="hard floor on θ (K)", ylabel="dT/d ln supply, ratio to matched control",
           title="(f) F: supply sensitivity / matched control")

    ax = axs[1, 0]
    lin_h = [r for r in h if r["loss"] == "power n=1" and r.get("persists")]
    lin_f = [r for r in f if r["loss"] == "power n=1" and r.get("persists")]
    ax.plot([r["energy_ev"] for r in lin_h], [r["cold_edge_k"] for r in lin_h], "-o", ms=2.5, color="tab:red",
            label="H: evolved cold edge (bottom axis)")
    for t0, ls in ((265.0, "--"), (283.0, "-.")):
        ax.axhline(t0, color="0.4", lw=0.9, ls=ls, label=f"bridge T0 = {t0:g} K")
    top = ax.twiny()
    top.plot([r["floor_k"] for r in lin_f], [r["cold_edge_k"] for r in lin_f], "-", color="tab:blue")
    top.set_xlabel("hard floor on θ (K), F (blue)")
    ax.plot([], [], "-", color="tab:blue", label="F: evolved cold edge (top axis)")
    ax.set(xlabel="E (eV), H (red)", ylabel="lowest T0 from which the evolved strain re-invades (K)",
           title="(d) invasion of the lifeless state needs T0 above the edge", ylim=(250, 290))
    ax.legend(fontsize=7, loc="upper left")

    fig.tight_layout()
    fig.savefig(out, dpi=130)


def write_csv(path: Path, rows: list[dict]) -> None:
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def run(outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    p, losses = reference()
    constraints = ([Constraint()] + [Constraint(energy_ev=e) for e in np.round(np.arange(0.05, 0.651, 0.05), 2)]
                   + [Constraint(floor_k=f) for f in np.arange(274.0, 300.01, 1.0)])
    rows = [scenario_row(p, c, loss) for loss in losses for c in constraints]
    paths = [row for loss in (losses[2], losses[0]) for c in (Constraint(), Constraint(energy_ev=0.32),
             Constraint(energy_ev=0.65), Constraint(floor_k=290.0)) for row in trait_path(p, c, loss)]
    write_csv(outdir / "darwinian_endpoints.csv", rows)
    write_csv(outdir / "darwinian_paths.csv", paths)
    plot(p, rows, paths, outdir / "darwinian_figures.png")


if __name__ == "__main__":
    run(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("models/haze_world/figures"))
