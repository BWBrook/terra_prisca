import json
from dataclasses import replace

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
