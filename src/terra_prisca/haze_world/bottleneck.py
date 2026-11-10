"""Conditional branching diagnostics for uncensored refuge trajectories.

Probabilities condition on a recorded environment and the specified birth/death
split. They are not joint endpoint probabilities for a stochastic ecosystem.
"""

import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from hashlib import sha256
import gzip
import json
from pathlib import Path

import numpy as np
from scipy.optimize import brentq
from scipy.special import logsumexp

from . import branching
from . import buffered_experiments as experiments
from . import bottleneck_runs as runs
from . import habitat_coupling as habitat
from . import population_coupling as core


def excursions(log_counts, threshold):
    """Sampled intervals below threshold, bracketed by their adjacent samples."""
    below = np.asarray(log_counts) < threshold
    starts = np.flatnonzero(below & np.r_[True, ~below[:-1]])
    ends = np.flatnonzero(below & np.r_[~below[1:], True])
    return [(max(int(a)-1, 0), min(int(b)+1, below.size-1), int(b) == below.size-1)
            for a, b in zip(starts, ends)]


def _log_probability(log_lambda):
    if log_lambda < -36:
        return float(log_lambda)
    if log_lambda > np.log(40.):
        return 0.
    return float(np.log(-np.expm1(-np.exp(log_lambda))))


def combine_windows(log_lambdas):
    """Conditional survival through windows, resetting to each recorded entry.

    This is a product of conditional diagnostics, not an exact correlated
    multi-excursion branching distribution. Single-window results are exact
    under the recorded environment and Poisson-entry convention.
    """
    values = np.asarray(log_lambdas, dtype=float)
    if values.ndim != 1 or not values.size or np.any(np.isnan(values)):
        raise ValueError("Provide nonempty finite-or-negative-infinite log intensities")

    def log_probability(log_scale):
        return sum(_log_probability(x+log_scale) for x in values)

    low, high = np.exp(log_probability(np.log(1e-3))), np.exp(log_probability(np.log(1e3)))
    classification = "robust_loss" if high < .01 else "robust_persistence" if low > .99 else "contingent"
    if np.any(np.isneginf(values)):
        half = np.inf
    else:
        half = brentq(lambda s: log_probability(s)-np.log(.5), -max(values)-50., -min(values)+50.)
    return dict(log_survival_probability=log_probability(0.), survival_probability=float(np.exp(log_probability(0.))),
                probability_scale_low=float(low), probability_scale_high=float(high), classification=classification,
                log_scale_for_half_survival=float(half), scale_for_half_survival=_exp(half),
                log_lambda=float(min(values)), expected_surviving_lineages=_exp(min(values)),
                lambda_semantics="single_window" if values.size == 1 else "limiting_window")


def _exp(value):
    return float(np.exp(value)) if value < np.log(np.finfo(float).max) else np.inf


def _indices(times, lo, hi, stride):
    chosen = np.arange(lo, hi+1, max(1, int(np.ceil(stride / np.median(np.diff(times))))))
    return np.unique(np.r_[chosen, hi]).astype(int)


def _rates(y, p, guild, indices):
    pairs = [branching.per_cell_rates(y[:, i], p, guild) for i in indices]
    return np.array([v[1] for v in pairs]), np.array([v[2] for v in pairs])


def _uptake_fraction(y, p, guild, indices):
    largest_local = largest_global = 0.
    for i in indices:
        f = habitat.fluxes(y[:, i], p)
        used = np.zeros(2)
        for j, weight in enumerate(p.weights):
            if not weight:
                continue
            uptake = np.asarray(f["local"][j]["uptake_h2_mol_l_yr"])
            denominator = uptake.sum()
            fraction = uptake[guild]/denominator if denominator > 0 else 0.
            largest_local = max(largest_local, fraction)
            used += weight*uptake
        if used.sum() > 0:
            largest_global = max(largest_global, used[guild]/used.sum())
    return float(largest_local), float(largest_global)


def _curvature(t, log_total, k):
    if k < 2 or k > t.size-3:
        return None
    lo, hi = max(0, k-3), min(t.size, k+4)
    coefficient = np.polyfit(t[lo:hi]-t[k], log_total[lo:hi], 2)[0]*2
    return float(coefficient) if coefficient > 0 else None


