from dataclasses import replace

import numpy as np
import pytest
from scipy.integrate import solve_ivp

from terra_prisca.haze_world import dormancy as model
from terra_prisca.haze_world import dormancy_chemical_integration as chemical
from terra_prisca.haze_world import dormancy_jacobian_integration as frozen
from terra_prisca.haze_world import dormancy_progress_integration as progress
from terra_prisca.haze_world import habitat_coupling as habitat


def counterexample(root=True):
    p=model.Dormancy(habitat.Habitats(),epsilon=.03)
    y=model.reference_state([21.,0.,4e-4,1e-4,.195],p);y[4]=1e-4
    c=chemical._Coordinates(y,p);z=c.encode(y)
    c.stage_positive[1]=root;z[1]=0.;z[3]=-3000.
    return p,y,c,z


def test_source_free_zero_root_has_exact_zero_chemical_derivative():
    p,y,c,z=counterexample()
    before=c.decode(z)[0].copy()
    exact=frozen.frozen._Coordinates.derivative(c,0.,z)
    assert np.all(np.isfinite(exact)) and exact[1]==0. and exact[3]==-1.
    with np.errstate(over="raise",invalid="raise"):
        matrix=chemical.coordinate_jacobian(0.,z,c)
    assert np.all(np.isfinite(matrix)) and matrix[3,1]==0.
    assert np.array_equal(c.decode(z)[0],before)
    assert c.chemical_conditioning_requests==[]
    with pytest.warns(RuntimeWarning):
        with pytest.raises(Exception,match="Nonfinite dormancy Newton matrix"):
            frozen.coordinate_jacobian(0.,z,c)


@pytest.mark.parametrize("root",[False,True])
def test_sole_active_allocation_gauge_derivative_is_exact_zero(root):
    p=model.Dormancy(habitat.Habitats(),epsilon=.03)
    y=model.reference_state([30.,3e-4,4e-4,1e-4,.195],p)
    c=chemical._Coordinates(y,p);z=c.encode(y)
    if not root:c.stage_positive[1]=False;z[1]=1.
    coefficient=model.fluxes(c.decode(z)[0],p)["local"][0]["acetate_production_per_gdw_yr"]
    z[3]=np.log(coefficient*y[1]/1.54e12/frozen.old.ACETATE_SCALE)
    matrix=chemical.coordinate_jacobian(0.,z,c)
    assert matrix[3,1]==0.
    assert np.all(np.isfinite(matrix))


def test_zero_linear_producer_requests_real_chart_conditioning_without_cap():
    p,y,c,z=counterexample(root=False)
    before=c.decode(z)[0].copy()
    with pytest.raises(frozen._ChemicalConditioning) as error:
        chemical.coordinate_jacobian(17.,z,c)
    assert error.value.indices==[0]
    assert error.value.chemical_cause["term"]=="own_linear_gradient"
    assert error.value.chemical_cause["log_abs_term"]>np.log(np.finfo(float).max)
    assert error.value.chemical_cause["trial_time_yr"]==17.
    assert np.array_equal(c.decode(z)[0],before) and c.acetate_positive[0]


@pytest.mark.parametrize("dispersal",[0.,1e-6])
@pytest.mark.parametrize("total",[-50.,0.,15.])
def test_chemical_directional_derivatives_in_unequal_habitats(dispersal,total):
    base=habitat.Habitats(patches=(habitat.Patch("bulk",.7),habitat.Patch("warm",.2,"buffered",286.),
        habitat.Patch("cold",.1,"buffered",278.)),dispersal_yr=dispersal)
    p=model.Dormancy(base,epsilon=.03)
    y=model.reference_state(habitat.embed_single([30.,3e-4,4e-4,1e-4,.195],base),p)
    y[p.dormant_indices]=[[1e-4,2e-4],[3e-4,1e-4],[2e-4,3e-4]]
    c=chemical._Coordinates(y,p);z=c.encode(y)
    index=int(c.groups[0]["indices"][0]);z[index]=z[index]**2;c.stage_positive[index]=False
    z[c.m]=total
    direction=np.linspace(-.1,.1,len(z));step=1e-6
    expected=(frozen.frozen._Coordinates.derivative(c,0.,z+step*direction)-frozen.frozen._Coordinates.derivative(c,0.,z-step*direction))/(2*step)
    predicted=chemical.coordinate_jacobian(0.,z,c)@direction
    ix=np.arange(3,c.m-1,6)
    assert np.allclose(predicted[ix],expected[ix],rtol=3e-5,atol=3e-8)
    assert np.all(np.isfinite(predicted))


def test_real_newton_condition_maps_accepted_stock_and_preserves_cause(monkeypatch):
    p=model.Dormancy(habitat.Habitats(),epsilon=.03)
    y=model.reference_state([21.,0.,4e-4,0.,.195],p);y[4]=1e-4
    original=chemical._Coordinates
    class RetainedTail(original):
        def encode(self,initial):
            state=super().encode(initial)
            self.acetate_positive[0]=True;state[3]=-3000.
            return state
    fired=[]
    class Request(chemical._ChemicalLSODA):
        def step(self):
            if not fired:
                fired.append(True)
                self._chemical_jacobian(self.t,self.y)
            return super().step()
    monkeypatch.setattr(chemical,"_Coordinates",RetainedTail)
    monkeypatch.setattr(chemical,"_ChemicalLSODA",Request)
    result=chemical.integrate_finite(y,p,1e-7,chemical.Census(minimum_cells=0.,census_yr=1e-8),sample_every_censuses=1,max_step=1e-7)
    assert result.status=="completed" and np.all(result.y>=0.)
    events=result.metadata["chemical_conditioning_requests"]
    assert len(events)==1 and events[0]["accepted_chart_conversion_applied"]
    assert events[0]["term"]=="own_linear_gradient" and events[0]["accepted_time_yr"]==0.
    chart=result.metadata["chemical_conditioning_events"][0]
    assert chart["kind"]=="newton_derivative_chemical_chart"
    assert chart["physical_state_bitwise_preserved"] and chart["decoded_amount_mol_l"]==0.
    assert chart["inventory_before"]==chart["inventory_after"]
    assert chart["conditioning_cause"]["accepted_coordinate_sha256"]==events[0]["accepted_coordinate_sha256"]
    assert np.all(result.y[1]==0.)


