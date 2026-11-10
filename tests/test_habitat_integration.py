from dataclasses import replace

import numpy as np
import pytest
from scipy.linalg import expm
from scipy.optimize import brentq
from scipy.optimize import minimize_scalar

from terra_prisca.haze_world import population_coupling as single
from terra_prisca.haze_world import habitat_coupling as model
from terra_prisca.haze_world import habitat_integration as solver
from terra_prisca.haze_world import refuge_integration as legacy_solver


def mixed():
    return next(e['y'] for e in single.equilibrium_states(single.reference()) if e['kind']=='mixed')


def habitats(d=0.,weights=(.96,.02,.02),base=None):
    return model.Habitats(base or single.reference(),
        (model.Patch('bulk',weights[0]),model.Patch('warm',weights[1],'buffered',286.),
         model.Patch('cold',weights[2],'buffered',278.)),d)


def toy(monkeypatch,p,growth,ratio_rate=0.,production=0.,decay=0.):
    def g(y):
        return np.asarray(growth(y) if callable(growth) else growth,dtype=float)
    def fluxes(y,params,**kwargs):
        values=g(y)
        return {'local':[dict(net_growth_yr=values[j],acetate_production_mol_l_yr=production*y[4*j+1],
                    acetate_production_per_gdw_yr=production,k_rec_yr=0.,k_other_yr=decay)
                    if w else None for j,w in enumerate(params.weights)]}
    def rhs(y,params,**kwargs):
        result=np.zeros(params.state_size);stocks=y[params.biomass_indices]
        exchange=params.dispersal_yr*(params.weights @ stocks-stocks)
        result[params.biomass_indices]=(stocks*g(y)+exchange)*(params.weights>0)[:,None]
        result[3:-1:4]=production*stocks[:,0]-decay*y[3:-1:4]
        result[-1]=ratio_rate
        return result
    monkeypatch.setattr(model,'fluxes',fluxes);monkeypatch.setattr(model,'rhs',rhs)
    return p


def test_coordinate_chain_rule_preserves_three_patch_physics_and_allocation_normalization():
    p=habitats(.001)
    y=model.embed_single(mixed(),p)*np.r_[np.tile([1.001,.999,1.001,1.002],3),1.000001]
    coordinates=solver._Coordinates(y,p);internal=coordinates.encode(y)
    internal[p.biomass_indices]*=1.001
    physical,_=coordinates.decode(internal)
    np.testing.assert_allclose(physical,y,rtol=2e-14,atol=1e-14)
    direction=coordinates.derivative(0.,internal)
    h=1e-7
    actual=(coordinates.decode(internal+h*direction)[0]-coordinates.decode(internal-h*direction)[0])/(2*h)
    np.testing.assert_allclose(actual,model.rhs(y,p),rtol=3e-5,atol=1e-8)
    np.testing.assert_allclose(direction[p.biomass_indices].sum(axis=0),0.,atol=1e-15)


def test_selected_tracking_trajectory_matches_published_two_patch_implementation():
    from terra_prisca.haze_world.refuge_experiments import conditional_start,design,parameters,seed_state
    case=design('pilot')[1];old=parameters(case)
    initial,_=conditional_start(old,1,201)
    y,_=seed_state(case,initial['y'])
    p=model.Habitats(old.base,(model.Patch('cold',old.weights[0],'tracking',old.offsets[0]),
                              model.Patch('warm',old.weights[1],'tracking',old.offsets[1])),old.dispersal_yr)
    result=solver.integrate_finite(y,p,100.,solver.Census(minimum_cells=0,census_yr=1),sample_every_censuses=1)
    control=legacy_solver.integrate_finite(y,old,100.,legacy_solver.Census(minimum_cells=0,census_yr=1),sample_every_censuses=1)
    assert result.success and control.success
    np.testing.assert_array_equal(result.t,control.t)
    np.testing.assert_allclose(result.y,control.y,rtol=5e-6,atol=1e-9)
    np.testing.assert_allclose(result.global_continuous_min_log_biomass,control.global_continuous_min_log_biomass,atol=2e-5)


