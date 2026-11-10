from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path

import numpy as np
import pytest
from scipy.integrate import solve_ivp

from terra_prisca.haze_world import dormancy as model
from terra_prisca.haze_world import dormancy_experiments as experiments
from terra_prisca.haze_world import dormancy_face_integration as face
from terra_prisca.haze_world import dormancy_stage_integration as stage
from terra_prisca.haze_world import habitat_coupling as habitat


def setup():
    p=model.Dormancy(habitat.Habitats(),epsilon=.03)
    y=model.reference_state([21.,0.,4e-4,1e-4,.195],p);y[4]=1e-4
    c=face._Coordinates(y,p);z=c.encode(y)
    return p,y,c,z


def retained():
    saved=json.loads((Path(__file__).parents[1]/'models/haze_world/review/dormancy_2241_regression.json').read_text())
    p=experiments.parameters(experiments.design()[85]);physical=np.asarray(saved['decoded_physical'])
    c=face._Coordinates(physical,p);z=np.asarray(saved['coordinates'])
    c.stage_positive[:]=saved['stage_positive'];c.acetate_positive[:]=saved['acetate_positive']
    for group,on in zip(c.groups,saved['groups_present']):group['present']=on
    return saved,p,physical,c,z


def test_face_is_returned_float_zero_not_algebraic_source_absence():
    saved,p,y,c,z=retained();before=stage.coordinate_jacobian(saved['time_yr'],z,c)
    rate=stage.frozen.frozen._Coordinates.derivative(c,saved['time_yr'],z)
    matrix=face.coordinate_jacobian(saved['time_yr'],z,c)
    assert z[7]==0. and not c.stage_positive[7] and rate[7]==0.
    assert np.max(abs(before))>1e184 and np.max(abs(matrix))<2e7
    assert matrix[7,7]==before[7,7]
    assert np.count_nonzero(matrix[7])==1 and np.count_nonzero(matrix[:,7])==1
    event=c.zero_face_newton_stats[7]
    assert event['first_retained_incoming_log_source']
    assert event['first_log_incoming_allocation_rate_yr']==pytest.approx(-897.8461311734387)
    assert event['calls']==1


@pytest.mark.parametrize('value',[np.nextafter(0.,1.),1e-200,1e-12])
def test_any_positive_allocation_restores_row_and_column(value):
    p,y,c,z=setup();z[0]=30.;z[1]=value
    original=stage.coordinate_jacobian(0.,z,c);matrix=face.coordinate_jacobian(0.,z,c)
    assert 1 not in c.zero_face_newton_stats
    assert np.array_equal(original[1],matrix[1]) and np.array_equal(original[:,1],matrix[:,1])


def test_subnormal_positive_returned_source_is_never_suppressed():
    base=habitat.Habitats(patches=(habitat.Patch('bulk',.5),habitat.Patch('warm',.5,'buffered',286.)),dispersal_yr=1e-9)
    p=model.Dormancy(base,epsilon=.03)
    y=model.reference_state(habitat.embed_single([30.,0.,4e-4,1e-4,.195],base),p);y[4]=1e-4
    c=face._Coordinates(y,p);z=c.encode(y)
    c.stage_positive[10]=False;z[10]=np.nextafter(0.,1.);z[7]=0.;c.stage_positive[7]=False
    rate=stage.frozen.frozen._Coordinates.derivative(c,0.,z)
    assert 0.<rate[7]<np.finfo(float).tiny
    original=stage.coordinate_jacobian(0.,z,c);matrix=face.coordinate_jacobian(0.,z,c)
    assert 7 not in c.zero_face_newton_stats
    assert np.array_equal(original[7],matrix[7]) and np.array_equal(original[:,7],matrix[:,7])


def test_each_matrix_rechecks_source_and_restores_waking_couplings():
    p,y,c,z=setup();initial=face.coordinate_jacobian(0.,z,c)
    assert c.zero_face_newton_stats[1]['calls']==1
    z[0]=30.;rate=stage.frozen.frozen._Coordinates.derivative(c,1.,z)
    assert rate[1]>0.
    expected=stage.coordinate_jacobian(1.,z,c);actual=face.coordinate_jacobian(1.,z,c)
    assert c.zero_face_newton_stats[1]['calls']==1
    assert np.array_equal(expected[1],actual[1]) and np.array_equal(expected[:,1],actual[:,1])
    assert not np.array_equal(initial[:,1],actual[:,1])


