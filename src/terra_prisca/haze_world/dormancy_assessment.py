"""Receipt-driven KD1--KD5 assessment after the T1 basin gate has closed."""

import argparse
from collections import Counter
import csv
from dataclasses import asdict
import gzip
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from . import buffered_experiments as e
from . import dormancy_experiments as runner
from . import turnover_assessment as endpoints
from . import turnover_survival as survival


PREDICTED_EPSILON = {("A_into_M", 0.): .006, ("A_into_M", .5): .0025,
                     ("M_into_A", 0.): .00046, ("M_into_A", .5): .00082}
GUARDED_PREFIX_SOURCES = frozenset(("src/terra_prisca/haze_world/dormancy_prefixes.py",
                                  "src/terra_prisca/haze_world/dormancy_trial_integration.py"))
JACOBIAN_SOURCES = frozenset(("src/terra_prisca/haze_world/dormancy_jacobian_experiments.py",
                              "src/terra_prisca/haze_world/dormancy_jacobian_integration.py",
                              "src/terra_prisca/haze_world/dormancy_trial_integration.py"))
PROGRESS_SOURCES = frozenset(("src/terra_prisca/haze_world/dormancy_progress_experiments.py",
                              "src/terra_prisca/haze_world/dormancy_progress_integration.py",
                              "src/terra_prisca/haze_world/dormancy_jacobian_integration.py",
                              "src/terra_prisca/haze_world/dormancy_trial_integration.py"))
CHEMICAL_SOURCES = frozenset(("src/terra_prisca/haze_world/dormancy_chemical_experiments.py",
                              "src/terra_prisca/haze_world/dormancy_chemical_integration.py",
                              "src/terra_prisca/haze_world/dormancy_progress_integration.py",
                              "src/terra_prisca/haze_world/dormancy_jacobian_integration.py",
                              "src/terra_prisca/haze_world/dormancy_trial_integration.py"))


def require_gate(path):
    if not path.exists():
        raise RuntimeError("T1 basin gate is absent; do not interpret T3")
    gate = json.loads(path.read_text())
    if gate.get("gate_passed") is not True:
        raise RuntimeError("T1 basin gate remains open; do not interpret T3")
    if not gate.get("source_sha256"):
        raise RuntimeError("T1 gate lacks its frozen source graph")
    for name, digest in gate["source_sha256"].items():
        if sha256((e.ROOT/name).read_bytes()).hexdigest() != digest:
            raise RuntimeError("T1 gate source differs: "+name)
    return dict(file=str(path.relative_to(e.ROOT)), sha256=sha256(path.read_bytes()).hexdigest(),
                gate_passed=True, qualification=gate)


def crossing_brackets(points):
    """Retain every resolved P=1/2 crossing without assuming monotonicity."""
    usable = sorted([p for p in points if p["eligible"]], key=lambda p: p["epsilon"])
    if len({p["epsilon"] for p in usable}) != len(usable):
        raise ValueError("Duplicate epsilon measurements in one response curve")
    target = np.log(.5)
    brackets = []
    for point in usable:
        if point["log_probability"] == target:
            brackets.append(dict(low=point["epsilon"], high=point["epsilon"],
                                 orientation="exact_sample", cases=[point["case_id"]]))
    for low, high in zip(usable, usable[1:]):
        a, b = low["log_probability"]-target, high["log_probability"]-target
        if a < 0 < b or b < 0 < a:
            brackets.append(dict(low=low["epsilon"], high=high["epsilon"],
                orientation="survival_to_loss" if a > 0 else "loss_to_survival",
                evidence="one_sided_terminal_loss" if any(p.get("probability_bound") == "finite_horizon_upper" for p in (low, high)) else "resolved_first_bottlenecks",
                cases=[low["case_id"], high["case_id"]]))
    constrained = sorted([p for p in points if p.get("macroscopic_protection")
                          or p["eligible"] and p["log_probability"] < target], key=lambda p: p["epsilon"])
    protection_intervals = []
    for low, high in zip(constrained, constrained[1:]):
        if bool(low.get("macroscopic_protection")) != bool(high.get("macroscopic_protection")):
            protection_intervals.append(dict(low=low["epsilon"], high=high["epsilon"],
                orientation="protection_to_loss" if low.get("macroscopic_protection") else "loss_to_protection",
                cases=[low["case_id"], high["case_id"]],
                evidence="Macroscopic census protection versus rare loss; not an exact P=1/2 bracket"))
    reversed_ = any(b["orientation"] == "loss_to_survival" for b in brackets)
    return dict(points=points, brackets=brackets, protection_loss_intervals=protection_intervals, reversed_crossing=reversed_,
                unique_decreasing_crossing=len(brackets) == 1 and not reversed_)


def prediction_band(curve, prediction):
    bounds = (prediction, 3*prediction)
    crossings = curve["brackets"]
    if not curve["unique_decreasing_crossing"]:
        status = "nonmonotone_or_multiple" if len(crossings) > 1 or curve["reversed_crossing"] else "unresolved"
    elif bounds[0] <= crossings[0]["low"] and crossings[0]["high"] <= bounds[1]:
        status = "supported_bracket"
    elif crossings[0]["high"] < bounds[0] or crossings[0]["low"] > bounds[1]:
        status = "refuted_bracket"
    else:
        status = "needs_refinement"
    measured = {p["epsilon"] for p in curve["points"]}
    requested = [v for v in bounds if not any(np.isclose(v, x, rtol=1e-10, atol=0.) for x in measured)]
    return dict(predicted_epsilon=prediction, predicted_band=list(bounds), status=status,
                suggested_epsilon=requested if status in ("unresolved", "needs_refinement") else [])


