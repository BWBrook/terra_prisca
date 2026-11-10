import json
from copy import deepcopy
from dataclasses import asdict, replace

import numpy as np
import pytest

from terra_prisca.haze_world import dormancy_assessment as a


def kd5_profile(case_id="dormancy_0125"):
    case = next(case for case in a.runner.design() if case.case_id == case_id)
    p = a.runner.parameters(case)
    record = dict(execution_status="complete", protocol=dict(case=asdict(case), mode="census",
        census=asdict(a.runner.Census())), summary=dict(settling_status="unsettled", endpoint_class=None))
    values = np.zeros((p.state_size, 3))
    values[1] = 1e-3
    values[2, 0], values[5, 0] = 1e-12, 1e-13
    active = np.full((p.n_patches, 2, 3), -np.inf)
    dormant = active.copy()
    active[0, 0] = np.log(values[1])
    active[0, 1, 0], dormant[0, 1, 0] = np.log(1e-12), np.log(1e-13)
    conversion = np.log(p.coupled.habitat_l_cm2*5.1e18/3e-13)
    profile = dict(t=np.array([0., 10., 100000.]), y=values, log_active=active, log_dormant=dormant,
        log_biomass=np.logaddexp(active, dormant),
        metadata=dict(external_immigration="none", global_log_cell_conversion=conversion),
        extinction_events=np.array(json.dumps([dict(time_yr=10., patch="bulk", guild="methanogen")])) )
    return record, profile


def test_kd5_exact_absorbing_exclusion_does_not_relabel_slow_resident_tails(monkeypatch):
    records, profiles = {}, {}
    for key in ("dormancy_0125", "dormancy_0127"):
        records[key], profiles[key] = kd5_profile(key)
    monkeypatch.setattr(a.survival, "load", lambda record, raw: profiles[record["protocol"]["case"]["case_id"]])
    monkeypatch.setattr(a, "probability_points", lambda *args: [])
    result = a.assess(records, {}, [], None, [])
    assert result["KD5"]["status"] == "supported_finite_dose_exclusion"
    assert result["KD5"]["stationary_endpoint_clause_status"] == "unresolved"
    assert result["stationary_counts"] == {"unsettled": 2}
    for row in result["KD5"]["finite_dose_cases"]:
        assert not row["stationary"] and row["endpoint"] is None
        assert row["methanogen_invasion_stays_acetogen"] is True
        evidence = row["finite_dose_exclusion_evidence"]
        assert evidence["verified_absorbing_methanogen_exclusion"]
        assert evidence["global_methanogen_removal_yr"] == 10.


def test_kd5_float_zero_with_a_retained_dormant_log_is_not_global_extinction(monkeypatch):
    record, data = kd5_profile()
    data["log_dormant"][0, 1, -1] = -1000.
    data["log_biomass"] = np.logaddexp(data["log_active"], data["log_dormant"])
    monkeypatch.setattr(a.survival, "load", lambda *args: data)
    row = a.kd5_case(record, None)
    assert data["y"][5, -1] == 0.
    assert not row["finite_dose_exclusion_evidence"]["both_stages_absent_after_global_loss"]
    assert row["finite_dose_exclusion_evidence"]["closed_absence_reversed"]
    assert row["methanogen_invasion_stays_acetogen"] is None


@pytest.mark.parametrize("change", ("immigration", "no_removal_event", "no_initial_dose", "uncensored", "short_horizon"))
def test_kd5_absorbing_gate_requires_the_logged_closed_census_protocol(monkeypatch, change):
    record, data = kd5_profile()
    if change == "immigration":
        data["metadata"]["external_immigration"] = "positive"
    elif change == "no_removal_event":
        data["extinction_events"] = np.array("[]")
    elif change == "no_initial_dose":
        data["y"][[2, 5], 0] = 0.
        data["log_active"][0, 1, 0] = data["log_dormant"][0, 1, 0] = -np.inf
        data["log_biomass"] = np.logaddexp(data["log_active"], data["log_dormant"])
    elif change == "uncensored":
        record["protocol"]["mode"] = "uncensored"
    else:
        record["protocol"]["case"]["years"] = 30000.
        data["t"][-1] = 30000.
    monkeypatch.setattr(a.survival, "load", lambda *args: data)
    row = a.kd5_case(record, None)
    assert not row["finite_dose_exclusion_evidence"]["verified_absorbing_methanogen_exclusion"]
    assert row["methanogen_invasion_stays_acetogen"] is None