def test_matrix_does_not_consume_chart_requests_or_mutate_stocks_or_charts():
    p,y,c,z=setup();c._pending_chemical={0:12.};c._pending_chemical_causes={0:{'marker':'retained'}}
    before=z.copy();physical=c.decode(z)[0].copy();stage_flags=c.stage_positive.copy();chemical_flags=c.acetate_positive.copy()
    pending=deepcopy(c._pending_chemical);causes=deepcopy(c._pending_chemical_causes)
    face.coordinate_jacobian(1.,z,c)
    assert z.tobytes()==before.tobytes() and c.decode(z)[0].tobytes()==physical.tobytes()
    assert np.array_equal(c.stage_positive,stage_flags) and np.array_equal(c.acetate_positive,chemical_flags)
    assert c._pending_chemical==pending and c._pending_chemical_causes==causes
    assert not c.chemical_events and not c.chemical_conditioning_requests and not c.stage_conditioning_events


def test_saved_2241_phase_progresses_without_overflow_loop(monkeypatch):
    saved,p,y,c,z=retained();original=face._Coordinates
    class Retained(original):
        def encode(self,initial):
            self.stage_positive[:]=saved['stage_positive'];self.acetate_positive[:]=saved['acetate_positive']
            for group,on in zip(self.groups,saved['groups_present']):group['present']=on
            return np.asarray(saved['coordinates']).copy()
    monkeypatch.setattr(face,'_Coordinates',Retained)
    result=face.integrate_finite(y,p,.1,face.Census(minimum_cells=0.,census_yr=.01),sample_every_censuses=1,max_step=.1)
    assert result.status=='completed' and result.t[-1]==.1
    assert result.metadata['accepted_steps']<100 and result.metadata['solver_failure_retries']==0
    assert not result.metadata['acetate_trial_retry_events'] and result.metadata['allocation_positivity_retries']==0
    assert np.all(np.isfinite(result.y)) and np.all(result.y>=0.)
    assert np.all(result.y[[1,7]]==0.)
    assert result.metadata['zero_face_newton_stats'][0][7]['calls']>0
    assert max(abs(model.redox_residual(v,p)) for v in result.y.T)<1e-16


def test_later_waking_establishes_from_exact_zero_without_seed():
    p,y,c,z=setup();process=face.Census(minimum_cells=0.,census_yr=.001)
    a=stage.integrate_finite(y,p,.01,process,sample_every_censuses=1,max_step=.001)
    b=face.integrate_finite(y,p,.01,process,sample_every_censuses=1,max_step=.001)
    assert b.status=='completed' and b.y[1,0]==0. and b.y[1].max()>5e-5
    assert np.allclose(a.y,b.y,rtol=3e-7,atol=1e-13) and np.all(b.y>=0.)
    assert not b.extinction_events


def test_nongated_flow_is_bitwise_unchanged():
    p,y,c,z=setup();y[1]=3e-4;y[5]=1e-4
    process=face.Census(minimum_cells=0.,census_yr=.25)
    a=stage.integrate_finite(y,p,1.,process,sample_every_censuses=1,max_step=.1)
    b=face.integrate_finite(y,p,1.,process,sample_every_censuses=1,max_step=.1)
    assert b.metadata['zero_face_newton_stats']==[{}]
    for name in ('t','y','log_biomass','global_continuous_min_log_biomass','census_times','census_activity'):
        assert np.array_equal(getattr(a,name),getattr(b,name))
    for name in a.ledger:assert np.array_equal(a.ledger[name],b.ledger[name])


def test_physical_radau_precision_and_minimum_accounting():
    p,y,c,z=setup();process=face.Census(minimum_cells=0.,census_yr=.1)
    result=face.integrate_finite(y,p,1.,process,sample_every_censuses=1,max_step=.1)
    reference=solve_ivp(lambda t,v:model.rhs(v,p,trial_extension=True),(0.,1.),y,method='Radau',rtol=2e-10,
        atol=[1e-9,1e-15,1e-15,1e-15,1e-15,1e-15,1e-13],t_eval=result.t)
    assert reference.success and result.status=='completed'
    assert np.allclose(result.y,reference.y,rtol=4e-6,atol=2e-11)
    mass=result.y[1:3]+result.y[4:6]
    assert np.all(result.global_continuous_min_log_biomass<=np.log(mass).min(axis=1)+1e-10)
    assert max(abs(model.redox_residual(v,p)) for v in result.y.T)<1e-16


def test_nonzero_census_and_zero_switching_contract_unchanged():
    p,y,c,z=setup();p=replace(p,switching_factor=0.);process=face.Census(census_yr=.25)
    conversion=p.coupled.habitat_l_cm2*process.surface_cm2/process.cell_mass_gdw
    y[1]=.5/conversion;y[4]=.4/conversion
    a=stage.integrate_finite(y,p,.5,process,sample_every_censuses=1,max_step=.25)
    b=face.integrate_finite(y,p,.5,process,sample_every_censuses=1,max_step=.25)
    assert a.extinction_events==b.extinction_events and a.extinction_events
    for key in a.ledger:assert np.array_equal(a.ledger[key],b.ledger[key])
    assert np.array_equal(a.y,b.y)
