from dataclasses import replace

import numpy as np
import pytest

from terra_prisca.haze_world import dormancy as d
from terra_prisca.haze_world import dormancy_integration as frozen
from terra_prisca.haze_world import dormancy_jacobian_integration as numerical
from terra_prisca.haze_world import habitat_coupling as h


def setup():
    p=d.Dormancy(h.Habitats(),epsilon=.1)
    y=d.reference_state([30.,3e-4,4e-4,1e-4,.195],p)
    return p,y


@pytest.mark.parametrize("ramp",["cubic","linear"])
def test_switching_matrix_slopes_have_no_false_waking_at_break_even(ramp):
    x=np.array([-1.,0.,.2,.5,.8,1.,2.])
    expected=[0.,0.,.96,1.5,.96,0.,0.] if ramp=="cubic" else [0.,0.,1.,1.,1.,0.,0.]
    assert np.allclose(numerical.switching_slope(x,ramp),expected)


def test_matrix_nonallocation_values_equal_frozen_coordinates():
    p,y=setup();y[p.dormant_indices]=1e-4
    c=numerical._Coordinates(y,p);z=c.encode(y)
    expected=frozen._Coordinates.derivative(c,0.,z)
    actual,_=numerical._matrix_values(z,c)
    indices=sorted(set(range(len(z)))-set(i for g in c.groups for i in g["indices"]))
    assert np.array_equal(actual[indices],expected[indices])


def test_newton_matrix_matches_directional_derivative_away_from_switches():
    p,y=setup();y[p.dormant_indices]=1e-4
    c=numerical._Coordinates(y,p);z=c.encode(y)
    direction=np.array([.2,.03,-.01,.1,-.02,.01,.001,.05,-.03])
    assert len(direction)==len(z)
    step=1e-6
    actual=(frozen._Coordinates.derivative(c,0.,z+step*direction)-frozen._Coordinates.derivative(c,0.,z-step*direction))/(2*step)
    predicted=numerical.coordinate_jacobian(0.,z,c)@direction
    assert np.allclose(predicted,actual,rtol=3e-4,atol=3e-8)


def test_positive_chemical_chart_conversion_preserves_every_physical_stock():
    p,y=setup();c=numerical._Coordinates(y,p);z=c.encode(y)
    z[3]=frozen.old._inverse(1e-300/frozen.old.ACETATE_SCALE)
    before=c.decode(z)[0]
    c.condition_chemicals(z,1.,[0],"test")
    assert not c.acetate_positive[0] and z[3]>0
    assert c.decode(z)[0].tobytes()==before.tobytes()
    event=c.chemical_events[0]
    assert event["physical_state_bitwise_preserved"]
    assert event["inventory_before"]==event["inventory_after"]
    assert event["old_log_concentration"]< -690


def test_zero_switching_recovers_frozen_trajectory_without_dormant_seed():
    p,y=setup();p=replace(p,switching_factor=0.)
    process=frozen.Census(minimum_cells=0.,census_yr=.5)
    a=frozen.integrate_finite(y,p,5.,process,sample_every_censuses=1,max_step=1.)
    b=numerical.integrate_finite(y,p,5.,process,sample_every_censuses=1,max_step=1.)
    assert b.status=="completed"
    assert np.array_equal(a.t,b.t)
    assert np.allclose(a.y,b.y,rtol=4e-6,atol=1e-11)
    assert np.all(b.y[p.dormant_indices]==0.) and np.all(np.isneginf(b.log_dormant))
    assert np.all(b.y>=0.)
    assert max(abs(d.redox_residual(x,p)) for x in b.y.T)<1e-16


def test_tiny_positive_chemical_pool_recovers_without_inventory_reset():
    p,y=setup();y[3]=1e-300
    result=numerical.integrate_finite(y,p,1.,frozen.Census(minimum_cells=0.,census_yr=.1),sample_every_censuses=1,max_step=.1)
    assert result.status=="completed" and np.all(result.y>=0)
    events=result.metadata["chemical_conditioning_events"]
    assert events and events[0]["decoded_amount_mol_l"]>0
    assert all(e["physical_state_bitwise_preserved"] for e in events)
    assert all(e["inventory_before"]==e["inventory_after"] for e in events)
    assert all(e["atol"]>0 for e in result.metadata["chemical_linear_atol_history"])
    assert max(abs(d.redox_residual(x,p)) for x in result.y.T)<1e-16
    assert np.all(result.global_continuous_min_log_biomass<=np.min(result.log_biomass,axis=(0,2))+1e-10)


def test_absent_guild_remains_absent_and_global_rare_log_is_preserved():
    p,y=setup();p=replace(p,switching_factor=0.)
    y[1]=0.;y[2]=np.nextafter(0.,1.)
    result=numerical.integrate_finite(y,p,1.,frozen.Census(minimum_cells=0.,census_yr=.1),sample_every_censuses=1,max_step=.1)
    assert result.status=="completed"
    assert np.all(result.y[1]==0.) and np.all(np.isneginf(result.log_biomass[:,0]))
    assert np.all(np.isfinite(result.log_biomass[:,1]))
    assert result.global_continuous_min_log_biomass[1]<-740


