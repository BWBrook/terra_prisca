"""One bounded precision continuation of the recorded 0068 cycle candidate.

    uv run python models/haze_world/review/dormancy_extended_cycle_precision.py

Observe annual accepted-flow states while retaining the ten-year one-cell
census. This runs only the authorized 2000-year continuation from year80000.
"""

from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import platform
from time import perf_counter
from types import FunctionType, SimpleNamespace

import numpy as np
from scipy.special import logsumexp

from terra_prisca.haze_world import dormancy_experiments as experiments
from terra_prisca.haze_world import dormancy_jacobian_integration as qualified
from terra_prisca.haze_world import dormancy_progress_integration as numerical
from terra_prisca.haze_world import dormancy_progress_experiments as runner
from terra_prisca.haze_world import turnover_survival as profiles
from dormancy_spatial_cycle_check import envelope

PROGRESS_SHA256 = "ee65a5d01009bb376146f64b883d3d6ec52670fb2bb2326bb2a4331e63d589a4"
QUALIFIED_SHA256 = "7046fc9baa47022fff7e700ea79f8e72e2c3195a77b9bd5f71e272d6a1c34310"
RAW = experiments.e.ROOT / "local/haze/dormancy_extended_cycle_precision"


def copied(function, namespace):
    result = FunctionType(function.__code__, namespace, function.__name__, function.__defaults__, function.__closure__)
    result.__kwdefaults__ = function.__kwdefaults__
    return result


