import json
from dataclasses import replace
from copy import deepcopy

import pytest

from terra_prisca.haze_world.finite_experiments import (
    Case, clean, design, initial_state, parameters, run_case,
)


def test_full_design_and_constant_fraction_initial_protocol():
    cases = design()
    assert len(cases) == 144 and len({c.case_id for c in cases}) == 144
    for case in cases:
        p, process = parameters(case)
        assert p.acetate_fraction == case.fraction
        assert process.immigration_cells_yr == (case.minimum_cells * case.relative_immigration_yr,) * 2
    p, _ = parameters(cases[0])
    assert all(parameters(c)[0].habitat_l_cm2 == p.habitat_l_cm2 for c in cases)
    assert all(parameters(c)[0].biology.exchange_mol_l_h_pa == p.biology.exchange_mol_l_h_pa for c in cases)


def test_both_invasion_directions_seed_the_absent_guild():
    forward = Case("forward", "products", .5, 1., 0., "A_into_M")
    reverse = replace(forward, case_id="reverse", direction="M_into_A")
    assert initial_state(forward)[1] == 1e-12
    assert initial_state(reverse)[2] == 1e-12
    assert initial_state(forward)[2] > 1e-6
    assert initial_state(reverse)[1] > 1e-6


def test_case_receipt_reuses_verified_raw_data_and_detects_corruption(tmp_path):
    case = Case("short", "fixed", .5, 1., 0., "A_into_M", years=10.)
    first = run_case(case, tmp_path)
    second = run_case(case, tmp_path)
    assert first["fingerprint"] == second["fingerprint"]
    assert first["summary"]["settling_status"] == "pilot_only"
    data = tmp_path / first["raw_file"]
    data.write_bytes(data.read_bytes() + b"corruption")
    with pytest.raises(RuntimeError, match="Receipt/data mismatch"):
        run_case(case, tmp_path)


def test_strict_json_preserves_unavailable_status():
    result = clean(dict(value=float("nan"), status="not_available"))
    assert json.loads(json.dumps(result, allow_nan=False)) == dict(value=None, status="not_available")


def test_trace_immigrants_do_not_become_a_functional_mixture(tmp_path):
    from terra_prisca.haze_world.finite_analysis import functional_record
    case = Case("sink", "fixed", .9, 1., 100., "M_into_A", years=1000.)
    receipt = run_case(case, tmp_path)
    row = functional_record(receipt, receipt, tmp_path / receipt["raw_file"])
    assert row["census_occupancy_label"] == "both_retained"
    assert row["catabolic_share_m"] < 1e-12
    assert row["instantaneous_functional_role"] == "acetogen_dominated"
    assert row["immigration_supported_sink_m"]
    assert row["attained_functional_role"] == "unsettled"


def test_later_horizon_is_selected_without_cherry_picking_or_changing_protocol(tmp_path):
    from terra_prisca.haze_world.finite_analysis import choose_runs, key
    case = Case("short", "fixed", .5, 1., 0., "A_into_M", years=10.)
    first = run_case(case, tmp_path)
    later = deepcopy(first)
    later["summary"].update(case_id="longer", years=20., settling_status="unsettled")
    later["protocol"]["case"].update(case_id="longer", years=20.)
    selected = choose_runs([(first, "original")], [(later, "extended")])
    assert selected[key(first["summary"])][0] is later
    assert first["summary"]["years"] == 10.
    changed = deepcopy(later)
    changed["protocol"]["parameters"]["climate"]["t_zero_k"] += 1.
    with pytest.raises(RuntimeError, match="changed more than"):
        choose_runs([(first, "original")], [(changed, "changed")])
