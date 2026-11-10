from dataclasses import replace
from fractions import Fraction
from types import SimpleNamespace

import numpy as np
import pytest
from scipy.integrate import Radau as ScipyRadau,solve_ivp
from scipy.integrate._ivp.radau import RadauDenseOutput

from terra_prisca.haze_world import dormancy as model
from terra_prisca.haze_world import dormancy_radau_integration as numerical
from terra_prisca.haze_world import dormancy_face_integration as upstream
from terra_prisca.haze_world import habitat_coupling as habitat


def setup():
    p=model.Dormancy(habitat.Habitats(),epsilon=.03)
    y=model.reference_state([30.,3e-4,4e-4,1e-4,.195],p)
    c=numerical._Coordinates(y,p);state=c.encode(y)
    atol=np.r_[np.array([1e-7,1e-14,1e-14,1e-8,1e-14,1e-14,1e-11]),np.full(len(c.groups),1e-8)]
    atol[:c.m][c.stage_positive]=1e-12
    return p,y,c,state,atol


def polynomial(c,state,amplitude=1e-50,index=4,end=None):
    Q=np.zeros((len(state),3));Q[index]=[-.5*amplitude,amplitude,0.]
    finish=state+Q.sum(axis=1) if end is None else end
    return RadauDenseOutput(10.,11.,state.copy(),Q),finish.copy()


def ratio(value):return Fraction(int(value['n'],16),int(value['d'],16))


def test_tiny_chord_has_native_anchors_and_reconstructible_certificate():
    p,y,c,state,atol=setup();native,end=polynomial(c,state)
    before=(native.y_old.tobytes(),native.Q.tobytes(),end.tobytes())
    dense=numerical._Dense(native,end,c,atol)
    assert dense.repaired==[4] and c.positive_dense_stats['extended_pieces']==1
    assert dense(native.t_old).tobytes()==native.y_old.tobytes() and dense(native.t).tobytes()==end.tobytes()
    assert np.all(dense(np.linspace(10.,11.,101))[4]>=0.)
    assert (native.y_old.tobytes(),native.Q.tobytes(),end.tobytes())==before
    event=c.positive_dense_stats['extensions'][0];component=event['components'][0]
    original=(Fraction(0),*map(Fraction.from_float,native.Q[4]))
    chord=(Fraction(0),Fraction.from_float(end[4]),Fraction(0),Fraction(0))
    assert [ratio(v) for v in component['difference_coefficients_exact']]==list(a-b for a,b in zip(chord,original))
    assert event['native_y_old']==native.y_old.tolist() and event['native_y_end']==end.tolist() and event['native_Q']==native.Q.tolist()
    assert component['defect_upper']<=component['cap']==np.finfo(float).eps**2
    assert event['H_lower']>0. and event['cell_curve_redistribution_upper']>0.
    unit=[tuple([numerical._f(old),*map(numerical._f,row)]) for old,row in zip(native.y_old,native.Q)]
    theta=np.array([[float(x) for x in numerical._theta_coefficients(poly)] for poly in unit])
    norm=numerical._normalizer_certificate(unit,theta,event['group_indices'],event['group_positive_charts'],{4:chord},end)
    assert list(norm['original'])==[ratio(v) for v in event['original_H_coefficients_exact']]
    assert list(norm['regularized'])==[ratio(v) for v in event['regularized_H_coefficients_exact']]
    assert float(norm['lower'])>=event['H_lower']


def test_larger_defect_is_declined_and_original_check_rejects():
    p,y,c,state,atol=setup();native,end=polynomial(c,state,1e-20)
    dense=numerical._Dense(native,end,c,atol)
    assert not dense.repaired and c.positive_dense_stats['declined_defect']==1
    assert not numerical._positive_piece(dense,10.,11.,c,state)


@pytest.mark.parametrize('kind',['root','absent','chemical'])
def test_other_charts_absent_groups_and_chemicals_never_receive_chords(kind):
    p,y,c,state,atol=setup();index=4
    if kind=='root':c.stage_positive[4]=True
    elif kind=='absent':c.groups[0]['present']=False
    else:index=3;c.acetate_positive[0]=False;state[3]=0.
    native,end=polynomial(c,state,index=index)
    dense=numerical._Dense(native,end,c,atol)
    assert not dense.repaired


