from collections import Counter
from dataclasses import replace

import numpy as np
import pytest

from terra_prisca.haze_world import dormancy_experiments as runs
from terra_prisca.haze_world import dormancy_starts as starts
from terra_prisca.haze_world import dormancy as model


def test_dormancy_protocol_has_main_slow_and_bistable_comparisons():
    cases=runs.design()
    assert len(cases)==128 and len({c.case_id for c in cases})==128
    assert Counter(c.group for c in cases)==dict(main=112,slow=12,bistable=4)
    assert all(c.switching_factor==1 and c.configuration=="none" for c in cases if c.group=="slow")
    assert all(c.loss_h==.002 and c.fraction==0 for c in cases if c.group=="bistable")


def test_wellmixed_stationary_resident_has_exactly_zero_dormant_stock():
    p=runs.parameters(runs.design()[0]);start=starts.conditional_states(p,1)["selected"]
    assert start is not None and start["well_mixed_embedding"]
    assert np.array_equal(start["y"][p.dormant_indices],np.zeros((p.n_patches,2)))
    assert start["max_scaled_residual"]<1e-8


def test_spatial_resident_bank_is_stationary_in_its_own_equations():
    case=next(c for c in runs.design() if c.configuration=="both" and c.epsilon==.001 and c.fraction==.5)
    p=runs.parameters(case);start=starts.conditional_states(p,0)["selected"]
    assert start is not None and not start["well_mixed_embedding"]
    assert np.max(start["y"][p.dormant_indices[:,0]])>0
    assert np.all(start["y"][p.dormant_indices[:,1]]==0)
    assert start["max_scaled_residual"]<1e-8
    assert start["dormant_balance_residual"]<1e-12
    disabled=replace(p,base=replace(p.base,base=replace(p.coupled,enabled=(True,False))))
    assert abs(model.redox_residual(start["y"],disabled))<1e-12


def test_spatial_starts_require_agreeing_conditional_spectra():
    case=next(c for c in runs.design() if c.configuration=="both" and c.epsilon==.01 and c.fraction==.5)
    p=runs.parameters(case);start=starts.conditional_states(p,1)["selected"]
    assert start is not None and start["supported_stable"] and start["stability"]=="stable"
    assert start["step_agreement"]
    assert {s["relative_step"] for s in start["spectra"]}=={1e-5,1e-6}
    assert all(s["max_real_yr"]<0 for s in start["spectra"])
    assert start["step_spread_yr"]<1e-8


def test_one_habitat_is_wellmixed_even_with_a_nonzero_exchange_parameter():
    p=runs.parameters(runs.design()[0]);p=replace(p,base=replace(p.base,dispersal_yr=.1))
    start=starts.conditional_states(p,1)["selected"]
    assert start is not None and start["well_mixed_embedding"] and start["supported_stable"]
    assert np.all(start["y"][p.dormant_indices]==0)


def test_linear_switch_corner_is_not_silently_certified_as_smooth():
    p=runs.parameters(runs.design()[0]);root=starts.conditional_states(p,1)["selected"]["y"]
    result=starts.resident_stability(root,replace(p,ramp="linear"),1)
    assert not result["supported_stable"]
    assert result["stability"]=="unqualified_nonsmooth_ramp"


def test_climate_corner_retains_both_one_sided_spectra(monkeypatch):
    from terra_prisca.haze_world import population_coupling as core
    p=runs.parameters(runs.design()[0])
    center=starts.conditional_states(p,1)["selected"]["y"].copy()
    center[-1]=core.response(p.coupled.climate.case).ratios[2]
    def corner_rhs(y,p):
        values=-(y-center)
        values[-1]=(y[-1]-center[-1]) if y[-1]>=center[-1] else -(y[-1]-center[-1])
        return values
    monkeypatch.setattr(model,"rhs",corner_rhs)
    result=starts.resident_stability(center,p,1)
    assert result["climate_corner"] and not result["supported_stable"]
    assert {s["ratio_side"] for s in result["spectra"]}=={-1,1}
    assert max(s["max_real_yr"] for s in result["spectra"])>.99
    assert min(s["max_real_yr"] for s in result["spectra"])<-.99


def test_stationary_root_without_stability_certificate_cannot_be_selected(monkeypatch):
    p=runs.parameters(runs.design()[0])
    monkeypatch.setattr(starts,"resident_stability",lambda *args,**kwargs:
        dict(stability="unstable",supported_stable=False,spectra=[]))
    result=starts.conditional_states(p,1)
    assert result["candidates"] and not result["qualifying"]
    assert result["selected"] is None


def test_cubic_stencil_bias_is_resolved_by_a_finer_pair_without_relaxing_tolerance():
    case=next(c for c in runs.design() if c.group=="bistable")
    p=runs.parameters(case);start=starts.conditional_states(p,1)["selected"]
    assert start is not None
    coarse=starts.resident_stability(start["y"],p,1,max_refinements=0)
    assert coarse["stability"]=="unresolved_step_dependence" and not coarse["supported_stable"]
    refined=starts.resident_stability(start["y"],p,1)
    assert refined["supported_stable"] and refined["step_refinements"]>=1
    assert max(refined["final_relative_steps"])<1e-5
    assert len(refined["spectra"])>len(coarse["spectra"])
    assert refined["step_spread_yr"]<coarse["step_spread_yr"]
    assert refined["max_real_yr"]==pytest.approx(-.00221267,rel=5e-4)
