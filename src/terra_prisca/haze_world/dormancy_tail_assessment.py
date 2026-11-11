"""Post-review macro-stationarity and resolved dormant-relaxation diagnostics.

Original trajectories, strict labels, endpoint comparisons and probabilities
remain untouched. A fixed root-bank forecast must explain the observed bank
variation before the additional relaxation class is assigned.
"""

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from scipy.linalg import expm
from scipy.optimize import least_squares

from . import dormancy as model
from . import dormancy_experiments as runner
from . import dormancy_starts
from . import turnover_assessment as endpoints
from . import turnover_survival as survival


ROOT = runner.e.ROOT
REVIEW = ROOT/"models/haze_world/review"
DESIGN = REVIEW/"dormancy-tail-classification-design-2026-11-11.md"
DIAGNOSTIC = REVIEW/"dormancy_endpoint_diagnostics.json"
STOCK_TOLERANCE = .001
TEMPERATURE_TOLERANCE_K = .01
TAIL_YEARS = 20000.


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def stock_floors(p, conversion):
    density = np.divide(np.exp(-conversion), p.weights,
                        out=np.full(p.n_patches, np.inf), where=p.weights > 0)
    return np.r_[np.array([[1., v, v, 1e-9, v, v] for v in density]).ravel(), .001], density


def scaled_derivatives(y, dy, p, density):
    values = np.zeros(p.state_size)
    loss = p.coupled.biology.loss_h*model.core.HOURS_PER_YEAR
    hydraulic = model.core.HENRY_30C_MOL_L_PA/(
        p.coupled.biology.exchange_mol_l_h_pa*model.core.HOURS_PER_YEAR)
    values[-1] = abs(dy[-1])*p.coupled.loss.lifetime_yr/max(y[-1], .001)
    for j in np.flatnonzero(p.weights > 0):
        values[6*j] = abs(dy[6*j])*hydraulic/max(y[6*j], 1.)
        values[6*j+3] = abs(dy[6*j+3])*p.coupled.acetate_lifetime_yr/max(y[6*j+3], 1e-9)
        for k in (1, 2, 4, 5):
            values[6*j+k] = abs(dy[6*j+k])/max(y[6*j+k], density[j])/loss
    return values


def macro_evidence(record, data, p):
    t, y = data["t"], data["y"]
    late = t >= t[-1]-TAIL_YEARS
    floor, density = stock_floors(p, data["metadata"]["global_log_cell_conversion"])
    sample = y[:, late]
    scale = np.maximum(np.mean(abs(sample), axis=1), floor)
    span = np.divide(np.ptp(sample, axis=1), scale,
                     out=np.zeros(p.state_size), where=scale > 0)
    active = np.flatnonzero(p.weights > 0)
    macro = np.r_[np.concatenate([6*j+np.array([0, 1, 2, 3]) for j in active]), p.state_size-1]
    failing = np.flatnonzero(span >= STOCK_TOLERANCE)
    dormant_only = all(k < p.state_size-1 and k % 6 in (4, 5) for k in failing)
    dy = model.rhs(y[:, -1], p)
    derivative = scaled_derivatives(y[:, -1], dy, p, density)
    total = sample[p.biomass_indices]+sample[p.dormant_indices]
    total_scale = np.maximum(np.mean(abs(total), axis=2), density[:, None])
    total_span = np.divide(np.ptp(total, axis=2), total_scale,
                           out=np.zeros((p.n_patches, 2)), where=total_scale > 0)
    total_derivative = np.divide(abs(dy[p.biomass_indices]+dy[p.dormant_indices]),
        np.maximum(y[p.biomass_indices, -1]+y[p.dormant_indices, -1], density[:, None]),
        out=np.zeros((p.n_patches, 2)), where=np.maximum(y[p.biomass_indices, -1]+y[p.dormant_indices, -1], density[:, None]) > 0)
    total_derivative /= p.coupled.biology.loss_h*model.core.HOURS_PER_YEAR
    occupied = (total >= density[:, None, None]*(1.-1e-10)) & (p.weights[:, None, None] > 0)
    occupancy_changes = int(np.count_nonzero(occupied[:, :, 1:] != occupied[:, :, :-1]))
    events = json.loads(str(data["extinction_events"]))
    late_culls = sum(event["time_yr"] >= t[-1]-TAIL_YEARS for event in events)
    thermal_span = float(np.max(np.ptp(data["temperatures_k"][active][:, late], axis=1)))
    tests = dict(dormant_only_failures=dormant_only,
        macro_stock_spans=bool(max(span[macro]) < STOCK_TOLERANCE),
        macro_terminal_derivatives=bool(max(derivative[macro]) < STOCK_TOLERANCE),
        total_guild_stock_spans=bool(max(total_span[active].ravel()) < STOCK_TOLERANCE),
        total_guild_terminal_derivatives=bool(max(total_derivative[active].ravel()) < STOCK_TOLERANCE),
        temperature_span=thermal_span < TEMPERATURE_TOLERANCE_K,
        minimum_horizon=bool(t[-1] >= 100000.),
        unchanged_occupancy=occupancy_changes == 0, no_late_culls=late_culls == 0)
    return dict(passed=all(tests.values()), tests=tests, failing_indices=failing.tolist(),
        maximum_macro_relative_span=float(max(span[macro])),
        maximum_macro_scaled_derivative=float(max(derivative[macro])),
        maximum_total_guild_relative_span=float(max(total_span[active].ravel())),
        maximum_total_guild_scaled_derivative=float(max(total_derivative[active].ravel())),
        temperature_span_k=thermal_span, occupancy_changes=occupancy_changes, late_culls=late_culls,
        late_start_yr=float(t[late][0]), late_end_yr=float(t[-1]))