@pytest.mark.parametrize('index',[0,6,3,4])
def test_all_constrained_negative_native_endpoints_are_rejected(index):
    p,y,c,state,atol=setup();c.acetate_positive[0]=False;state[3]=0.
    native,end=polynomial(c,state);end[index]=-1e-50
    dense=numerical._Dense(native,end,c,atol)
    assert index in dense.negative_end
    assert not numerical._positive_piece(dense,10.,11.,c,state)
    assert not numerical._positive_piece(dense,10.,11.,c,state)
    assert c.positive_dense_stats['negative_native_endpoint_rejections']==1
    if index in (3,4):assert index not in dense.repaired


def test_positive_chord_and_polynomial_metadata_agree_to_roundoff():
    p,y,c,state,atol=setup();native,end=polynomial(c,state)
    dense=numerical._Dense(native,end,c,atol);grid=np.linspace(10.,11.,51)
    power=dense.yh@np.array([((grid-11.)/1.)**k for k in range(4)])
    assert np.allclose(power,dense(grid),rtol=8*np.finfo(float).eps,atol=1e-64)
    assert numerical._positive_piece(dense,10.,11.,c,state)


class FakeRadau:
    mode='tiny'
    def __init__(self,fun,time,state,bound,**options):
        self.fun=fun;self.t=time;self.y=state.copy();self.bound=bound
        self.nfev=self.njev=self.nlu=0;self.sol=None
    def _step_impl(self):
        old=self.y.copy();left=self.t;self.t=min(self.bound,left+1.)
        Q=np.zeros((len(old),3))
        if self.mode=='tiny':Q[4]=[-.5e-50,1e-50,0.]
        elif self.mode=='exit':Q[0,0]=-32.;Q[6,0]=-.25
        elif self.mode=='corner':Q[6,0]=.08
        self.y=old+Q.sum(axis=1);self.sol=RadauDenseOutput(left,self.t,old,Q)
        return True,None


def test_native_dense_cache_counts_each_extension_once(monkeypatch):
    p,y,c,state,atol=setup();monkeypatch.setattr(numerical,'Radau',FakeRadau)
    instance=numerical._Radau(c.derivative,0.,state,1.,nominal_max_step=1.,events=[],progress_events=[],max_step=1.,first_step=1e-6,rtol=2e-8,atol=atol)
    instance.step();a=instance.dense_output();b=instance.dense_output()
    assert a is b and c.positive_dense_stats['native_dense_pieces']==1
    assert c.positive_dense_stats['extended_pieces']==1 and c.positive_dense_stats['extended_components']==1


def test_domain_exit_uses_valid_prefix_despite_negative_later_native_endpoint(monkeypatch):
    class Exit(FakeRadau):mode='exit'
    monkeypatch.setattr(numerical,'Radau',Exit)
    p,y,c,state,atol=setup();y[-1]=.125
    result=numerical.integrate(y,p,2.,max_step=1.)
    assert result.status=='domain_exit' and result.t[-1]==pytest.approx(.5)
    assert result.y[-1,-1]==0. and result.y[0,-1]==pytest.approx(14.)
    stats=result.metadata['positive_dense_stats'][0]
    assert stats['negative_native_endpoint_pieces']==1 and stats['negative_native_endpoint_rejections']==0
    assert np.all(result.y>=0.)


def test_climate_vertices_remain_in_temperature_extrema(monkeypatch):
    class Corner(FakeRadau):mode='corner'
    monkeypatch.setattr(numerical,'Radau',Corner)
    p,y,c,state,atol=setup();y[-1]=.12
    result=numerical.integrate_finite(y,p,1.,numerical.Census(minimum_cells=0.,census_yr=1.),sample_every_censuses=1,max_step=1.)
    response=model.core.response(p.coupled.climate.case);vertices=response.ratios
    sampled=np.r_[.12,.20,vertices[(vertices>=.12)&(vertices<=.20)]]
    assert result.metadata['global_max_temperature_k']==max(model.core.temperature_k(sampled,p.coupled.climate))


def test_zero_width_exit_checks_accepted_point_not_extrapolated_polynomial():
    p,y,c,state,atol=setup();native,end=polynomial(c,state)
    end[0]=-1.;dense=numerical._Dense(native,end,c,atol)
    assert numerical._positive_piece(dense,10.,10.,c,state)


