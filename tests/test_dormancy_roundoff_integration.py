from types import SimpleNamespace

import numpy as np
import pytest
from scipy.integrate._ivp.radau import RadauDenseOutput

from terra_prisca.haze_world import dormancy as model
from terra_prisca.haze_world import dormancy_roundoff_integration as numerical
from terra_prisca.haze_world import habitat_coupling as habitat


def pure_coords(decode=None):
    return SimpleNamespace(decode=decode or (lambda value:(value.copy(),None)),
        roundoff_stagnation_stats=dict(attempts=0,accepted=0,declined={},extra_correction_exceptions=0,accepted_events=[]))


def correction():
    return np.array([1.,-900.]),np.zeros((3,2)),np.zeros((3,2)),np.ones(2),1e-4


def test_qualifier_accepts_exact64spacing_boundary_and_rejects65():
    y,Z,dW,scale,tol=correction();coords=pure_coords()
    for count,expected in [(64,True),(65,False)]:
        proposed=Z.copy();proposed[:,0]=count*np.spacing(y[0])
        okay,reason,event=numerical._qualify_update(y,Z,proposed,dW,scale,tol,coords)
        assert okay is expected
        assert event['coordinate_update']['maximum_update_spacings']==count
        assert event['physical_update']['maximum_update_spacings']==count
        assert reason==('accepted_roundoff_stagnation' if expected else 'coordinate_spacing')


def test_native_absolute_correction_norm_remains_independent_gate():
    y,Z,dW,scale,tol=correction();dW[:]=1.
    okay,reason,event=numerical._qualify_update(y,Z,Z.copy(),dW,scale,tol,pure_coords())
    assert not okay and reason=='native_absolute_norm' and event['correction_norm']==1.
    assert event['coordinate_update']['maximum_update_spacings']==0.


def test_retained_log_coordinate_cannot_hide_behind_zero_decoded_biomass():
    y,Z,dW,scale,tol=correction();proposed=Z.copy();proposed[:,1]=1e-8
    coords=pure_coords(lambda value:(np.array([value[0],0.]),None))
    okay,reason,event=numerical._qualify_update(y,Z,proposed,dW,scale,tol,coords)
    assert not okay and reason=='coordinate_spacing'
    assert event['coordinate_update']['worst_index']==1
    assert event['physical_update']['maximum_update_spacings']==0.


def test_decoded_physical_gate_is_independent_of_coordinate_gate():
    y,Z,dW,scale,tol=correction();proposed=Z.copy();proposed[:,0]=np.spacing(1.)
    coords=pure_coords(lambda value:(np.array([1e200 if value[0]>1. else 0.,0.]),None))
    okay,reason,event=numerical._qualify_update(y,Z,proposed,dW,scale,tol,coords)
    assert not okay and reason=='physical_spacing'
    assert event['coordinate_update']['maximum_update_spacings']==1.


@pytest.mark.parametrize('kind',['state','proposal','correction','scale','zero_scale','decoded'])
def test_nonfinite_or_invalid_inputs_never_qualify(kind):
    y,Z,dW,scale,tol=correction();proposed=Z.copy();coords=pure_coords()
    if kind=='state':Z[0,0]=np.nan
    elif kind=='proposal':proposed[0,0]=np.inf
    elif kind=='correction':dW[0,0]=np.nan
    elif kind=='scale':scale[0]=np.inf
    elif kind=='zero_scale':scale[0]=0.
    else:coords=pure_coords(lambda value:(np.array([np.nan,0.]),None))
    assert not numerical._qualify_update(y,Z,proposed,dW,scale,tol,coords)[0]


def test_minimum_subnormal_is_zero_stage_spacing():
    y=np.zeros(2);Z=np.zeros((3,2));proposed=Z.copy();proposed[0,0]=np.nextafter(0.,1.)
    okay,reason,event=numerical._qualify_update(y,Z,proposed,Z.copy(),np.ones(2),1e-4,pure_coords())
    assert okay and event['coordinate_update']['maximum_update_spacings']==1.
    assert event['coordinate_update']['machine_spacing']==np.nextafter(0.,1.)


@pytest.mark.parametrize('converged,iterations',[(True,2),(False,1)])
def test_outside_fallback_original_objects_return_without_rhs_or_lu(converged,iterations):
    y,Z,dW,scale,tol=correction();coords=pure_coords();rate=1.1
    forbidden=lambda *args:pytest.fail('Unexpected extra correction')
    result=numerical._finish(coords,converged,iterations,Z,rate,forbidden,0.,y,1.,Z.copy(),scale,tol,object(),object(),forbidden)
    assert result[0] is converged and result[1]==iterations and result[2] is Z and result[3] is rate
    assert coords.roundoff_stagnation_stats['attempts']==0