def model_key(case):
    return tuple(case[k] for k in ("fraction", "epsilon", "configuration", "dispersal_yr",
                                   "loss_h", "switching_factor", "ramp"))


def mixed_root(seed, p):
    active = np.flatnonzero(p.weights > 0)
    n = len(active)
    if np.any(seed[p.biomass_indices[active]] <= 0) or np.any(seed[6*active+3] <= 0):
        raise ArithmeticError("Mixed-root seed lacks positive active stocks")
    values = np.r_[seed[6*active]/100., np.log(seed[p.biomass_indices[active]].ravel()/1e-3),
                   np.log(seed[6*active+3]/1e-3), seed[-1]/.2]
    supply = model.core.supply_h2(p.coupled)*model.core.HOURS_PER_YEAR
    loss = p.coupled.biology.loss_h*model.core.HOURS_PER_YEAR
    pressure_max = p.coupled.biology.atmosphere_pa+model.core.supply_h2(p.coupled)/p.coupled.biology.exchange_mol_l_h_pa

    def decode(z):
        y = np.zeros(p.state_size)
        y[6*active] = 100*z[:n]
        y[p.biomass_indices[active]] = 1e-3*np.exp(z[n:3*n]).reshape(n, 2)
        y[6*active+3] = 1e-3*np.exp(z[3*n:4*n])
        y[-1] = .2*z[-1]
        return dormancy_starts.dormant_balance(y, p)

    def equations(z):
        y = decode(z)
        dy = model.rhs(y, p, trial_extension=True)
        return np.r_[dy[6*active]*model.core.HENRY_30C_MOL_L_PA/supply,
            (dy[p.biomass_indices[active]]/(loss*y[p.biomass_indices[active]])).ravel(),
            dy[6*active+3]/(supply/4), dy[-1]/(model.core.inventory_to_ratio(p.coupled)*supply/4)]

    fit = least_squares(equations, values,
        bounds=(np.r_[np.zeros(n), np.full(3*n, -100.), 0.],
                np.r_[np.full(n, pressure_max/100.), np.full(3*n, 30.), 5.]),
        jac="3-point", x_scale="jac", ftol=1e-12, xtol=1e-12, gtol=1e-12, max_nfev=1000)
    y = decode(fit.x)
    residual = float(max(abs(equations(fit.x))))
    if residual > 1e-8 or "unsupported" in model.temperature_flags(y, p):
        raise ArithmeticError("Mixed root did not meet the existing preparation residual/domain criterion")
    return y, dict(kind="nearby_mixed_root", max_scaled_balance_residual=residual,
                   function_evaluations=fit.nfev, scope="One root from the late mean, not root completeness or a basin proof")


