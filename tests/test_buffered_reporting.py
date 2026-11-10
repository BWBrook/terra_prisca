from copy import deepcopy

import pytest

from terra_prisca.haze_world import buffered_experiments as e
from terra_prisca.haze_world.buffered_reporting import assess_main, pairs, select


def test_extension_selection_preserves_later_unsettled_evidence():
    original=dict(protocol=dict(case=dict(case_id="main",years=100000,fraction=.5),parameters=dict(d=.001)))
    later=deepcopy(original);later["protocol"]["case"].update(case_id="later",years=200000)
    later["summary"]={"settling_status":"unsettled"}
    assert list(select([original],[later]).values())==[later]
    altered=deepcopy(later);altered["protocol"]["parameters"]["d"]=1.
    with pytest.raises(RuntimeError,match="scientific protocol"):select([original],[altered])


def test_matching_temperature_does_not_override_different_population_stocks():
    from dataclasses import asdict
    a=dict(**asdict(e.design()[24]),base_case_id="a",settling_status="census_stationary",endpoint_class="coexistence",
           global_temperature_k=281.5,final_y=[30.,.001,.001,.001]*3+[.195])
    for patch in ("bulk","warm","cold"):a["occupancy_"+patch]="both"
    m=deepcopy(a);m.update(direction="M_into_A",base_case_id="m")
    assert pairs([a,m])[0]["matching_endpoint"]
    m["final_y"][1]*=2
    assert not pairs([a,m])[0]["matching_endpoint"]


def test_unsettled_mutual_survival_does_not_open_sensitivity_gate():
    from dataclasses import asdict
    rows=[dict(**asdict(c),settling_status="unsettled",global_after_census_min_zero_a=False,
               global_after_census_min_zero_m=False) for c in e.design() if c.configuration=="both"
          and c.fraction<=.5 and c.dispersal_yr<=.001]
    result=assess_main(rows,[])
    assert result["B1_pass"] and not result["B2_settled"]
    assert result["sensitivity_gate"]=="characterize_before_sensitivities"