def analyze_arrays(t, y, log_biomass, metadata, p, guild, dense_min_log=None, dense_min_time=None):
    """Return a flat guild summary and individual probability-window evidence.

    Dense minima, when supplied, are *global log cell counts*, not densities.
    Sampled rates are linear between recorded times. Biological zeros in
    inactive habitats remain excluded; active retained logarithms can be far
    below physical floating-point range.
    """
    t, y, logs = np.asarray(t), np.asarray(y), np.asarray(log_biomass)
    if t.ndim != 1 or t.size < 2 or np.any(np.diff(t) <= 0):
        raise ValueError("Provide increasing sampled times")
    if y.shape != (p.state_size, t.size) or logs.shape != (p.n_patches, 2, t.size):
        raise ValueError("Trajectory arrays do not match the model")
    active = np.flatnonzero(p.weights > 0)
    log_cells = logs[active, guild, :].T + np.log(p.weights[active]) + metadata["global_log_cell_conversion"]
    if np.any(~np.isfinite(log_cells)):
        raise ValueError("Uncensored initially present guilds require retained finite logs")
    log_total = logsumexp(log_cells, axis=1)
    k = int(np.argmin(log_total))
    minimum = float(log_total[k]) if dense_min_log is None else float(dense_min_log)
    minimum_time = float(t[k]) if dense_min_time is None else float(dense_min_time)
    threshold = min(np.log(1e16), minimum+np.log(1e8))
    prescribed = threshold
    windows = excursions(log_total, threshold)
    local = global_ = 0.
    reductions = 0
    while windows:
        local = global_ = 0.
        for lo, hi, terminal in windows:
            a, b = _uptake_fraction(y, p, guild, np.arange(lo, hi+1))
            local, global_ = max(local, a), max(global_, b)
        if max(local, global_) <= 1e-10:
            break
        threshold -= np.log(10.)
        reductions += 1
        windows = excursions(log_total, threshold)
    rare = bool(windows)
    if not windows:
        windows = [(0, len(t)-1, False)]
    evidence = []
    for lo, hi, terminal in windows:
        indices = np.arange(lo, hi+1) if rare else _indices(t, lo, hi, 10.)
        birth, death = _rates(y, p, guild, indices)
        logu = branching.backward_survival(t[indices], birth, death, branching.migration_matrix(p),
                                          max_step=1. if rare else 10.)
        result = branching.lineages(log_cells[lo], logu)
        a, b = _uptake_fraction(y, p, guild, indices) if rare else (None, None)
        minimum_index = lo+int(np.argmin(log_total[lo:hi+1]))
        evidence.append(dict(start_yr=float(t[lo]), end_yr=float(t[hi]), terminal_excursion=terminal,
            minimum_log_cells=float(log_total[minimum_index]), minimum_time_yr=float(t[minimum_index]),
            log_entry_cells=log_cells[lo].tolist(), log_type_survival=logu.tolist(),
            maximum_local_uptake_fraction=a, maximum_global_uptake_fraction=b,
            rate_samples=len(indices), rate_max_spacing_yr=float(max(np.diff(t[indices]))), **result))
    combined = combine_windows([v["log_lambda"] for v in evidence])
    primary = {key: evidence[0][key] for key in ("log_lambda", "expected_surviving_lineages", "survival_probability",
        "probability_scale_low", "probability_scale_high", "classification", "log_scale_for_half_survival", "scale_for_half_survival")}
    curvature = _curvature(t, log_total, k)
    _, b_min, d_min = branching.per_cell_rates(y[:, k], p, guild)
    proportions = np.exp(log_cells[k]-log_total[k])
    late = np.flatnonzero(t >= max(t[0], t[-1]-5000.))
    late = _indices(t, int(late[0]), int(late[-1]), 10.)
    birth, death = _rates(y, p, guild, late)
    weights = np.exp(log_cells[late]-log_total[late, None])
    growth = np.sum(weights*(birth-death), axis=1)
    migration = branching.migration_matrix(p)
    operator = np.diag(birth[-1]-death[-1]-migration.sum(axis=1))+migration.T
    eigenvalue = float(max(np.linalg.eigvals(operator).real))
    temperatures = np.array([habitat.temperatures(y[:, i], p)[active] for i in late])
    pressure = y[4*active[:, None], late]
    stable_environment = bool(np.max(np.ptp(temperatures, axis=0)) < .01
                              and np.max(np.ptp(pressure, axis=1)/np.maximum(np.mean(pressure, axis=1), 1.)) < .001
                              and np.max(np.ptp(birth, axis=0)/np.maximum(np.mean(birth, axis=0), 1.)) < .001
                              and np.max(np.ptp(death, axis=0)/np.maximum(np.mean(death, axis=0), 1.)) < .001)
    if p.base.activity_feedback != "fixed":
        acetate = y[4*active[:, None]+3, late]
        methane = y[-1, late]
        stable_environment &= bool(np.max(np.ptp(acetate, axis=1)/np.maximum(np.mean(acetate, axis=1), 1e-15)) < .001
                                   and np.ptp(methane)/max(np.mean(methane), .001) < .001)
    sustained_negative = bool(t[-1]-t[late[0]] >= 4999. and np.all(growth < -1e-9))
    terminal_rare = bool(rare and any(v[2] for v in windows))
    exclusion_supported = bool(terminal_rare and sustained_negative and eigenvalue < -1e-9 and stable_environment)
    row = dict(guild=experiments.GUILDS[guild], horizon_yr=float(t[-1]), log_min_cells=minimum,
        sample_max_spacing_yr=float(max(np.diff(t))),
        log10_min_cells=minimum/np.log(10.), min_cells=_exp(minimum), min_time_yr=minimum_time,
        sampled_log_min_cells=float(log_total[k]), sampled_min_time_yr=float(t[k]),
        curvature_yr2=curvature, bottleneck_width_yr=None if curvature is None else float(np.sqrt(2*np.pi/curvature)),
        weighted_birth_at_min_yr=float(proportions@b_min), weighted_death_at_min_yr=float(proportions@d_min),
        log_threshold_cells=float(threshold), prescribed_log_threshold_cells=float(prescribed), threshold_reductions=reductions,
        window_count=len(evidence), rare_window=rare,
        probability_scope="rare_windows_conditional" if rare else "nonrare_full_path_frozen_environment",
        rarity_status="locally_and_globally_linear" if rare else "minimum_not_locally_linear" if reductions else "never_globally_rare",
        terminal_rare_excursion=terminal_rare, late_growth_min_yr=float(min(growth)), late_growth_max_yr=float(max(growth)),
        final_global_net_growth_yr=float(growth[-1]), final_invasion_eigenvalue_yr=eigenvalue,
        late_environment_stationary=stable_environment, sustained_late_negative=sustained_negative,
        exclusion_supported=exclusion_supported, needs_extension=bool(terminal_rare and not exclusion_supported),
        terminal_log_cells=float(log_total[-1]),
        terminal_presence_probability_upper_bound=float(np.exp(min(0., log_total[-1]))),
        terminal_presence_upper_bound_at_high_scale=float(np.exp(min(0., log_total[-1]+np.log(1000.)))),
        peak_global_temperature_k=float(metadata.get("global_max_temperature_k",
            np.max(core.temperature_k(y[-1], p.base.climate)))), **primary)
    row.update(log_survival_probability=_log_probability(primary["log_lambda"]),
               survival_probability_underflow=bool(primary["survival_probability"] == 0. and np.isfinite(primary["log_lambda"])),
               lambda_semantics="first_window" if rare else "full_path_conditional",
               conditional_reset_product_survival_probability=combined["survival_probability"],
               conditional_reset_product_log_probability=combined["log_survival_probability"],
               conditional_reset_product_classification=combined["classification"],
               conditional_reset_product_half_scale=combined["scale_for_half_survival"])
    row.update(first_window_log_lambda=evidence[0]["log_lambda"],
               first_window_survival_probability=evidence[0]["survival_probability"],
               first_window_min_log_cells=evidence[0]["minimum_log_cells"],
               first_window_cells_for_half_survival_at_min=_exp(evidence[0]["minimum_log_cells"]+primary["log_scale_for_half_survival"]),
               global_minimum_in_first_window=bool(evidence[0]["start_yr"] <= minimum_time <= evidence[0]["end_yr"]),
               first_likely_loss_window_end_yr=next((v["end_yr"] for v in evidence if v["survival_probability"] < .5), None),
               first_robust_loss_window_end_yr=next((v["end_yr"] for v in evidence if v["probability_scale_high"] < .01), None))
    for stride in (1, 10):
        census = np.isclose(t/stride, np.rint(t/stride), atol=1e-8, rtol=0.)
        chosen = np.flatnonzero(census & (t > 0))
        below = chosen[log_total[chosen] < 0]
        row[f"posthoc_global_floor_{stride}yr_loss"] = bool(below.size)
        row[f"posthoc_global_floor_{stride}yr_first_loss_yr"] = float(t[below[0]]) if below.size else None
        row[f"posthoc_global_floor_{stride}yr_min_log_cells"] = float(min(log_total[chosen])) if chosen.size else None
        row[f"posthoc_global_floor_{stride}yr_sampling_complete"] = bool(chosen.size == int(np.floor(t[-1]/stride)))
    return row, evidence