def speed_comparison(fast, slow):
    intervals = [dict(low=b["low"]/a["high"], high=b["high"]/a["low"])
                 for a in fast["brackets"] for b in slow["brackets"]]
    unique = fast["unique_decreasing_crossing"] and slow["unique_decreasing_crossing"]
    if not unique:
        status = "unresolved_or_multiple"
    elif all(1/3 <= v["low"] and v["high"] <= 3 for v in intervals):
        status = "supported_bracket"
    elif any(v["high"] < 1/3 or v["low"] > 3 for v in intervals):
        status = "refuted_bracket"
    else:
        status = "needs_refinement"
    return dict(status=status, slow_over_fast_intervals=intervals)


def probability_points(records, rows, fraction, direction, switching_factor):
    points = []
    resident = "m" if direction == "A_into_M" else "a"
    for case_id, record in records.items():
        case = record["protocol"]["case"]
        if not (case["configuration"] == "none" and case["loss_h"] == .001
                and case["fraction"] == fraction and case["direction"] == direction
                and case["switching_factor"] == switching_factor and case["ramp"] == "cubic"):
            continue
        row = rows[(case_id, resident)]
        conditional = bool(row.get("downstream_of_other_guild_subcell_bound")
                           or row.get("overlaps_other_guild_likely_loss_window"))
        log_probability = survival.bottleneck._log_probability(row["log_lambda"])
        terminal_loss_bound = bool(row["terminal_window"] and log_probability < np.log(.5))
        eligible = bool(row["rare_window"] and (not row["terminal_window"] or terminal_loss_bound))
        summary = record.get("summary", {})
        minimum = summary.get("global_pre_extinction_min_log_cells_"+resident)
        refinement = record.get("assessment_role") == "first_window_refinement_only"
        protected = bool(not refinement and minimum is not None and minimum > np.log(1e16)
                         and not summary.get("global_pre_extinction_min_zero_"+resident, True)
                         and summary.get("global_present_"+resident, False))
        points.append(dict(case_id=case_id, epsilon=case["epsilon"],
            evidence_scope=record.get("assessment_role", "planned_100k"),
            refinement_parent_case_id=record.get("refinement_parent_case_id"),
            log_probability=log_probability, probability=row["survival_probability"],
            eligible=eligible, terminal=bool(row["terminal_window"]),
            probability_bound="finite_horizon_upper" if row["terminal_window"] else "resolved_first_bottleneck" if row["rare_window"] else "nonrare_conditional_diagnostic",
            macroscopic_protection=protected, census_horizon_yr=case.get("years"),
            window_status=row["window_status"], conditional_on_other_guild=conditional,
            classification=row["classification"], minimum_time_yr=row["minimum_time_yr"],
            end_yr=row["end_yr"], log_min_cells=row["log_min_cells"]))
    return sorted(points, key=lambda p: p["epsilon"])


def project_profile(profile):
    y = profile["y"]
    n = (y.shape[0]-1)//6
    local = y[:-1].reshape(n, 6, y.shape[1])
    projected = np.stack((local[:, 0], local[:, 1]+local[:, 4],
                          local[:, 2]+local[:, 5], local[:, 3]), axis=1)
    return dict(y=np.vstack((projected.reshape(4*n, -1), y[-1:])), metadata=profile["metadata"])


def _numerical_protocol(protocol, physical, root):
    sources = protocol["source_sha256"]
    if not physical or any(sources.get(name) != digest for name, digest in physical.items()):
        raise RuntimeError("Probability physical source graph differs from native freeze")
    extras = set(sources)-set(physical)
    if extras:
        if extras == GUARDED_PREFIX_SOURCES and protocol.get("solver") == "nonfinite_stage_trial_rejection":
            variant = "guarded"
        elif extras == JACOBIAN_SOURCES and protocol.get("solver") == "analytic_dormancy_switching_jacobian":
            variant = "analytic_jacobian"
        elif extras == PROGRESS_SOURCES and protocol.get("solver") == "analytic_dormancy_jacobian_progress_restart":
            variant = "analytic_jacobian_progress_restart"
        elif extras == CHEMICAL_SOURCES and protocol.get("solver") == "analytic_dormancy_chemical_jacobian":
            variant = "analytic_chemical_jacobian"
        else:
            raise RuntimeError("Unapproved probability source superset or solver protocol")
        if (protocol.get("mode") not in ("census", "uncensored")
                or not protocol.get("architecture") or not protocol.get("operating_system")):
            raise RuntimeError("Unapproved probability source superset or solver protocol")
    else:
        if protocol.get("solver") is not None or protocol.get("mode") != "census":
            raise RuntimeError("An uncensored probability profile requires the declared guarded source superset")
        variant = "native"
    for name, digest in sources.items():
        path = root/name
        if not path.is_file() or sha256(path.read_bytes()).hexdigest() != digest:
            raise RuntimeError("Probability source differs from current file: "+name)
    process = protocol["census"]
    if protocol["mode"] == "census":
        if process["minimum_cells"] != 1. or process["census_yr"] != 10.:
            raise RuntimeError("Probability census must retain its native one-cell ten-year process")
    elif process["minimum_cells"] != 0. or process["census_yr"] != 1.:
        raise RuntimeError("Probability prefix must be annual and uncensored")
    return variant


