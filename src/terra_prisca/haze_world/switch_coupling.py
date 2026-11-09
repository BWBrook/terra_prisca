"""Reduced coupling of the acetogen/methanogen switch to haze-world climate.

uv run python -m terra_prisca.haze_world.switch_coupling [output_directory]

Microbial competition is fast relative to the methane inventory, so the guild mix enters
the haze-world budget only through the catabolic routing factor
    R(s) = 1 - (1 - f_ac) s,       s = acetogen share of captured H2,
    dr/dt = c [R(s) eta(T(r)) Phi + Phi_abiotic] - L(r).
The two-guild switch is imported as one temperature T_sw: acetogens win below it,
methanogens above (the orientation of every located exchange in competition-switches.md).
Mixed communities follow d logit(s)/dt = -g (T(r) - T_sw) with g > 0.

Capture efficiency eta is the inherited methanogen closure for both guilds,
an assumption even at a mixed state: common R* does not identify capture
with the closure of a different physiological model. See the independent
review and the explicit population_coupling variant.
"""

from __future__ import annotations

import csv
import json
import sys
from dataclasses import dataclass, replace
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq

from .darwinian import Loss, climate_slopes, reference
from .experiments import flux_for_potential
from .methane_budget import Params, atmosphere, capture_efficiency, response, temperature_k

FIGURES = Path(__file__).resolve().parents[3] / "models/haze_world/figures/switch_coupling"


@dataclass(frozen=True)
class Switch:
    t_switch_k: float
    f_ac: float
    selection_per_k_yr: float = 1.0

    def routing(self, s):
        return 1.0 - (1.0 - self.f_ac) * np.asarray(s, dtype=float)


def tendency(r, s, q: Params, loss: Loss, sw: Switch):
    cr = atmosphere(q.case)["flux_to_ratio_per_yr"]
    eta = capture_efficiency(temperature_k(r, q), q)
    return cr * (sw.routing(s) * eta * q.donor_flux + q.abiotic_flux) - loss.rate(r)