def test_lazy_initialization_keeps_initial_jacobian_conditioning_in_driver(monkeypatch):
    original=numerical._Radau._chemical_jacobian;fired=[]
    def request(self,time,state):
        if not fired:
            fired.append(True);raise numerical.stage._stage_error(1,time,state,'injected_initial_jacobian')
        return original(self,time,state)
    monkeypatch.setattr(numerical._Radau,'_chemical_jacobian',request)
    p,y,c,state,atol=setup()
    result=numerical.integrate_finite(y,p,.01,numerical.Census(minimum_cells=0.,census_yr=.001),sample_every_censuses=1,max_step=.001)
    assert result.status=='completed' and len(fired)==1
    events=result.metadata['stage_conditioning_events']
    assert events[0]['time_yr']==0. and events[0]['phase']=='native_step'
    assert events[0]['physical_state_bitwise_preserved'] and events[0]['total_coordinates_bitwise_preserved']
    work=result.metadata['radau_work'][0]
    assert work['constructor_failures']==1 and work['constructor_jacobian_attempts']>=1
    assert work['jacobian_attempts']>=work['constructor_jacobian_attempts']


def test_failed_native_state_is_not_adopted_and_rhs_counts_are_synchronized(monkeypatch):
    observations=[];fired=[];ceilings=[]
    class FailOnce(ScipyRadau):
        def __init__(self,fun,*args,**kwargs):
            ceilings.append(kwargs['max_step'])
            def seen(t,y):observations.append(float(t));return fun(t,y)
            super().__init__(seen,*args,**kwargs)
        def _step_impl(self):
            if not fired:
                fired.append(True)
                for delta in (1e-5,2e-5,4e-5):self.fun(self.t+delta,self.y)
                self.y=self.y*1.01;self.t+=4e-5
                return False,'injected native failure'
            return super()._step_impl()
    monkeypatch.setattr(numerical,'Radau',FailOnce)
    p,y,c,state,atol=setup()
    instance=numerical._Radau(c.derivative,0.,state,.01,nominal_max_step=.01,events=[],progress_events=[],max_step=.01,first_step=1e-6,rtol=2e-8,atol=atol)
    instance.step()
    assert instance.status=='failed' and instance.t==0. and instance.y.tobytes()==state.tobytes()
    assert instance.nfev==len(observations)
    fired.clear();observations.clear();ceilings.clear()
    result=numerical.integrate_finite(y,p,.01,numerical.Census(minimum_cells=0.,census_yr=.001),sample_every_censuses=1,max_step=.01)
    assert result.status=='completed' and result.metadata['solver_failure_retries']==1
    assert result.metadata['nfev']==len(observations)==result.metadata['radau_work'][0]['rhs_evaluations']
    reduced=next(i for i,value in enumerate(ceilings) if value<.01)
    assert .01 in ceilings[reduced+1:] and np.all(result.y>=0.)


def test_exception_counter_finally_does_not_adopt_trial_state(monkeypatch):
    observations=[]
    class Broken(ScipyRadau):
        def __init__(self,fun,*args,**kwargs):
            def seen(t,y):observations.append(t);return fun(t,y)
            super().__init__(seen,*args,**kwargs)
        def _step_impl(self):
            self.fun(self.t+.001,self.y);self.y=self.y*1.01;self.t+=.001
            raise RuntimeError('unrelated native error')
    monkeypatch.setattr(numerical,'Radau',Broken)
    p,y,c,state,atol=setup();instance=numerical._Radau(c.derivative,0.,state,.01,nominal_max_step=.01,events=[],progress_events=[],max_step=.01,first_step=1e-6,rtol=2e-8,atol=atol)
    with pytest.raises(RuntimeError,match='unrelated native error'):instance.step()
    assert instance.t==0. and instance.y.tobytes()==state.tobytes()
    assert instance.nfev==len(observations)


def test_census_restart_and_ledger_are_retained():
    base=habitat.Habitats(patches=(habitat.Patch('bulk',1.,'buffered',286.),))
    p=model.Dormancy(base,epsilon=.03);process=numerical.Census(census_yr=.5)
    conversion=p.coupled.habitat_l_cm2*process.surface_cm2/process.cell_mass_gdw
    y=model.reference_state([21.,2./conversion,4e-4,1e-4,.195],p)
    result=numerical.integrate_finite(y,p,4.,process,sample_every_censuses=1,max_step=.5)
    assert result.status=='completed' and result.extinction_events
    assert all(event['time_yr']>0. for event in result.extinction_events)
    assert np.all(result.y>=0.)
    assert result.ledger['inventory_jump_h2_mol_l'].sum()==sum(event['inventory_jump_h2_mol_l'] for event in result.extinction_events)
    assert np.array_equal(result.census_times,np.arange(0.,4.1,.5))


