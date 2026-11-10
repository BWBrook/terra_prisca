"""Recompute threshold precision controls from saved profiles; no integrations."""

from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from terra_prisca.haze_world import dormancy_experiments as experiment
from terra_prisca.haze_world import dormancy_chemical_experiments as numerical
from terra_prisca.haze_world import dormancy_branching
from terra_prisca.haze_world import turnover_survival as survival


CASES = ("dormancy_0000_eps0.006", "dormancy_0056_eps0.002499",
         "dormancy_0001_eps0.00046", "dormancy_0057_eps0.00082")


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def receipt(raw, fingerprint):
    matches = [p for p in raw.glob("*.receipt.json")
               if json.loads(p.read_text())["fingerprint"] == fingerprint]
    if len(matches) != 1:
        raise RuntimeError("Missing or duplicate precision receipt: "+fingerprint)
    record = json.loads(matches[0].read_text())
    assert record["execution_status"] == "complete"
    assert sha256(experiment.e.dumps(record["protocol"]).encode()).hexdigest() == fingerprint
    assert record["protocol"]["source_sha256"] == numerical.sources()
    return record, digest(matches[0])


def verify():
    raw = experiment.RAW
    controls = experiment.e.ROOT/"local/haze/dormancy_threshold_precision"
    plan_path = controls/"controls.json"
    plan = json.loads(plan_path.read_text())
    assert {r["case_id"] for r in plan["rows"]} == set(CASES)
    rows = []
    for item in sorted(plan["rows"], key=lambda row: row["case_id"]):
        original, original_receipt_hash = receipt(raw, item["original_fingerprint"])
        control, control_receipt_hash = receipt(controls, item["control_fingerprint"])
        a_case, b_case = original["protocol"]["case"], control["protocol"]["case"]
        assert all(v == b_case[k] for k, v in a_case.items() if k not in ("max_step_yr", "rtol"))
        assert b_case["max_step_yr"] == 1. and b_case["rtol"] == 2e-9
        assert original["protocol"]["parameters"] == control["protocol"]["parameters"]
        assert original["protocol"]["census"] == control["protocol"]["census"]
        assert original["protocol"]["mode"] == control["protocol"]["mode"] == "uncensored"
        case = experiment.Case(**a_case)
        p = experiment.parameters(case)
        a, b = survival.load(original, raw), survival.load(control, controls)
        assert np.array_equal(a["t"], b["t"])
        guild = 1 if case.direction == "A_into_M" else 0
        coarse = survival.analyze(a, p, guild, True)
        fine = survival.analyze(b, p, guild, True)
        stride = survival.analyze(a, p, guild, True, rate_stride=2.)
        step = survival.analyze(a, p, guild, True, max_step=.5)
        assert coarse["rare_window"] and fine["rare_window"]
        assert not coarse["terminal_window"] and not fine["terminal_window"]
        acounts = survival.counts(a, p, guild, True)[0]
        bcounts = survival.counts(b, p, guild, True)[0]
        assert np.all(np.isfinite(acounts)) and np.all(np.isfinite(bcounts))
        rows.append(dict(case_id=case.case_id, original_fingerprint=original["fingerprint"],
            control_fingerprint=control["fingerprint"],
            original_receipt_sha256=original_receipt_hash, control_receipt_sha256=control_receipt_hash,
            original_raw_file=original["raw_file"], original_raw_sha256=original["raw_sha256"],
            control_raw_file=control["raw_file"], control_raw_sha256=control["raw_sha256"],
            original_probability=coarse["survival_probability"], control_probability=fine["survival_probability"],
            probability_difference=fine["survival_probability"]-coarse["survival_probability"],
            log_lambda_difference=fine["log_lambda"]-coarse["log_lambda"],
            rate_spacing2_log_lambda_difference=stride["log_lambda"]-coarse["log_lambda"],
            probability_step_half_log_lambda_difference=step["log_lambda"]-coarse["log_lambda"],
            maximum_common_temperature_difference_k=float(np.max(abs(a["temperatures_k"][p.weights > 0]-b["temperatures_k"][p.weights > 0]))),
            maximum_common_global_log_count_difference=float(np.max(abs(acounts-bcounts))),
            original_first_window={k: coarse[k] for k in ("start_yr", "end_yr", "minimum_time_yr", "window_status", "sampled_window_climate_domains")},
            control_first_window={k: fine[k] for k in ("start_yr", "end_yr", "minimum_time_yr", "window_status")},
            scope="Recorded first resident bottleneck, default global cell-count scale; not a joint endpoint probability"))
    sources = (Path(__file__), Path(survival.__file__), Path(dormancy_branching.__file__),
               Path(survival.branching.__file__), Path(survival.bottleneck.__file__))
    return dict(rows=rows, numerical_source_sha256=numerical.sources(),
        source_sha256={str(p.relative_to(experiment.e.ROOT)): digest(p) for p in sources},
        control_plan_sha256=digest(plan_path), observational_controller_sha256=plan["controller_sha256"],
        maximum_probability_difference=max(abs(r["probability_difference"]) for r in rows),
        scope="Tenfold tighter physical rtol and1yr maximum step; annual versus2yr rate grid; probability maximum step1versus0.5yr. Saved trajectories only; no altered populations or stationarity flags.")


if __name__ == "__main__":
    result = verify()
    Path(__file__).with_suffix(".json").write_text(experiment.e.dumps(result)+"\n")
    print(json.dumps(dict(controls=len(result["rows"]), maximum_probability_difference=result["maximum_probability_difference"])))