def test_actual_W_and_supplied_LU_are_used_without_reconstruction_or_mutation():
    y=np.array([1.,2.]);W=np.full((3,2),1e-15);Z=numerical._NATIVE['T'].dot(W)
    scale=np.ones(2);real_lu,complex_lu=object(),object();calls=[];rhs_calls=[];coords=pure_coords()
    F=np.array([2e-14,3e-14])
    def rhs(time,value):rhs_calls.append((time,value.copy()));return F.copy()
    def solve(lu,residual):
        calls.append((lu,residual.copy()))
        return np.zeros(2,dtype=complex if lu is complex_lu else float)
    before=(W.tobytes(),Z.tobytes(),y.tobytes(),scale.tobytes())
    result=numerical._finish(coords,False,2,Z,1.1,rhs,5.,y,.25,W,scale,1e-4,real_lu,complex_lu,solve)
    assert result[0] and result[1]==3 and np.array_equal(result[2],Z)
    assert calls[0][0] is real_lu and calls[1][0] is complex_lu and len(rhs_calls)==3
    matrix=np.tile(F,(3,1))
    assert np.array_equal(calls[0][1],matrix.T.dot(numerical._NATIVE['TI_REAL'])-numerical._NATIVE['MU_REAL']/.25*W[0])
    assert np.array_equal(calls[1][1],matrix.T.dot(numerical._NATIVE['TI_COMPLEX'])-numerical._NATIVE['MU_COMPLEX']/.25*(W[1]+1j*W[2]))
    assert (W.tobytes(),Z.tobytes(),y.tobytes(),scale.tobytes())==before
    assert coords.roundoff_stagnation_stats['accepted']==1


@pytest.mark.parametrize('kind',['nonfinite_rate','nonfinite_rhs','exception'])
def test_extra_correction_exclusions_preserve_original_or_propagate(kind):
    y,Z,dW,scale,tol=correction();coords=pure_coords();rate=np.inf if kind=='nonfinite_rate' else 1.1
    def rhs(*unused):
        if kind=='exception':raise RuntimeError('original physical guard')
        return np.full(2,np.nan)
    forbidden=lambda *args:pytest.fail('LU after nonfinite RHS')
    if kind=='exception':
        with pytest.raises(RuntimeError,match='physical guard'):
            numerical._finish(coords,False,2,Z,rate,rhs,0.,y,1.,Z.copy(),scale,tol,None,None,forbidden)
        assert coords.roundoff_stagnation_stats['extra_correction_exceptions']==1
    else:
        result=numerical._finish(coords,False,2,Z,rate,rhs,0.,y,1.,Z.copy(),scale,tol,None,None,forbidden)
        assert not result[0] and result[2] is Z and result[3] is rate


def setup():
    p=model.Dormancy(habitat.Habitats(),epsilon=.03)
    y=model.reference_state([30.,3e-4,4e-4,1e-4,.195],p)
    coords=numerical._Coordinates(y,p);state=coords.encode(y)
    return p,y,coords,state


@pytest.mark.parametrize('outcome',['success','failure','exception'])
def test_inherited_zero_predictor_restoration_and_new_dense_success(monkeypatch,outcome):
    p,y,coords,state=setup();state[4]=1e-30
    instance=numerical._NativeRoundoff(lambda t,v:np.zeros_like(v),0.,state,1.,coordinates=coords,
        max_step=1.,first_step=.01,rtol=2e-8,atol=1e-12,jac=np.zeros((len(state),len(state))))
    previous,new=object(),object();instance.sol=previous;before=instance.y.tobytes()
    def step(self):
        assert self.sol is None;self.sol=new
        if outcome=='exception':raise RuntimeError('injected native error')
        return outcome=='success','native result'
    monkeypatch.setattr(numerical._CollocationInjected,'_step_impl',step)
    if outcome=='exception':
        with pytest.raises(RuntimeError,match='native error'):instance._step_impl()
    else:assert instance._step_impl()[0] is (outcome=='success')
    assert instance.sol is (new if outcome=='success' else previous)
    assert instance.y.tobytes()==before and instance.t==0.


