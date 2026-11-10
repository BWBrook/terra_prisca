import json
from copy import deepcopy

import numpy as np
import pytest

from terra_prisca.haze_world import dormancy_assessment as a


def point(epsilon, probability, eligible=True):
    return dict(epsilon=epsilon, probability=probability,
                log_probability=np.log(probability) if probability else -np.inf,
                eligible=eligible, case_id=str(epsilon))


def test_all_epsilon_crossings_survive_nonmonotonic_response():
    curve = a.crossing_brackets([point(.0001, .9), point(.001, .1), point(.01, .8), point(.1, 0.)])
    assert [b["orientation"] for b in curve["brackets"]] == ["survival_to_loss", "loss_to_survival", "survival_to_loss"]
    assert curve["reversed_crossing"] and not curve["unique_decreasing_crossing"]
    assert a.prediction_band(curve, .001)["status"] == "nonmonotone_or_multiple"


def test_unresolved_or_terminal_points_do_not_create_threshold():
    curve = a.crossing_brackets([point(.0001, .9), point(.001, .1, eligible=False)])
    assert curve["brackets"] == []
    assert a.prediction_band(curve, .0003)["status"] == "unresolved"


def test_probability_points_accept_native_lineage_fields_under_underflow():
    case = dict(configuration="none", loss_h=.001, fraction=0., direction="A_into_M",
                switching_factor=10., ramp="cubic", epsilon=.01)
    row = dict(rare_window=True, terminal_window=False, log_lambda=-1000., survival_probability=0.,
               window_status="first_minimum_linear", classification="robust_loss", minimum_time_yr=100.,
               end_yr=200., log_min_cells=-900.)
    points = a.probability_points({"case": dict(protocol=dict(case=case))}, {("case", "m"): row},
                                  0., "A_into_M", 10.)
    assert points[0]["log_probability"] == -1000.
    assert points[0]["eligible"]
    row["terminal_window"] = True
    point = a.probability_points({"case": dict(protocol=dict(case=case))}, {("case", "m"): row},
                                 0., "A_into_M", 10.)[0]
    assert point["eligible"] and point["probability_bound"] == "finite_horizon_upper"
    row.update(log_lambda=5., survival_probability=1.)
    assert not a.probability_points({"case": dict(protocol=dict(case=case))}, {("case", "m"): row},
                                    0., "A_into_M", 10.)[0]["eligible"]


def test_macroscopic_protection_is_retained_without_an_exact_probability_bracket():
    protected = point(.001, 1., eligible=False)|dict(macroscopic_protection=True)
    lost = point(.01, .01)|dict(probability_bound="finite_horizon_upper")
    curve = a.crossing_brackets([protected, lost])
    assert curve["brackets"] == []
    assert curve["protection_loss_intervals"][0]["low"] == .001
    assert curve["protection_loss_intervals"][0]["high"] == .01
    assert "not an exact" in curve["protection_loss_intervals"][0]["evidence"]


def test_refinement_targets_protected_loss_gap_without_extending_terminal_loss():
    protected = point(.001, 1., eligible=False)|dict(macroscopic_protection=True, terminal=False, end_yr=30000.)
    lost = point(.01, .01)|dict(probability_bound="finite_horizon_upper", terminal=True, end_yr=30000.)
    curve = a.crossing_brackets([protected, lost])|dict(fraction=0., direction="A_into_M", switching_factor=10.)
    assessment = dict(KD3=dict(curves=[curve]), KD4=dict(comparisons=[dict(fraction=0., direction="A_into_M", status="unresolved_or_multiple")]))
    requested = a.refinement_requests(assessment)
    assert requested["epsilon"][0]["epsilon"] == pytest.approx(np.sqrt(.001*.01))
    assert requested["uncensored_horizons"] == []


def test_prediction_band_requires_the_entire_bracket():
    curve = a.crossing_brackets([point(.001, .8), point(.003, .2)])
    assert a.prediction_band(curve, .001)["status"] == "supported_bracket"
    assert a.prediction_band(curve, .002)["status"] == "needs_refinement"
    assert a.prediction_band(curve, .004)["status"] == "refuted_bracket"


def test_switching_speed_uses_both_edges_of_both_brackets():
    fast = a.crossing_brackets([point(.001, .8), point(.002, .2)])
    slow = a.crossing_brackets([point(.002, .8), point(.004, .2)])
    comparison = a.speed_comparison(fast, slow)
    assert comparison["slow_over_fast_intervals"] == [dict(low=1., high=4.)]
    assert comparison["status"] == "needs_refinement"