def test_shared_habitat_zero_stage_creation_matches_physical_radau():
    from scipy.integrate import solve_ivp

    base=h.Habitats(patches=(h.Patch("bulk",.98),h.Patch("warm",.02,"buffered",286.)),dispersal_yr=.001)
    p=d.Dormancy(base,epsilon=.003)
    y=d.reference_state(h.embed_single([30.,3e-4,4e-4,1e-4,.195],base),p)
    initial=d.fluxes(y,p)
    assert np.all(y[p.dormant_indices]==0.)
    assert np.any((initial["net_growth_yr"]>0)&(initial["sigma_yr"]==0.))
    result=numerical.integrate_finite(y,p,3.,frozen.Census(minimum_cells=0.,census_yr=.25),sample_every_censuses=1,max_step=.1)
    independent=solve_ivp(lambda t,z:d.rhs(z,p,trial_extension=True),(0.,3.),y,method="Radau",rtol=2e-10,
        atol=np.r_[np.tile([1e-9,1e-15,1e-15,1e-15,1e-15,1e-15],2),1e-13],t_eval=result.t)
    assert result.status=="completed" and independent.success
    assert np.allclose(result.y,independent.y,rtol=4e-6,atol=2e-11)
    assert np.all(result.y>=0.)
    net_history=np.array([d.fluxes(stock,p)["net_growth_yr"] for stock in result.y.T])
    assert np.any((initial["net_growth_yr"]>0)&(net_history.min(axis=0)<0))
    masses=np.sum(p.weights[:,None,None]*(result.y[p.biomass_indices]+result.y[p.dormant_indices]),axis=0)
    assert np.all(result.global_continuous_min_log_biomass<=np.log(masses).min(axis=1)+1e-10)


def test_underflowed_source_free_root_has_finite_newton_limit():
    p,y=setup();y[2]=0.;y[5]=1e-4
    c=numerical._Coordinates(y,p);z=c.encode(y)
    c.stage_positive[2]=True;z[2]=0.
    z[c.m+1]=-800.
    z[0]=1.
    rate=frozen._Coordinates.derivative(c,0.,z)
    assert rate[2]==0.
    matrix=numerical.coordinate_jacobian(0.,z,c)
    assert np.all(np.isfinite(matrix))
    assert matrix[2,2]<0.
    assert np.count_nonzero(matrix[2])==1
    assert np.isfinite(c.global_logs(z)[1])


def test_zero_root_with_real_incoming_source_requests_existing_linear_chart():
    p,y=setup();y[2]=0.;y[5]=1e-4
    c=numerical._Coordinates(y,p);z=c.encode(y)
    c.stage_positive[2]=True;z[2]=0.;z[0]=200.
    before=c.decode(z)[0].copy()
    with pytest.raises(frozen._StageSourceOverflow) as error:
        numerical.coordinate_jacobian(0.,z,c)
    assert error.value.index==2
    assert np.array_equal(c.decode(z)[0],before)


def test_captured_1399_year_waking_pole_advances_without_stock_reset():
    import json
    from pathlib import Path
    from terra_prisca.haze_world import dormancy_experiments as runner

    fixture=json.loads((Path(__file__).parents[1]/"models/haze_world/review/dormancy_1399_regression.json").read_text())
    case=next(c for c in runner.design() if c.case_id==fixture["case_id"])
    p=runner.parameters(case)
    initial=np.zeros(p.state_size)
    initial[p.biomass_indices[p.weights>0]]=1e-4
    c=numerical._Coordinates(initial,p)
    c.stage_positive[:]=fixture["stage_positive"]
    c.acetate_positive[:]=fixture["acetate_positive"]
    internal=np.asarray(fixture["state"])
    time=fixture["time_yr"]
    atol=np.r_[np.tile([1e-7,1e-14,1e-14,1e-11,1e-14,1e-14],p.n_patches),1e-11,np.full(len(c.groups),1e-8)]
    atol[np.r_[p.biomass_indices.ravel(),p.dormant_indices.ravel()]]=min(1e-14,p.dispersal_yr*min(p.weights[p.weights>0])*1e-7)
    atol[:c.m][c.stage_positive]=1e-12
    solver=numerical._GuardedLSODA(c.derivative,time,internal,time+1.,nominal_max_step=10.,events=[],max_step=10.,first_step=1e-6,rtol=case.rtol,atol=atol)
    steps=0
    while solver.status=="running" and steps<500:
        start=solver.y.copy();left=solver.t
        solver.step();steps+=1
        assert solver.t>left
        assert frozen._positive_piece(solver.dense_output(),left,solver.t,c,start)
        assert np.all(c.decode(solver.y)[0]>=0.)
    assert solver.status=="finished" and steps<500
    assert c.rejected==[] and c.chemical_events==[]
    assert np.all(np.isfinite(c.global_logs(solver.y)))