def validate_probability_protocol(receipt, census, root=None):
    """Compare native physics after validating each numerical declaration."""
    root = e.ROOT if root is None else Path(root)
    prefix, reference = receipt["protocol"], census["protocol"]
    if reference.get("mode") != "census":
        raise RuntimeError("The selected probability baseline must be a census")
    physical = runner.sources()
    _numerical_protocol(reference, physical, root)
    variant = _numerical_protocol(prefix, physical, root)
    if prefix["parameters"] != reference["parameters"]:
        raise RuntimeError("Probability physical parameters differ from census")
    excluded = ("years", "max_step_yr", "rtol")
    if {k: v for k, v in prefix["case"].items() if k not in excluded} != {
            k: v for k, v in reference["case"].items() if k not in excluded}:
        raise RuntimeError("Probability scientific case differs from census")
    for name in ("cell_mass_gdw", "surface_cm2"):
        if prefix["census"][name] != reference["census"][name]:
            raise RuntimeError("Probability cell-count convention differs from census")
    if prefix.get("mode") == "census":
        if receipt["fingerprint"] != census["fingerprint"]:
            raise RuntimeError("Reused probability census is not the selected receipt")
        if sum(v for k, v in receipt["summary"].items() if k.startswith("culls_")):
            raise RuntimeError("Only an unculled census can supply probability evidence")
        if prefix["census"] != reference["census"]:
            raise RuntimeError("Reused census convention differs")
    return variant+"_"+prefix["mode"]+"_unchanged_physics" if variant != "native" else "exact_source_graph"


def validate_selection_manifest(manifest, raw):
    path = raw/"receipt_selection.json"
    digest = sha256(path.read_bytes()).hexdigest() if path.exists() else None
    if manifest.get("receipt_selection_sha256") != digest:
        raise RuntimeError("Assessment receipt selection differs from the current plan")
    return digest


def assessment_records(all_records):
    expected = {case.case_id: case for case in runner.design()}
    planned, refinements = {}, {}
    for key, case in expected.items():
        record = all_records.get(key)
        if (record is None or record["execution_status"] != "complete"
                or record["protocol"]["case"]["years"] < case.years
                or record["summary"].get("terminal_time_yr", 0.) < case.years):
            raise RuntimeError("Missing full planned T3 horizon: "+key)
        actual = record["protocol"]["case"]
        if any(actual[k] != v for k, v in asdict(case).items() if k not in ("years", "max_step_yr", "rtol")):
            raise RuntimeError("Planned T3 protocol differs: "+key)
        planned[key] = record|dict(assessment_role="planned_100k")
    for key, record in all_records.items():
        if key in expected or "_eps" not in key:
            continue
        parent, _ = key.split("_eps", 1)
        case = record["protocol"]["case"]
        if parent not in expected or key != case["case_id"] or key != f"{parent}_eps{case['epsilon']:g}":
            raise RuntimeError("Refinement lacks a canonical planned parent: "+key)
        base = expected[parent]
        if base.configuration != "none" or base.loss_h != .001 or base.group not in ("main", "slow"):
            raise RuntimeError("Refinement parent is outside the KD3/KD4 design: "+key)
        excluded = ("case_id", "epsilon", "years", "max_step_yr", "rtol")
        if any(case[k] != v for k, v in asdict(base).items() if k not in excluded):
            raise RuntimeError("Refinement scientific design differs from parent: "+key)
        if (not np.isfinite(case["epsilon"]) or case["epsilon"] <= 0 or case["years"] <= 0
                or record["execution_status"] != "complete" or record["protocol"]["mode"] != "census"
                or record["summary"].get("terminal_time_yr") != case["years"]):
            raise RuntimeError("Incomplete refinement census: "+key)
        if e.dumps(record["protocol"]["parameters"]) != e.dumps(asdict(runner.parameters(runner.Case(**case)))):
            raise RuntimeError("Refinement physical parameters differ from its case: "+key)
        refinements[key] = record|dict(assessment_role="first_window_refinement_only", refinement_parent_case_id=parent)
    return planned, refinements


def validate_refinement_window(row, receipt, census, raw):
    if receipt["protocol"]["mode"] != "uncensored":
        raise RuntimeError("A first-window refinement requires its annual uncensored prefix")
    horizon = census["protocol"]["case"]["years"]
    if horizon >= 100000.:
        return "full_horizon_refinement_first_window_evidence"
    prefix_horizon = receipt["protocol"]["case"]["years"]
    if prefix_horizon != horizon:
        raise RuntimeError("Short refinement census and prefix horizons differ")
    for record in (receipt, census):
        data = survival.load(record, raw)
        if data["t"][-1] != horizon:
            raise RuntimeError("Short refinement actual horizon differs from its declaration")
    if (not row["rare_window"] or row["terminal_window"] or row["window_status"] != "first_minimum_linear"
            or not 0. <= row["start_yr"] < row["minimum_time_yr"] < row["end_yr"] < horizon):
        raise RuntimeError("Short refinement lacks a closed first rare resident window")
    return "matching_short_horizons_closed_first_resident_window"


