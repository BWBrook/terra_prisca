"""Supply diagrams and transient checks for the full population coupling.

    uv run python -m terra_prisca.haze_world.population_experiments

One fixed habitat volume and hydrogen exchange coefficient serve every supply.
Large raw records remain in ignored local storage; public outputs stay compact.
"""

import argparse
from collections import Counter
import csv
from dataclasses import asdict, replace
import gzip
from hashlib import sha256
import importlib.metadata
import io
import itertools
import json
from pathlib import Path

import numpy as np
from scipy.optimize import brentq

from .experiments import flux_for_potential
from .methane_budget import temperature_k
from .population_coupling import (HOURS_PER_YEAR, Coupled, equilibrium_states,
                                  fluxes, integrate, jacobian, reference, rhs, supply_h2)
from .two_guilds import BASE, HENRY_30C_MOL_L_PA

POTENTIALS = tuple(np.round(np.linspace(.12, .60, 25), 8))
FRACTIONS = (0., .5, .9, 1.)
LAGS = (.01, 1., 100., 10000.)
VARIANTS = ("constant", "cold_limited")
POOL_FLAG_MOL_L = .01


def at_potential(base, potential):
    return replace(base, climate=replace(base.climate,
                   donor_flux=float(flux_for_potential(potential, base.climate))))


def configurations(base):
    for variant, fraction, lag, potential in itertools.product(VARIANTS, FRACTIONS, LAGS, POTENTIALS):
        p = replace(at_potential(base, potential), recycling_variant=variant,
                    acetate_fraction=fraction, acetate_lifetime_yr=lag)
        yield dict(group="coupled", potential=float(potential), fraction=fraction,
                   lag_yr=lag, recycling=variant), p
    for potential in POTENTIALS:
        yield dict(group="methanogen_only", potential=float(potential), fraction=base.acetate_fraction,
                   lag_yr=base.acetate_lifetime_yr, recycling=base.recycling_variant), replace(
                       at_potential(base, potential), enabled=(False, True))
    for potential in (.22, .3, .5):
        original = at_potential(base, potential)
        original = replace(original, biology=replace(original.biology, low_temperature_variant="arrhenius_continuation"))
        for fraction in (.5, 1.):
            yield dict(group="continuation_coupled", potential=potential, fraction=fraction,
                       lag_yr=1., recycling="constant"), replace(original, acetate_fraction=fraction)
        yield dict(group="continuation_methanogen_only", potential=potential, fraction=.5,
                   lag_yr=1., recycling="constant"), replace(original, enabled=(False, True))
    for potential, scale in itertools.product((.12, .3, .6), (.1, 10.)):
        p = at_potential(base, potential)
        p = replace(p, biology=replace(p.biology, exchange_mol_l_h_pa=p.biology.exchange_mol_l_h_pa * scale))
        yield dict(group="outlet_check", potential=potential, fraction=.5, lag_yr=1., recycling="constant"), p


def _json(value):
    if isinstance(value, np.ndarray):
        return [_json(x) for x in value]
    if isinstance(value, (complex, np.complexfloating)):
        return [_json(float(value.real)), _json(float(value.imag))]
    if isinstance(value, dict):
        return {k: _json(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json(v) for v in value]
    if isinstance(value, np.generic):
        return _json(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def write_csv(path, rows, columns=None):
    if not rows:
        path.write_text(",".join(columns) + "\n" if columns else "")
        return
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: (format(v, ".10g") if np.isfinite(v) else "") if isinstance(v, (float, np.floating)) else v
                             for k, v in row.items()})