def _grid(q: Params, loss: Loss, n: int = 6001):
    cr = atmosphere(q.case)["flux_to_ratio_per_yr"]
    r_hi = 1.01 * loss.inverse(cr * (q.donor_flux + q.abiotic_flux))
    resp = response(q.case)
    return np.unique(np.r_[np.linspace(0.0, r_hi, n), np.geomspace(1e-12, r_hi, n // 2),
                           resp.ratios[resp.ratios < r_hi]])


def _sign_changes(f, grid):
    v = f(grid)
    out = []
    for i in np.flatnonzero(np.sign(v[:-1]) * np.sign(v[1:]) < 0):
        out.append((brentq(lambda x: float(f(np.array([x]))[0]), grid[i], grid[i + 1], xtol=1e-14, rtol=1e-13),
                    bool(v[i] > 0)))
    return out


def pure_states(q: Params, loss: Loss, sw: Switch) -> list[dict]:
    """Equilibria with s = 0 or 1 that are consistent with the switch orientation. With f_ac = 1
    the mix does not affect climate, so methanogen-labelled states stand for any mix.
    A state is r-stable when the tendency falls through zero; it resists invasion when it sits
    strictly on its own side of T_sw."""
    out = []
    grid = _grid(q, loss)
    for s, guild in ((0.0, "methanogen"), (1.0, "acetogen")):
        if guild == "acetogen" and sw.f_ac == 1.0:
            continue
        for r, falls in _sign_changes(lambda x: tendency(x, s, q, loss, sw), grid):
            t = float(temperature_k(r, q))
            living = float(capture_efficiency(t, q)) > 0.0
            if living and sw.f_ac < 1.0 and (t < sw.t_switch_k if guild == "methanogen" else t > sw.t_switch_k):
                continue
            out.append(dict(kind=guild if living else "no_capture", s=s, r=r, t_k=t,
                            stable=falls, eta=float(capture_efficiency(t, q))))
    unique = {}
    for e in out:
        if e["kind"] == "no_capture":
            unique.setdefault(round(e["r"], 12), e)
        else:
            unique[(e["kind"], round(e["r"], 12))] = e
    return sorted(unique.values(), key=lambda e: e["r"])


def mixed_states(q: Params, loss: Loss, sw: Switch) -> list[dict]:
    """States pinned at T(r) = T_sw with 0 < s < 1, with the analytic 2x2 Jacobian in (r, logit s).
    J = [[f_r, f_x], [-g T_r, 0]], f_x = -c (1 - f_ac) eta Phi s(1 - s) < 0, so det = f_x g T_r
    is positive only where T_r < 0 (the haze-cooling branch). Both one-sided slopes are checked
    at a climate vertex."""
    if sw.f_ac >= 1.0:
        return []
    cr = atmosphere(q.case)["flux_to_ratio_per_yr"]
    grid = _grid(q, loss)
    out = []
    for r, _ in _sign_changes(lambda x: np.asarray(temperature_k(x, q)) - sw.t_switch_k, grid):
        eta = float(capture_efficiency(sw.t_switch_k, q))
        if eta <= 0.0:
            continue
        s = (eta * q.donor_flux + q.abiotic_flux - float(loss.rate(r)) / cr) / ((1.0 - sw.f_ac) * eta * q.donor_flux)
        if not 0.0 < s < 1.0:
            continue
        sides = []
        for t_r in climate_slopes(r, q):
            h = 1e-9
            eta_t = (float(capture_efficiency(sw.t_switch_k + h, q)) - float(capture_efficiency(sw.t_switch_k - h, q))) / (2 * h)
            f_r = cr * float(sw.routing(s)) * q.donor_flux * eta_t * t_r - loss.slope(r)
            f_x = -cr * (1.0 - sw.f_ac) * eta * q.donor_flux * s * (1.0 - s)
            jac = np.array([[f_r, f_x], [-sw.selection_per_k_yr * t_r, 0.0]])
            sides.append(dict(t_r=t_r, trace=float(np.trace(jac)), det=float(np.linalg.det(jac)),
                              max_real=float(np.max(np.linalg.eigvals(jac).real))))
        out.append(dict(kind="mixed", s=float(s), r=r, t_k=sw.t_switch_k, eta=eta,
                        stable=all(x["max_real"] < 0 for x in sides), sides=sides))
    return out


def states(q: Params, loss: Loss, sw: Switch) -> list[dict]:
    return sorted(pure_states(q, loss, sw) + mixed_states(q, loss, sw), key=lambda e: e["r"])


def integrate(q: Params, loss: Loss, sw: Switch, r0: float, s0: float, years: float = 2e5) -> dict:
    x0 = float(np.log(s0 / (1 - s0)))

    def rhs(_, y):
        r, x = max(y[0], 0.0), y[1]
        s = 0.5 * (1.0 + np.tanh(0.5 * x))
        return [float(tendency(np.array([r]), s, q, loss, sw)[0]),
                -sw.selection_per_k_yr * (float(temperature_k(r, q)) - sw.t_switch_k)]

    sol = solve_ivp(rhs, (0.0, years), [r0, x0], method="LSODA", rtol=1e-9, atol=[1e-12, 1e-9],
                    max_step=years / 200)
    r, x = sol.y[0, -1], sol.y[1, -1]
    return dict(r=float(r), s=float(0.5 * (1.0 + np.tanh(0.5 * x))), t_k=float(temperature_k(r, q)), success=bool(sol.success))


def sweep(q: Params, loss: Loss, potentials, switches) -> list[dict]:
    rows = []
    for sw in switches:
        for pot in potentials:
            qq = replace(q, donor_flux=float(flux_for_potential(pot, q)))
            for e in states(qq, loss, sw):
                rows.append(dict(t_switch_k=sw.t_switch_k, f_ac=sw.f_ac, potential=round(float(pot), 6),
                                 kind=e["kind"], s=round(e["s"], 8), r=round(e["r"], 9), t_k=round(e["t_k"], 5),
                                 stable=e["stable"]))
    return rows


def plot(rows: list[dict], baseline: list[dict], out: Path) -> None:
    t_sws = sorted({r["t_switch_k"] for r in rows})
    f_acs = sorted({r["f_ac"] for r in rows})
    fig, axes = plt.subplots(len(f_acs), len(t_sws), figsize=(4.2 * len(t_sws), 3.4 * len(f_acs)),
                             sharex=True, sharey=True, squeeze=False)
    colors = {"methanogen": "#2a6f97", "acetogen": "#c8553d", "mixed": "#6a994e", "no_capture": "#7f7f7f"}
    for i, f in enumerate(f_acs):
        for j, tsw in enumerate(t_sws):
            ax = axes[i, j]
            b = [r for r in baseline if r["stable"]]
            ax.plot([r["potential"] for r in b], [r["t_k"] for r in b], ".", color="#bbbbbb", ms=3,
                    label="haze world, methanogens only")
            for kind, c in colors.items():
                for stable, marker in ((True, "o"), (False, "x")):
                    sel = [r for r in rows if r["t_switch_k"] == tsw and r["f_ac"] == f and r["kind"] == kind
                           and r["stable"] == stable]
                    if sel:
                        ax.plot([r["potential"] for r in sel], [r["t_k"] for r in sel], marker, color=c, ms=3.5,
                                mfc=c if stable else "none", label=f"{kind}{'' if stable else ' (unstable)'}")
            ax.axhline(tsw, color="k", lw=0.6, ls=":")
            ax.set_ylim(277.0, 299.0)
            ax.set_title(f"T_sw = {tsw} K, f_ac = {f}", fontsize=9)
            if i == len(f_acs) - 1:
                ax.set_xlabel("donor potential (CH4/CO2 at full capture)")
            if j == 0:
                ax.set_ylabel("surface temperature (K)")
    handles, labels = [], []
    for ax in axes.flat:
        for h, lab in zip(*ax.get_legend_handles_labels()):
            if lab not in labels:
                handles.append(h)
                labels.append(lab)
    fig.legend(handles, labels, loc="lower center", ncol=4, fontsize=8, frameon=False)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(out, dpi=150)
    plt.close(fig)


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main(out: Path = FIGURES) -> None:
    out.mkdir(parents=True, exist_ok=True)
    p, losses = reference()
    loss = losses[2]
    potentials = np.round(np.linspace(0.12, 0.60, 49), 4)
    switches = [Switch(t, f) for t in (278.5, 281.5, 282.8) for f in (0.0, 0.5, 0.9)]
    rows = sweep(p, loss, potentials, switches)
    baseline = sweep(p, loss, potentials, [Switch(250.0, 1.0)])
    write_csv(out / "states.csv", rows)
    ref = {}
    for sw in switches:
        ref[f"T_sw={sw.t_switch_k}, f_ac={sw.f_ac}"] = [
            {k: v for k, v in e.items() if k != "sides"} for e in states(p, loss, sw)]
    checks = []
    for sw in (Switch(281.5, 0.0), Switch(282.8, 0.5)):
        mixed = [e for e in mixed_states(p, loss, sw) if e["stable"]]
        for g in (0.1, 1.0, 10.0):
            end = integrate(p, loss, replace(sw, selection_per_k_yr=g), r0=0.1953, s0=0.01)
            checks.append(dict(t_switch_k=sw.t_switch_k, f_ac=sw.f_ac, g=g, predicted_s=mixed[0]["s"] if mixed else None,
                               **end))
    (out / "summary.json").write_text(json.dumps(dict(reference_states=ref, dynamic_checks=checks,
                                                       loss=loss.label, potentials=list(map(float, potentials))),
                                                  indent=2, default=float) + "\n")
    plot(rows, baseline, out / "switch_coupling.png")
    print(json.dumps(dict(reference_states=ref, dynamic_checks=checks), indent=1, default=float))


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else FIGURES)