def probability_rows(path, records, raw, uncensored_records):
    rows = json.loads(path.read_text())
    selected = {}
    for row in rows:
        case_id = row["case_id"]
        if case_id not in records:
            continue
        if row.get("census_fingerprint") != records[case_id]["fingerprint"]:
            raise RuntimeError("First-window census baseline differs from selected receipt: "+case_id)
        if row.get("ramp", "cubic") != "cubic":
            raise RuntimeError("Mixed switching ramps in T3 survival output")
        payload = raw/row["source_raw_file"]
        if not payload.exists() or sha256(payload.read_bytes()).hexdigest() != row["source_raw_sha256"]:
            raise RuntimeError("Changed first-window source profile: "+case_id)
        receipt = json.loads(payload.with_suffix(".receipt.json").read_text())
        if (receipt["execution_status"] != "complete" or receipt["raw_sha256"] != row["source_raw_sha256"]
                or sha256(e.dumps(receipt["protocol"]).encode()).hexdigest() != receipt["fingerprint"]):
            raise RuntimeError("First-window profile does not match the T3 freeze: "+case_id)
        if receipt["protocol"]["mode"] == "uncensored":
            if receipt["fingerprint"] != uncensored_records.get(case_id, {}).get("fingerprint"):
                raise RuntimeError("First-window uncensored profile is not the selected receipt: "+case_id)
        contract = validate_probability_protocol(receipt, records[case_id])
        case = records[case_id]["protocol"]["case"]
        for name in ("fraction", "epsilon", "configuration", "dispersal_yr", "direction",
                     "loss_h", "switching_factor", "ramp"):
            if row[name] != case[name] or receipt["protocol"]["case"][name] != case[name]:
                raise RuntimeError("First-window protocol differs: "+case_id+"/"+name)
        refinement_contract = None
        if records[case_id].get("assessment_role") == "first_window_refinement_only":
            resident = "m" if case["direction"] == "A_into_M" else "a"
            if row["guild"] == resident:
                refinement_contract = validate_refinement_window(row, receipt, records[case_id], raw)
        key = (case_id, row["guild"])
        if key in selected:
            raise RuntimeError("Duplicate first-window evidence: "+str(key))
        selected[key] = row|dict(numerical_profile_contract=contract,
                                 refinement_horizon_contract=refinement_contract,
                                 scoring_profile_source_sha256=receipt["protocol"]["source_sha256"])
    missing = [(c, g) for c in records for g in e.GUILDS if (c, g) not in selected]
    if missing:
        raise RuntimeError("Missing first-window evidence: "+str(missing[:8]))
    return selected


def first_minimum(row, raw):
    """Use a dense global minimum only when it belongs to this first window."""
    value = row["log_min_cells"]
    time = row["minimum_time_yr"]
    source = "sampled_first_minimum"
    data = survival.load(dict(raw_file=row["source_raw_file"], raw_sha256=row["source_raw_sha256"]), raw)
    guild = 0 if row["guild"] == "a" else 1
    dense_time = float(data["min_times"][guild])
    dense_value = float(data["min_log_biomass"][guild]+data["metadata"]["global_log_cell_conversion"])
    if row["start_yr"] <= dense_time <= row["end_yr"] and dense_value < value:
        value, time, source = dense_value, dense_time, "dense_global_minimum_in_first_window"
    return dict(log_min_cells=float(value), log10_min_cells=float(value/np.log(10.)),
                minimum_time_yr=float(time), minimum_source=source)


def reference_records(path, raw):
    with path.open() as stream:
        selected = list(csv.DictReader(stream))
    result = []
    for row in selected:
        if float(row["fraction"]) not in (0., .5):
            continue
        file = raw/row["raw_file"]
        if sha256(file.read_bytes()).hexdigest() != row["selected_raw_sha256"]:
            raise RuntimeError("Changed frozen reference payload")
        receipt = json.loads(file.with_name(file.name.replace(".json.gz", ".receipt.json")).read_text())
        if (receipt["execution_status"] != "complete" or receipt["raw_sha256"] != row["selected_raw_sha256"]
                or sha256(e.dumps(receipt["protocol"]).encode()).hexdigest() != receipt["fingerprint"]):
            raise RuntimeError("Invalid frozen reference receipt")
        result.append(receipt)
    return result


def reference_comparisons(records, raw, reference_table, reference_raw):
    reference = reference_records(reference_table, reference_raw)
    comparisons = []
    for case_id, record in records.items():
        case = record["protocol"]["case"]
        if case["loss_h"] != .001 or case["switching_factor"] != 10:
            continue
        matches = [r for r in reference if all(r["protocol"]["case"][k] == case[k]
                   for k in ("fraction", "configuration", "direction"))
                   and (case["configuration"] == "none" or r["protocol"]["case"]["dispersal_yr"] == case["dispersal_yr"])]
        if not matches:
            raise RuntimeError("Missing matching frozen reference: "+case_id)
        baseline = min(matches, key=lambda r: r["protocol"]["case"]["dispersal_yr"])
        culls = sum(v for k, v in baseline["summary"].items() if k.startswith("culls_"))
        if culls:
            continue
        with gzip.open(reference_raw/baseline["raw_file"], "rt") as stream:
            old = json.load(stream)["result"]
        old_profile = dict(y=np.asarray(old["y"]), metadata=old["metadata"])
        new = survival.load(record, raw)
        projected = dict(protocol=dict(parameters=record["protocol"]["parameters"]["base"]),
                         summary=record["summary"]|dict(global_temperature_k=record["summary"]["temperature_k"]))
        result = endpoints.compare(projected, baseline, project_profile(new), old_profile)
        p = runner.parameters(runner.Case(**case))
        final = new["y"][:, -1]
        active = p.weights@final[p.biomass_indices]
        dormant = p.weights@final[p.dormant_indices]
        comparisons.append(dict(case_id=case_id, reference_case_id=baseline["protocol"]["case"]["case_id"],
            reference_raw_file=baseline["raw_file"], reference_raw_sha256=baseline["raw_sha256"],
            dormancy_horizon_yr=case["years"], reference_horizon_yr=baseline["protocol"]["case"]["years"],
            dormancy_terminal_time_yr=float(new["t"][-1]), reference_terminal_time_yr=float(old["t"][-1]),
            dormant_fraction_a=float(dormant[0]/(active[0]+dormant[0])) if active[0]+dormant[0] else 0.,
            dormant_fraction_m=float(dormant[1]/(active[1]+dormant[1])) if active[1]+dormant[1] else 0.,
            **result))
    return comparisons