def test_projection_preserves_total_guild_counts_and_environment():
    profile = dict(y=np.array([[10., 11.], [1., 2.], [3., 4.], [5., 6.], [7., 8.], [9., 10.], [.2, .3]]),
                   metadata=dict(global_log_cell_conversion=42.))
    projected = a.project_profile(profile)
    np.testing.assert_array_equal(projected["y"], [[10., 11.], [8., 10.], [12., 14.], [5., 6.], [.2, .3]])
    assert projected["metadata"] == profile["metadata"]


def test_first_minimum_ignores_later_dense_ghost_minimum(monkeypatch):
    data = dict(min_times=np.array([90., 30.]), min_log_biomass=np.array([-100., -50.]),
                metadata=dict(global_log_cell_conversion=10.))
    monkeypatch.setattr(a.survival, "load", lambda record, raw: data)
    row = dict(guild="a", log_min_cells=5., minimum_time_yr=20., start_yr=10., end_yr=40.,
               source_raw_file="uncensored.npz", source_raw_sha256="checked")
    result = a.first_minimum(row, None)
    assert result["log_min_cells"] == 5.
    assert result["minimum_source"] == "sampled_first_minimum"
    data["min_times"][0] = 21.
    assert a.first_minimum(row, None)["log_min_cells"] == -90.


def test_t1_gate_is_explicit_and_source_bound(tmp_path, monkeypatch):
    monkeypatch.setattr(a.e, "ROOT", tmp_path)
    path = tmp_path/"basins_gate.json"
    path.write_text(json.dumps(dict(gate_passed=False)))
    with pytest.raises(RuntimeError, match="remains open"):
        a.require_gate(path)
    source = tmp_path/"source.py"; source.write_text("frozen")
    digest = a.sha256(source.read_bytes()).hexdigest()
    path.write_text(json.dumps(dict(gate_passed=True, source_sha256={"source.py": digest})))
    assert a.require_gate(path)["gate_passed"]
    source.write_text("changed")
    with pytest.raises(RuntimeError, match="source differs"):
        a.require_gate(path)


def profile_contract(tmp_path, monkeypatch):
    paths = ["physical.py", *sorted(a.GUARDED_PREFIX_SOURCES)]
    hashes = {}
    for name in paths:
        path = tmp_path/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(name)
        hashes[name] = a.sha256(path.read_bytes()).hexdigest()
    physical = {"physical.py": hashes["physical.py"]}
    monkeypatch.setattr(a.runner, "sources", lambda: dict(physical))
    protocol = dict(source_sha256={"physical.py": hashes["physical.py"]}, mode="census",
                    parameters=dict(biology=dict(loss_h=.001)), case=dict(case_id="case", epsilon=.01, years=100000.,
                    fraction=0., configuration="none", dispersal_yr=0., direction="A_into_M", loss_h=.001,
                    switching_factor=10., ramp="cubic"),
                    census=dict(minimum_cells=1., census_yr=10., cell_mass_gdw=3e-13, surface_cm2=5.1e18))
    census = dict(protocol=protocol, summary=dict(culls_bulk_a=0),
                  fingerprint=a.sha256(a.e.dumps(protocol).encode()).hexdigest())
    prefix = deepcopy(census)
    prefix["protocol"].update(source_sha256=hashes, mode="uncensored", solver="nonfinite_stage_trial_rejection",
                              architecture="arm64", operating_system="Darwin")
    prefix["protocol"]["case"]["years"] = 30000.
    prefix["protocol"]["census"].update(minimum_cells=0., census_yr=1.)
    return prefix, census


def test_declared_guarded_prefix_superset_and_exact_unculled_census_are_accepted(tmp_path, monkeypatch):
    prefix, census = profile_contract(tmp_path, monkeypatch)
    assert a.validate_probability_protocol(prefix, census, tmp_path) == "guarded_uncensored_unchanged_physics"
    assert a.validate_probability_protocol(census, census, tmp_path) == "exact_source_graph"
    census["summary"]["culls_bulk_a"] = 1
    with pytest.raises(RuntimeError, match="unculled"):
        a.validate_probability_protocol(census, census, tmp_path)


