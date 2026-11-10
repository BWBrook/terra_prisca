from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest

from terra_prisca.haze_world import refuge_experiments as experiment
from terra_prisca.haze_world.refuge_integration import Census


def case(**values):
    return replace(experiment.Case("check",.5,.05,8.6,.001,"A_into_M",years=100.),**values)


def resident_state():
    return np.array([30.,0.,.001,0.,30.,0.,.001,0.,.195])


def start_info():
    return dict(candidate_count=0,qualifying_count=0,ambiguous=False,selected_ratio=None,
                coverage=dict(status="no_supported_ratio_interval"),candidates=[])


def test_registered_designs_and_supplemental_variants_remain_distinct():
    main=experiment.design("main")
    subsets=experiment.design("subsets")
    assert len(main)==432 and len(subsets)==78 and len(experiment.equilibrium_design())==432
    assert len({c.case_id for c in main})==432
    assert all(c.activity=="fixed" and c.seed_origin=="both" and c.census_yr==10. and c.years==100000. for c in main)
    assert len({tuple(v for k,v in vars(c).items() if k!="case_id") for c in subsets})==78
    assert sum(c.seed_origin!="both" for c in subsets)==12
    assert sum(c.activity=="products" for c in subsets)==6
    assert sum(c.census_yr==1. for c in subsets)==6
    assert len(experiment.design("pilot"))==4 and all(c.years==1000. for c in experiment.design("pilot"))


def test_seed_origin_comparison_preserves_total_global_dose():
    records=[]
    for origin in ("both","cold","warm"):
        c=case(seed_origin=origin)
        y,dose=experiment.seed_state(c,resident_state())
        p=experiment.parameters(c)
        assert p.weights@y[experiment.model.BIOMASS_INDICES[:,0]]==pytest.approx(1e-12)
        records.append(dose["global_seed_cells"])
        if origin=="warm":
            assert y[1]==0. and y[5]==pytest.approx(1e-12/.05)
    assert max(records)==pytest.approx(min(records))
    with pytest.raises(ValueError,match="inactive"):
        experiment.seed_state(case(warm_fraction=0.,seed_origin="warm"),resident_state())


def test_conditional_start_requires_each_active_patch_and_records_highest_ratio_choice():
    p=experiment.parameters(case())
    good=resident_state()
    missing=good.copy();missing[6]=0.
    candidates=[dict(y=good,r=.1,stability="stable"),dict(y=good,r=.2,stability="stable"),
                dict(y=good,r=.3,stability="unstable"),dict(y=missing,r=.4,stability="stable")]
    selected,qualifying=experiment.select_start(candidates,p,1)
    assert selected["r"]==.2 and len(qualifying)==2
    selected,qualifying=experiment.select_start(candidates[2:],p,1)
    assert selected is None and not qualifying


def test_unsupported_start_is_a_resumable_attempt_not_an_extinction_endpoint(monkeypatch,tmp_path):
    monkeypatch.setattr(experiment,"conditional_start",lambda *args:(None,start_info()))
    c=case()
    first=experiment.run_case(c,tmp_path)
    row=first["summary"]
    assert row["attempt_status"]=="no_supported_conditional_start_found"
    assert row["global_temperature_k"] is None and row["endpoint_class"] is None
    assert experiment.run_case(c,tmp_path)["raw_sha256"]==first["raw_sha256"]
    data=tmp_path/first["raw_file"]
    data.write_bytes(data.read_bytes()+b"corruption")
    with pytest.raises(RuntimeError,match="check.*Receipt/data mismatch"):
        experiment.run_case(c,tmp_path)


def test_unexpected_solver_failure_names_case_and_writes_no_completion_receipt(monkeypatch,tmp_path):
    monkeypatch.setattr(experiment,"conditional_start",lambda *args:(dict(y=resident_state()),start_info()))
    def fail(*args,**kwargs):
        raise RuntimeError("Deliberate numerical failure")
    monkeypatch.setattr(experiment,"integrate_finite",fail)
    with pytest.raises(RuntimeError,match="Refuge case check failed.*Deliberate numerical failure"):
        experiment.run_case(case(),tmp_path)
    assert not list(tmp_path.glob("*.receipt.json"))


def test_domain_exit_preserves_prefix_diagnostics_without_a_physical_endpoint():
    c=case(contrast_k=0.)
    y=resident_state()
    result=SimpleNamespace(t=np.array([0.,3.]),y=np.column_stack((y,y)),
        temperatures_k=np.array([[281.,281.],[281.,303.15]]),status="domain_exit",domain_exit=dict(time_yr=3.),
        physiology_domains=np.array([["measured","measured"],["measured","measured"]]),climate_domains=np.array(["arney","arney"]),
        continuous_min_log_biomass=np.full((2,2),-np.inf),pre_removal_min_log_biomass=np.full((2,2),-np.inf),
        after_census_min_log_biomass=np.full((2,2),-np.inf),extinction_events=[],
        global_continuous_min_log_biomass=np.array([-np.inf,-20.]),global_continuous_min_times_yr=np.zeros(2),
        global_pre_extinction_min_log_biomass=np.array([-np.inf,-20.]),global_pre_extinction_min_times_yr=np.zeros(2),
        global_after_census_min_log_biomass=np.array([-np.inf,-20.]),
        metadata=dict(nfev=1,solver_resets=0,accepted_steps=1,wall_seconds=.1,global_log_cell_conversion=67.,
            global_min_temperature_k=281.,global_max_temperature_k=303.15,
            patch_min_temperature_k=[281.,281.],patch_max_temperature_k=[281.,303.15]))
    row=experiment.summarize(c,experiment.parameters(c),Census(),result,start_info())
    assert row["attempt_status"]=="domain_exit" and row["domain_exit_time_yr"]==3.
    assert row["global_temperature_k"] is None and row["methane_ratio"] is None and row["endpoint_class"] is None
    assert row["terminal_global_temperature_k"] is not None
    assert row["continuous_min_zero_cold_a"] and row["continuous_min_log_cells_cold_a"] is None
    assert row["global_continuous_min_zero_a"] and row["global_continuous_min_log_cells_a"] is None
    assert not row["global_continuous_min_zero_m"] and row["global_continuous_min_log_cells_m"]==47.


def test_collector_refuses_missing_requested_receipt(tmp_path):
    with pytest.raises(RuntimeError,match="Missing qualified completion receipt: check"):
        experiment.collect([case()],tmp_path,tmp_path/"public","pilot")