def test_kd5_methanogen_exclusion_alone_does_not_prove_acetogen_bulk(monkeypatch):
    record, data = kd5_profile()
    data["y"][1, -1] = 0.
    data["log_active"][0, 0, -1] = -np.inf
    data["log_biomass"] = np.logaddexp(data["log_active"], data["log_dormant"])
    monkeypatch.setattr(a.survival, "load", lambda *args: data)
    row = a.kd5_case(record, None)
    assert row["finite_dose_exclusion_evidence"]["verified_absorbing_methanogen_exclusion"]
    assert not row["finite_dose_exclusion_evidence"]["observed_final_bulk_acetogen_present"]
    assert row["methanogen_invasion_stays_acetogen"] is None


def test_kd5_requires_both_prescribed_doses_and_retains_a_stationary_counterexample(monkeypatch):
    record, data = kd5_profile()
    monkeypatch.setattr(a.survival, "load", lambda *args: data)
    row = a.kd5_case(record, None)
    assert a.kd5_clauses([row, row])["status"] == "unresolved"
    record["summary"].update(settling_status="census_stationary", endpoint_class="methanogen_only")
    data["y"][2] = 1e-3
    data["y"][1, 1:] = 0.
    data["log_active"][0, 1] = np.log(1e-3)
    data["log_active"][0, 0, 1:] = -np.inf
    data["log_biomass"] = np.logaddexp(data["log_active"], data["log_dormant"])
    data["extinction_events"] = np.array("[]")
    row = a.kd5_case(record, None)
    assert row["methanogen_invasion_stays_acetogen"] is False
    assert a.kd5_clauses([row])["status"] == "refuted_finite_dose"


def refinement_profiles(monkeypatch):
    parent = a.runner.design()[0]
    child = replace(parent, case_id=parent.case_id+"_eps0.006", epsilon=.006, years=3000.)
    def receipt(case):
        return json.loads(a.e.dumps(dict(execution_status="complete",
            protocol=dict(case=asdict(case), mode="census", parameters=asdict(a.runner.parameters(case))),
            summary=dict(terminal_time_yr=case.years, settling_status="pilot_only" if case.years<100000 else "census_stationary"))))
    monkeypatch.setattr(a.runner, "design", lambda: [parent])
    return parent, child, {parent.case_id: receipt(parent), child.case_id: receipt(child)}


def test_short_refinement_is_separate_from_complete_planned_endpoints(monkeypatch):
    parent, child, records = refinement_profiles(monkeypatch)
    before = deepcopy(records)
    planned, refinements = a.assessment_records(records)
    assert set(planned) == {parent.case_id} and set(refinements) == {child.case_id}
    assert planned[parent.case_id]["assessment_role"] == "planned_100k"
    assert refinements[child.case_id]["assessment_role"] == "first_window_refinement_only"
    assert refinements[child.case_id]["refinement_parent_case_id"] == parent.case_id
    assert records == before


@pytest.mark.parametrize("actual", (3000., 99999.))
def test_a_short_planned_profile_cannot_be_replaced_by_a_refinement(monkeypatch, actual):
    parent, child, records = refinement_profiles(monkeypatch)
    records[parent.case_id]["summary"]["terminal_time_yr"] = actual
    with pytest.raises(RuntimeError, match="full planned T3 horizon"):
        a.assessment_records(records)


@pytest.mark.parametrize("change", ("loss_h", "fraction", "switching_factor", "parameters", "parent"))
def test_refinements_require_the_parent_scientific_design_except_epsilon_and_id(monkeypatch, change):
    parent, child, records = refinement_profiles(monkeypatch)
    record = records[child.case_id]
    if change == "parameters":
        record["protocol"]["parameters"]["epsilon"] = .1
    elif change == "parent":
        records["unknown_eps0.006"] = records.pop(child.case_id)
    else:
        record["protocol"]["case"][change] = {"loss_h": .002, "fraction": .5, "switching_factor": 1.}[change]
    with pytest.raises(RuntimeError, match="Refinement"):
        a.assessment_records(records)


