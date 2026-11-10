from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import pytest

from terra_prisca.haze_world import dormancy as model
from terra_prisca.haze_world import dormancy_chemical_integration as chemical
from terra_prisca.haze_world import dormancy_experiments as experiments
from terra_prisca.haze_world import dormancy_jacobian_integration as frozen
from terra_prisca.haze_world import dormancy_stage_integration as stage
from terra_prisca.haze_world import habitat_coupling as habitat


def setup():
    p=model.Dormancy(habitat.Habitats(),epsilon=.03)
    y=model.reference_state([30.,3e-4,4e-4,1e-4,.195],p)
    return p,y


def tiny_root(root=1e-320):
    base=habitat.Habitats(patches=(habitat.Patch('bulk',.5),habitat.Patch('warm',.5,'buffered',286.)),dispersal_yr=1e-9)
    p=model.Dormancy(base,epsilon=.003)
    y=model.reference_state(habitat.embed_single([21.,0.,0.,0.,.195],base),p)
    y[4]=1e-4
    c=stage._Coordinates(y,p);z=c.encode(y)
    c.stage_positive[1]=False;z[1]=0.
    c.stage_positive[7]=True;z[7]=root
    return p,y,c,z


def test_true_unrepresentable_root_newton_row_is_typed_and_saved_stock_maps_exactly():
    p,y,c,z=tiny_root()
    physical=c.decode(z)[0].copy();total=z[c.m:].copy();guilds=c.global_logs(z).copy()
    rate=c.derivative(17.,z)
    assert np.all(np.isfinite(rate))
    with np.errstate(over='raise',invalid='raise'):
        with pytest.raises(stage._StageSourceOverflow) as error:stage.coordinate_jacobian(17.,z,c)
    assert error.value.index==7 and error.value.stage_cause['term']=='root_allocation_newton_row'
    assert error.value.stage_cause['trial_time_yr']==17.
    event=c.condition_stage(z,17.,7,'native_step',error.value)
    assert c.decode(z)[0].tobytes()==physical.tobytes()
    assert z[c.m:].tobytes()==total.tobytes() and c.global_logs(z).tobytes()==guilds.tobytes()
    assert event['retained_stage_log_lost'] and event['log_allocation']==2*np.log(1e-320)
    assert event['inventory_before']==event['inventory_after'] and event['linear_allocation']==0.
    assert np.all(np.isfinite(stage.coordinate_jacobian(17.,z,c)))
    assert np.all(np.isfinite(c.derivative(17.,z)))


def test_hypothetical_trial_root_zero_never_replaces_saved_accepted_root():
    p,y,c,z=tiny_root(.1)
    saved=z.copy();physical=c.decode(z)[0].copy();totals=z[c.m:].copy()
    trial=z.copy();trial[7]=0.
    error=stage._stage_error(7,18.,trial,'zero_root_source_or_differential')
    event=c.condition_stage(z,17.,7,'native_step',error)
    assert z[7]==saved[7]**2 and z[7]>0.
    assert c.decode(z)[0].tobytes()==physical.tobytes() and z[c.m:].tobytes()==totals.tobytes()
    assert event['accepted_coordinate_sha256']==sha256(saved.tobytes()).hexdigest()
    assert event['cause']['trial_coordinate_sha256']!=event['accepted_coordinate_sha256']
    assert event['cause']['trial_root']==0. and event['prior_root']==.1
    assert not event['retained_stage_log_lost']


def test_real_waking_has_finite_rhs_but_unrepresentable_exact_diagonal():
    p,y=setup();y[1]=0.;y[4]=1e-4
    c=stage._Coordinates(y,p);z=c.encode(y);c.stage_positive[1]=True;z[1]=np.sqrt(1e-307)
    flux=model.fluxes(c.decode(z)[0],p,trial_extension=True)
    assert flux['rho_yr'][0,0]>35.
    assert np.all(np.isfinite(c.derivative(0.,z)))
    with pytest.raises(stage._StageSourceOverflow):stage.coordinate_jacobian(0.,z,c)
    before=c.decode(z)[0].copy();c.condition_stage(z,0.,1,'native_step')
    assert before.tobytes()==c.decode(z)[0].tobytes() and z[1]>0.
    assert np.all(np.isfinite(stage.coordinate_jacobian(0.,z,c)))


