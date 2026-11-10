from copy import deepcopy

import pytest

from terra_prisca.haze_world.refuge_reporting import choose_extensions, direction_pairs


def test_extension_selection_retains_later_unsettled_result_and_rejects_changed_physics():
    original = dict(protocol=dict(case=dict(case_id="base", years=100000., fraction=.5),
                                  parameters=dict(contrast_k=8.6)),
                    summary=dict(settling_status="census_stationary"))
    later = deepcopy(original)
    later["protocol"]["case"].update(case_id="later", years=200000.)
    later["summary"]["settling_status"] = "unsettled"
    selected = choose_extensions([original], [later])
    assert list(selected.values()) == [later]
    assert original["protocol"]["case"]["years"] == 100000.
    changed = deepcopy(later)
    changed["protocol"]["parameters"]["contrast_k"] = 8.7
    with pytest.raises(RuntimeError, match="changed more than"):
        choose_extensions([original], [changed])


def test_direction_match_requires_community_stocks_not_temperature_alone():
    common = dict(case_id="first", fraction=.5, warm_fraction=.5, contrast_k=0., dispersal_yr=.001,
                  direction="A_into_M", activity="fixed", seed_origin="both", census_yr=10., years=100000.,
                  settling_status="census_stationary", attempt_status="completed", base_case_id="first",
                  endpoint_class="spatial_coexistence",
                  global_temperature_k=281.5, methane_ratio=.195,
                  pressure_cold_pa=30., pressure_warm_pa=30., acetate_cold_mol_l=.001, acetate_warm_mol_l=.001,
                  cells_cold_a=1e25, cells_cold_m=1e25, cells_warm_a=1e25, cells_warm_m=1e25,
                  occupancy_cold="both", occupancy_warm="both")
    second = dict(common, case_id="second", base_case_id="second", direction="M_into_A")
    assert direction_pairs([common, second])[0]["matching_endpoint"]
    second.update(cells_cold_m=0., occupancy_cold="acetogen")
    comparison = direction_pairs([common, second])[0]
    assert comparison["global_temperature_difference_k"] == 0.
    assert not comparison["matching_endpoint"]