def refinement_window():
    census = dict(protocol=dict(mode="census", case=dict(years=3000.)))
    prefix = dict(protocol=dict(mode="uncensored", case=dict(years=3000.)))
    row = dict(rare_window=True, terminal_window=False, window_status="first_minimum_linear",
               start_yr=100., minimum_time_yr=900., end_yr=2000.)
    return row, prefix, census


def test_matching_short_refinement_requires_a_closed_linear_first_window(monkeypatch):
    row, prefix, census = refinement_window()
    monkeypatch.setattr(a.survival, "load", lambda *args: dict(t=np.array([0., 3000.])))
    assert a.validate_refinement_window(row, prefix, census, None) == "matching_short_horizons_closed_first_resident_window"


@pytest.mark.parametrize("change", ("terminal", "nonlinear", "boundary", "mismatched_horizons", "actual_horizon", "censored_prefix"))
def test_short_refinement_does_not_supply_an_unresolved_or_mismatched_crossing(monkeypatch, change):
    row, prefix, census = refinement_window()
    actual = 3000.
    if change == "terminal": row["terminal_window"] = True
    elif change == "nonlinear": row["rare_window"] = False
    elif change == "boundary": row["end_yr"] = 3000.
    elif change == "mismatched_horizons": prefix["protocol"]["case"]["years"] = 5000.
    elif change == "actual_horizon": actual = 2999.
    else: prefix["protocol"]["mode"] = "census"
    monkeypatch.setattr(a.survival, "load", lambda *args: dict(t=np.array([0., actual])))
    with pytest.raises(RuntimeError):
        a.validate_refinement_window(row, prefix, census, None)


def test_existing_full_horizon_refinement_keeps_its_terminal_bound_contract():
    row, prefix, census = refinement_window()
    census["protocol"]["case"]["years"] = 100000.
    row["terminal_window"] = True
    assert a.validate_refinement_window(row, prefix, census, None) == "full_horizon_refinement_first_window_evidence"


def test_refinement_probability_has_no_long_horizon_macroscopic_protection_claim():
    case = dict(configuration="none", loss_h=.001, fraction=0., direction="A_into_M", switching_factor=10., ramp="cubic", epsilon=.006, years=3000.)
    record = dict(protocol=dict(case=case), assessment_role="first_window_refinement_only",
        refinement_parent_case_id="dormancy_0000", summary=dict(global_pre_extinction_min_log_cells_m=np.log(1e20),
        global_pre_extinction_min_zero_m=False, global_present_m=True))
    row = dict(rare_window=True, terminal_window=False, log_lambda=1., survival_probability=.9,
        window_status="first_minimum_linear", classification="contingent", minimum_time_yr=900., end_yr=2000., log_min_cells=20.)
    point = a.probability_points({"refinement": record}, {("refinement", "m"): row}, 0., "A_into_M", 10.)[0]
    assert point["eligible"] and not point["macroscopic_protection"]
    assert point["evidence_scope"] == "first_window_refinement_only"


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


def test_probability_reader_labels_closed_short_refinement_without_changing_its_score(tmp_path, monkeypatch):
    prefix, census = profile_contract(tmp_path, monkeypatch)
    for record in (prefix, census):
        record["protocol"]["case"]["years"] = 3000.
        record["fingerprint"] = a.sha256(a.e.dumps(record["protocol"]).encode()).hexdigest()
    census["assessment_role"] = "first_window_refinement_only"
    monkeypatch.setattr(a.e, "ROOT", tmp_path)
    monkeypatch.setattr(a.survival, "load", lambda *args: dict(t=np.array([0., 3000.])))
    payload = tmp_path/"short.npz"; payload.write_bytes(b"separately hashed short refinement")
    digest = a.sha256(payload.read_bytes()).hexdigest()
    prefix.update(execution_status="complete", raw_sha256=digest)
    payload.with_suffix(".receipt.json").write_text(a.e.dumps(prefix))
    rows = [prefix["protocol"]["case"]|dict(guild=g, source_raw_file=payload.name, source_raw_sha256=digest,
        census_fingerprint=census["fingerprint"], rare_window=True, terminal_window=False,
        window_status="first_minimum_linear", start_yr=100., minimum_time_yr=900., end_yr=2000., survival_probability=.7869)
        for g in ("a", "m")]
    path = tmp_path/"first_survival.json"; path.write_text(a.e.dumps(rows))
    accepted = a.probability_rows(path, {"case": census}, tmp_path, {"case": prefix})
    assert accepted[("case", "m")]["refinement_horizon_contract"] == "matching_short_horizons_closed_first_resident_window"
    assert accepted[("case", "m")]["survival_probability"] == .7869
    assert accepted[("case", "a")]["refinement_horizon_contract"] is None


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