def kd1_endpoint_clauses(comparisons):
    evidence = []
    horizons = ("dormancy_horizon_yr", "reference_horizon_yr", "dormancy_terminal_time_yr", "reference_terminal_time_yr")
    for row in comparisons:
        literal = all(row.get(name) == 100000. for name in horizons)
        same_state = bool(row["same_global_occupancy"] and row["same_local_occupancy"]
                          and row["temperature_difference_k"] < .01
                          and row["maximum_relative_stock_difference"] < .001)
        evidence.append(row|dict(literal_100k_comparison=literal, same_finite_state=same_state,
                                  literal_100k_agreement=same_state if literal else None))
    literal = [row for row in evidence if row["literal_100k_comparison"]]
    stationary = [row for row in evidence if row["both_stationary"]]
    if any(not row["same_finite_state"] for row in literal):
        finite_status = "refuted"
    elif evidence and len(literal) == len(evidence):
        finite_status = "supported_verified_100k_comparisons"
    else:
        finite_status = "unresolved"
    if any(not row["same_endpoint"] for row in stationary):
        stationary_status = "refuted"
    elif evidence and len(stationary) == len(evidence):
        stationary_status = "supported_selected_stationary_comparisons"
    else:
        stationary_status = "unresolved"
    return dict(no_reference_removal_endpoint_comparisons=evidence,
                literal_100k_clause_status=finite_status, literal_100k_verified_comparisons=len(literal),
                asymptotic_endpoint_clause_status=stationary_status, stationary_endpoint_comparisons=len(stationary),
                comparison_scope="Literal finite-time agreement uses both declared and actual 100kyr horizons, common chemical/total-guild stocks, occupancy and temperature; stationarity is tested separately")


def kd5_case(record, raw):
    case, summary = record["protocol"]["case"], record["summary"]
    stationary = summary["settling_status"] == "census_stationary"
    row = dict(case_id=case["case_id"], direction=case["direction"], epsilon=case["epsilon"],
               stationary=stationary, endpoint=summary["endpoint_class"],
               methanogen_invasion_stays_acetogen=None)
    if case["direction"] != "M_into_A":
        return row
    data = survival.load(record, raw)
    p = runner.parameters(runner.Case(**case))
    active = p.weights > 0
    stages = np.stack((data["log_active"][active, 1], data["log_dormant"][active, 1]))
    indices = np.r_[p.biomass_indices[active, 1], p.dormant_indices[active, 1]]
    absent = (np.all(np.isneginf(stages), axis=(0, 1))
              & np.all(np.isneginf(data["log_biomass"][active, 1]), axis=0)
              & np.all(data["y"][indices] == 0., axis=0))
    missing = np.flatnonzero(absent)
    first = int(missing[0]) if missing.size else None
    removal_time = float(data["t"][first]) if first is not None else None
    events = json.loads(str(data["extinction_events"]))
    removal_logged = any(ev["guild"] == "methanogen" and ev["patch"] in np.asarray(p.patch_names)[active]
                         and ev["time_yr"] == removal_time for ev in events)
    census = record["protocol"]["census"]
    complete = (record["execution_status"] == "complete" and record["protocol"]["mode"] == "census"
                and census["minimum_cells"] == 1. and case["years"] >= 100000.
                and data["t"][-1] == case["years"])
    specified = (case["group"] == "bistable" and case["loss_h"] == .002 and case["fraction"] == 0.
                 and case["configuration"] == "none" and case["dispersal_yr"] == 0.)
    closed = data["metadata"].get("external_immigration") == "none"
    initial_dose = bool(np.any(np.isfinite(stages[:, :, 0])))
    retained_absence = bool(first is not None and np.all(absent[first:]))
    reversed_absence = bool(closed and first is not None and not retained_absence)
    absorbing = bool(complete and specified and closed and initial_dose and removal_logged and retained_absence)
    bulk = p.patch_names.index("bulk")
    log_cells = float(np.logaddexp(data["log_active"][bulk, 0, -1], data["log_dormant"][bulk, 0, -1])
                      + data["metadata"]["global_log_cell_conversion"]+np.log(p.weights[bulk]))
    acetogen_bulk = bool(log_cells >= -1e-10)
    evidence = dict(protocol_complete=bool(complete), specified_bistable_parameters=bool(specified),
        no_external_immigration=closed, initial_methanogen_dose_present=initial_dose,
        global_methanogen_removal_yr=removal_time, removal_event_at_global_loss=removal_logged,
        both_stages_absent_after_global_loss=retained_absence,
        closed_absence_reversed=reversed_absence,
        verified_absorbing_methanogen_exclusion=absorbing,
        observed_final_bulk_acetogen_present=acetogen_bulk, observed_final_bulk_acetogen_log_cells=log_cells,
        scope="Exact census removal of both methanogen stages everywhere is absorbing in the closed model. Acetogen occupancy is observed at the recorded horizon; neither eternal acetogen persistence nor continuous-attractor stability is inferred.")
    row["finite_dose_exclusion_evidence"] = evidence
    if absorbing and acetogen_bulk:
        row["methanogen_invasion_stays_acetogen"] = True
    elif complete and specified and closed and not reversed_absence and stationary and summary["endpoint_class"] != "acetogen_only":
        row["methanogen_invasion_stays_acetogen"] = False
    return row