def load_npz(record, raw=runs.RAW):
    path = raw/record["raw_file"]
    if sha256(path.read_bytes()).hexdigest() != record["raw_sha256"]:
        raise RuntimeError("Uncensored raw checksum differs")
    with np.load(path, allow_pickle=False) as data:
        result = {name: data[name] for name in data.files}
    result["metadata"] = json.loads(str(result["metadata"]))
    return result


def load_original(record):
    path = experiments.RAW/record["raw_file"]
    if sha256(path.read_bytes()).hexdigest() != record["raw_sha256"]:
        raise RuntimeError("Original uncensored checksum differs")
    with gzip.open(path, "rt") as stream:
        payload = json.load(stream)
    r = payload["result"]
    return dict(t=np.asarray(r["t"]), y=np.asarray(r["y"]), log_biomass=np.asarray(r["log_biomass"]),
                metadata=r["metadata"], min_log_biomass=np.asarray(r["global_continuous_min_log_biomass"]),
                min_times=np.asarray(r["global_continuous_min_times_yr"]))


def _analyze_task(task):
    case, record, original, baseline_row = task
    p = experiments.parameters(case)
    data = load_original(record) if original else load_npz(record)
    conversion = data["metadata"]["global_log_cell_conversion"]
    rows, windows = [], []
    for g in ((0, 1) if baseline_row is not None else (0,)):
        row, evidence = analyze_arrays(data["t"], data["y"], data["log_biomass"], data["metadata"], p, g,
            dense_min_log=data["min_log_biomass"][g]+conversion, dense_min_time=data["min_times"][g])
        row.update(**asdict(case), source_raw_sha256=record["raw_sha256"], source_raw_file=record["raw_file"],
                   reused_uncensored_original=original)
        if baseline_row:
            row.update(base_case_id=baseline_row["base_case_id"], census_endpoint_class=baseline_row["endpoint_class"],
                       census_global_present=baseline_row[f"global_present_{experiments.GUILDS[g]}"],
                       any_local_cull=any(int(baseline_row[f"culls_{patch}_{guild}"])
                           for patch in ("bulk", "warm", "cold") for guild in experiments.GUILDS))
        rows.append(row)
        windows.append(dict(case_id=case.case_id, guild=experiments.GUILDS[g], windows=evidence))
    for g in range(2) if len(rows) == 2 else ():
        other = windows[1-g]["windows"]
        first_below = rows[1-g]["posthoc_global_floor_1yr_first_loss_yr"]
        loss_time = first_below if first_below is not None else other[0]["minimum_time_yr"]
        likely = [loss_time] if other[0]["survival_probability"] < .5 else []
        strong = [loss_time] if other[0]["survival_probability"] < .01 else []
        robust = [loss_time] if other[0]["probability_scale_high"] < .01 else []
        for window in windows[g]["windows"]:
            window["downstream_of_other_guild_likely_loss"] = bool(likely and min(likely) < window["start_yr"])
            window["downstream_of_other_guild_strong_loss"] = bool(strong and min(strong) < window["start_yr"])
            window["downstream_of_other_guild_robust_loss"] = bool(robust and min(robust) < window["start_yr"])
        rows[g]["downstream_of_other_guild_likely_loss"] = any(v["downstream_of_other_guild_likely_loss"] for v in windows[g]["windows"])
        rows[g]["downstream_of_other_guild_strong_loss"] = any(v["downstream_of_other_guild_strong_loss"] for v in windows[g]["windows"])
        rows[g]["downstream_of_other_guild_robust_loss"] = any(v["downstream_of_other_guild_robust_loss"] for v in windows[g]["windows"])
        rows[g]["other_guild_first_likely_loss_time_yr"] = min(likely) if likely else None
        rows[g]["community_probability_warning"] = "Per-guild recorded-environment diagnostic; not a joint stochastic community endpoint probability"
    return rows, windows