def stage_prefix(prefix, native, root):
    stage = chemical_prefix(prefix, native, root)
    for name in a.STAGE_SOURCES-a.CHEMICAL_SOURCES:
        path = root/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(name)
        stage["protocol"]["source_sha256"][name] = a.sha256(path.read_bytes()).hexdigest()
    stage["protocol"]["solver"] = "analytic_dormancy_stage_conditioning"
    stage["fingerprint"] = a.sha256(a.e.dumps(stage["protocol"]).encode()).hexdigest()
    return stage


def test_exact_seven_file_stage_variant_accepts_both_modes_and_shared_native_physics(tmp_path, monkeypatch):
    guard, native = profile_contract(tmp_path, monkeypatch)
    stage = stage_prefix(guard, native, tmp_path)
    census = guarded_census(stage, native)
    assert len(set(stage["protocol"]["source_sha256"])-set(native["protocol"]["source_sha256"])) == 7
    assert a.validate_probability_protocol(stage, native, tmp_path) == "analytic_stage_conditioning_uncensored_unchanged_physics"
    assert a.validate_probability_protocol(stage, census, tmp_path) == "analytic_stage_conditioning_uncensored_unchanged_physics"
    assert a.validate_probability_protocol(census, census, tmp_path) == "analytic_stage_conditioning_census_unchanged_physics"


@pytest.mark.parametrize("missing", sorted(a.STAGE_SOURCES))
def test_stage_variant_rejects_each_incomplete_seven_file_source_set(tmp_path, monkeypatch, missing):
    guard, native = profile_contract(tmp_path, monkeypatch)
    stage = stage_prefix(guard, native, tmp_path)
    del stage["protocol"]["source_sha256"][missing]
    with pytest.raises(RuntimeError, match="Unapproved"):
        a.validate_probability_protocol(stage, native, tmp_path)


@pytest.mark.parametrize("changed", ("unrelated_extra", "stale_stage", "wrong_flag", "missing_platform", "parameters", "census_process"))
def test_stage_variant_retains_source_parameter_platform_and_census_contracts(tmp_path, monkeypatch, changed):
    guard, native = profile_contract(tmp_path, monkeypatch)
    stage = stage_prefix(guard, native, tmp_path)
    if changed == "unrelated_extra":
        path = tmp_path/"unrelated.py"; path.write_text("unrelated")
        stage["protocol"]["source_sha256"]["unrelated.py"] = a.sha256(path.read_bytes()).hexdigest()
    elif changed == "stale_stage":
        (tmp_path/"src/terra_prisca/haze_world/dormancy_stage_integration.py").write_text("changed")
    elif changed == "wrong_flag":
        stage["protocol"]["solver"] = "analytic_dormancy_chemical_jacobian"
    elif changed == "missing_platform":
        del stage["protocol"]["operating_system"]
    elif changed == "parameters":
        stage["protocol"]["parameters"]["biology"]["loss_h"] = .002
    else:
        stage["protocol"]["census"]["census_yr"] = 10.
    with pytest.raises(RuntimeError):
        a.validate_probability_protocol(stage, native, tmp_path)


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


def face_prefix(prefix, native, root):
    face = stage_prefix(prefix, native, root)
    for name in a.FACE_SOURCES-a.STAGE_SOURCES:
        path = root/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(name)
        face["protocol"]["source_sha256"][name] = a.sha256(path.read_bytes()).hexdigest()
    face["protocol"]["solver"] = "analytic_dormancy_zero_face_newton"
    face["fingerprint"] = a.sha256(a.e.dumps(face["protocol"]).encode()).hexdigest()
    return face