def test_ordinary_path_census_minima_and_ledger_match_chemical_bitwise():
    p,y=setup();process=stage.Census(minimum_cells=0.,census_yr=.25)
    a=chemical.integrate_finite(y,p,2.,process,sample_every_censuses=1,max_step=1.)
    b=stage.integrate_finite(y,p,2.,process,sample_every_censuses=1,max_step=1.)
    for name in ('t','y','log_biomass','log_active','log_dormant','log_acetate','global_continuous_min_log_biomass','global_continuous_min_times_yr','census_times','census_activity'):
        assert np.array_equal(getattr(a,name),getattr(b,name))
    for name in a.ledger:assert np.array_equal(a.ledger[name],b.ledger[name])
    assert a.extinction_events==b.extinction_events and b.metadata['stage_conditioning_events']==[]


def test_poststep_conditioning_restarts_from_exact_saved_endpoint(monkeypatch):
    p,y=setup();y[0]=21.;constructors=[];fired=[]
    original_coordinates=stage._Coordinates
    class Coordinates(original_coordinates):
        poststep=False
        def derivative(self,time,state):
            if self.poststep and not fired:
                fired.append((float(time),state.copy()))
                self.poststep=False
                trial=state.copy();trial[1]=0.
                raise stage._stage_error(1,time+.01,trial,'injected_trial_zero')
            return super().derivative(time,state)
    class Solver(stage._StageLSODA):
        def __init__(self,fun,time,state,*args,**kwargs):
            fun.__self__.poststep=False
            constructors.append((float(time),state.copy(),fun.__self__.stage_positive.copy()))
            super().__init__(fun,time,state,*args,**kwargs)
        def dense_output(self):
            result=super().dense_output();self.coordinates.poststep=True;return result
    monkeypatch.setattr(stage,'_Coordinates',Coordinates);monkeypatch.setattr(stage,'_StageLSODA',Solver)
    process=stage.Census(minimum_cells=0.,census_yr=.1)
    result=stage.integrate_finite(y,p,.2,process,sample_every_censuses=1,max_step=.1)
    assert result.status=='completed' and len(fired)==1
    event=result.metadata['stage_conditioning_events'][0]
    assert event['phase']=='accepted_poststep' and event['physical_state_bitwise_preserved']
    saved=fired[0][1];assert event['accepted_coordinate_sha256']==sha256(saved.tobytes()).hexdigest()
    restart=next(row for row in constructors if row[0]==fired[0][0])
    assert not restart[2][1] and restart[1][1]==saved[1]**2
    assert restart[1][-2:].tobytes()==saved[-2:].tobytes()
    assert result.metadata['accepted_steps']>1 and result.metadata['solver_resets']>=1
    assert result.metadata['allocation_positivity_retries']==0
    assert np.all(result.y>=0.) and not result.extinction_events
    assert max(abs(model.redox_residual(v,p)) for v in result.y.T)<1e-16


def test_nonzero_census_and_zero_switching_keep_exact_contract():
    p,y=setup();p=replace(p,switching_factor=0.)
    process=stage.Census(census_yr=.25)
    conversion=p.coupled.habitat_l_cm2*process.surface_cm2/process.cell_mass_gdw
    y[1]=.5/conversion;y[4]=.4/conversion
    a=chemical.integrate_finite(y,p,.5,process,sample_every_censuses=1,max_step=.25)
    b=stage.integrate_finite(y,p,.5,process,sample_every_censuses=1,max_step=.25)
    assert a.extinction_events==b.extinction_events and a.extinction_events
    for key in a.ledger:assert np.array_equal(a.ledger[key],b.ledger[key])
    assert np.array_equal(a.y,b.y)
    assert np.all(b.y[p.dormant_indices[:,1]]==0.)