def state_record(case_id, state_id, metadata, e, p):
    y, f = e["y"], fluxes(e["y"], p)
    uptake = f["uptake_h2_mol_l_yr"]
    leading = e["eigenvalues"][int(np.argmax(e["eigenvalues"].real))]
    scales = np.r_[f["supply_h2_mol_l_yr"] / HENRY_30C_MOL_L_PA,
                   np.maximum(p.biology.loss_h * HOURS_PER_YEAR * y[1:3], 1e-15),
                   max(f["acetate_production_mol_l_yr"], 1e-15),
                   max(f["methane_source_ratio_yr"], f["methane_loss_ratio_yr"], 1e-15)]
    return dict(case_id=case_id, state_id=state_id, **metadata, kind=e["kind"],
                stability=e["stability"], climate_domain=e["domain"], temperature_k=e["t_k"],
                methane_ratio=e["r"], pressure_pa=y[0], biomass_a_g_l=y[1], biomass_m_g_l=y[2],
                acetate_mol_l=y[3], acetate_above_10mm=bool(y[3] > POOL_FLAG_MOL_L),
                physiology_continued_below_4c=bool(e["t_k"] < 277.15),
                capture_fraction=float(sum(uptake) / f["supply_h2_mol_l_yr"]),
                a_uptake_share=float(uptake[0] / sum(uptake)) if sum(uptake) > 0 else None,
                uptake_share_status="defined" if sum(uptake) > 0 else "no_uptake",
                effective_recycling=f["k_rec_yr"] / (f["k_rec_yr"] + f["k_other_yr"]),
                max_real_yr=e["max_real_yr"], leading_imag_yr=abs(float(leading.imag)),
                eigenvalue_count=len(e["eigenvalues"]),
                max_scaled_rhs_error=float(max(abs(rhs(y, p)) / scales)),
                relative_redox_residual=abs(e["redox_residual"]) / f["supply_h2_mol_l_yr"])


def _mixed(states):
    candidates = [e for e in states if e["kind"] == "mixed"]
    return candidates[0] if len(candidates) == 1 else None


def stability_changes(cases, states_by_case):
    lookup = {(m["recycling"], m["fraction"], m["potential"], m["lag_yr"]): (key, m, p)
              for key, (m, p) in cases.items() if m["group"] == "coupled"}
    brackets = []
    for variant, fraction, potential in itertools.product(VARIANTS, FRACTIONS, POTENTIALS):
        for low, high in zip(LAGS[:-1], LAGS[1:]):
            left = lookup[(variant, fraction, float(potential), low)]
            right = lookup[(variant, fraction, float(potential), high)]
            a, b = _mixed(states_by_case[left[0]]), _mixed(states_by_case[right[0]])
            if a is None or b is None or a["max_real_yr"] * b["max_real_yr"] >= 0:
                continue
            brackets.append((dict(recycling=variant, fraction=fraction, potential=float(potential),
                                  lower_lag_yr=low, upper_lag_yr=high,
                                  lower_max_real_yr=a["max_real_yr"], upper_max_real_yr=b["max_real_yr"]), left[2]))
    brackets.sort(key=lambda pair: (abs(pair[0]["potential"] - .3), abs(pair[0]["fraction"] - .5), pair[0]["recycling"]))
    output = []
    for number, (row, original) in enumerate(brackets):
        row.update(refined=False, crossing_lag_yr=None, leading_imag_yr=None,
                   candidate_type="unrefined_stability_change")
        if number < 16:
            def evaluate(log_lag):
                p = replace(original, acetate_lifetime_yr=float(np.exp(log_lag)))
                state = _mixed(equilibrium_states(p))
                return state["max_real_yr"] if state is not None else np.nan
            try:
                location = brentq(evaluate, np.log(row["lower_lag_yr"]), np.log(row["upper_lag_yr"]), xtol=1e-7)
            except ValueError:
                row["candidate_type"] = "unresolved_branch_bracket"
            else:
                p = replace(original, acetate_lifetime_yr=float(np.exp(location)))
                state = _mixed(equilibrium_states(p))
                eigen = state["eigenvalues"][np.argmax(state["eigenvalues"].real)]
                row.update(refined=True, crossing_lag_yr=float(np.exp(location)),
                           leading_imag_yr=abs(float(eigen.imag)),
                           candidate_type="complex_pair_candidate" if abs(eigen.imag) > 1e-8 else "real_mode_candidate")
        output.append(row)
    return output