def test_verified_MRO_root_guard_and_original_module_globals(monkeypatch):
    p,y,coords,state=setup();coords.stage_positive[4]=True;state[4]=1e-20
    original_solver=numerical._NATIVE_STEP.__globals__['solve_collocation_system']
    monkeypatch.setitem(numerical._INJECTED_GLOBALS,'_NativeRadau',lambda *args,**kwargs:pytest.fail('Native before root guard'))
    instance=numerical._Radau(coords.derivative,0.,state,1.,nominal_max_step=1.,events=[],progress_events=[],
        max_step=1.,first_step=1e-6,rtol=2e-8,atol=np.full(len(state),1e-8))
    with pytest.raises(numerical.stage._StageSourceOverflow):instance._step_impl()
    assert instance._radau is None and instance.y.tobytes()==state.tobytes()
    assert numerical._Radau._step_impl is numerical.conditioned._Radau._step_impl
    assert numerical._NativeRoundoff._step_impl is numerical.predictor._NativeRadau._step_impl
    assert numerical._NATIVE_STEP.__globals__['solve_collocation_system'] is original_solver
    assert numerical._TRANSFORM['return_count']==1 and numerical._TRANSFORM['restored_ast_identical']


class FakeNative:
    def __init__(self,fun,time,state,bound,*,coordinates,**kwargs):
        self.t=time;self.y=state.copy();self.bound=bound
        self.nfev=self.njev=self.nlu=0;self.sol=None
    def _step_impl(self):
        old=self.y.copy();left=self.t;self.t=min(self.bound,left+10.)
        Q=np.zeros((len(old),3));Q[0,0]=-32.;Q[6,0]=-.25;Q[4]=[-.5e-27,1e-27,0.]
        self.y=old+Q.sum(axis=1);self.sol=RadauDenseOutput(left,self.t,old,Q)
        return True,None


def test_terminal_budget_and_domain_prefix_compose_without_endpoint_relaxation(monkeypatch):
    monkeypatch.setitem(numerical._INJECTED_GLOBALS,'_NativeRadau',FakeNative)
    p,y,coords,state=setup();y[2]=0.;y[-1]=.125
    result=numerical.integrate_finite(y,p,10.,numerical.Census(),sample_every_censuses=1,max_step=10.)
    assert result.status=='domain_exit' and result.t[-1]==pytest.approx(5.)
    assert result.y[0,-1]==pytest.approx(14.) and np.all(result.y>=0.)
    stats=result.metadata['positive_dense_stats'][0]
    assert stats['negative_native_endpoint_pieces']==1 and stats['negative_native_endpoint_rejections']==0
    assert result.metadata['terminal_dense_stats'][0]['broader_budget_extensions']==1
    assert stats['extensions'][0]['components'][0]['root_atol_squared_budget']==1e-24


@pytest.mark.parametrize('mode',['uncensored','implicit_uncensored','two_guilds','rare_census'])
def test_strict_budget_outside_terminal_face_and_ordinary_physical_composition(mode):
    p,y,coords,state=setup();kwargs={};process=numerical.Census()
    if mode=='uncensored':process=numerical.Census(minimum_cells=0.,census_yr=.01)
    elif mode=='rare_census':
        conversion=p.coupled.habitat_l_cm2*process.surface_cm2/process.cell_mass_gdw
        y[1]=1000./conversion;y[2]=0.
    if mode=='implicit_uncensored':result=numerical.integrate(y,p,.01,max_step=.001)
    else:result=numerical.integrate_finite(y,p,.01,process,sample_every_censuses=1,max_step=.001)
    assert result.status=='completed' and np.all(np.isfinite(result.y)) and np.all(result.y>=0.)
    assert result.metadata['terminal_dense_stats'][0]['broader_budget_pieces']==0
    assert result.metadata['numerical_variant']=='radau_dormancy_roundoff_stagnation'
    assert 'zero_stage_predictor_stats' in result.metadata and 'roundoff_stagnation_stats' in result.metadata
    for event in result.metadata['positive_dense_stats'][0]['extensions']:
        assert 'terminal_macro_certificate' not in event
    frozen=numerical.predictor._Coordinates(y,p);original=frozen.encode(y)
    fresh=numerical._Coordinates(y,p);new=fresh.encode(y)
    assert fresh.derivative(0.,new).tobytes()==frozen.derivative(0.,original).tobytes()
    assert max(abs(model.redox_residual(value,p)) for value in result.y.T)<1e-16
