import numpy as np

from terra_prisca.haze_world.turnover_assessment import compare,methane_tail


def record(**summary):
    return dict(summary=dict(settling_status="census_stationary",global_present_a=True,
                global_present_m=True,global_temperature_k=281.5,**summary),
                protocol=dict(parameters=dict(patches=[dict(weight=1.)])))


def profile(values):
    return dict(y=np.asarray(values)[:,None],metadata=dict(global_log_cell_conversion=np.log(1e29)))


def test_equal_climate_with_different_biomass_is_not_equal_endpoint():
    a=record();b=record()
    result=compare(a,b,profile([10.,.001,.002,.0001,.2]),profile([10.,.002,.001,.0001,.2]))
    assert result["temperature_difference_k"]==0
    assert result["both_stationary"] and result["same_global_occupancy"]
    assert not result["same_endpoint"]


def test_matching_endpoints_still_require_stationarity():
    a=record();b=record();b["summary"]["settling_status"]="unsettled"
    p=profile([10.,.001,.002,.0001,.2])
    result=compare(a,b,p,p)
    assert not result["both_stationary"] and not result["same_endpoint"]


def test_patch_specific_cell_floor_distinguishes_local_occupancy():
    a=record();a["protocol"]["parameters"]["patches"]=[dict(weight=.98),dict(weight=.02)]
    b=record();b["protocol"]["parameters"]["patches"]=[dict(weight=.98),dict(weight=.02)]
    first=profile([10.,1e-28,.002,.0001,10.,0.,.002,.0001,.2])
    second=profile([10.,1e-28,.002,.0001,10.,6e-28,.002,.0001,.2])
    result=compare(a,b,first,second)
    assert result["same_global_occupancy"] and not result["same_local_occupancy"]
    assert result["local_occupancy_first"]=="11;01"
    assert result["local_occupancy_second"]=="11;11"
    assert not result["same_endpoint"]


def test_subcell_stock_comparison_uses_actual_floor_symmetrically():
    a=record();b=record()
    first=profile([10.,0.,.002,.0001,.2])
    second=profile([10.,5e-33,.002,.0001,.2])
    second["metadata"]["global_log_cell_conversion"]=np.log(1e28)
    forward=compare(a,b,first,second)
    backward=compare(b,a,second,first)
    assert forward["maximum_relative_stock_difference"]==backward["maximum_relative_stock_difference"]
    assert np.isclose(forward["maximum_relative_stock_difference"],5e-5)
    assert forward["same_endpoint"]


def test_absent_methanogens_leave_an_exact_abiotic_methane_tail():
    from terra_prisca.haze_world import turnover_experiments as e,habitat_coupling as h
    p=e.parameters(e.design()[0]);t=np.array([80000.,90000.,100000.])
    y=h.embed_single([30.,.001,0.,.001,.2],p)
    equilibrium=h.fluxes(y,p)["abiotic_ratio_yr"]*p.base.loss.lifetime_yr
    states=np.repeat(y[:,None],len(t),axis=1)
    states[-1]=equilibrium+.01*np.exp(-(t-t[0])/p.base.loss.lifetime_yr)
    result=methane_tail(dict(t=t,y=states),p)
    assert result["kind"]=="exact_abiotic_relaxation"
    assert result["maximum_methane_ratio_residual"]<1e-16
    states[p.biomass_indices[0,1],1]=1e-30
    assert methane_tail(dict(t=t,y=states),p)["kind"]=="not_an_exact_abiotic_tail"