def test_native_source_graph_does_not_hide_an_undeclared_uncensored_solver(tmp_path, monkeypatch):
    prefix, census = profile_contract(tmp_path, monkeypatch)
    prefix["protocol"]["source_sha256"] = dict(census["protocol"]["source_sha256"])
    del prefix["protocol"]["solver"]
    with pytest.raises(RuntimeError, match="guarded source superset"):
        a.validate_probability_protocol(prefix, census, tmp_path)


@pytest.mark.parametrize("jacobian", (False, True))
def test_probability_rows_consume_receipted_guarded_superset(tmp_path, monkeypatch, jacobian):
    prefix, census = profile_contract(tmp_path, monkeypatch)
    if jacobian:
        prefix = jacobian_prefix(prefix, census, tmp_path)
        census = guarded_census(prefix, census)
    monkeypatch.setattr(a.e, "ROOT", tmp_path)
    payload = tmp_path/"guarded.npz"; payload.write_bytes(b"payload hash is checked; arrays are loaded later")
    digest = a.sha256(payload.read_bytes()).hexdigest()
    prefix.update(execution_status="complete", raw_sha256=digest,
                  fingerprint=a.sha256(a.e.dumps(prefix["protocol"]).encode()).hexdigest())
    payload.with_suffix(".receipt.json").write_text(a.e.dumps(prefix))
    rows = [prefix["protocol"]["case"]|dict(guild=g, source_raw_file=payload.name, source_raw_sha256=digest,
                                           census_fingerprint=census["fingerprint"])
            for g in ("a", "m")]
    path = tmp_path/"first_survival.json"; path.write_text(a.e.dumps(rows))
    accepted = a.probability_rows(path, {"case": census}, tmp_path, {"case": prefix})
    assert len(accepted) == 2
    expected = "analytic_jacobian_uncensored_unchanged_physics" if jacobian else "guarded_uncensored_unchanged_physics"
    assert all(v["numerical_profile_contract"] == expected for v in accepted.values())
    rows[0]["census_fingerprint"] = "superseded-census-receipt"
    path.write_text(a.e.dumps(rows))
    with pytest.raises(RuntimeError, match="census baseline differs"):
        a.probability_rows(path, {"case": census}, tmp_path, {"case": prefix})
    rows[0]["census_fingerprint"] = census["fingerprint"]
    path.write_text(a.e.dumps(rows))
    with pytest.raises(RuntimeError, match="uncensored profile is not the selected"):
        a.probability_rows(path, {"case": census}, tmp_path,
                           {"case": dict(fingerprint="a-newer-selected-prefix")})


@pytest.mark.parametrize("changed", ("physical_hash", "unexpected_extra", "parameters", "solver_flag", "new_file_hash", "count_convention", "censoring"))
def test_guarded_prefix_rejects_undeclared_physical_or_numerical_changes(tmp_path, monkeypatch, changed):
    prefix, census = profile_contract(tmp_path, monkeypatch)
    if changed == "physical_hash":
        prefix["protocol"]["source_sha256"]["physical.py"] = "changed"
    elif changed == "unexpected_extra":
        prefix["protocol"]["source_sha256"]["unexpected.py"] = "extra"
    elif changed == "parameters":
        prefix["protocol"]["parameters"]["biology"]["loss_h"] = .002
    elif changed == "solver_flag":
        del prefix["protocol"]["solver"]
    elif changed == "new_file_hash":
        (tmp_path/sorted(a.GUARDED_PREFIX_SOURCES)[0]).write_text("different")
    elif changed == "count_convention":
        prefix["protocol"]["census"]["cell_mass_gdw"] = 1e-13
    else:
        prefix["protocol"]["census"]["minimum_cells"] = 1.
    with pytest.raises(RuntimeError):
        a.validate_probability_protocol(prefix, census, tmp_path)


def guarded_census(prefix, census):
    guarded = deepcopy(prefix)
    guarded["protocol"].update(mode="census", case=deepcopy(census["protocol"]["case"]),
                               census=deepcopy(census["protocol"]["census"]))
    guarded["fingerprint"] = a.sha256(a.e.dumps(guarded["protocol"]).encode()).hexdigest()
    return guarded


def jacobian_prefix(prefix, native, root):
    jacobian = deepcopy(prefix)
    sources = dict(native["protocol"]["source_sha256"])
    for name in a.JACOBIAN_SOURCES:
        path = root/name
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(name)
        sources[name] = a.sha256(path.read_bytes()).hexdigest()
    jacobian["protocol"].update(source_sha256=sources, solver="analytic_dormancy_switching_jacobian")
    jacobian["fingerprint"] = a.sha256(a.e.dumps(jacobian["protocol"]).encode()).hexdigest()
    return jacobian