def root_comparison(y, root, p, conversion):
    floor, density = stock_floors(p, conversion)
    active = np.flatnonzero(p.weights > 0)
    macro = np.r_[np.concatenate([6*j+np.array([0, 1, 2, 3]) for j in active]), p.state_size-1]
    relative = abs(y-root)/np.maximum.reduce([abs(y), abs(root), floor])
    totals = [v[p.biomass_indices]+v[p.dormant_indices] for v in (y, root)]
    total_difference = abs(totals[0]-totals[1])/np.maximum.reduce([abs(totals[0]), abs(totals[1]), np.broadcast_to(density[:, None], totals[0].shape)])
    occupancy = [(value >= density[:, None]*(1.-1e-10)) & (p.weights[:, None] > 0) for value in totals]
    thermal = abs(float(model.core.temperature_k(y[-1], p.coupled.climate))-float(model.core.temperature_k(root[-1], p.coupled.climate)))
    same_occupancy = bool(np.array_equal(*occupancy))
    passed = bool(max(relative[macro]) < STOCK_TOLERANCE and max(total_difference[active].ravel()) < STOCK_TOLERANCE
                  and thermal < TEMPERATURE_TOLERANCE_K and same_occupancy)
    return dict(passed=passed, maximum_macro_stock_difference=float(max(relative[macro])),
        maximum_total_guild_difference=float(max(total_difference[active].ravel())),
        temperature_difference_k=thermal, same_local_occupancy=same_occupancy,
        maximum_full_stock_difference=float(max(relative)))


def select_root(record, data, p, records):
    present = [bool(record["summary"]["global_present_"+g]) for g in ("a", "m")]
    if all(present):
        late = data["t"] >= data["t"][-1]-TAIL_YEARS
        return mixed_root(np.mean(data["y"][:, late], axis=1), p)
    if not any(present):
        raise ArithmeticError("No present guild for a resident-bank comparison")
    guild = present.index(True)
    candidates = []
    key = model_key(record["protocol"]["case"])
    for other in records.values():
        if model_key(other["protocol"]["case"]) != key:
            continue
        resident = 1 if other["protocol"]["case"]["direction"] == "A_into_M" else 0
        if resident != guild:
            continue
        for candidate in other["start"]["qualifying"]:
            root = dormancy_starts.dormant_balance(np.asarray(candidate["y"]).copy(), p)
            distance = root_comparison(data["y"][:, -1], root, p, data["metadata"]["global_log_cell_conversion"])
            candidates.append((distance["maximum_macro_stock_difference"], root, other, candidate))
    if not candidates:
        raise ArithmeticError("No recorded conditional resident root at matching parameters")
    _, root, origin, certificate = min(candidates, key=lambda value: value[0])
    return root, dict(kind="recorded_conditional_resident_root", resident_guild=guild,
        origin_case=origin["protocol"]["case"]["case_id"], origin_fingerprint=origin["fingerprint"],
        conditional_stability=certificate["stability"], max_scaled_balance_residual=certificate["max_scaled_residual"],
        stationary_bank_recomputed=True,
        scope="Observed present-guild face only; an absent invader may still grow on reintroduction")


def bank_forecast(times, initial, matrix, source):
    """Affine linear bank prediction over the actual saved intervals."""
    times = np.asarray(times)
    n = len(initial)
    augmented = np.zeros((n+1, n+1))
    augmented[:n, :n], augmented[:n, n] = matrix, source
    result = np.empty((n, len(times)))
    result[:, 0] = initial
    kernels = {}
    for k, duration in enumerate(np.diff(times), 1):
        if duration <= 0:
            raise ValueError("Bank forecast times must increase")
        if duration not in kernels:
            kernel = expm(augmented*duration)
            if np.any(~np.isfinite(kernel)) or np.any(kernel < 0):
                raise ArithmeticError("Affine-bank exponential lost nonnegativity")
            kernels[duration] = kernel
        result[:, k] = (kernels[duration]@np.r_[result[:, k-1], 1.])[:n]
    return result


