"""Bounded audit and 2k-year precision continuation of canonical 0012.

    uv run python models/haze_world/review/dormancy0012_cycle_check.py

The autonomous physical state starts at the recorded year80000. Relative
solver time restarts at0; the ten-year one-cell census remains phase aligned.
No frozen physical or numerical source is modified.
"""

from collections import Counter
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import platform
from time import perf_counter
from types import FunctionType, SimpleNamespace

import numpy as np
from scipy.special import logsumexp

from terra_prisca.haze_world import dormancy as model
from terra_prisca.haze_world import dormancy_experiments as experiments
from terra_prisca.haze_world import dormancy_jacobian_integration as qualified
from terra_prisca.haze_world import dormancy_chemical_integration as numerical
from terra_prisca.haze_world import dormancy_chemical_experiments as runner
from terra_prisca.haze_world import turnover_survival as profiles
from dormancy_spatial_cycle_check import envelope
from dormancy_extended_cycle_check import direct_root, complete_cycle_mean

ROOT = experiments.e.ROOT
HERE = Path(__file__).parent
RAW = ROOT / "local/haze/dormancy_0012_cycle_precision"
FINGERPRINT = "14f5c49a3088e852d97f80363fccb5c42ba6988ea03778e4ebf7c140c0430d2a"
HELPER_SHA = "75c538cb2bfabf0e8b497d6f7b60e8714ab2a69880d8836ec5201ac05b626cd1"


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def copied(function, namespace):
    result = FunctionType(function.__code__, namespace, function.__name__, function.__defaults__, function.__closure__)
    result.__kwdefaults__ = function.__kwdefaults__
    return result


def culls(events, left, right):
    selected = [event for event in events if left < event["time_yr"] <= right]
    return dict(count=len(selected), by_patch_guild=dict(Counter(f"{e['patch']}:{e['guild']}" for e in selected)),
        removed_cells=float(sum(e["removed_cells"] for e in selected)),
        events=selected)


def global_minimum(data, p, conversion, left, right):
    use = (data["t"] >= left) & (data["t"] <= right)
    active = p.weights > 0
    logs = logsumexp(data["log_biomass"][active][:, :, use]+np.log(p.weights[active, None, None]), axis=0)
    return ((logs.min(axis=1)+conversion)/np.log(10)).tolist()