def test_exact_jacobian_source_variant_accepts_both_modes_and_cross_variant_baseline(tmp_path, monkeypatch):
    guard, native = profile_contract(tmp_path, monkeypatch)
    jacobian = jacobian_prefix(guard, native, tmp_path)
    census = guarded_census(jacobian, native)
    assert a.validate_probability_protocol(jacobian, native, tmp_path) == "analytic_jacobian_uncensored_unchanged_physics"
    assert a.validate_probability_protocol(jacobian, census, tmp_path) == "analytic_jacobian_uncensored_unchanged_physics"
    assert a.validate_probability_protocol(census, census, tmp_path) == "analytic_jacobian_census_unchanged_physics"
    assert a.validate_probability_protocol(guard, census, tmp_path) == "guarded_uncensored_unchanged_physics"
    assert a.validate_probability_protocol(jacobian, guarded_census(guard, native), tmp_path) == "analytic_jacobian_uncensored_unchanged_physics"


@pytest.mark.parametrize("changed", ("missing_trial", "missing_runner", "old_prefix_extra", "old_flag", "new_flag_old_set", "mixed_partial_set", "provenance", "new_file_hash"))
def test_jacobian_declaration_rejects_partial_mixed_or_unverified_sources(tmp_path, monkeypatch, changed):
    guard, native = profile_contract(tmp_path, monkeypatch)
    jacobian = jacobian_prefix(guard, native, tmp_path)
    sources = jacobian["protocol"]["source_sha256"]
    old_runner = "src/terra_prisca/haze_world/dormancy_prefixes.py"
    new_runner = "src/terra_prisca/haze_world/dormancy_jacobian_experiments.py"
    new_helper = "src/terra_prisca/haze_world/dormancy_jacobian_integration.py"
    trial = "src/terra_prisca/haze_world/dormancy_trial_integration.py"
    if changed == "missing_trial":
        del sources[trial]
    elif changed == "missing_runner":
        del sources[new_runner]
    elif changed == "old_prefix_extra":
        sources[old_runner] = guard["protocol"]["source_sha256"][old_runner]
    elif changed == "old_flag":
        jacobian["protocol"]["solver"] = "nonfinite_stage_trial_rejection"
    elif changed == "new_flag_old_set":
        jacobian["protocol"]["source_sha256"] = dict(guard["protocol"]["source_sha256"])
    elif changed == "mixed_partial_set":
        del sources[new_helper]
        sources[old_runner] = guard["protocol"]["source_sha256"][old_runner]
    elif changed == "provenance":
        del jacobian["protocol"]["operating_system"]
    else:
        (tmp_path/new_helper).write_text("changed")
    with pytest.raises(RuntimeError):
        a.validate_probability_protocol(jacobian, native, tmp_path)


def progress_prefix(prefix, native, root):
    progress = deepcopy(prefix)
    sources = dict(native["protocol"]["source_sha256"])
    for name in a.PROGRESS_SOURCES:
        path = root/name
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(name)
        sources[name] = a.sha256(path.read_bytes()).hexdigest()
    progress["protocol"].update(source_sha256=sources, solver="analytic_dormancy_jacobian_progress_restart")
    progress["fingerprint"] = a.sha256(a.e.dumps(progress["protocol"]).encode()).hexdigest()
    return progress


def test_exact_progress_restart_variant_accepts_census_and_uncensored_modes(tmp_path, monkeypatch):
    guard, native = profile_contract(tmp_path, monkeypatch)
    progress = progress_prefix(guard, native, tmp_path)
    census = guarded_census(progress, native)
    assert a.validate_probability_protocol(progress, native, tmp_path) == "analytic_jacobian_progress_restart_uncensored_unchanged_physics"
    assert a.validate_probability_protocol(progress, census, tmp_path) == "analytic_jacobian_progress_restart_uncensored_unchanged_physics"
    assert a.validate_probability_protocol(census, census, tmp_path) == "analytic_jacobian_progress_restart_census_unchanged_physics"