def test_physical_flow_zero_switching_and_minima_match_independent_radau():
    p,y,c,state,atol=setup();p=replace(p,switching_factor=0.)
    result=numerical.integrate_finite(y,p,1.,numerical.Census(minimum_cells=0.,census_yr=.1),sample_every_censuses=1,max_step=.1)
    independent=solve_ivp(lambda t,v:model.rhs(v,p,trial_extension=True),(0.,1.),y,method='Radau',rtol=2e-10,atol=[1e-9,1e-15,1e-15,1e-15,1e-15,1e-15,1e-13],t_eval=result.t)
    assert result.status=='completed' and independent.success
    assert np.allclose(result.y,independent.y,rtol=4e-6,atol=2e-11)
    assert np.all(result.y[p.dormant_indices]==0.) and np.all(result.y>=0.)
    assert max(abs(model.redox_residual(v,p)) for v in result.y.T)<1e-16
    assert np.all(result.global_continuous_min_log_biomass<=np.log(result.y[1:3]).min(axis=1)+1e-10)


def test_terminal_notification_needs_no_native_backend():
    p,y,c,state,atol=setup();instance=numerical._Radau(c.derivative,1.,state,1.,nominal_max_step=1.,events=[],progress_events=[],max_step=1.,rtol=2e-8,atol=atol)
    assert instance.step() is None and instance.status=='finished' and instance._radau is None


def test_absent_guild_and_rare_retained_log_stock_remain_distinct():
    p,y,c,state,atol=setup();p=replace(p,switching_factor=0.)
    y[1]=0.;y[2]=np.nextafter(0.,1.)
    result=numerical.integrate_finite(y,p,1.,numerical.Census(minimum_cells=0.,census_yr=.1),sample_every_censuses=1,max_step=.1)
    assert result.status=='completed'
    assert np.all(result.y[1]==0.) and np.all(np.isneginf(result.log_biomass[:,0]))
    assert np.all(np.isfinite(result.log_biomass[:,1]))
    assert result.global_continuous_min_log_biomass[1]<-740


def test_shared_habitat_flow_and_contemporaneous_global_minima():
    base=habitat.Habitats(patches=(habitat.Patch('bulk',.96),habitat.Patch('warm',.02,'buffered',286.),habitat.Patch('cold',.02,'buffered',278.)),dispersal_yr=.001)
    p=model.Dormancy(base,epsilon=.003)
    y=model.reference_state(habitat.embed_single([30.,3e-4,4e-4,1e-4,.195],base),p)
    result=numerical.integrate_finite(y,p,.2,numerical.Census(minimum_cells=0.,census_yr=.05),sample_every_censuses=1,max_step=.05)
    reference=solve_ivp(lambda t,v:model.rhs(v,p,trial_extension=True),(0.,.2),y,method='Radau',rtol=2e-10,
        atol=np.r_[np.tile([1e-9,1e-15,1e-15,1e-15,1e-15,1e-15],3),1e-13],t_eval=result.t)
    assert result.status=='completed' and reference.success
    assert np.allclose(result.y,reference.y,rtol=4e-6,atol=2e-11)
    masses=np.sum(p.weights[:,None,None]*(result.y[p.biomass_indices]+result.y[p.dormant_indices]),axis=0)
    assert np.all(result.global_continuous_min_log_biomass<=np.log(masses).min(axis=1)+1e-10)
    assert max(abs(model.redox_residual(v,p)) for v in result.y.T)<1e-16


def test_census_interior_restart_uses_chord_without_mutating_native_end(monkeypatch):
    backends=[]
    class CensusBackend(FakeRadau):
        def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);backends.append(self)
        def _step_impl(self):
            old=self.y.copy();left=self.t;self.t=min(self.bound,left+1.)
            Q=np.zeros((len(old),3))
            if old[1]>0.:Q[4]=[-.5e-50,1e-50,0.];Q[7,0]=-2.
            self.y=old+Q.sum(axis=1);self.native_end_bytes=self.y.tobytes()
            self.sol=RadauDenseOutput(left,self.t,old,Q)
            return True,None
    monkeypatch.setattr(numerical,'Radau',CensusBackend)
    p,y,c,state,atol=setup();process=numerical.Census(census_yr=.5)
    conversion=p.coupled.habitat_l_cm2*process.surface_cm2/process.cell_mass_gdw
    y[1]=2./conversion
    result=numerical.integrate_finite(y,p,1.,process,sample_every_censuses=1,max_step=1.)
    assert result.status=='completed' and result.extinction_events[0]['time_yr']==.5
    assert result.metadata['positive_dense_stats'][0]['extended_pieces']==1
    assert len(backends)==2 and backends[0].y.tobytes()==backends[0].native_end_bytes
    assert result.y[1,-1]==0. and result.y[4,-1]==0.
    assert result.extinction_events[0]['removed_cells']<1.