def resolution_audit(cases, states_by_case):
    rows = []
    for index, (case_id, (metadata, p)) in enumerate(cases.items()):
        if index % 37 != 0 and metadata["potential"] != .3:
            continue
        # Equal-ratio states of different guilds can swap order by roundoff.
        coarse = sorted(states_by_case[case_id], key=lambda e: (e["kind"], e["r"]))
        fine = sorted(equilibrium_states(p, n_grid=1001), key=lambda e: (e["kind"], e["r"]))
        same = len(coarse) == len(fine) and [e["kind"] for e in coarse] == [e["kind"] for e in fine]
        types = same and [e["stability"] for e in coarse] == [e["stability"] for e in fine]
        rows.append(dict(case_id=case_id, coarse_states=len(coarse), fine_states=len(fine),
                         matching_kinds_and_stability=types,
                         max_ratio_difference=max((abs(a["r"] - b["r"]) for a, b in zip(coarse, fine)), default=0.) if same else None))
    return rows


def lag_spectral_audit(cases, states_by_case, raw):
    rows = []
    for case_id, (metadata, original) in cases.items():
        if (metadata["group"] != "coupled" or metadata["potential"] not in (.22, .24, .3, .5)
                or metadata["fraction"] not in (.5, .9) or metadata["lag_yr"] != 1.):
            continue
        state = _mixed(states_by_case[case_id])
        if state is None:
            continue
        for lag in np.geomspace(.01, 10000., 61):
            p = replace(original, acetate_lifetime_yr=float(lag))
            y = state["y"].copy()
            y[3] *= lag / original.acetate_lifetime_yr
            values = np.linalg.eigvals(jacobian(y, p))
            leading = values[np.argmax(values.real)]
            description = dict(state, y=y, eigenvalues=values, max_real_yr=float(leading.real))
            record = state_record(case_id, f"{case_id}_lag_{lag:.8g}", metadata, description, p)
            rows.append(dict(case_id=case_id, recycling=metadata["recycling"], fraction=metadata["fraction"],
                             potential=metadata["potential"], lag_yr=float(lag),
                             max_real_yr=float(leading.real), leading_imag_yr=abs(float(leading.imag)),
                             acetate_mol_l=float(y[3]), max_scaled_rhs_error=record["max_scaled_rhs_error"]))
            raw.write(json.dumps(_json(dict(record="lag_spectrum", **rows[-1], eigenvalues=values)), allow_nan=False) + "\n")
    return rows


def _trajectory(run_id, case_id, y0, p, e, years, raw):
    scales = np.maximum(abs(e["y"]), [1., 1e-6, 1e-6, 1e-6, .001])
    times = np.unique(np.r_[0., np.geomspace(1e-5, 100., 121), np.linspace(100., years, 1601)])
    result = integrate(y0, p, years, sample_times=times)
    distance = np.max(abs((result.y.T - e["y"]) / scales), axis=1)
    temperatures = np.asarray(temperature_k(result.y[4], p.climate))
    raw.write(json.dumps(_json(dict(record="trajectory", run_id=run_id, case_id=case_id,
                                    times=result.t, y=result.y, log_biomass=result.log_biomass,
                                    positive_coordinates=result.positive_coordinates)), allow_nan=False) + "\n")
    points = []
    public_times = np.unique(np.r_[0., np.geomspace(1e-5, 100., 61), np.linspace(100., years, 320)])
    indices = np.unique(np.minimum(np.searchsorted(result.t, public_times), len(result.t) - 1))
    for i in indices:
        points.append(dict(run_id=run_id, case_id=case_id, time_yr=float(result.t[i]),
                           pressure_pa=float(result.y[0, i]), biomass_a_g_l=float(result.y[1, i]),
                           biomass_m_g_l=float(result.y[2, i]), acetate_mol_l=float(result.y[3, i]),
                           methane_ratio=float(result.y[4, i]), temperature_k=float(temperatures[i]),
                           log_biomass_a=float(result.log_biomass[0, i]),
                           log_biomass_m=float(result.log_biomass[1, i]),
                           scaled_distance=float(distance[i])))
    late = result.y[:, result.t >= .9 * years]
    late_span = max((np.max(late, axis=1) - np.min(late, axis=1)) / scales)
    summary = dict(run_id=run_id, case_id=case_id, predicted_stability=e["stability"],
                   duration_yr=years, start_scaled_distance=float(distance[0]),
                   end_scaled_distance=float(distance[-1]), max_scaled_distance=float(max(distance)),
                   temperature_min_k=float(min(temperatures)), temperature_max_k=float(max(temperatures)),
                   min_log_biomass_a=float(min(result.log_biomass[0])),
                   min_log_biomass_m=float(min(result.log_biomass[1])),
                   end_methane_tendency_ratio_yr=float(rhs(result.y[:, -1], p)[4]),
                   late_state_span_scaled=float(late_span),
                   near_mixed_at_end=bool(distance[-1] < 1e-5 and late_span < 1e-5),
                   integration_success=bool(result.success))
    return points, summary