def test_exact_nine_file_face_variant_preserves_both_recording_contracts(tmp_path, monkeypatch):
    prefix, native = profile_contract(tmp_path, monkeypatch)
    face = face_prefix(prefix, native, tmp_path)
    census = guarded_census(face, native)
    assert len(set(face["protocol"]["source_sha256"])-set(native["protocol"]["source_sha256"])) == 9
    assert a.validate_probability_protocol(face, native, tmp_path) == "zero_linear_face_newton_uncensored_unchanged_physics"
    assert a.validate_probability_protocol(face, census, tmp_path) == "zero_linear_face_newton_uncensored_unchanged_physics"
    assert a.validate_probability_protocol(census, census, tmp_path) == "zero_linear_face_newton_census_unchanged_physics"


@pytest.mark.parametrize("missing", sorted(a.FACE_SOURCES))
def test_face_variant_rejects_each_incomplete_source_graph(tmp_path, monkeypatch, missing):
    prefix, native = profile_contract(tmp_path, monkeypatch)
    face = face_prefix(prefix, native, tmp_path)
    del face["protocol"]["source_sha256"][missing]
    with pytest.raises(RuntimeError, match="Unapproved"):
        a.validate_probability_protocol(face, native, tmp_path)


@pytest.mark.parametrize("changed", ("extra", "stale_helper", "flag", "platform", "parameters", "census"))
def test_face_variant_retains_all_physical_and_provenance_guards(tmp_path, monkeypatch, changed):
    prefix, native = profile_contract(tmp_path, monkeypatch)
    face = face_prefix(prefix, native, tmp_path)
    if changed == "extra":
        face["protocol"]["source_sha256"]["unrelated.py"] = "unrelated"
    elif changed == "stale_helper":
        (tmp_path/"src/terra_prisca/haze_world/dormancy_face_integration.py").write_text("changed")
    elif changed == "flag":
        face["protocol"]["solver"] = "analytic_dormancy_stage_conditioning"
    elif changed == "platform":
        del face["protocol"]["architecture"]
    elif changed == "parameters":
        face["protocol"]["parameters"]["biology"]["loss_h"] = .002
    else:
        face["protocol"]["census"]["census_yr"] = 10.
    with pytest.raises(RuntimeError):
        a.validate_probability_protocol(face, native, tmp_path)


def radau_prefix(prefix, native, root):
    radau = face_prefix(prefix, native, root)
    for name in a.RADAU_SOURCES-a.FACE_SOURCES:
        path = root/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(name)
        radau["protocol"]["source_sha256"][name] = a.sha256(path.read_bytes()).hexdigest()
    radau["protocol"]["solver"] = "radau_dormancy_positive_dense"
    radau["fingerprint"] = a.sha256(a.e.dumps(radau["protocol"]).encode()).hexdigest()
    return radau


def test_exact_eleven_file_radau_variant_preserves_both_recording_contracts(tmp_path, monkeypatch):
    prefix, native = profile_contract(tmp_path, monkeypatch)
    radau = radau_prefix(prefix, native, tmp_path)
    census = guarded_census(radau, native)
    assert len(set(radau["protocol"]["source_sha256"])-set(native["protocol"]["source_sha256"])) == 11
    assert a.validate_probability_protocol(radau, native, tmp_path) == "radau_positive_dense_uncensored_unchanged_physics"
    assert a.validate_probability_protocol(radau, census, tmp_path) == "radau_positive_dense_uncensored_unchanged_physics"
    assert a.validate_probability_protocol(census, census, tmp_path) == "radau_positive_dense_census_unchanged_physics"


@pytest.mark.parametrize("missing", sorted(a.RADAU_SOURCES))
def test_radau_variant_rejects_each_incomplete_source_graph(tmp_path, monkeypatch, missing):
    prefix, native = profile_contract(tmp_path, monkeypatch)
    radau = radau_prefix(prefix, native, tmp_path)
    del radau["protocol"]["source_sha256"][missing]
    with pytest.raises(RuntimeError, match="Unapproved"):
        a.validate_probability_protocol(radau, native, tmp_path)