def kd5_clauses(cases):
    required = {case.case_id for case in runner.design() if case.group == "bistable" and case.direction == "M_into_A"}
    selected = [row for row in cases if row["direction"] == "M_into_A"]
    covered = required <= {row["case_id"] for row in selected}
    if any(row["methanogen_invasion_stays_acetogen"] is False for row in selected):
        finite = "refuted_finite_dose"
    elif covered and all(row["methanogen_invasion_stays_acetogen"] is True for row in selected):
        finite = "supported_finite_dose_exclusion"
    else:
        finite = "unresolved"
    stationary = [row for row in selected if row["stationary"]]
    if any(row["endpoint"] != "acetogen_only" for row in stationary):
        settled = "refuted_stationary_endpoint"
    elif covered and len(stationary) == len(selected):
        settled = "supported_tested_stationary_endpoints"
    else:
        settled = "unresolved"
    return dict(status=finite, stationary_endpoint_clause_status=settled,
                required_methanogen_invasion_cases=sorted(required))


def assess(records, rows, pairs, raw, reference_comparison):
    curves = []
    for fraction in (0., .5):
        for direction in ("A_into_M", "M_into_A"):
            for factor in (10., 1.):
                curve = crossing_brackets(probability_points(records, rows, fraction, direction, factor))
                curve.update(fraction=fraction, direction=direction, switching_factor=factor,
                             displaced_guild="m" if direction == "A_into_M" else "a")
                if factor == 10:
                    curve["prediction"] = prediction_band(curve, PREDICTED_EPSILON[(direction, fraction)])
                curves.append(curve)
    speed = []
    for fraction in (0., .5):
        for direction in ("A_into_M", "M_into_A"):
            selected = {c["switching_factor"]: c for c in curves
                        if c["fraction"] == fraction and c["direction"] == direction}
            speed.append(dict(fraction=fraction, direction=direction,
                              **speed_comparison(selected[10.], selected[1.])))
    overshoot = []
    bistable = []
    for case_id, record in records.items():
        case = record["protocol"]["case"]
        if (case["group"] == "main" and case["fraction"] == 0. and case["configuration"] == "warm"
                and case["dispersal_yr"] == 1e-9 and case["direction"] == "A_into_M"):
            row = rows[(case_id, "a")]
            minimum = first_minimum(row, raw)
            overshoot.append(dict(case_id=case_id, epsilon=case["epsilon"], **minimum,
                threshold_1e13_pass=bool(minimum["log_min_cells"] > np.log(1e13)),
                first_window_class=row["classification"], rare_window=row["rare_window"],
                robust_persistence=row["classification"] == "robust_persistence",
                conditional_on_other_guild=bool(row.get("downstream_of_other_guild_subcell_bound")
                                              or row.get("overlaps_other_guild_likely_loss_window"))))
        if case["group"] == "bistable":
            bistable.append(kd5_case(record, raw))
    kd2 = "refuted" if any(not r["threshold_1e13_pass"] for r in overshoot) else "supported_grid" if len(overshoot) >= 7 and all(r["robust_persistence"] for r in overshoot) else "unresolved"
    return dict(KD1=dict(status="refuted_as_stated_for_spatial_equilibria",
            well_mixed_stationary_locations="Preserved analytically for epsilon>0; zero dormant resident bank at g=L",
            spatial_stationary_claim="Refuted by the source-sink counterexample in the design review; local growth can sustain dormancy",
            **kd1_endpoint_clauses(reference_comparison)),
        KD2=dict(status=kd2, overshoot_cases=overshoot),
        KD3=dict(curves=curves, prediction_scope="Measured first-window P=1/2 brackets; no monotonicity or lower-bound theorem assumed"),
        KD4=dict(comparisons=speed), KD5=dict(**kd5_clauses(bistable), finite_dose_cases=bistable,
            scope="Specified active methanogen doses with zero dormant invader. Absorbing finite-dose exclusion is assessed separately from stationary endpoints; neither proves continuous bistability or the prediction for untested epsilon."),
        opposite_invasion_pairs=pairs,
        stationary_counts=dict(Counter(r["summary"]["settling_status"] for r in records.values()
                                       if r.get("assessment_role") != "first_window_refinement_only")))