def test_new_flow_matches_independent_physical_radau_and_keeps_minima():
    base=habitat.Habitats(patches=(habitat.Patch("bulk",.98),habitat.Patch("warm",.02,"buffered",286.)),dispersal_yr=.001)
    p=model.Dormancy(base,epsilon=.003)
    y=model.reference_state(habitat.embed_single([30.,3e-4,4e-4,1e-4,.195],base),p)
    y[p.dormant_indices]=1e-5
    result=chemical.integrate_finite(y,p,1.,chemical.Census(minimum_cells=0.,census_yr=.25),sample_every_censuses=1,max_step=.1)
    reference=solve_ivp(lambda t,z:model.rhs(z,p,trial_extension=True),(0.,1.),y,method="Radau",rtol=2e-10,
        atol=np.r_[np.tile([1e-9,1e-15,1e-15,1e-15,1e-15,1e-15],2),1e-13],t_eval=result.t)
    assert result.status=="completed" and reference.success
    assert np.allclose(result.y,reference.y,rtol=4e-6,atol=2e-11)
    assert np.all(result.y>=0.)
    masses=np.sum(p.weights[:,None,None]*(result.y[p.biomass_indices]+result.y[p.dormant_indices]),axis=0)
    assert np.all(result.global_continuous_min_log_biomass<=np.log(masses).min(axis=1)+1e-10)
    assert max(abs(model.redox_residual(z,p)) for z in result.y.T)<1e-16


def test_zero_switching_and_nonzero_census_keep_frozen_contract():
    p=model.Dormancy(habitat.Habitats(),epsilon=.03,switching_factor=0.)
    process=chemical.Census(census_yr=.25)
    conversion=p.coupled.habitat_l_cm2*process.surface_cm2/process.cell_mass_gdw
    y=model.reference_state([30.,.5/conversion,4e-4,1e-4,.195],p);y[4]=.4/conversion
    a=progress.integrate_finite(y,p,.5,process,sample_every_censuses=1,max_step=.25)
    b=chemical.integrate_finite(y,p,.5,process,sample_every_censuses=1,max_step=.25)
    assert b.status=="completed" and a.extinction_events==b.extinction_events
    assert a.extinction_events
    for key in a.ledger:assert np.array_equal(a.ledger[key],b.ledger[key])
    assert np.allclose(a.y,b.y,rtol=4e-6,atol=2e-11)
    assert np.all(b.y[p.dormant_indices[:,1]]==0.)


def edge_solver(pressure,acetate,end):
    p=model.Dormancy(habitat.Habitats(),epsilon=.03)
    y=model.reference_state([pressure,0.,4e-4,acetate,.195],p);y[4]=1e-4
    c=chemical._Coordinates(y,p);state=c.encode(y)
    def make(value):
        atol=np.r_[np.tile([1e-7,1e-14,1e-14,1e-11,1e-14,1e-14],p.n_patches),1e-11,np.full(len(c.groups),1e-8)]
        atol[:c.m][c.stage_positive]=1e-12
        for patch,on in enumerate(c.acetate_positive):
            if on:atol[6*patch+3]=1e-8
        return chemical._ChemicalLSODA(c.derivative,1000.,value,end,nominal_max_step=.001,
            events=[],progress_events=[],max_step=.001,first_step=min(1e-6,end-1000.),rtol=2e-8,atol=atol)
    return c,state,make


def test_initial_zero_linear_producer_arrival_maps_positive_chemical_at_absolute_time():
    c,state,make=edge_solver(30.,1e-100,1000.001)
    before=c.decode(state)[0].copy();solver=make(state)
    with pytest.raises(frozen._ChemicalConditioning) as error:
        solver.step()
    assert error.value.chemical_cause["kind"]=="linear_producer_arrival"
    assert error.value.chemical_cause["accepted_time_yr"]==1000.
    assert "trial_time_yr" not in error.value.chemical_cause
    assert c.acetate_positive[0] and np.array_equal(c.decode(state)[0],before)
    c.condition_chemicals(state,1000.,error.value.indices,"accepted_rate_chemical_chart")
    assert not c.acetate_positive[0] and state[3]>0.
    assert c.decode(state)[0].tobytes()==before.tobytes()
    assert c.chemical_events[-1]["kind"]=="linear_producer_arrival_chemical_chart"
    assert c.chemical_events[-1]["inventory_before"]==c.chemical_events[-1]["inventory_after"]
    solver=make(state);steps=0
    while solver.status=="running" and steps<500:
        left=solver.t;solver.step();steps+=1
        assert solver.t>left
    assert solver.status=="finished" and steps<500
    assert np.all(c.decode(solver.y)[0]>=0.)


def test_source_free_zero_linear_producer_does_not_request_unnecessary_conversion():
    c,state,make=edge_solver(21.,1e-4,1000.0000001)
    before=state.copy();solver=make(state)
    solver.step()
    assert solver.t>1000.
    assert c.acetate_positive[0] and c.chemical_conditioning_requests==[]
    assert c.chemical_events==[] and before[3]==state[3]