def test_zero_refuges_follow_single_habitat_and_ignore_inactive_temperatures():
    p=model.Habitats(single.reference(),(model.Patch('bulk',1.),model.Patch('warm',0.,'buffered',1000.),
                                        model.Patch('cold',0.,'buffered',100.)),1.)
    initial=mixed()*[1.01,.99,1.01,1.001,1.00001]
    result=solver.integrate(model.embed_single(initial,p),p,10.)
    control=single.integrate(initial,p.base,10.,sample_times=result.t)
    np.testing.assert_allclose(np.vstack((result.y[:4],result.y[-1])),control.y,rtol=4e-6,atol=1e-9)
    assert np.all(result.y[4:-1]==0)
    assert np.all(result.physiology_domains[1:]=='inactive')


def test_three_patch_exchange_recovers_local_zeros_without_creating_an_absent_guild(monkeypatch):
    p=toy(monkeypatch,habitats(.1),[[0.,100.]]*3)
    initial=model.embed_single(mixed(),p);initial[p.biomass_indices]=0.;initial[5]=.001
    result=solver.integrate(initial,p,30.)
    total=p.weights[1]*.001
    expected=total+(initial[p.biomass_indices[:,0],None]-total)*np.exp(-p.dispersal_yr*result.t)
    np.testing.assert_allclose(result.y[p.biomass_indices[:,0]],expected,rtol=4e-6,atol=1e-12)
    np.testing.assert_allclose(p.weights @ result.y[p.biomass_indices[:,0]],total,rtol=2e-13)
    assert np.all(result.y[p.biomass_indices[:,1]]==0)
    assert np.all(np.isneginf(result.log_biomass[:,1]))
    assert result.y[9,0]==0 and result.y[9,-1]>0


def test_shared_rare_minima_match_a_three_patch_linear_population_system(monkeypatch):
    growth=np.array([-2.,.2,1.])
    p=toy(monkeypatch,habitats(.01,weights=(.6,.2,.2)),np.column_stack((growth,np.zeros(3))))
    initial=model.embed_single(mixed(),p);initial[p.biomass_indices]=0.
    initial[p.biomass_indices[:,0]]=1e-25
    result=solver.integrate(initial,p,10.)
    matrix=np.diag(growth-p.dispersal_yr)+p.dispersal_yr*np.outer(np.ones(3),p.weights)
    exact=lambda t:expm(matrix*t) @ np.full(3,1e-25)
    expected=np.array([exact(t) for t in result.t]).T
    np.testing.assert_allclose(result.y[p.biomass_indices[:,0]],expected,rtol=4e-6,atol=1e-45)
    for j in (0,):
        minimum=minimize_scalar(lambda t:np.log(exact(t)[j]),bounds=(0.,10.),method='bounded')
        assert result.continuous_min_log_biomass[j,0]==pytest.approx(minimum.fun,abs=2e-6)
        assert result.continuous_min_times_yr[j,0]==pytest.approx(minimum.x,abs=3e-5)
    minimum=minimize_scalar(lambda t:np.log(p.weights @ exact(t)),bounds=(0.,10.),method='bounded')
    assert result.global_continuous_min_log_biomass[0]==pytest.approx(minimum.fun,abs=2e-6)
    assert result.global_continuous_min_times_yr[0]==pytest.approx(minimum.x,abs=3e-5)


def test_tiny_exchange_keeps_rare_sink_populations_numerically_resolved(monkeypatch):
    growth=np.array([-10.,0.,-20.])
    p=toy(monkeypatch,habitats(1e-9),np.column_stack((growth,np.zeros(3))))
    initial=model.embed_single(mixed(),p);initial[p.biomass_indices]=0.;initial[5]=.001
    result=solver.integrate(initial,p,10.)
    matrix=np.diag(growth-p.dispersal_yr)+p.dispersal_yr*np.outer(np.ones(3),p.weights)
    expected=expm(matrix*10.) @ initial[p.biomass_indices[:,0]]
    np.testing.assert_allclose(result.y[p.biomass_indices[:,0],-1],expected,rtol=1e-5,atol=1e-23)
    relative=abs(model.rhs(result.y[:,-1],p)[p.biomass_indices[:,0]]/expected)
    assert max(relative)<1e-4