def _records():
    result = {}
    def priority(record):
        protocol = record["protocol"]
        return (protocol["years"], protocol.get("solver") == "accepted_state_trial_retry_v1",
                protocol.get("max_step_yr", np.inf) == 10.)
    for path in runs.RAW.glob("*.receipt.json"):
        record = json.loads(path.read_text())
        if record["execution_status"] != "complete":
            continue
        if sha256(experiments.dumps(record["protocol"]).encode()).hexdigest() != record["fingerprint"]:
            raise RuntimeError("Uncensored protocol fingerprint differs: "+path.name)
        key = record["protocol"]["case"]["case_id"]
        if key in result and priority(record) == priority(result[key]) and record["protocol"] != result[key]["protocol"]:
            raise RuntimeError("Ambiguous uncensored protocols at equal horizon: "+key)
        if key not in result or priority(record) > priority(result[key]):
            result[key] = record
    for record in result.values():
        for name, digest in record["protocol"]["source_sha256"].items():
            if sha256((experiments.ROOT/name).read_bytes()).hexdigest() != digest:
                raise RuntimeError("Selected uncensored physical source differs: "+name)
    return result


def threshold_crossings(rows, field, target):
    ordered = sorted(rows, key=lambda r:r["dispersal_yr"])
    crossings = []
    for a, b in zip(ordered[:-1], ordered[1:]):
        x, y = a[field]-target, b[field]-target
        if x == 0:
            crossings.append(dict(bracket_yr=[a["dispersal_yr"], a["dispersal_yr"]],
                                  interpolated_yr=a["dispersal_yr"]))
        elif x*y < 0 or y == 0:
            fraction = -x/(y-x)
            estimate = np.exp(np.log(a["dispersal_yr"])+fraction*np.log(b["dispersal_yr"]/a["dispersal_yr"]))
            crossings.append(dict(bracket_yr=[a["dispersal_yr"], b["dispersal_yr"]], interpolated_yr=float(estimate)))
    return crossings