def transient_checks(cases, states_by_case, raw):
    selected = []
    for variant in VARIANTS:
        candidates = [(key, p, _mixed(states_by_case[key])) for key, (m, p) in cases.items()
                      if m["group"] == "coupled" and m["recycling"] == variant
                      and m["potential"] == .3 and m["fraction"] == .5 and m["lag_yr"] == 1.]
        selected.extend((key, p, e) for key, p, e in candidates if e is not None and e["stable"])
    unstable = [(key, p, e) for key, (m, p) in cases.items() if m["group"] == "coupled"
                for e in states_by_case[key] if e["kind"] == "mixed" and e["stability"] == "unstable" and e["domain"] == "arney"]
    unstable.sort(key=lambda item: (abs(cases[item[0]][0]["potential"] - .3),
                                    abs(cases[item[0]][0]["fraction"] - .5), -item[2]["max_real_yr"]))
    selected.extend(unstable[:2])
    if not unstable:
        candidates = [(key, p, _mixed(states_by_case[key])) for key, (m, p) in cases.items()
                      if m["group"] == "coupled" and m["recycling"] == "constant"
                      and m["potential"] == .3 and m["fraction"] == .5 and m["lag_yr"] == 10000.]
        selected.extend((key, p, e) for key, p, e in candidates if e is not None)
    points, summaries = [], []
    for case_id, p, e in selected:
        for sign in (-1, 1):
            y0 = e["y"].copy()
            y0[1] *= 1 + sign * .01
            y0[2] *= 1 - sign * .01
            years = min(250000., max(20000., 12 / max(abs(e["max_real_yr"]), 1e-12)))
            run_id = f"{case_id}_{'plus' if sign > 0 else 'minus'}"
            run_points, summary = _trajectory(run_id, case_id, y0, p, e, years, raw)
            points.extend(run_points)
            summaries.append(summary)
    target = next(((key, p, _mixed(states_by_case[key])) for key, (m, p) in cases.items()
                   if m["group"] == "coupled" and m["recycling"] == "constant" and m["potential"] == .3
                   and m["fraction"] == .5 and m["lag_yr"] == 1.), None)
    control = next((e for key, (m, _) in cases.items() if m["group"] == "methanogen_only" and m["potential"] == .3
                    for e in states_by_case[key] if e["kind"] == "methanogen" and e["stable"]), None)
    if target is not None and target[2] is not None and control is not None:
        case_id, p, e = target
        for seed, years in ((1e-12, 100000.), (1e-120, 20000.)):
            y0 = control["y"].copy()
            y0[1] = seed
            run_id = f"{case_id}_invasion_{seed:g}"
            run_points, summary = _trajectory(run_id, case_id, y0, p, e, years, raw)
            points.extend(run_points)
            summaries.append(summary)
    return points, summaries