def test_local_cull_recolonization_and_conservative_mass_ledger(monkeypatch):
    p=toy(monkeypatch,habitats(.1,base=replace(single.reference(),habitat_l_cm2=1.)),[[0.,0.]]*3)
    initial=model.embed_single(mixed(),p);initial[p.biomass_indices]=0
    initial[5]=100./p.weights[1];initial[9]=.5/p.weights[2]
    result=solver.integrate_finite(initial,p,20.,solver.Census(cell_mass_gdw=1.,surface_cm2=1.),sample_every_censuses=1)
    assert len(result.extinction_events)==1 and result.extinction_events[0]['patch']=='cold'
    assert result.extinction_events[0]['time_yr']==0
    assert result.ledger['culled_cells'].sum()==pytest.approx(.5)
    assert result.ledger['culled_h2_mol'].sum()==pytest.approx(.5*single.ASSIMILATION_A)
    assert result.y[9,-1]>0
    np.testing.assert_allclose(p.weights @ result.y[p.biomass_indices[:,0]],100.,rtol=2e-12)
    assert np.isneginf(result.after_census_min_log_biomass[2,0])
    assert result.global_pre_extinction_min_log_biomass[0]==pytest.approx(np.log(100.),abs=2e-12)


def test_global_loss_remains_absorbing_after_environment_improves(monkeypatch):
    p=habitats(.1,base=replace(single.reference(),habitat_l_cm2=1.))
    p=toy(monkeypatch,p,lambda y:[[-1. if y[-1]<.192 else 100.,0.]]*3,ratio_rate=.001)
    initial=model.embed_single(mixed(),p);initial[p.biomass_indices]=0.
    initial[p.biomass_indices[:,0]]=2./p.weights;initial[-1]=.19
    result=solver.integrate_finite(initial,p,4.,solver.Census(census_yr=1.,cell_mass_gdw=1.,surface_cm2=1.),sample_every_censuses=1)
    assert len(result.extinction_events)==3
    assert all(e['time_yr']==1. for e in result.extinction_events)
    assert np.all(result.y[p.biomass_indices[:,0]][:,result.t>=1.]==0.)
    assert result.global_pre_extinction_min_log_biomass[0]==pytest.approx(np.log(6.)-1.,abs=2e-6)
    assert np.isneginf(result.global_after_census_min_log_biomass[0])


def test_global_minimum_is_not_sum_of_asynchronous_patch_minima(monkeypatch):
    p=model.Habitats(single.reference(),tuple(model.Patch(str(j),1/3) for j in range(3)),0.)
    centers=np.array([1.,5.,9.]);scale=1e-20
    p=toy(monkeypatch,p,lambda y:np.column_stack((.2*((y[-1]-.19)/.001-centers),np.zeros(3))),ratio_rate=.001)
    initial=model.embed_single(mixed(),p);initial[p.biomass_indices]=0.
    initial[p.biomass_indices[:,0]]=scale*np.exp(.1*centers**2);initial[-1]=.19
    result=solver.integrate(initial,p,10.,max_step=.2)
    np.testing.assert_allclose(result.continuous_min_times_yr[:,0],centers,atol=3e-5)
    assert result.global_continuous_min_times_yr[0]==pytest.approx(5.,abs=3e-5)
    expected=np.log(scale*(2*np.exp(1.6)+1)/3)
    assert result.global_continuous_min_log_biomass[0]==pytest.approx(expected,abs=2e-6)
    assert np.exp(expected)>3*(p.weights @ np.exp(result.continuous_min_log_biomass[:,0]))