def fit_bank(observed, predicted, floor):
    error = np.max(abs(observed-predicted), axis=1)
    scale = np.maximum(np.mean(abs(observed), axis=1), floor)
    variation = np.ptp(observed, axis=1)
    normalized = np.divide(error, scale, out=np.zeros_like(error), where=scale > 0)
    range_error = np.divide(error, variation, out=np.full_like(error, np.inf), where=variation > 0)
    return normalized, range_error


def bank_evidence(data, root, p, failures):
    late = data["t"] >= data["t"][-1]-TAIL_YEARS
    times, values = data["t"][late], data["y"][:, late]
    conversion = data["metadata"]["global_log_cell_conversion"]
    _, density = stock_floors(p, conversion)
    active = np.flatnonzero(p.weights > 0)
    flux = model.fluxes(root, p)
    sampled = [model.fluxes(value, p) for value in values.T]
    rows = []
    for guild in range(2):
        matrix = -np.diag(flux["rho_yr"][active, guild]+flux["dormant_loss_yr"]+p.dispersal_yr)
        matrix += p.dispersal_yr*np.ones((len(active), 1))*p.weights[active][None, :]
        source = flux["sigma_yr"][active, guild]*root[p.biomass_indices[active, guild]]
        indices = p.dormant_indices[active, guild]
        observed = values[indices]
        predicted = bank_forecast(times, observed[:, 0], matrix, source)
        normalized, range_error = fit_bank(observed, predicted, density[active])
        sigma = np.array([f["sigma_yr"][active, guild] for f in sampled])
        entry = sigma*values[p.biomass_indices[active, guild]].T
        retained = data["log_active"][active, guild][:, late].T
        log_entry = np.log(sigma, out=np.full_like(sigma, -np.inf), where=sigma > 0)+retained
        sampled_source_free = bool(not np.any(np.isfinite(log_entry)))
        for j, index in enumerate(indices):
            failing = int(index) in failures
            passed = bool(normalized[j] <= STOCK_TOLERANCE and range_error[j] <= STOCK_TOLERANCE)
            rows.append(dict(index=int(index), patch=p.patch_names[active[j]], guild=("a", "m")[guild],
                originally_failing=failing, fit_passed=passed, normalized_prediction_error=float(normalized[j]),
                error_fraction_of_observed_range=float(range_error[j]) if np.isfinite(range_error[j]) else None,
                observed_min_gdw_l=float(min(observed[j])), observed_max_gdw_l=float(max(observed[j])),
                observed_final_gdw_l=float(observed[j, -1]), predicted_final_gdw_l=float(predicted[j, -1]),
                root_gdw_l=float(root[index]),
                maximum_world_cells=float(max(observed[j])*p.weights[active[j]]*np.exp(conversion)),
                root_world_cells=float(root[index]*p.weights[active[j]]*np.exp(conversion)),
                sampled_entry_source_free=sampled_source_free,
                sampled_retained_entry_source_present=bool(np.any(np.isfinite(log_entry[:, j]))),
                sampled_entry_source_range_gdw_l_yr=[float(min(entry[:, j])), float(max(entry[:, j]))],
                root_entry_source_gdw_l_yr=float(source[j]),
                bank_eigenvalues_yr=np.linalg.eigvals(matrix).real.tolist(),
                mechanism="sampled_source_free_linear_decay" if sampled_source_free and np.all(source == 0.) else "root_supported_linear_relaxation"))
    return dict(passed=all(row["fit_passed"] for row in rows if row["originally_failing"]), stocks=rows,
        scope="Frozen-root affine bank forecast at saved states; no between-sample proof, relative terminal-bank accuracy or global-attractor claim")