def plot_states(rows, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    colors = {"methanogen": "#4679b4", "acetogen": "#dc8f38", "mixed": "#3f8b60", "lifeless": "#888888"}
    controls = [r for r in rows if r["group"] == "methanogen_only" and r["stability"] == "stable"]
    for variant in VARIANTS:
        fig, axes = plt.subplots(4, 4, figsize=(12, 9), sharex=True, sharey=True, layout="constrained")
        for i, lag in enumerate(LAGS):
            for j, fraction in enumerate(FRACTIONS):
                ax = axes[i, j]
                ax.plot([r["potential"] for r in controls], [r["temperature_k"] for r in controls],
                        ".", color="#bdbdbd", ms=4, zorder=0)
                for kind, color in colors.items():
                    for stability, marker in (("stable", "o"), ("unstable", "x"), ("marginal", "+")):
                        subset = [r for r in rows if r["group"] == "coupled" and r["recycling"] == variant
                                  and r["lag_yr"] == lag and r["fraction"] == fraction and r["kind"] == kind
                                  and r["stability"] == stability]
                        ax.scatter([r["potential"] for r in subset], [r["temperature_k"] for r in subset],
                                   s=11, marker=marker, color=color, alpha=.75)
                ax.set_ylim(272.5, 299.)
                if i == 0:
                    ax.set_title(f"Nominal acetate fraction f={fraction:g}")
                if j == 0:
                    ax.set_ylabel(f"Lag {lag:g} yr\nTemperature (K)")
                if i == 3:
                    ax.set_xlabel("Donor potential")
        fig.suptitle(f"Full population coupling: {variant.replace('_', ' ')} recycling")
        from matplotlib.lines import Line2D
        handles = [Line2D([], [], color=c, marker="o", ls="", label=k) for k, c in colors.items()]
        handles += [Line2D([], [], color="#444444", marker="x", ls="", label="unstable"),
                    Line2D([], [], color="#bdbdbd", marker="o", ls="", label="M-only, same physiology")]
        fig.legend(handles=handles, loc="outside lower center", ncol=3, frameon=False)
        fig.savefig(output / f"supply_diagram_{variant}.png", dpi=140)
        plt.close(fig)


def plot_stability(rows, transients, output):
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout="constrained")
    for variant, color in zip(VARIANTS, ("#4679b4", "#dc8f38")):
        for lag, marker in zip(LAGS, ("o", "s", "^", "v")):
            subset = [r for r in rows if r["kind"] == "mixed" and r["recycling"] == variant and r["lag_yr"] == lag]
            axes[0].scatter([r["potential"] for r in subset], [r["max_real_yr"] for r in subset],
                            s=15, marker=marker, facecolor=color if variant == "constant" else "none",
                            edgecolor=color, label=f"{variant.replace('_', ' ')}, {lag:g} yr")
    axes[0].axhline(0., color="#555555", lw=1)
    axes[0].set(xlabel="Donor potential", ylabel="Largest eigenvalue real part (yr⁻¹)",
                title="Full-spectrum local stability: mixed states")
    axes[0].set_yscale("symlog", linthresh=1e-5)
    for run_id in dict.fromkeys(r["run_id"] for r in transients):
        subset = [r for r in transients if r["run_id"] == run_id]
        axes[1].plot([max(r["time_yr"], 1e-5) for r in subset],
                     [max(r["scaled_distance"], 1e-14) for r in subset], lw=1, label=run_id)
    axes[1].set(xscale="log", yscale="log", xlabel="Time (yr)", ylabel="Scaled distance from equilibrium",
                title="Perturbed population integrations")
    axes[0].legend(fontsize=6)
    axes[1].legend(fontsize=6)
    fig.savefig(output / "stability_and_transients.png", dpi=145)
    plt.close(fig)


def plot_invasions(transients, output):
    import matplotlib.pyplot as plt
    run_ids = [name for name in dict.fromkeys(r["run_id"] for r in transients) if "_invasion_" in name]
    if not run_ids:
        return
    fig, axes = plt.subplots(2, len(run_ids), figsize=(10, 6), squeeze=False, layout="constrained")
    for column, run_id in enumerate(run_ids):
        selected = [r for r in transients if r["run_id"] == run_id]
        times = [r["time_yr"] for r in selected]
        axes[0, column].plot(times, [r["temperature_k"] for r in selected], color="#555555", lw=1)
        axes[0, column].axhline(281.534822805, color="#3f8b60", lw=.8, ls="--")
        axes[0, column].set_title(f"Acetogen seed {run_id.split('_invasion_')[1]} gDW/L")
        axes[0, column].set_ylabel("Temperature (K)")
        for field, name, color in (("log_biomass_a", "acetogens", "#dc8f38"),
                                   ("log_biomass_m", "methanogens", "#4679b4")):
            axes[1, column].plot(times, [r[field] / np.log(10.) for r in selected], label=name, color=color, lw=1)
        axes[1, column].set(xlabel="Time (yr)", ylabel="log₁₀ biomass (gDW/L)")
        axes[1, column].legend(frameon=False)
    fig.suptitle("Invasion from the methanogen-only control: continuum trajectories")
    fig.savefig(output / "invasion_paths.png", dpi=145)
    plt.close(fig)