def test_zero_acetate_start_and_log_production_below_physical_underflow(monkeypatch):
    p=toy(monkeypatch,habitats(.01),[[0.,0.]]*3,production=.01,decay=1.)
    initial=model.embed_single(mixed(),p);initial[p.biomass_indices]=0.;initial[p.biomass_indices[:,0]]=.001;initial[3:-1:4]=0.
    result=solver.integrate(initial,p,20.)
    expected=1e-5*(-np.expm1(-result.t))
    np.testing.assert_allclose(result.y[3:-1:4],np.tile(expected,(3,1)),rtol=3e-6,atol=1e-13)
    assert np.all(result.y>=0) and np.all(result.y[3:-1:4,0]==0)
    assert len(result.metadata['acetate_coordinate_switches'])==3
    p=toy(monkeypatch,p,[[-1.,0.]]*3,production=1.,decay=2.)
    initial[p.biomass_indices[:,0]]=1e-20;initial[3:-1:4]=1e-20
    result=solver.integrate(initial,p,1000.)
    np.testing.assert_allclose(result.log_acetate,np.tile(np.log(1e-20)-result.t,(3,1)),atol=3e-6)
    assert np.all(result.y[p.biomass_indices[:,0],-1]==0)
    assert np.all(np.isfinite(result.log_biomass[:,0,-1]))


def test_exit_is_detected_on_a_nonmonotone_climate_path_and_fixed_refuge_is_constant(monkeypatch):
    p=model.Habitats(single.reference(),(model.Patch('bulk',.96),model.Patch('warm',.02,'tracking',10.),
                                        model.Patch('cold',.02,'buffered',278.)),0.)
    p=toy(monkeypatch,p,[[0.,0.]]*3,ratio_rate=.01)
    initial=model.embed_single(mixed(),p);initial[-1]=.01
    root=brentq(lambda r:single.temperature_k(r,p.base.climate)+10.-303.15,.01,.166)
    result=solver.integrate(initial,p,18.5)
    assert result.status=='domain_exit'
    assert result.t[-1]==pytest.approx((root-.01)/.01,abs=1e-7)
    assert result.temperatures_k[1,-1]==pytest.approx(303.15,abs=1e-8)
    np.testing.assert_array_equal(result.temperatures_k[2],278.)


def test_dense_temperature_and_mean_departure_include_unsampled_peak(monkeypatch):
    p=toy(monkeypatch,habitats(),[[0.,0.]]*3,ratio_rate=.01)
    initial=model.embed_single(mixed(),p);initial[-1]=.01
    result=solver.integrate_finite(initial,p,18.5,solver.Census(minimum_cells=0),sample_every_censuses=100)
    peak=max(single.response(p.base.climate.case).temperatures_k)
    assert result.success
    assert result.metadata['global_max_temperature_k']==peak
    assert peak>max(result.temperatures_k[0])+.1
    np.testing.assert_allclose(result.metadata['patch_min_temperature_k'][1:],[286.,278.])
    np.testing.assert_allclose(result.metadata['patch_max_temperature_k'][1:],[286.,278.])
    assert result.metadata['temperature_mean_departure_min_k']==pytest.approx(.02*(286.-peak)+.02*(278.-peak))


def test_exact_zero_last_allocation_is_anchored_without_creating_mass():
    p=habitats(.001);initial=model.embed_single(mixed(),p);initial[9]=0.
    coordinates=solver._Coordinates(initial,p);start=coordinates.encode(initial)
    class Dense:
        t_old,t,h=0.,1.,1.
        def __init__(self,coefficients):
            self.yh=np.zeros((len(start),3));self.yh[:,0]=start
            self.yh[9,:len(coefficients)]=coefficients
        def __call__(self,time):return np.polynomial.polynomial.polyval(time-1.,self.yh.T)
    dense=Dense([7.07087986e-9,7.07087996e-9])
    assert dense(0.)[9]<0
    minima,at=solver._dense_minima(dense,0.,1.,coordinates,start)
    assert np.isneginf(minima[2,0]) and at[2,0]==0.
    start[9]=.1;dense=Dense([.1,.8,.8])
    with pytest.raises(RuntimeError,match='nonnegative domain'):
        solver._dense_minima(dense,0.,1.,coordinates,start)