def main():
    if digest(Path(numerical.__file__)) != HELPER_SHA:
        raise RuntimeError("The requested chemical helper changed")
    record_file = experiments.RAW / f"dormancy_0012_census_t100000-{FINGERPRINT[:16]}.receipt.json"
    record = json.loads(record_file.read_text())
    if record["execution_status"] != "complete" or record["fingerprint"] != FINGERPRINT:
        raise RuntimeError("The requested canonical record is absent or incomplete")
    if sha256(experiments.e.dumps(record["protocol"]).encode()).hexdigest() != FINGERPRINT:
        raise RuntimeError("The native protocol fingerprint changed")
    source = runner.sources()
    if record["protocol"]["source_sha256"] != source:
        raise RuntimeError("The original and continuation source graphs differ")
    data = profiles.load(record, experiments.RAW)
    p = experiments.parameters(experiments.Case(**record["protocol"]["case"]))
    index = np.flatnonzero(data["t"] == 80000.)
    if len(index) != 1:
        raise RuntimeError("The recorded 80k-year state is absent or ambiguous")
    initial = data["y"][:, index[0]].copy()
    process = numerical.Census(**record["protocol"]["census"])
    if process.minimum_cells != 1. or process.census_yr != 10.:
        raise RuntimeError("The required census changed")
    coordinates = numerical._Coordinates(initial, p)
    roundtrip, stage_logs = coordinates.decode(coordinates.encode(initial))
    original_logs = np.stack((data["log_active"][:, :, index[0]], data["log_dormant"][:, :, index[0]]), axis=2)
    same_finite = np.isfinite(original_logs) & np.isfinite(stage_logs)
    lost = np.isfinite(original_logs) & np.isneginf(stage_logs)
    added = np.isneginf(original_logs) & np.isfinite(stage_logs)
    log_changes = [dict(patch=p.patch_names[j], guild=("acetogen", "methanogen")[g], stage=("active", "dormant")[s],
        original_log_gdw_l=float(original_logs[j, g, s]), reconstructed_log_gdw_l=float(stage_logs[j, g, s]))
        for j, g, s in zip(*np.where(lost | added))]
    if np.any(added):
        raise RuntimeError("Physical initialization unexpectedly added a represented stage")
    relative = np.divide(abs(roundtrip-initial), abs(initial), out=np.zeros_like(initial), where=initial != 0.)
    if not np.allclose(roundtrip, initial, rtol=8*np.finfo(float).eps, atol=0.):
        raise RuntimeError("Initial physical coordinate round trip exceeds floating-point roundoff")
    events = json.loads(str(data["extinction_events"]))
    conversion = data["metadata"]["global_log_cell_conversion"]
    late = data["t"] >= 80000.
    protocol = dict(source_sha256=source, checker_sha256=digest(Path(__file__)),
        imported_review_sha256={name: digest(HERE/name) for name in ("dormancy_spatial_cycle_check.py", "dormancy_extended_cycle_check.py")},
        case=record["protocol"]["case"], original_fingerprint=FINGERPRINT,
        original_receipt=str(record_file.relative_to(ROOT)), original_receipt_sha256=digest(record_file),
        original_raw_file=record["raw_file"], original_raw_sha256=record["raw_sha256"],
        absolute_start_yr=80000., relative_solver_start_yr=0., duration_yr=2000., initial_y=initial.tolist(),
        initial_coordinate_roundtrip_maximum_relative_error=float(max(relative)),
        initial_finite_stage_log_maximum_absolute_difference=float(max(abs(original_logs[same_finite]-stage_logs[same_finite]))),
        initial_stage_log_finite_mask_changes=log_changes,
        initialization_scope="Exact recorded physical input, with fresh solver history/charts and relative time. Any below-float log-stage loss is listed; no seed or physical stock reset.",
        census=asdict(process), annual_observations=True, rtol=2e-9, max_step_yr=1., wall_limit_seconds=180.,
        architecture=platform.machine(), operating_system=platform.system())
    fingerprint = sha256(experiments.e.dumps(protocol).encode()).hexdigest()
    result = dict(protocol=protocol, fingerprint=fingerprint,
        native_status=record["summary"]["settling_status"], native_summary=record["summary"],
        native_windows=[envelope(data, p, a, b) for a, b in ((40000., 60000.), (60000., 80000.), (80000., 100000.))],
        native_matched_window=envelope(data, p, 80000., 82000.), native_complete_cycle_mean=complete_cycle_mean(data, p),
        native_matched_culls=culls(events, 80000., 82000.), native_late_culls=culls(events, 80000., 100000.),
        native_matched_minimum_global_log10_cells=global_minimum(data, p, conversion, 80000., 82000.),
        native_late_minimum_global_log10_cells=global_minimum(data, p, conversion, 80000., 100000.),
        switch_temperatures_k=list(model.core.switch_temperatures(p.coupled.biology)),
        scope="Finite censused spatial-dormancy oscillation candidate. Recurrent local culls distinguish this hybrid trajectory from an unculled continuous cycle. No global-basin or periodic-orbit proof.")
    try:
        result["mixed_equilibrium"] = direct_root(np.mean(data["y"][:, late], axis=1), p)
    except Exception as error:
        result["mixed_equilibrium"] = dict(status="unresolved", error=repr(error))
    RAW.mkdir(exist_ok=True)
    samples = {}
    next_sample = [0]
    accepted = [0.]
    started = perf_counter()

    class ReviewLimit(RuntimeError):
        pass

    class Bounded(numerical._ChemicalLSODA):
        def _initialize(self, time, state, bound, options):
            original = self._physical_rhs
            def observed(t, y):
                if perf_counter()-started > 180.:
                    raise ReviewLimit("The 0012 precision continuation reached its wall limit")
                return original(t, y)
            self._physical_rhs = observed
            return super()._initialize(time, state, bound, options)

    original_minima = qualified._dense_minima
    def observe(dense, left, right, coords, state, previous=None):
        answer = original_minima(dense, left, right, coords, state, previous)
        accepted[0] = float(right)
        if left == round(left) and int(left) in samples:
            physical, stages = coords.decode(state)
            samples[int(left)] = physical.copy(), stages.copy()
        while next_sample[0] <= right+16*np.finfo(float).eps*max(1., right):
            time = float(min(next_sample[0], right))
            if time >= left:
                internal = state.copy() if time == left else dense(time)
                physical, stages = coords.decode(internal)
                samples[next_sample[0]] = physical.copy(), stages.copy()
            next_sample[0] += 1
        return answer
    sampled = qualified.integrate.__globals__.copy()
    sampled["_dense_minima"] = observe
    namespace = numerical.integrate.__globals__.copy()
    namespace.update(frozen=SimpleNamespace(integrate=copied(qualified.integrate, sampled)), _ChemicalLSODA=Bounded)
    function = copied(numerical.integrate, namespace)

    def merge_official(times, values, stages):
        for k, time in enumerate(times):
            if time == round(time):
                samples[int(time)] = np.asarray(values[k]).copy(), np.asarray(stages[k]).copy()

    try:
        flow = function(initial, p, 2000., census=process, sample_every_censuses=1, rtol=2e-9, max_step=1.)
        merge_official(flow.t, flow.y.T, np.moveaxis(np.stack((flow.log_active, flow.log_dormant), axis=2), -1, 0))
        if flow.status != "completed":
            raise RuntimeError("The continuation left its supported domain")
        result.update(status="completed", metadata=experiments.e.clean(flow.metadata), control_culls=culls(flow.extinction_events, 0., 2000.),
            control_dense_minimum_global_log10_cells=((flow.global_continuous_min_log_biomass+conversion)/np.log(10)).tolist())
    except Exception as error:
        result.update(status="wall_limit" if isinstance(error, ReviewLimit) else "failed", error=repr(error),
            native_zero_time_events=getattr(error, "native_zero_time_events", []),
            chemical_conditioning_requests=getattr(error, "chemical_conditioning_requests", []))
        trace = error.__traceback__
        while trace:
            frame = trace.tb_frame
            if frame.f_code is qualified.integrate.__code__:
                state = frame.f_locals
                merge_official(state.get("times", []), state.get("samples", []), state.get("stage_samples", []))
                result["partial_culls"] = culls(state.get("events", []), 0., 2000.)
            trace = trace.tb_next
    result.update(wall_seconds=perf_counter()-started, accepted_duration_yr=accepted[0], source_unchanged=runner.sources() == source)
    if samples:
        time = np.array(sorted(samples), dtype=float)
        values = np.column_stack([samples[int(t)][0] for t in time])
        stages = np.stack([samples[int(t)][1] for t in time], axis=-1)
        logs = logsumexp(stages, axis=2)
        payload = RAW/f"dormancy0012-{fingerprint[:16]}.npz"
        np.savez_compressed(payload, t=time+80000., y=values, log_biomass=logs, log_active=stages[:, :, 0], log_dormant=stages[:, :, 1])
        result.update(raw_file=str(payload.relative_to(ROOT)), raw_sha256=digest(payload), nonnegative_stocks=bool(np.all(values >= 0.)))
        if result["status"] == "completed":
            if not np.array_equal(time, np.arange(2001.)):
                raise RuntimeError("Annual accepted-flow observations are incomplete")
            common, native_index, control_index = np.intersect1d(data["t"], time+80000., return_indices=True)
            native_t = np.asarray(model.core.temperature_k(data["y"][-1, native_index], p.coupled.climate))
            control_t = np.asarray(model.core.temperature_k(values[-1, control_index], p.coupled.climate))
            result.update(control_window=envelope(dict(t=time, y=values), p, 0., 2000.),
                common_times=int(len(common)), common_time_maximum_temperature_difference_k=float(max(abs(native_t-control_t))),
                control_sampled_minimum_global_log10_cells=global_minimum(dict(t=time, y=values, log_biomass=logs), p, conversion, 0., 2000.))
    result["continuation_scope"] = "Same75c helper and LSODA family, tighter tolerance/smaller step and fresh relative-time history. Exact physical initialization; no independent-solver or asymptotic-attractor proof."
    target = RAW/f"dormancy0012-{fingerprint[:16]}.receipt.json"
    target.write_text(experiments.e.dumps(result)+"\n")
    compact = dict(result)
    compact["full_receipt_file"] = str(target.relative_to(ROOT))
    compact["full_receipt_sha256"] = digest(target)
    for name in ("native_matched_culls", "native_late_culls", "control_culls", "partial_culls"):
        if name in compact:
            compact[name] = {key: value for key, value in compact[name].items() if key != "events"}
    compact.pop("metadata", None)
    Path(__file__).with_suffix(".json").write_text(experiments.e.dumps(compact)+"\n")
    print(json.dumps({name: result.get(name) for name in ("status", "wall_seconds", "accepted_duration_yr", "common_time_maximum_temperature_difference_k")}), flush=True)


if __name__ == "__main__":
    main()