def run(output, raw_output):
    output.mkdir(parents=True, exist_ok=True)
    raw_output.parent.mkdir(parents=True, exist_ok=True)
    base = reference(.3)
    cases, states_by_case, rows, configuration_rows, spectra = {}, {}, [], [], []
    with raw_output.open("wb") as binary, gzip.GzipFile(filename="", mode="wb", fileobj=binary, mtime=0) as compressed, io.TextIOWrapper(compressed) as raw:
        for number, (metadata, p) in enumerate(configurations(base)):
            metadata = dict(metadata, low_temperature_variant=p.biology.low_temperature_variant,
                            exchange_scale=p.biology.exchange_mol_l_h_pa / base.biology.exchange_mol_l_h_pa)
            case_id = f"case_{number:04d}"
            cases[case_id] = metadata, p
            states = equilibrium_states(p)
            states_by_case[case_id] = states
            configuration_rows.append(dict(case_id=case_id, **metadata, supply_h2_mol_l_h=supply_h2(p),
                                           habitat_l_cm2=p.habitat_l_cm2, exchange_mol_l_h_pa=p.biology.exchange_mol_l_h_pa,
                                           guilds_enabled="A+M" if all(p.enabled) else "M"))
            for index, state in enumerate(states):
                state_id = f"{case_id}_state_{index}"
                rows.append(state_record(case_id, state_id, metadata, state, p))
                for mode, value in enumerate(state["eigenvalues"]):
                    spectra.append(dict(state_id=state_id, recycling=metadata["recycling"], group=metadata["group"],
                                        mode=mode, real_yr=float(value.real), imag_yr=float(value.imag)))
                raw.write(json.dumps(_json(dict(record="equilibrium", case_id=case_id, state_id=state_id,
                                                parameters=asdict(p), state=state, fluxes=fluxes(state["y"], p))), allow_nan=False) + "\n")
        candidates = stability_changes(cases, states_by_case)
        resolution = resolution_audit(cases, states_by_case)
        lag_audit = lag_spectral_audit(cases, states_by_case, raw)
        trajectories, transient_summary = transient_checks(cases, states_by_case, raw)
    write_csv(output / "configurations.csv", configuration_rows)
    for variant in VARIANTS:
        write_csv(output / f"equilibria_{variant}.csv", [r for r in rows if r["group"] == "coupled" and r["recycling"] == variant])
        write_csv(output / f"eigenvalues_{variant}.csv", [r for r in spectra if r["group"] == "coupled" and r["recycling"] == variant])
    write_csv(output / "methanogen_only.csv", [r for r in rows if r["group"] == "methanogen_only"])
    write_csv(output / "continuation_check.csv", [r for r in rows if r["group"].startswith("continuation_") or
              (r["potential"] in (.22, .3, .5) and r["recycling"] == "constant" and r["lag_yr"] == 1.
               and (r["group"] == "methanogen_only" or r["group"] == "coupled" and r["fraction"] in (.5, 1.)))])
    write_csv(output / "outlet_check.csv", [r for r in rows if r["group"] == "outlet_check" or
              (r["group"] == "coupled" and r["potential"] in (.12, .3, .6) and r["recycling"] == "constant"
               and r["lag_yr"] == 1. and r["fraction"] == .5)])
    write_csv(output / "stability_change_candidates.csv", candidates,
              columns=("recycling", "fraction", "potential", "lower_lag_yr", "upper_lag_yr",
                       "lower_max_real_yr", "upper_max_real_yr", "refined", "crossing_lag_yr",
                       "leading_imag_yr", "candidate_type"))
    write_csv(output / "resolution_audit.csv", resolution)
    write_csv(output / "lag_spectral_audit.csv", lag_audit)
    write_csv(output / "trajectories.csv", trajectories)
    write_csv(output / "transient_summary.csv", transient_summary)
    groups = {}
    for variant in VARIANTS:
        selected = [r for r in rows if r["group"] == "coupled" and r["recycling"] == variant]
        stable = [r for r in selected if r["stability"] == "stable"]
        groups[variant] = dict(configurations=sum(m["group"] == "coupled" and m["recycling"] == variant for m, _ in cases.values()),
                               states=len(selected), stable_kinds=dict(Counter(r["kind"] for r in stable)),
                               mixed_stability=dict(Counter(r["stability"] for r in selected if r["kind"] == "mixed")),
                               stable_climate_domains=dict(Counter(r["climate_domain"] for r in stable)),
                               stable_acetate_above_10mm=sum(r["acetate_above_10mm"] for r in stable),
                               stable_temperature_range_k=[min(r["temperature_k"] for r in stable), max(r["temperature_k"] for r in stable)])
    source_paths = [Path(__file__), Path(__file__).with_name("population_coupling.py"),
                    Path(__file__).with_name("two_guilds.py"), Path(__file__).with_name("methane_budget.py"),
                    Path(__file__).with_name("woodii1998.py"), BASE.parent / "haze_response/arney2016/figure4.csv",
                    BASE / "evidence/kotsyurbenko2001_table2.csv", BASE / "evidence/peters1998_chemostat.csv"]
    manifest = dict(reference=_json(asdict(base)), configurations=len(cases), groups=groups,
                    state_records=len(rows), coarse_grid=501, resolution_audit=dict(configurations=len(resolution),
                    mismatches=sum(not r["matching_kinds_and_stability"] for r in resolution),
                    max_ratio_difference=max((r["max_ratio_difference"] for r in resolution if r["max_ratio_difference"] is not None), default=None)),
                    stability_change_candidates=len(candidates), refined_candidates=sum(r["refined"] for r in candidates),
                    dense_lag_audit=dict(states=len(lag_audit), source_cases=len({r["case_id"] for r in lag_audit}),
                        unstable_states=sum(r["max_real_yr"] > 1e-9 for r in lag_audit),
                        maximum_real_yr=max(r["max_real_yr"] for r in lag_audit),
                        max_scaled_rhs_error=max(r["max_scaled_rhs_error"] for r in lag_audit)),
                    trajectories=len(transient_summary), max_scaled_equilibrium_rhs_error=max(r["max_scaled_rhs_error"] for r in rows),
                    max_relative_redox_residual=max(r["relative_redox_residual"] for r in rows),
                    pool_flag_mol_l=POOL_FLAG_MOL_L,
                    raw_path="local/haze/population_coupling/raw_records.jsonl.gz",
                    raw_sha256=sha256(raw_output.read_bytes()).hexdigest(),
                    long_invasion_protocol=dict(reference_potential=.3, acetate_fraction=.5, acetate_lifetime_yr=1.,
                        recycling_variant="constant", initial_resident="stable methanogen-only control with same physiology",
                        acetogen_seed_g_l=1e-12, duration_yr=100000.,
                        solver="population_coupling.integrate: LSODA with softplus positive biomass coordinates",
                        reproduction="standalone CLI generates trajectory; no cache or checkpoint input"),
                    inactive_inherited_climate_fields=["growth_ratio_max", "t_opt_k", "t_halfwidth_k", "thermal", "maintenance_flux"],
                    unavailable_estimates="null in JSON or empty in CSV; accompanying status fields identify why",
                    input_sha256={str(path.relative_to(BASE.parents[1])): sha256(path.read_bytes()).hexdigest() for path in source_paths},
                    packages={name: importlib.metadata.version(name) for name in ("numpy", "scipy", "matplotlib")},
                    caveats=["Conditional model, not Archean calibration.",
                             "Reference habitat, timescales, recycling-temperature response and low-methane climate bridge are assumptions.",
                             "Equilibrium uptake thresholds keep reference product activities despite explicit acetate pools.",
                             "A complex eigenvalue is not evidence of sustained oscillations; crossings are candidates only.",
                             "Finite equilibrium grids cannot exclude every tangent or unresolved branch."])
    (output / "manifest.json").write_text(json.dumps(_json(manifest), indent=2, allow_nan=False) + "\n")
    plot_states(rows, output)
    plot_stability(rows, trajectories, output)
    plot_invasions(trajectories, output)
    if any(path.stat().st_size >= 1_000_000 for path in output.iterdir()):
        raise RuntimeError("A public experiment output exceeded the 1 MB limit")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=BASE / "figures/population_coupling")
    parser.add_argument("--raw", type=Path, default=BASE.parents[1] / "local/haze/population_coupling/raw_records.jsonl.gz")
    args = parser.parse_args()
    print(json.dumps(_json(run(args.output, args.raw)), indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