def main():
    for module, expected in ((numerical, PROGRESS_SHA256), (qualified, QUALIFIED_SHA256)):
        if sha256(Path(module.__file__).read_bytes()).hexdigest() != expected:
            raise RuntimeError("The requested numerical variant changed")
    record = profiles.records(experiments.RAW, "census")["dormancy_0068"]
    data = profiles.load(record, experiments.RAW)
    p = experiments.parameters(experiments.Case(**record["protocol"]["case"]))
    start = np.flatnonzero(data["t"] == 80000.)
    if len(start) != 1:
        raise RuntimeError("Missing or ambiguous recorded 80k-year state")
    initial = data["y"][:, start[0]].copy()
    process = numerical.Census(**record["protocol"]["census"])
    source = runner.sources()
    for path, expected in record["protocol"]["source_sha256"].items():
        if source[path] != expected:
            raise RuntimeError("A frozen original dependency changed")
    protocol = dict(case=record["protocol"]["case"], source_sha256=source,
        checker_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
        envelope_checker_sha256=sha256(Path(__file__).with_name("dormancy_spatial_cycle_check.py").read_bytes()).hexdigest(),
        original_fingerprint=record["fingerprint"], original_raw_file=record["raw_file"], original_raw_sha256=record["raw_sha256"],
        absolute_start_yr=80000., duration_yr=2000., initial_y=initial.tolist(), census=asdict(process),
        output_stride_yr=1., rtol=2e-9, max_step_yr=1., wall_limit_seconds=180.,
        architecture=platform.machine(), operating_system=platform.system(),
        sampling="Annual observations of accepted dense pieces; official post-census snapshots override observations at shared dates")
    fingerprint = sha256(experiments.e.dumps(protocol).encode()).hexdigest()
    RAW.mkdir(exist_ok=True)
    started = perf_counter()
    accepted = [0.]
    samples = {}
    next_sample = [0]

    class ReviewLimit(RuntimeError):
        pass

    class Bounded(numerical._ProgressLSODA):
        def _initialize(self, time, state, bound, options):
            original = self._physical_rhs
            def observed(t, y):
                if perf_counter()-started > 180.:
                    raise ReviewLimit("The 0068 precision continuation reached its wall limit")
                return original(t, y)
            self._physical_rhs = observed
            return super()._initialize(time, state, bound, options)

    original_minima = qualified._dense_minima
    def observe(dense, left, right, coordinates, state, previous=None):
        answer = original_minima(dense, left, right, coordinates, state, previous)
        accepted[0] = float(right)
        while next_sample[0] <= right+16*np.finfo(float).eps*max(1., right):
            time = float(min(next_sample[0], right))
            if time >= left:
                internal = state.copy() if time == left else dense(time)
                physical, stages = coordinates.decode(internal)
                samples[next_sample[0]] = physical.copy(), stages.copy()
            next_sample[0] += 1
        return answer
    sampled = qualified.integrate.__globals__.copy()
    sampled["_dense_minima"] = observe
    namespace = numerical.integrate.__globals__.copy()
    namespace.update(_ProgressLSODA=Bounded, qualified=SimpleNamespace(integrate=copied(qualified.integrate, sampled)))
    function = copied(numerical.integrate, namespace)
    answer = dict(protocol=protocol, fingerprint=fingerprint)
    try:
        result = function(initial, p, 2000., census=process, sample_every_censuses=1, rtol=2e-9, max_step=1.)
        if result.status != "completed":
            raise RuntimeError("The precision continuation left its supported domain")
        for k, time in enumerate(result.t):
            if time != round(time):
                raise RuntimeError("Nonannual official snapshot")
            stages = np.stack((result.log_active[:, :, k], result.log_dormant[:, :, k]), axis=2)
            samples[int(time)] = result.y[:, k].copy(), stages
        times = np.array(sorted(samples), dtype=float)
        if not np.array_equal(times, np.arange(2001.)):
            raise RuntimeError("The accepted-flow observer missed annual samples")
        values = np.column_stack([samples[int(t)][0] for t in times])
        stages = np.stack([samples[int(t)][1] for t in times], axis=-1)
        logs = logsumexp(stages, axis=2)
        roundtrip = np.divide(abs(values[:, 0]-initial), abs(initial), out=np.zeros_like(initial), where=initial != 0.)
        if not np.allclose(values[:, 0], initial, rtol=8*np.finfo(float).eps, atol=0.):
            raise RuntimeError("The initial coordinate round trip exceeds floating-point roundoff")
        absolute = times+80000.
        common, native_index, control_index = np.intersect1d(data["t"], absolute, return_indices=True)
        native_temperature = np.asarray(qualified.model.core.temperature_k(data["y"][-1, native_index], p.coupled.climate))
        control_temperature = np.asarray(qualified.model.core.temperature_k(values[-1, control_index], p.coupled.climate))
        active = p.weights > 0
        global_logs = logsumexp(logs[active]+np.log(p.weights[active, None, None]), axis=0)
        conversion = result.metadata["global_log_cell_conversion"]
        native = envelope(data, p, 80000., 100000.)
        control = envelope(dict(t=times, y=values), p, 0., 2000.)
        payload = RAW / f"dormancy_0068_precision2000-{fingerprint[:16]}.npz"
        np.savez_compressed(payload, t=absolute, y=values, log_biomass=logs,
            log_active=stages[:, :, 0], log_dormant=stages[:, :, 1])
        answer.update(status="completed", raw_file=str(payload.relative_to(experiments.e.ROOT)),
            raw_sha256=sha256(payload.read_bytes()).hexdigest(), metadata=experiments.e.clean(result.metadata),
            native=native, control=control, common_times=int(len(common)),
            common_time_maximum_temperature_difference_k=float(max(abs(native_temperature-control_temperature))),
            period_relative_difference=control["period_yr"]/native["period_yr"]-1,
            sampled_range_relative_difference=control["sampled_range_k"]/native["sampled_range_k"]-1,
            initial_coordinate_roundtrip_maximum_relative_error=float(max(roundtrip)),
            sampled_minimum_global_log10_cells=((np.min(global_logs, axis=1)+conversion)/np.log(10)).tolist(),
            dense_minimum_global_log10_cells=((result.global_continuous_min_log_biomass+conversion)/np.log(10)).tolist(),
            census_removals=len(result.extinction_events), nonnegative_stocks=bool(np.all(values >= 0.)),
            scope="Same LSODA family with current qualified analytic-Jacobian/progress variant and finer resolution; not an independent-solver, basin or periodic-orbit proof")
    except ReviewLimit as error:
        answer.update(status="review_wall_limit", error=str(error))
    except Exception as error:
        answer.update(status="review_failed", error=repr(error), native_zero_time_events=getattr(error, "native_zero_time_events", []))
    answer.update(wall_seconds=perf_counter()-started, accepted_duration_yr=accepted[0], source_unchanged=runner.sources() == source)
    receipt = RAW / f"dormancy_0068_precision2000-{fingerprint[:16]}.receipt.json"
    receipt.write_text(experiments.e.dumps(answer)+"\n")
    print(json.dumps({key: answer[key] for key in ("status", "wall_seconds", "accepted_duration_yr")}), flush=True)


if __name__ == "__main__":
    main()