@pytest.mark.parametrize("changed", ("missing_parent_helper", "missing_progress_helper", "missing_runner", "mixed_partial_set", "wrong_solver", "new_file_hash"))
def test_progress_restart_rejects_partial_mixed_or_unverified_sources(tmp_path, monkeypatch, changed):
    guard, native = profile_contract(tmp_path, monkeypatch)
    progress = progress_prefix(guard, native, tmp_path)
    sources = progress["protocol"]["source_sha256"]
    parent = "src/terra_prisca/haze_world/dormancy_jacobian_integration.py"
    helper = "src/terra_prisca/haze_world/dormancy_progress_integration.py"
    runner = "src/terra_prisca/haze_world/dormancy_progress_experiments.py"
    if changed == "missing_parent_helper":
        del sources[parent]
    elif changed == "missing_progress_helper":
        del sources[helper]
    elif changed == "missing_runner":
        del sources[runner]
    elif changed == "mixed_partial_set":
        del sources[runner]
        sources["src/terra_prisca/haze_world/dormancy_jacobian_experiments.py"] = "wrong-runner"
    elif changed == "wrong_solver":
        progress["protocol"]["solver"] = "analytic_dormancy_switching_jacobian"
    else:
        (tmp_path/helper).write_text("changed")
    with pytest.raises(RuntimeError):
        a.validate_probability_protocol(progress, native, tmp_path)


def chemical_prefix(prefix, native, root):
    chemical = deepcopy(prefix)
    sources = dict(native["protocol"]["source_sha256"])
    for name in a.CHEMICAL_SOURCES:
        path = root/name
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(name)
        sources[name] = a.sha256(path.read_bytes()).hexdigest()
    chemical["protocol"].update(source_sha256=sources, solver="analytic_dormancy_chemical_jacobian")
    chemical["fingerprint"] = a.sha256(a.e.dumps(chemical["protocol"]).encode()).hexdigest()
    return chemical


def test_exact_chemical_jacobian_variant_accepts_census_and_uncensored_modes(tmp_path, monkeypatch):
    guard, native = profile_contract(tmp_path, monkeypatch)
    chemical = chemical_prefix(guard, native, tmp_path)
    census = guarded_census(chemical, native)
    assert a.validate_probability_protocol(chemical, native, tmp_path) == "analytic_chemical_jacobian_uncensored_unchanged_physics"
    assert a.validate_probability_protocol(chemical, census, tmp_path) == "analytic_chemical_jacobian_uncensored_unchanged_physics"
    assert a.validate_probability_protocol(census, census, tmp_path) == "analytic_chemical_jacobian_census_unchanged_physics"


@pytest.mark.parametrize("changed", ("missing_parent_helper", "missing_chemical_helper", "missing_runner", "mixed_partial_set", "wrong_solver", "new_file_hash"))
def test_chemical_jacobian_rejects_partial_mixed_or_unverified_sources(tmp_path, monkeypatch, changed):
    guard, native = profile_contract(tmp_path, monkeypatch)
    chemical = chemical_prefix(guard, native, tmp_path)
    sources = chemical["protocol"]["source_sha256"]
    parent = "src/terra_prisca/haze_world/dormancy_progress_integration.py"
    helper = "src/terra_prisca/haze_world/dormancy_chemical_integration.py"
    runner = "src/terra_prisca/haze_world/dormancy_chemical_experiments.py"
    if changed == "missing_parent_helper":
        del sources[parent]
    elif changed == "missing_chemical_helper":
        del sources[helper]
    elif changed == "missing_runner":
        del sources[runner]
    elif changed == "mixed_partial_set":
        del sources[runner]
        sources["src/terra_prisca/haze_world/dormancy_progress_experiments.py"] = "wrong-runner"
    elif changed == "wrong_solver":
        chemical["protocol"]["solver"] = "analytic_dormancy_jacobian_progress_restart"
    else:
        (tmp_path/helper).write_text("changed")
    with pytest.raises(RuntimeError):
        a.validate_probability_protocol(chemical, native, tmp_path)


def test_guarded_baseline_and_guarded_unculled_census_reuse_share_native_physics(tmp_path, monkeypatch):
    prefix, native = profile_contract(tmp_path, monkeypatch)
    census = guarded_census(prefix, native)
    assert a.validate_probability_protocol(prefix, census, tmp_path) == "guarded_uncensored_unchanged_physics"
    assert a.validate_probability_protocol(census, census, tmp_path) == "guarded_census_unchanged_physics"
    with pytest.raises(RuntimeError, match="not the selected receipt"):
        a.validate_probability_protocol(native, census, tmp_path)
    census["summary"]["culls_bulk_a"] = 1
    assert a.validate_probability_protocol(prefix, census, tmp_path) == "guarded_uncensored_unchanged_physics"
    with pytest.raises(RuntimeError, match="unculled"):
        a.validate_probability_protocol(census, census, tmp_path)