@pytest.mark.parametrize("changed", ("extra", "stale_helper", "flag", "platform", "parameters", "census"))
def test_radau_variant_retains_all_physical_and_provenance_guards(tmp_path, monkeypatch, changed):
    prefix, native = profile_contract(tmp_path, monkeypatch)
    radau = radau_prefix(prefix, native, tmp_path)
    if changed == "extra":
        radau["protocol"]["source_sha256"]["unrelated.py"] = "unrelated"
    elif changed == "stale_helper":
        (tmp_path/"src/terra_prisca/haze_world/dormancy_radau_integration.py").write_text("changed")
    elif changed == "flag":
        radau["protocol"]["solver"] = "analytic_dormancy_zero_face_newton"
    elif changed == "platform":
        del radau["protocol"]["architecture"]
    elif changed == "parameters":
        radau["protocol"]["parameters"]["biology"]["loss_h"] = .002
    else:
        radau["protocol"]["census"]["census_yr"] = 10.
    with pytest.raises(RuntimeError):
        a.validate_probability_protocol(radau, native, tmp_path)


def conditioned_prefix(prefix, native, root):
    radau = radau_prefix(prefix, native, root)
    for name in a.CONDITIONED_SOURCES-a.RADAU_SOURCES:
        path = root/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(name)
        radau["protocol"]["source_sha256"][name] = a.sha256(path.read_bytes()).hexdigest()
    radau["protocol"]["solver"] = "radau_dormancy_tolerance_conditioning"
    radau["fingerprint"] = a.sha256(a.e.dumps(radau["protocol"]).encode()).hexdigest()
    return radau


def test_exact_thirteen_file_conditioned_variant_preserves_both_recording_contracts(tmp_path, monkeypatch):
    prefix, native = profile_contract(tmp_path, monkeypatch)
    radau = conditioned_prefix(prefix, native, tmp_path)
    census = guarded_census(radau, native)
    assert len(set(radau["protocol"]["source_sha256"])-set(native["protocol"]["source_sha256"])) == 13
    assert a.validate_probability_protocol(radau, native, tmp_path) == "radau_tolerance_conditioning_uncensored_unchanged_physics"
    assert a.validate_probability_protocol(radau, census, tmp_path) == "radau_tolerance_conditioning_uncensored_unchanged_physics"
    assert a.validate_probability_protocol(census, census, tmp_path) == "radau_tolerance_conditioning_census_unchanged_physics"


@pytest.mark.parametrize("missing", sorted(a.CONDITIONED_SOURCES))
def test_conditioned_variant_rejects_each_incomplete_source_graph(tmp_path, monkeypatch, missing):
    prefix, native = profile_contract(tmp_path, monkeypatch)
    radau = conditioned_prefix(prefix, native, tmp_path)
    del radau["protocol"]["source_sha256"][missing]
    with pytest.raises(RuntimeError, match="Unapproved"):
        a.validate_probability_protocol(radau, native, tmp_path)


@pytest.mark.parametrize("changed", ("extra", "stale_helper", "flag", "platform", "parameters", "census"))
def test_conditioned_variant_retains_all_physical_and_provenance_guards(tmp_path, monkeypatch, changed):
    prefix, native = profile_contract(tmp_path, monkeypatch)
    radau = conditioned_prefix(prefix, native, tmp_path)
    if changed == "extra":
        radau["protocol"]["source_sha256"]["unrelated.py"] = "unrelated"
    elif changed == "stale_helper":
        (tmp_path/"src/terra_prisca/haze_world/dormancy_conditioned_integration.py").write_text("changed")
    elif changed == "flag":
        radau["protocol"]["solver"] = "analytic_dormancy_zero_face_newton"
    elif changed == "platform":
        del radau["protocol"]["architecture"]
    elif changed == "parameters":
        radau["protocol"]["parameters"]["biology"]["loss_h"] = .002
    else:
        radau["protocol"]["census"]["census_yr"] = 10.
    with pytest.raises(RuntimeError):
        a.validate_probability_protocol(radau, native, tmp_path)


def terminal_prefix(prefix, native, root):
    radau = conditioned_prefix(prefix, native, root)
    for name in a.TERMINAL_SOURCES-a.CONDITIONED_SOURCES:
        path = root/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(name)
        radau["protocol"]["source_sha256"][name] = a.sha256(path.read_bytes()).hexdigest()
    radau["protocol"]["solver"] = "radau_dormancy_terminal_dense_budget"
    radau["fingerprint"] = a.sha256(a.e.dumps(radau["protocol"]).encode()).hexdigest()
    return radau


