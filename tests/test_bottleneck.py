from types import SimpleNamespace
from hashlib import sha256
import json

import numpy as np
import pytest

from terra_prisca.haze_world import bottleneck as b


def test_excursions_bracket_each_bottleneck_and_preserve_terminal_censoring():
    result = b.excursions(np.array([10., 2., 1., 10., 3., 10., 2., 1.]), 5.)
    assert result == [(0, 3, False), (3, 5, False), (5, 7, True)]
    assert b.excursions(np.array([10., 11.]), 5.) == []


def test_multiple_windows_multiply_probabilities_and_reclassify_count_scale():
    logs = np.log([.2, .4])
    result = b.combine_windows(logs)
    assert result["survival_probability"] == pytest.approx((1-np.exp(-.2))*(1-np.exp(-.4)))
    assert result["lambda_semantics"] == "limiting_window"
    scale = result["scale_for_half_survival"]
    assert np.prod(-np.expm1(-np.exp(logs)*scale)) == pytest.approx(.5)
    assert b.combine_windows([-1000.])["classification"] == "robust_loss"
    assert b.combine_windows([20.])["classification"] == "robust_persistence"


def test_threshold_crossings_keep_multiple_transitions_and_logarithmic_brackets():
    rows = [dict(dispersal_yr=10.**k, value=v) for k,v in enumerate((-1., 1., -1., 1.))]
    crossings = b.threshold_crossings(rows, "value", 0.)
    assert len(crossings) == 3
    assert crossings[0]["bracket_yr"] == [1., 10.]
    assert crossings[0]["interpolated_yr"] == pytest.approx(np.sqrt(10.))


def test_record_selection_prefers_declared_numerical_variant_and_checks_current_sources(tmp_path, monkeypatch):
    source = tmp_path/"physical.py"; source.write_text("accepted source\n")
    current = sha256(source.read_bytes()).hexdigest()
    monkeypatch.setattr(b.runs, "RAW", tmp_path)
    monkeypatch.setattr(b.experiments, "ROOT", tmp_path)
    for name, solver, digest in (("older", None, "historical digest"), ("current", "accepted_state_trial_retry_v1", current)):
        protocol = dict(case=dict(case_id="case"), years=30000., max_step_yr=10., solver=solver,
                        source_sha256={"physical.py": digest})
        record = dict(execution_status="complete", protocol=protocol,
                      fingerprint=sha256(b.experiments.dumps(protocol).encode()).hexdigest(), raw_file=name)
        (tmp_path/(name+".receipt.json")).write_text(json.dumps(record))
    assert b._records()["case"]["raw_file"] == "current"
    source.write_text("different source\n")
    with pytest.raises(RuntimeError, match="physical source differs"):
        b._records()


def test_nonreturning_rare_guild_reports_positive_finite_horizon_survival(monkeypatch):
    p = SimpleNamespace(weights=np.array([1.]), n_patches=1, state_size=5,
                        base=SimpleNamespace(climate=None, activity_feedback="fixed"))
    monkeypatch.setattr(b.branching, "per_cell_rates", lambda y, p, guild: (np.array([0]), np.array([0.]), np.array([.001])))
    monkeypatch.setattr(b.branching, "migration_matrix", lambda p: np.zeros((1, 1)))
    monkeypatch.setattr(b.habitat, "temperatures", lambda y, p: np.array([280.]))
    monkeypatch.setattr(b, "_uptake_fraction", lambda *args: (0., 0.))
    monkeypatch.setattr(b.core, "temperature_k", lambda r, p: np.full(np.shape(r), 280.))
    t = np.arange(0., 6001., 10.)
    y = np.zeros((5, t.size)); y[0] = 10.
    logs = np.zeros((1, 2, t.size)); logs[0, 0] = -t*.001
    row, windows = b.analyze_arrays(t, y, logs, {"global_log_cell_conversion": 0.}, p, 0)
    assert row["terminal_rare_excursion"]
    assert row["exclusion_supported"]
    assert not row["needs_extension"]
    expected = 1-np.exp(-np.exp(-6.))
    assert row["survival_probability"] == pytest.approx(expected, rel=1e-7)
    assert row["survival_probability"] > 0.
    assert windows[0]["terminal_excursion"]


def test_nonreturn_with_positive_invasion_growth_requires_extension(monkeypatch):
    p = SimpleNamespace(weights=np.array([1.]), n_patches=1, state_size=5,
                        base=SimpleNamespace(climate=None, activity_feedback="fixed"))
    monkeypatch.setattr(b.branching, "per_cell_rates", lambda y, p, guild: (np.array([0]), np.array([.002]), np.array([.001])))
    monkeypatch.setattr(b.branching, "migration_matrix", lambda p: np.zeros((1, 1)))
    monkeypatch.setattr(b.habitat, "temperatures", lambda y, p: np.array([280.]))
    monkeypatch.setattr(b, "_uptake_fraction", lambda *args: (0., 0.))
    monkeypatch.setattr(b.core, "temperature_k", lambda r, p: np.full(np.shape(r), 280.))
    t = np.arange(0., 6001., 10.)
    y = np.zeros((5, t.size)); y[0] = 10.
    logs = np.zeros((1, 2, t.size)); logs[0, 0] = -20.+t*.001
    row, _ = b.analyze_arrays(t, y, logs, {"global_log_cell_conversion": 0.}, p, 0)
    assert row["terminal_rare_excursion"]
    assert row["final_invasion_eigenvalue_yr"] > 0
    assert row["needs_extension"]
    assert not row["exclusion_supported"]