def refinement_requests(assessment):
    requests = []
    horizons = []
    for curve in assessment["KD3"]["curves"]:
        points = curve["points"]
        if not points:
            continue
        base = next((p["case_id"] for p in points if "_eps" not in p["case_id"]), points[0]["case_id"])
        proposed = list(curve.get("prediction", {}).get("suggested_epsilon", []))
        if not curve["brackets"] and curve["protection_loss_intervals"]:
            intervals = curve["protection_loss_intervals"]
            proposed = [v for v in proposed if any(b["low"] < v < b["high"] for b in intervals)]
            if not proposed:
                proposed = [float(np.sqrt(b["low"]*b["high"])) for b in intervals]
        speed = next(v for v in assessment["KD4"]["comparisons"] if v["fraction"] == curve["fraction"]
                     and v["direction"] == curve["direction"])
        if speed["status"] == "needs_refinement":
            proposed += [float(np.sqrt(b["low"]*b["high"])) for b in curve["brackets"] if b["low"] < b["high"]]
        measured = {p["epsilon"] for p in points}
        for epsilon in sorted(set(proposed)):
            if not any(np.isclose(epsilon, v, rtol=1e-10, atol=0.) for v in measured):
                requests.append(dict(base_case_id=base, epsilon=epsilon,
                    switching_factor=curve["switching_factor"], fraction=curve["fraction"], direction=curve["direction"],
                    assessment_role="first_window_refinement_only",
                    horizon_requirement="Matching short census and annual uncensored horizons containing a closed first rare resident window; no100k endpoint requirement",
                    reason="Resolve KD3 predicted band or KD4 threshold-ratio bracket; run both census and uncensored protocols"))
        horizons += [dict(case_id=p["case_id"], current_uncensored_horizon_yr=p["end_yr"],
                         reason="First bottleneck remains terminal; no infinite-horizon threshold assigned")
                     for p in points if p["terminal"] and p["log_probability"] >= np.log(.5)]
    return dict(epsilon=requests, uncensored_horizons=horizons)