def test_exact_fifteen_file_terminal_variant_preserves_both_recording_contracts(tmp_path, monkeypatch):
    prefix, native = profile_contract(tmp_path, monkeypatch)
    radau = terminal_prefix(prefix, native, tmp_path)
    census = guarded_census(radau, native)
    assert len(set(radau["protocol"]["source_sha256"])-set(native["protocol"]["source_sha256"])) == 15
    assert a.validate_probability_protocol(radau, native, tmp_path) == "radau_terminal_dense_budget_uncensored_unchanged_physics"
    assert a.validate_probability_protocol(radau, census, tmp_path) == "radau_terminal_dense_budget_uncensored_unchanged_physics"
    assert a.validate_probability_protocol(census, census, tmp_path) == "radau_terminal_dense_budget_census_unchanged_physics"


@pytest.mark.parametrize("missing", sorted(a.TERMINAL_SOURCES))
def test_terminal_variant_rejects_each_incomplete_source_graph(tmp_path, monkeypatch, missing):
    prefix, native = profile_contract(tmp_path, monkeypatch)
    radau = terminal_prefix(prefix, native, tmp_path)
    del radau["protocol"]["source_sha256"][missing]
    with pytest.raises(RuntimeError, match="Unapproved"):
        a.validate_probability_protocol(radau, native, tmp_path)


@pytest.mark.parametrize("changed", ("extra", "stale_helper", "flag", "platform", "parameters", "census"))
def test_terminal_variant_retains_all_physical_and_provenance_guards(tmp_path, monkeypatch, changed):
    prefix, native = profile_contract(tmp_path, monkeypatch)
    radau = terminal_prefix(prefix, native, tmp_path)
    if changed == "extra":
        radau["protocol"]["source_sha256"]["unrelated.py"] = "unrelated"
    elif changed == "stale_helper":
        (tmp_path/"src/terra_prisca/haze_world/dormancy_terminal_integration.py").write_text("changed")
    elif changed == "flag":
        radau["protocol"]["solver"] = "analytic_dormancy_zero_face_newton"
    elif changed == "platform":
        del radau["protocol"]["architecture"]
    elif changed == "parameters":
        radau["protocol"]["parameters"]["biology"]["loss_h"] = .002
    else:
        radau["protocol"]["census"]["census_yr"] = 10.
    with pytest.raises(RuntimeError):
        a.validate_probability_protocol(radau, native, tmp_path)


def predictor_prefix(prefix, native, root):
    radau = conditioned_prefix(prefix, native, root)
    for name in a.PREDICTOR_SOURCES-a.CONDITIONED_SOURCES:
        path = root/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(name)
        radau["protocol"]["source_sha256"][name] = a.sha256(path.read_bytes()).hexdigest()
    radau["protocol"]["solver"] = "radau_dormancy_zero_stage_predictor"
    radau["fingerprint"] = a.sha256(a.e.dumps(radau["protocol"]).encode()).hexdigest()
    return radau


def test_exact_fifteen_file_predictor_variant_preserves_both_recording_contracts(tmp_path, monkeypatch):
    prefix, native = profile_contract(tmp_path, monkeypatch)
    radau = predictor_prefix(prefix, native, tmp_path)
    census = guarded_census(radau, native)
    assert len(set(radau["protocol"]["source_sha256"])-set(native["protocol"]["source_sha256"])) == 15
    assert a.validate_probability_protocol(radau, native, tmp_path) == "radau_zero_stage_predictor_uncensored_unchanged_physics"
    assert a.validate_probability_protocol(radau, census, tmp_path) == "radau_zero_stage_predictor_uncensored_unchanged_physics"
    assert a.validate_probability_protocol(census, census, tmp_path) == "radau_zero_stage_predictor_census_unchanged_physics"


@pytest.mark.parametrize("missing", sorted(a.PREDICTOR_SOURCES))
def test_predictor_variant_rejects_each_incomplete_source_graph(tmp_path, monkeypatch, missing):
    prefix, native = profile_contract(tmp_path, monkeypatch)
    radau = predictor_prefix(prefix, native, tmp_path)
    del radau["protocol"]["source_sha256"][missing]
    with pytest.raises(RuntimeError, match="Unapproved"):
        a.validate_probability_protocol(radau, native, tmp_path)