def compare_macro(a, b, da, db, pa):
    original = endpoints.compare(a, b, da, db, dormant=True)
    ya, yb = da["y"][:, -1], db["y"][:, -1]
    floor_a, density_a = stock_floors(pa, da["metadata"]["global_log_cell_conversion"])
    floor_b, density_b = stock_floors(pa, db["metadata"]["global_log_cell_conversion"])
    floor = np.maximum(floor_a, floor_b)
    active = np.flatnonzero(pa.weights > 0)
    indices = np.r_[np.concatenate([6*j+np.array([0, 1, 2, 3]) for j in active]), pa.state_size-1]
    relative = abs(ya-yb)/np.maximum.reduce([abs(ya), abs(yb), floor])
    totals = [v[pa.biomass_indices]+v[pa.dormant_indices] for v in (ya, yb)]
    density = np.maximum(density_a, density_b)
    delta = abs(totals[0]-totals[1])/np.maximum.reduce([abs(totals[0]), abs(totals[1]), np.broadcast_to(density[:, None], totals[0].shape)])
    same = bool(original["same_local_occupancy"] and original["same_global_occupancy"]
        and original["temperature_difference_k"] < TEMPERATURE_TOLERANCE_K
        and max(relative[indices]) < STOCK_TOLERANCE and max(delta[active].ravel()) < STOCK_TOLERANCE)
    return original|dict(same_macro_state=same, maximum_macro_stock_difference=float(max(relative[indices])),
                         maximum_total_guild_difference=float(max(delta[active].ravel())))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=runner.RAW)
    parser.add_argument("--output", type=Path, default=REVIEW/"dormancy-tail-assessment-2026-11-11.json")
    args = parser.parse_args()
    diagnostic = json.loads(DIAGNOSTIC.read_text())
    expected = {row["case_id"]: row for row in diagnostic["rows"] if row["classification"] == "dormant_stock_only_stationarity_failure"}
    all_records = survival.records(args.raw_dir, "census")
    records = {case.case_id: all_records[case.case_id] for case in runner.design()}
    selection = {item["case_id"]: item for item in diagnostic["selected_receipts"]}
    for key, record in records.items():
        if any(record[field] != selection[key][field] for field in ("fingerprint", "raw_file", "raw_sha256")):
            raise RuntimeError("Physical snapshot differs from the existing selected diagnostic")
    sources = {str(Path(module.__file__).relative_to(ROOT)): digest(module.__file__) for module in
               (model, runner, dormancy_starts, survival, endpoints)}
    own_hash, design_hash, diagnostic_hash = digest(__file__), digest(DESIGN), digest(DIAGNOSTIC)
    selector_hash = digest(args.raw_dir/"receipt_selection.json")
    if selector_hash != diagnostic["receipt_selection_sha256"]:
        raise RuntimeError("Changed receipt selector")
    rows, root_targets = {}, {}
    for key, record in records.items():
        if key not in expected:
            strict = record["summary"]["settling_status"] == "census_stationary"
            macro = None
            if strict:
                data = survival.load(record, args.raw_dir)
                p = runner.parameters(runner.Case(**record["protocol"]["case"]))
                macro = macro_evidence(record, data, p)
            rows[key] = dict(case_id=key, strict_status=record["summary"]["settling_status"],
                             additional_class="strict_stationary" if strict else "other_unsettled",
                             macro=macro, macro_stationary=bool(strict and macro["passed"]))
            continue
        if record["fingerprint"] != expected[key]["fingerprint"] or record["raw_sha256"] != expected[key]["raw_sha256"]:
            raise RuntimeError("Candidate snapshot differs from selected physical record")
        data = survival.load(record, args.raw_dir)
        p = runner.parameters(runner.Case(**record["protocol"]["case"]))
        row = dict(case_id=key, fingerprint=record["fingerprint"], raw_file=record["raw_file"], raw_sha256=record["raw_sha256"],
                   strict_status=record["summary"]["settling_status"], macro=macro_evidence(record, data, p))
        row["macro_stationary"] = row["macro"]["passed"]
        row["additional_class"] = "macro_stationary_bank_unresolved" if row["macro_stationary"] else "macro_unsettled"
        if row["macro_stationary"]:
            try:
                root, provenance = select_root(record, data, p, records)
                row["root"] = dict(y=root.tolist(), provenance=provenance,
                    comparison=root_comparison(data["y"][:, -1], root, p, data["metadata"]["global_log_cell_conversion"]))
                row["bank"] = bank_evidence(data, root, p, row["macro"]["failing_indices"])
                if row["root"]["comparison"]["passed"] and row["bank"]["passed"]:
                    row["additional_class"] = "settled_up_to_dormant_relaxation"
                    root_targets[key] = root
            except (ArithmeticError, ValueError, np.linalg.LinAlgError) as error:
                row["root_or_bank_error"] = str(error)
        rows[key] = row
        print(key, row["additional_class"], flush=True)
    pairs = []
    groups = {}
    for key, record in records.items():
        groups.setdefault(model_key(record["protocol"]["case"]), {})[record["protocol"]["case"]["direction"]] = record
    for pair in groups.values():
        a, b = pair["A_into_M"], pair["M_into_A"]
        ka, kb = (v["protocol"]["case"]["case_id"] for v in (a, b))
        da, db = (survival.load(v, args.raw_dir) for v in (a, b))
        p = runner.parameters(runner.Case(**a["protocol"]["case"]))
        comparison = compare_macro(a, b, da, db, p)
        both_macro = rows[ka]["macro_stationary"] and rows[kb]["macro_stationary"]
        item = dict(case_a_into_m=ka, case_m_into_a=kb, both_macro_stationary=both_macro,
            original_strict=bool(comparison["both_stationary"]), original_same_endpoint=bool(comparison["same_endpoint"]),
            same_observed_macro_state=bool(both_macro and comparison["same_macro_state"]),
            temperature_difference_k=comparison["temperature_difference_k"],
            same_local_occupancy=comparison["same_local_occupancy"],
            same_global_occupancy=comparison["same_global_occupancy"],
            maximum_macro_stock_difference=comparison["maximum_macro_stock_difference"],
            maximum_total_guild_difference=comparison["maximum_total_guild_difference"],
            full_limiting_root_comparison=None)
        if both_macro and ka in root_targets and kb in root_targets:
            ra, rb = root_targets[ka], root_targets[kb]
            floor, _ = stock_floors(p, min(da["metadata"]["global_log_cell_conversion"], db["metadata"]["global_log_cell_conversion"]))
            difference = abs(ra-rb)/np.maximum.reduce([abs(ra), abs(rb), floor])
            thermal = abs(float(model.core.temperature_k(ra[-1], p.coupled.climate))-float(model.core.temperature_k(rb[-1], p.coupled.climate)))
            item["full_limiting_root_comparison"] = dict(maximum_stock_difference=float(max(difference)),
                temperature_difference_k=thermal,
                same=bool(max(difference) < STOCK_TOLERANCE and comparison["same_local_occupancy"] and thermal < TEMPERATURE_TOLERANCE_K))
        pairs.append(item)
    result = dict(schema="dormancy_tail_assessment_v1", amendment="Post-review descriptive classification; original labels and probability evidence retained",
        criteria=dict(relative_stock_tolerance=STOCK_TOLERANCE, temperature_tolerance_k=TEMPERATURE_TOLERANCE_K,
                      window_years=TAIL_YEARS, bank_error_fraction_of_observed_range=STOCK_TOLERANCE),
        counts=dict(Counter(row["additional_class"] for row in rows.values())),
        pair_counts=dict(total=len(pairs), strict_both_stationary=sum(v["original_strict"] for v in pairs),
            strict_same_endpoint=sum(v["original_same_endpoint"] for v in pairs),
            both_macro_stationary=sum(v["both_macro_stationary"] for v in pairs),
            same_observed_macro_state=sum(v["same_observed_macro_state"] for v in pairs)),
        source_sha256=sources, assessment_source_sha256=own_hash,
        design_sha256=design_hash, diagnostic_sha256=diagnostic_hash,
        receipt_selection_sha256=selector_hash, selected_receipts=diagnostic["selected_receipts"],
        rows=list(rows.values()), pairs=pairs,
        scope="Finite-record macro-state agreement and resolved bank forecasts; no full-state equality for unresolved banks, asymptotic-attractor or joint demographic-persistence claim")
    for name, before in sources.items():
        if digest(ROOT/name) != before:
            raise RuntimeError("Analysis dependency changed during assessment")
    if (digest(__file__), digest(DESIGN), digest(DIAGNOSTIC), digest(args.raw_dir/"receipt_selection.json")) != (own_hash, design_hash, diagnostic_hash, selector_hash):
        raise RuntimeError("Assessment source or pinned input changed during assessment")
    args.output.write_text(runner.e.dumps(result)+"\n")
    print(runner.e.dumps(dict(counts=result["counts"], pairs=result["pair_counts"])))


if __name__ == "__main__":
    main()