@pytest.mark.parametrize("changed", ("physical_hash", "unexpected_extra", "solver_flag", "provenance", "census_process", "new_file_hash"))
def test_guarded_census_is_independently_validated_against_native_freeze(tmp_path, monkeypatch, changed):
    prefix, native = profile_contract(tmp_path, monkeypatch)
    census = guarded_census(prefix, native)
    if changed == "physical_hash":
        census["protocol"]["source_sha256"]["physical.py"] = "same-but-wrong"
        prefix["protocol"]["source_sha256"]["physical.py"] = "same-but-wrong"
    elif changed == "unexpected_extra":
        census["protocol"]["source_sha256"]["unexpected.py"] = "extra"
    elif changed == "solver_flag":
        del census["protocol"]["solver"]
    elif changed == "provenance":
        del census["protocol"]["architecture"]
    elif changed == "census_process":
        census["protocol"]["census"]["census_yr"] = 1.
    else:
        (tmp_path/sorted(a.GUARDED_PREFIX_SOURCES)[0]).write_text("different")
    with pytest.raises(RuntimeError):
        a.validate_probability_protocol(prefix, census, tmp_path)


def test_current_selection_plan_must_match_both_derived_manifests(tmp_path):
    assert a.validate_selection_manifest(dict(receipt_selection_sha256=None), tmp_path) is None
    path = tmp_path/"receipt_selection.json"
    path.write_text(json.dumps(dict(schema="turnover_dormancy_receipt_selection_v1",
                                   selections=dict(census=dict(case="selected-fingerprint")))))
    digest = a.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(RuntimeError, match="selection differs"):
        a.validate_selection_manifest(dict(receipt_selection_sha256=None), tmp_path)
    assert a.validate_selection_manifest(dict(receipt_selection_sha256=digest), tmp_path) == digest
    path.write_text(path.read_text().replace("selected-fingerprint", "another-fingerprint"))
    with pytest.raises(RuntimeError, match="selection differs"):
        a.validate_selection_manifest(dict(receipt_selection_sha256=digest), tmp_path)


def kd1_comparison(**changes):
    return dict(dormancy_horizon_yr=100000., reference_horizon_yr=100000.,
                dormancy_terminal_time_yr=100000., reference_terminal_time_yr=100000.,
                both_stationary=False, same_global_occupancy=True, same_local_occupancy=True,
                temperature_difference_k=0., maximum_relative_stock_difference=.2, same_endpoint=False)|changes


def test_nonstationary_matched_100k_state_refutes_literal_clause():
    result = a.kd1_endpoint_clauses([kd1_comparison()])
    assert result["literal_100k_clause_status"] == "refuted"
    assert result["asymptotic_endpoint_clause_status"] == "unresolved"
    assert result["literal_100k_verified_comparisons"] == 1
    assert result["no_reference_removal_endpoint_comparisons"][0]["literal_100k_agreement"] is False


@pytest.mark.parametrize("changed", ("dormancy_horizon_yr", "reference_horizon_yr", "dormancy_terminal_time_yr", "reference_terminal_time_yr"))
def test_declared_and_actual_horizons_are_all_required_for_literal_refutation(changed):
    row = kd1_comparison(**{changed: 200000.})
    result = a.kd1_endpoint_clauses([row])
    assert result["literal_100k_clause_status"] == "unresolved"
    assert result["literal_100k_verified_comparisons"] == 0
    assert result["no_reference_removal_endpoint_comparisons"][0]["literal_100k_agreement"] is None


def test_stationary_extended_difference_does_not_masquerade_as_literal_100k():
    row = kd1_comparison(dormancy_horizon_yr=200000., dormancy_terminal_time_yr=200000., both_stationary=True)
    result = a.kd1_endpoint_clauses([row])
    assert result["literal_100k_clause_status"] == "unresolved"
    assert result["asymptotic_endpoint_clause_status"] == "refuted"


def test_finite_agreement_does_not_require_stationarity_but_does_require_local_occupancy():
    row = kd1_comparison(maximum_relative_stock_difference=0.)
    result = a.kd1_endpoint_clauses([row])
    assert result["literal_100k_clause_status"] == "supported_verified_100k_comparisons"
    assert result["asymptotic_endpoint_clause_status"] == "unresolved"
    result = a.kd1_endpoint_clauses([row|dict(same_local_occupancy=False)])
    assert result["literal_100k_clause_status"] == "refuted"
