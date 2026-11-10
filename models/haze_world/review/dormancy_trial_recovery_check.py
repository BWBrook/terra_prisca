"""Qualify the named trial guard on the unchanged uncensored0000 start."""

import argparse
from collections import Counter
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter
from types import FunctionType, SimpleNamespace

import numpy as np
from scipy.special import logsumexp

from terra_prisca.haze_world import dormancy_experiments as runner
from terra_prisca.haze_world import dormancy_integration as frozen
from terra_prisca.haze_world import dormancy_trial_integration as trial
from terra_prisca.haze_world import dormancy as model


def check(years, wall_seconds):
    case = runner.design(years)[0]
    p = runner.parameters(case)
    _, original_protocol = runner.identity(case, "uncensored")
    initial = np.asarray(runner.dormancy_starts.conditional_states(p, 1)["selected"]["y"]).copy()
    for patch, weight in enumerate(p.weights):
        if weight:
            initial[6*patch+1] = 1e-12
            initial[6*patch+4] = 0.
    source = runner.sources() | {str(Path(trial.__file__).relative_to(runner.e.ROOT)):
                                sha256(Path(trial.__file__).read_bytes()).hexdigest()}
    protocol = dict(case=asdict(case), source_sha256=source,
                    mode="uncensored_named_trial_guard_review", initial=initial.tolist(),
                    census=original_protocol["census"],
                    review_script_sha256=sha256(Path(__file__).read_bytes()).hexdigest())
    fingerprint = sha256(runner.e.dumps(protocol).encode()).hexdigest()
    raw = runner.e.ROOT/"local/haze/dormancy_trial_review"
    raw.mkdir(exist_ok=True)
    summary_path = Path(__file__).with_name(f"dormancy_trial_recovery_{years:g}.json")
    if years == 30000:
        prior = json.loads(Path(__file__).with_name("dormancy_trial_recovery_3000.json").read_text())
        if prior["status"] != "completed" or prior["protocol"]["source_sha256"] != source:
            raise RuntimeError("Qualify the current3000-year trial-guard smoke first")
    accepted, counts, progress = [0.], dict(constructors=0, rhs=0), []
    rejected, acetate, conditioned = [], [], []
    started, last = perf_counter(), [perf_counter()]

    class ReviewLimit(RuntimeError):
        pass

    class Observed(trial._GuardedLSODA):
        def __init__(self, *args, **kwargs):
            counts["constructors"] += 1
            rejected[:] = [kwargs["rejected"]]
            acetate[:] = [kwargs["events"]]
            conditioned[:] = [kwargs["conditioned"]]
            super().__init__(*args, **kwargs)

        def _initialize(self, time, state, bound, options):
            original = self._physical_rhs
            def bounded(t, y):
                counts["rhs"] += 1
                if perf_counter()-started > wall_seconds:
                    raise ReviewLimit("Bounded actual-recovery review reached its wall limit")
                return original(t, y)
            self._physical_rhs = bounded
            super()._initialize(time, state, bound, options)

        def step(self):
            message = super().step()
            if perf_counter()-last[0] > 5:
                row = dict(wall_seconds=perf_counter()-started, accepted_time_yr=accepted[0],
                           native_time_yr=float(self.t), status=self.status, step_size=self.step_size,
                           rejections=len(self._rejected), acetate_rejections=len(self._retry_events),
                           live_max_step=float(self._lsoda_solver._integrator.rwork[5]), **counts)
                progress.append(row)
                print(json.dumps(row), flush=True)
                last[0] = perf_counter()
            return message

    dense_minima = frozen._dense_minima
    def observed_minima(*args, **kwargs):
        result = dense_minima(*args, **kwargs)
        accepted[0] = float(args[2])
        return result
    namespace = trial.integrate.__globals__.copy()
    namespace["_GuardedLSODA"] = Observed
    frozen_namespace = frozen.integrate.__globals__.copy()
    frozen_namespace["_dense_minima"] = observed_minima
    frozen_function = FunctionType(frozen.integrate.__code__, frozen_namespace,
                                   frozen.integrate.__name__, frozen.integrate.__defaults__,
                                   frozen.integrate.__closure__)
    frozen_function.__kwdefaults__ = frozen.integrate.__kwdefaults__
    namespace["frozen"] = SimpleNamespace(integrate=frozen_function)
    function = FunctionType(trial.integrate.__code__, namespace, trial.integrate.__name__,
                            trial.integrate.__defaults__, trial.integrate.__closure__)
    function.__kwdefaults__ = trial.integrate.__kwdefaults__
    answer = dict(protocol=protocol, fingerprint=fingerprint)
    try:
        process = trial.Census(**original_protocol["census"])
        result = function(initial, p, years, census=process, sample_every_censuses=1,
                          max_step=case.max_step_yr, rtol=case.rtol)
        payload = raw/f"actual0000_t{years:g}-{fingerprint[:16]}.npz"
        np.savez_compressed(payload, t=result.t, y=result.y, log_biomass=result.log_biomass,
                            log_active=result.log_active, log_dormant=result.log_dormant)
        active = p.weights > 0
        sampled = logsumexp(result.log_biomass[active]+np.log(p.weights[active])[:, None, None], axis=0)
        answer.update(status=result.status, raw_file=str(payload.relative_to(runner.e.ROOT)),
                      raw_sha256=sha256(payload.read_bytes()).hexdigest(), metadata=runner.e.clean(result.metadata),
                      nonnegative_stocks=bool(np.all(result.y >= 0)),
                      finite_present_guild_logs=bool(np.all(np.isfinite(result.log_biomass[active]))),
                      minima_bound_samples=bool(np.all(result.global_continuous_min_log_biomass <= np.min(sampled, axis=1)+1e-10)),
                      max_redox_residual=float(max(abs(model.redox_residual(y, p)) for y in result.y[:, ::100].T)),
                      global_min_log_biomass=result.global_continuous_min_log_biomass.tolist(),
                      global_min_times_yr=result.global_continuous_min_times_yr.tolist())
        if years == 1000:
            reference = frozen.integrate(initial, p, years, census=process,
                                         sample_every_censuses=1, max_step=case.max_step_yr, rtol=case.rtol)
            answer["frozen_bitwise"] = {name: bool(np.array_equal(getattr(reference, name), getattr(result, name)))
                for name in ("t", "y", "log_biomass", "log_active", "log_dormant",
                             "global_continuous_min_log_biomass", "global_continuous_min_times_yr")}
    except ReviewLimit as error:
        answer.update(status="review_wall_limit", error=str(error))
    except Exception as error:
        answer.update(status="review_failed", error=repr(error))
    answer.update(wall_seconds=perf_counter()-started, accepted_time_yr=accepted[0], counts=counts,
                  progress=progress, rejected_trials=rejected[0] if rejected else [],
                  acetate_trials=acetate[0] if acetate else [],
                  conditioned_trials=conditioned[0] if conditioned else [],
                  source_unchanged=runner.sources() == original_protocol["source_sha256"]
                    and sha256(Path(trial.__file__).read_bytes()).hexdigest()
                    == source[str(Path(trial.__file__).relative_to(runner.e.ROOT))])
    receipt = raw/f"actual0000_t{years:g}-{fingerprint[:16]}.receipt.json"
    receipt.write_text(runner.e.dumps(answer)+"\n")
    public = {k: v for k, v in answer.items() if k not in
              ("progress", "rejected_trials", "acetate_trials", "conditioned_trials", "metadata")}
    public.update(raw_receipt=str(receipt.relative_to(runner.e.ROOT)),
                  raw_receipt_sha256=sha256(receipt.read_bytes()).hexdigest(),
                  rejected_trial_kinds=dict(Counter(e["kind"] for e in answer["rejected_trials"])),
                  acetate_trial_count=len(answer["acetate_trials"]),
                  stage_conditioning_count=len(answer["conditioned_trials"]))
    if "metadata" in answer:
        excluded = ("trial_guard_events", "trial_guard_stage_conditioning_events",
                    "trial_guard_chemical_chart_events", "trial_guard_solver_constructions",
                    "acetate_trial_retry_events", "stage_coordinate_switches", "stage_source_restarts")
        public["metadata"] = {k: v for k, v in answer["metadata"].items() if k not in excluded}
    summary_path.write_text(runner.e.dumps(public)+"\n")
    print(json.dumps({k: answer[k] for k in ("status", "wall_seconds", "accepted_time_yr", "counts")}), flush=True)
    return answer


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--years", type=float, choices=(1000., 3000., 30000.), default=3000.)
    parser.add_argument("--wall-seconds", type=float, default=300.)
    args = parser.parse_args()
    check(args.years, args.wall_seconds)