@pytest.mark.parametrize("changed", ("extra", "stale_helper", "flag", "platform", "parameters", "census"))
def test_predictor_variant_retains_all_physical_and_provenance_guards(tmp_path, monkeypatch, changed):
    prefix, native = profile_contract(tmp_path, monkeypatch)
    radau = predictor_prefix(prefix, native, tmp_path)
    if changed == "extra":
        radau["protocol"]["source_sha256"]["unrelated.py"] = "unrelated"
    elif changed == "stale_helper":
        (tmp_path/"src/terra_prisca/haze_world/dormancy_predictor_integration.py").write_text("changed")
    elif changed == "flag":
        radau["protocol"]["solver"] = "analytic_dormancy_zero_face_newton"
    elif changed == "platform":
        del radau["protocol"]["architecture"]
    elif changed == "parameters":
        radau["protocol"]["parameters"]["biology"]["loss_h"] = .002
    else:
        radau["protocol"]["census"]["census_yr"] = 10.
    with pytest.raises(RuntimeError):
        a.validate_probability_protocol(radau, native, tmp_path)


def roundoff_prefix(prefix, native, root):
    radau = terminal_prefix(prefix, native, root)
    for name in a.ROUNDOFF_SOURCES-a.TERMINAL_SOURCES:
        path = root/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(name)
        radau["protocol"]["source_sha256"][name] = a.sha256(path.read_bytes()).hexdigest()
    radau["protocol"]["solver"] = "radau_dormancy_roundoff_stagnation"
    radau["fingerprint"] = a.sha256(a.e.dumps(radau["protocol"]).encode()).hexdigest()
    return radau


def test_exact_nineteen_file_roundoff_variant_preserves_both_recording_contracts(tmp_path, monkeypatch):
    prefix, native = profile_contract(tmp_path, monkeypatch)
    radau = roundoff_prefix(prefix, native, tmp_path)
    census = guarded_census(radau, native)
    assert len(set(radau["protocol"]["source_sha256"])-set(native["protocol"]["source_sha256"])) == 19
    assert a.validate_probability_protocol(radau, native, tmp_path) == "radau_roundoff_stagnation_uncensored_unchanged_physics"
    assert a.validate_probability_protocol(radau, census, tmp_path) == "radau_roundoff_stagnation_uncensored_unchanged_physics"
    assert a.validate_probability_protocol(census, census, tmp_path) == "radau_roundoff_stagnation_census_unchanged_physics"


@pytest.mark.parametrize("missing", sorted(a.ROUNDOFF_SOURCES))
def test_roundoff_variant_rejects_each_incomplete_source_graph(tmp_path, monkeypatch, missing):
    prefix, native = profile_contract(tmp_path, monkeypatch)
    radau = roundoff_prefix(prefix, native, tmp_path)
    del radau["protocol"]["source_sha256"][missing]
    with pytest.raises(RuntimeError, match="Unapproved"):
        a.validate_probability_protocol(radau, native, tmp_path)


@pytest.mark.parametrize("changed", ("extra", "stale_helper", "flag", "platform", "parameters", "census"))
def test_roundoff_variant_retains_all_physical_and_provenance_guards(tmp_path, monkeypatch, changed):
    prefix, native = profile_contract(tmp_path, monkeypatch)
    radau = roundoff_prefix(prefix, native, tmp_path)
    if changed == "extra":
        radau["protocol"]["source_sha256"]["unrelated.py"] = "unrelated"
    elif changed == "stale_helper":
        (tmp_path/"src/terra_prisca/haze_world/dormancy_roundoff_integration.py").write_text("changed")
    elif changed == "flag":
        radau["protocol"]["solver"] = "analytic_dormancy_zero_face_newton"
    elif changed == "platform":
        del radau["protocol"]["architecture"]
    elif changed == "parameters":
        radau["protocol"]["parameters"]["biology"]["loss_h"] = .002
    else:
        radau["protocol"]["census"]["census_yr"] = 10.
    with pytest.raises(RuntimeError):
        a.validate_probability_protocol(radau, native, tmp_path)