def test_allocation_directional_derivative_in_unequal_habitats():
    base=habitat.Habitats(patches=(habitat.Patch('bulk',.7),habitat.Patch('warm',.2,'buffered',286.),habitat.Patch('cold',.1,'buffered',278.)),dispersal_yr=1e-6)
    p=model.Dormancy(base,epsilon=.03)
    y=model.reference_state(habitat.embed_single([30.,3e-4,4e-4,1e-4,.195],base),p);y[p.dormant_indices]=1e-4
    c=stage._Coordinates(y,p);z=c.encode(y)
    direction=np.linspace(-.1,.1,len(z));step=1e-6
    expected=(c.derivative(0.,z+step*direction)-c.derivative(0.,z-step*direction))/(2*step)
    assert np.allclose(stage.coordinate_jacobian(0.,z,c)@direction,expected,rtol=3e-5,atol=3e-8)


def test_actual_4550_accepted_state_source_is_preserved_and_becomes_finite():
    path=Path(__file__).parents[1]/'models/haze_world/review/dormancy_4550_regression.json'
    saved=json.loads(path.read_text());case=next(c for c in experiments.design() if c.case_id=='dormancy_0107')
    p=experiments.parameters(case);y=np.asarray(saved['decoded_physical'])
    c=stage._Coordinates(y,p);z=np.asarray(saved['accepted'],dtype=float)
    c.stage_positive[:]=saved['stage_positive'];c.acetate_positive[:]=saved['acetate_positive']
    for group,present in zip(c.groups,saved['groups_present']):group['present']=present
    before=c.decode(z)[0].copy()
    with pytest.raises(stage._StageSourceOverflow) as error:c.derivative(saved['time_yr'],z)
    assert error.value.index==7
    event=c.condition_stage(z,saved['time_yr'],7,'accepted_poststep',error.value)
    assert event['log_incoming_allocation_rate_yr']> -np.inf and event['linear_allocation']==0.
    assert c.decode(z)[0].tobytes()==before.tobytes() and np.all(np.isfinite(c.derivative(saved['time_yr'],z)))
    conditioned=[7]
    for _ in range(len(z)):
        try:matrix=stage.coordinate_jacobian(saved['time_yr'],z,c);break
        except stage._StageSourceOverflow as error:
            conditioned.append(error.index);c.condition_stage(z,saved['time_yr'],error.index,'native_step',error)
    assert conditioned==[7,1] and np.all(np.isfinite(matrix))
    assert c.decode(z)[0].tobytes()==before.tobytes()


def test_actual_4550_saved_state_runs_forward_through_both_chart_conditions(monkeypatch):
    saved=json.loads((Path(__file__).parents[1]/'models/haze_world/review/dormancy_4550_regression.json').read_text())
    case=next(c for c in experiments.design() if c.case_id=='dormancy_0107')
    p=experiments.parameters(case);physical=np.asarray(saved['decoded_physical']);original=stage._Coordinates
    class Retained(original):
        def encode(self,initial):
            self.stage_positive[:]=saved['stage_positive'];self.acetate_positive[:]=saved['acetate_positive']
            for group,present in zip(self.groups,saved['groups_present']):group['present']=present
            return np.asarray(saved['accepted']).copy()
    monkeypatch.setattr(stage,'_Coordinates',Retained)
    result=stage.integrate_finite(physical,p,10.,stage.Census(minimum_cells=0.,census_yr=1.),sample_every_censuses=1,max_step=1.)
    assert result.status=='completed' and result.t[-1]==10.
    assert np.all(np.isfinite(result.y)) and np.all(result.y>=0.)
    events=result.metadata['stage_conditioning_events']
    assert events[0]['state_index']==7 and events[0]['phase']=='solver_construction'
    assert any(row['state_index']==1 for row in events)
    assert all(row['physical_state_bitwise_preserved'] and row['total_coordinates_bitwise_preserved'] for row in events)
    assert all(row['inventory_before']==row['inventory_after'] for row in events)
    assert np.all(np.isfinite(result.log_biomass[p.weights>0]))
    assert not result.extinction_events
    assert max(abs(model.redox_residual(v,p)) for v in result.y.T)<1e-16


def test_native_terminal_zero_time_notification_is_unchanged():
    p,y=setup();c=stage._Coordinates(y,p);state=c.encode(y);events=[]
    solver=stage._StageLSODA(c.derivative,1.,state,1.,nominal_max_step=1.,events=[],progress_events=events,max_step=1.,rtol=2e-8,atol=1e-8)
    assert solver.step() is None and solver.status=='finished' and solver.t==1.
    assert not events and not c.stage_conditioning_events