def exchange_figure(rows, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    groups = {}
    for row in rows:
        if row["guild"] == "a":
            groups.setdefault((row["fraction"], row["refuge_fraction"]), []).append(row)
    criteria = []
    fig, axes = plt.subplots(2, 2, figsize=(11, 8), constrained_layout=True)
    colors = plt.cm.tab10(np.arange(len(groups)))
    for color, ((fraction, area), group) in zip(colors, sorted(groups.items())):
        group.sort(key=lambda r:r["dispersal_yr"])
        d = np.array([r["dispersal_yr"] for r in group])
        label = f"f={fraction:g}, warm area={100*area:g}%"
        minimum = [r["log10_min_cells"] for r in group]
        axes[0,0].plot(d, minimum, color=color, label=label)
        axes[0,1].plot(d, [r["peak_global_temperature_k"] for r in group], color=color)
        axes[1,0].plot(d, [r["survival_probability"] for r in group], color=color)
        axes[1,1].plot(d*area, minimum, color=color)
        comparisons = {}
        for field, target, name, marker in (("posthoc_global_floor_1yr_min_log_cells",0.,"one_year_floor","o"),
                ("posthoc_global_floor_10yr_min_log_cells",0.,"ten_year_floor","s"),
                ("log_lambda",np.log(np.log(2.)),"half_survival","x")):
            comparisons[name] = threshold_crossings(group, field, target)
            for crossing in comparisons[name]:
                intensity = np.interp(np.log(crossing["interpolated_yr"]), np.log(d), [r["log_lambda"] for r in group])
                probability = branching.probability_from_log_intensity(intensity)
                axes[1,0].scatter(crossing["interpolated_yr"], probability, marker=marker, color=color,
                                  s=45, facecolors="none" if marker != "x" else color)
        criteria.append(dict(fraction=fraction, refuge_fraction=area, transitions=comparisons))
    for ax in axes.flat:
        ax.set_xscale("log"); ax.grid(alpha=.2)
    axes[0,0].set_ylabel("log₁₀ minimum global acetogen cells")
    axes[0,0].axhline(0., color=".5", ls=":", lw=1)
    axes[0,0].legend(frameon=False, fontsize=9)
    axes[0,1].set_ylabel("Peak global temperature (K)")
    axes[1,0].set_ylabel("First-window survival probability")
    axes[1,0].set_ylim(-.03, 1.03); axes[1,0].axhline(.5, color=".5", ls=":", lw=1)
    axes[1,1].set_ylabel("log₁₀ minimum global acetogen cells")
    for ax in (axes[0,0], axes[0,1], axes[1,0]):ax.set_xlabel("Cell exchange (per year)")
    axes[1,1].set_xlabel("Cell exchange × warm area (per year)")
    from matplotlib.lines import Line2D
    handles = [Line2D([], [], color=".3", marker=m, ls="none", markerfacecolor="none", label=l)
               for m,l in (("o","1-year global floor"),("s","10-year global floor"),("x","50% survival"))]
    axes[1,0].legend(handles=handles, frameon=False, fontsize=8, loc="upper left")
    fig.suptitle("Warm refuge: acetogen invasion and the first demographic bottleneck")
    fig.savefig(output/"exchange_continuation.png", dpi=160); plt.close(fig)
    (output/"exchange_thresholds.json").write_text(experiments.dumps(dict(groups=criteria,
        method="All sampled threshold crossings retained; linear interpolation of threshold statistic against log exchange; brackets remain primary evidence",
        survival_scope="First rare-window Poisson survival in the recorded environment; floor diagnostics are global posthoc counts"))+"\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("planned", "exchange"), default="planned")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--case-id", action="append")
    args = parser.parse_args()
    records = _records()
    tasks = []
    def selected(case):
        return not args.case_id or case.case_id in args.case_id or case.case_id.rsplit("_t", 1)[0] in args.case_id
    if args.stage == "planned":
        for case, row, original in runs.planned():
            if not selected(case):
                continue
            culled = any(int(row[f"culls_{patch}_{g}"]) for patch in ("bulk", "warm", "cold") for g in experiments.GUILDS)
            if culled and case.case_id not in records:
                raise RuntimeError("Missing required uncensored trajectory: "+case.case_id)
            tasks.append((case, records[case.case_id] if culled else original, not culled, row))
    else:
        for case in runs.continuation():
            if not selected(case):
                continue
            if case.case_id not in records:
                raise RuntimeError("Missing exchange continuation: "+case.case_id)
            tasks.append((case, records[case.case_id], False, None))
    if args.case_id and len(tasks) != len(args.case_id):
        raise RuntimeError("Unknown selected case")
    rows, windows = [], []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for i, (r, w) in enumerate(pool.map(_analyze_task, tasks), 1):
            rows.extend(r); windows.extend(w)
            print(i, len(tasks), r[0]["case_id"], flush=True)
    runs.OUTPUT.mkdir(parents=True, exist_ok=True)
    name = "survival" if args.stage == "planned" else "exchange_continuation"
    if args.case_id:
        name += "_selection"
    experiments.table(runs.OUTPUT/(name+".csv"), [experiments.clean(r) for r in rows])
    (runs.OUTPUT/(name+"_windows.json")).write_text(experiments.dumps(windows)+"\n")
    manifest = dict(source_sha256={str(path.relative_to(experiments.ROOT)):sha256(path.read_bytes()).hexdigest()
                                  for path in (Path(__file__), Path(branching.__file__))},
        rows=len(rows), profiles=len(tasks), stage=args.stage,
        classification_counts={k:sum(r["classification"] == k for r in rows) for k in ("robust_loss", "robust_persistence", "contingent")},
        needs_extension=[dict(case_id=r["case_id"], guild=r["guild"]) for r in rows if r["needs_extension"]],
        interpretation="Conditional per-guild recorded-environment diagnostics; not joint stochastic community endpoint probabilities")
    (runs.OUTPUT/(name+"_manifest.json")).write_text(experiments.dumps(manifest)+"\n")
    if args.stage == "exchange" and not args.case_id:
        exchange_figure(rows, runs.OUTPUT)


if __name__ == "__main__":
    main()