def figures(assessment, records, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 2, figsize=(9, 6), sharex=True, sharey=True, layout="constrained")
    for ax, (fraction, direction) in zip(axes.flat, ((f, d) for f in (0., .5) for d in ("A_into_M", "M_into_A"))):
        for factor, color in ((10., "#4b758e"), (1., "#ba773f")):
            curve = next(c for c in assessment["KD3"]["curves"] if c["fraction"] == fraction
                         and c["direction"] == direction and c["switching_factor"] == factor)
            points = curve["points"]
            for point in points:
                ax.scatter(point["epsilon"], point["probability"], color=color,
                           marker="v" if point.get("terminal") and point["eligible"] else ("o" if factor == 10 else "D") if point["eligible"] else "x",
                           facecolor=color if factor == 10 or not point["eligible"] else "none", s=40)
            for bracket in curve["brackets"]:
                ax.plot([bracket["low"], bracket["high"]], [.5, .5], color=color, linewidth=5, alpha=.35)
        prediction = PREDICTED_EPSILON[(direction, fraction)]
        ax.axvspan(prediction, 3*prediction, color=".8", alpha=.35)
        ax.axhline(.5, color=".5", linewidth=.8, linestyle=":")
        ax.set_xscale("log"); ax.set_ylim(-.03, 1.03); ax.grid(alpha=.15)
        ax.set_title(f"f={fraction:g}; displaced {'methanogens' if direction == 'A_into_M' else 'acetogens'}")
    for ax in axes[-1]: ax.set_xlabel("Dormant / active loss ratio epsilon")
    for ax in axes[:, 0]: ax.set_ylabel("First-window survival probability")
    fig.suptitle("No refuges: blue switching 10 L; orange L; grey predicted band\nCircles/diamonds: resolved; triangles: terminal loss bound; crosses: other diagnostics")
    fig.savefig(output/"seed_bank_survival.png", dpi=170); plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.8), sharex=True, sharey=True, layout="constrained")
    for ax, fraction in zip(axes, (0., .5)):
        for direction, marker in (("A_into_M", "o"), ("M_into_A", "s")):
            for configuration, d, color, offset in (("none", 0., ".4", .94), ("warm", 1e-9, "#bb7040", .98),
                                                   ("warm", 1e-6, "#d5a445", 1.02), ("both", 1e-6, "#72569a", 1.06)):
                selected = [r["summary"] for r in records.values() if all(r["protocol"]["case"][k] == v for k, v in
                    dict(group="main", fraction=fraction, direction=direction, configuration=configuration, dispersal_yr=d).items())]
                for row in selected:
                    ax.scatter(row["epsilon"]*offset, row["temperature_k"], marker=marker,
                        edgecolor=color, facecolor=color if row["settling_status"] == "census_stationary" else "none", s=38)
        ax.set_xscale("log"); ax.set_title(f"Acetate recycling f={fraction:g}"); ax.grid(alpha=.15)
        ax.set_xlabel("Dormant / active loss ratio epsilon")
    axes[0].set_ylabel("Endpoint temperature (K)")
    fig.suptitle("Cubic dormancy: circle A into M; square M into A; hollow unsettled\nGrey none; brown warm 1e-9; gold warm 1e-6; purple both 1e-6; x offsets up to 6%")
    fig.savefig(output/"endpoints.png", dpi=170); plt.close(fig)
    fig, ax = plt.subplots(figsize=(6.5, 3.8), layout="constrained")
    points = assessment["KD2"]["overshoot_cases"]
    ax.scatter([p["epsilon"] for p in points], [p["log10_min_cells"] for p in points], color="#4b758e")
    ax.axhline(13, color="#b66f38", linestyle="--", label="KD2 prediction: above 1e13 cells")
    ax.axhline(-14.25, color=".5", linestyle=":", label="Pre-run spec reference: log10 minimum -14.25")
    ax.set_xscale("log"); ax.grid(alpha=.15); ax.legend(frameon=False, fontsize=8)
    ax.set_xlabel("Dormant / active loss ratio epsilon"); ax.set_ylabel("First global acetogen minimum (log10 cells)")
    ax.set_title("Warm refuge, exchange 1e-9/year, no acetate recycling\nAcetogens invading methanogens; X+Z across all habitats")
    fig.savefig(output/"overshoot_minima.png", dpi=170); plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=runner.RAW)
    parser.add_argument("--output", type=Path, default=runner.OUTPUT)
    parser.add_argument("--gate", type=Path, default=e.ROOT/"models/haze_world/figures/turnover/basins_gate.json")
    parser.add_argument("--reference-table", type=Path, default=e.OUTPUT/"selected_main.csv")
    parser.add_argument("--reference-raw", type=Path, default=e.RAW)
    args = parser.parse_args()
    gate = require_gate(args.gate)
    all_records = survival.records(args.raw_dir, "census")
    expected = {c.case_id: c for c in runner.design()}
    planned, refinements = assessment_records(all_records)
    records = planned|refinements
    probability_file = args.output/"first_survival.json"
    probability_manifest = args.output/"first_survival_manifest.json"
    probability_metadata = json.loads(probability_manifest.read_text())
    selection_digest = validate_selection_manifest(probability_metadata, args.raw_dir)
    for name, digest in probability_metadata["source_sha256"].items():
        if sha256((e.ROOT/name).read_bytes()).hexdigest() != digest:
            raise RuntimeError("First-window scoring source changed")
    rows = probability_rows(probability_file, records, args.raw_dir,
                            survival.records(args.raw_dir, "uncensored"))
    with (args.output/"endpoint_pairs.csv").open() as stream:
        pairs = [{k: True if v == "True" else False if v == "False" else v for k, v in row.items()}
                 for row in csv.DictReader(stream)]
    if len(pairs) != len(expected)//2 or any(not all(k in p for k in ("same_local_occupancy", "same_endpoint")) for p in pairs):
        raise RuntimeError("Incomplete endpoint-pair assessment")
    endpoint_manifest = json.loads((args.output/"endpoint_assessment.json").read_text())
    validate_selection_manifest(endpoint_manifest, args.raw_dir)
    for name, digest in endpoint_manifest["source_sha256"].items():
        if sha256((e.ROOT/name).read_bytes()).hexdigest() != digest:
            raise RuntimeError("Endpoint comparator source changed")
    for item in endpoint_manifest["receipts"]:
        if item["case_id"] not in planned:
            raise RuntimeError("Endpoint manifest contains a nonplanned refinement")
        record = planned[item["case_id"]]
        if any(item[k] != record[k] for k in ("fingerprint", "raw_file", "raw_sha256")):
            raise RuntimeError("Endpoint-pair profile differs from selected T3 receipt")
    if (len(endpoint_manifest["receipts"]) != len(planned)
            or {item["case_id"] for item in endpoint_manifest["receipts"]} != set(planned)):
        raise RuntimeError("Endpoint manifest lacks the128 planned cases")
    reference = reference_comparisons(planned, args.raw_dir, args.reference_table, args.reference_raw)
    assessment = assess(records, rows, pairs, args.raw_dir, reference)
    assessment["refinement_requests"] = refinement_requests(assessment)
    assessment.update(t1_gate=gate, physical_cases=len(planned), planned_cases=len(expected),
        first_window_refinement_cases=len(refinements),
        first_window_refinements=[dict(case_id=c, parent_case_id=r["refinement_parent_case_id"],
            census_horizon_yr=r["protocol"]["case"]["years"],
            resident_horizon_contract=rows[(c, "m" if r["protocol"]["case"]["direction"] == "A_into_M" else "a")]["refinement_horizon_contract"],
            scope="KD3/KD4 first-window evidence only; excluded from endpoint pairs, reference endpoint comparisons and long-horizon macroscopic-protection claims")
            for c, r in refinements.items()],
        receipt_selection_sha256=selection_digest,
        condition="Cubic switching; measured microbial kinetics plus named extrapolations; not an Archean calibration",
        probability_scope="First resolved global guild bottleneck in a recorded environment; conditional on other guild; not local occupancy or joint endpoint probability",
        source_sha256={str(p.relative_to(e.ROOT)): sha256(p.read_bytes()).hexdigest() for p in
                       (Path(__file__), Path(endpoints.__file__), Path(survival.__file__))},
        inputs={str(p.relative_to(e.ROOT)): sha256(p.read_bytes()).hexdigest() for p in
                (probability_file, probability_manifest, args.output/"endpoint_pairs.csv", args.output/"endpoint_assessment.json", args.reference_table)},
        receipts=[dict(case_id=c, assessment_role=r["assessment_role"],
                       **{k: r[k] for k in ("fingerprint", "raw_file", "raw_sha256")}) for c, r in records.items()])
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output/"prediction_assessment.json").write_text(e.dumps(assessment)+"\n")
    figures(assessment, planned, args.output)


if __name__ == "__main__":
    main()
