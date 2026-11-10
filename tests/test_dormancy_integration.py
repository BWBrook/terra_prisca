from dataclasses import replace

import numpy as np
import pytest
from numpy.polynomial import Polynomial
from scipy.integrate import solve_ivp

from terra_prisca.haze_world import dormancy as d, dormancy_integration as n
from terra_prisca.haze_world import habitat_coupling as h
from terra_prisca.haze_world import bottleneck_integration as old


def test_zero_switching_tracks_reference_trajectory_without_a_dormant_seed():
    base=h.Habitats();p=d.Dormancy(base,switching_factor=0.)
    original=np.array([30.,3e-4,4e-4,1e-4,.195])
    a=old.integrate_finite(original,base,10.,n.Census(minimum_cells=0.,census_yr=1.),sample_every_censuses=1)
    b=n.integrate_finite(d.reference_state(original,p),p,10.,n.Census(minimum_cells=0.,census_yr=1.),sample_every_censuses=1)
    projected=np.array([d.active_state(y,p) for y in b.y.T]).T
    assert b.status=="completed"
    assert np.allclose(a.y,projected,rtol=2e-6,atol=2e-10)
    assert np.all(b.y[p.dormant_indices]==0.)
    assert np.all(np.isneginf(b.log_dormant))


def test_census_counts_both_stages_and_exports_their_combined_inventory():
    p=d.Dormancy();y=d.reference_state([30.,1e-30,1e-32,1e-4,.195],p)
    y[p.dormant_indices]=[[1e-28,1e-32]]
    r=n.integrate_finite(y,p,0.,n.Census())
    assert r.y[1,0]==pytest.approx(y[1])
    assert r.y[4,0]==pytest.approx(y[4])
    assert r.y[2,0]==0 and r.y[5,0]==0
    assert len(r.extinction_events)==1 and r.extinction_events[0]["guild"]=="methanogen"
    expected=p.coupled.biology.assimilation_m*(y[2]+y[5])
    assert sum(r.ledger["inventory_jump_h2_mol_l"].ravel())==pytest.approx(expected)


def test_dormant_only_population_can_wake_without_an_added_active_seed():
    base=h.Habitats(replace(h.Habitats().base,enabled=(True,False)))
    p=d.Dormancy(base)
    y=d.reference_state([200.,0.,0.,0.,.195],p);y[4]=1e-4
    r=n.integrate_finite(y,p,1.,n.Census(minimum_cells=0.,census_yr=.25),sample_every_censuses=1)
    assert np.isneginf(r.log_active[0,0,0])
    assert r.y[1,-1]>0 and r.y[4,-1]>=0
    assert np.all(r.y>=0) and r.extinction_events==[]
    assert np.all(np.isfinite(r.log_biomass[0,0]))


def test_global_minima_are_contemporaneous_sums_of_active_and_dormant_stocks():
    base=h.Habitats(patches=(h.Patch("bulk",.98),h.Patch("warm",.02,"buffered",286.)),dispersal_yr=.001)
    p=d.Dormancy(base)
    y=d.reference_state(h.embed_single([30.,3e-4,4e-4,1e-4,.195],base),p)
    r=n.integrate_finite(y,p,5.,n.Census(minimum_cells=0.,census_yr=1.),sample_every_censuses=1)
    masses=np.sum(p.weights[:,None,None]*(r.y[p.biomass_indices]+r.y[p.dormant_indices]),axis=0)
    assert np.all(r.global_continuous_min_log_biomass<=np.log(masses).min(axis=1)+1e-10)
    assert np.all(np.isfinite(r.global_continuous_min_log_biomass))
    assert np.all(r.y>=0)


def test_local_census_loss_is_recolonized_only_from_existing_metapopulation():
    base=h.Habitats(patches=(h.Patch("bulk",.98),h.Patch("warm",.02,"buffered",286.)),dispersal_yr=.001)
    p=d.Dormancy(base)
    y=d.reference_state(h.embed_single([30.,3e-4,0.,1e-4,.195],base),p);y[7]=1e-40
    r=n.integrate_finite(y,p,1.,n.Census(census_yr=.25),sample_every_censuses=1)
    assert len(r.extinction_events)==1 and r.extinction_events[0]["patch"]=="warm"
    assert r.y[7,0]==0 and r.y[7,-1]>0
    assert np.all(r.y[p.biomass_indices[:,1]]==0) and np.all(r.y[p.dormant_indices[:,1]]==0)
    assert np.all(np.isneginf(r.log_biomass[:,1]))


def test_dense_combined_minima_are_invariant_to_stage_coordinate_promotion():
    base=h.Habitats(patches=(h.Patch("bulk",.98),h.Patch("warm",.02,"buffered",286.)),dispersal_yr=.001)
    p=d.Dormancy(base);physical=d.reference_state(h.embed_single([30.,3e-4,4e-4,1e-4,.195],base),p)
    physical[p.dormant_indices]=1e-5
    roots=n._Coordinates(physical,p);linear=n._Coordinates(physical,p)
    linear.stage_positive[:]=False
    state=roots.encode(physical)
    polynomials=[Polynomial([v]) for v in state]
    a=roots.groups[0]
    stages=(Polynomial([.31,.01]),Polynomial([.001,.001]),Polynomial([.4]),Polynomial([.5]))
    for index,poly in zip(a["indices"],stages):polynomials[index]=poly
    polynomials[roots.m]=Polynomial([state[roots.m]+.25,1.,1.])
    physical_polys=polynomials.copy()
    for g in roots.groups:
        for index in g["indices"]:physical_polys[index]=polynomials[index]**2
    class Dense:
        t_old=0.;t=1.;h=1.
        def __init__(self,polys):
            self.polys=polys;self.yh=np.zeros((len(polys),5))
            for j,poly in enumerate(polys):self.yh[j,:len(poly.coef)]=poly.coef
        def __call__(self,t):return np.array([poly(t-1.) for poly in self.polys])
    first,second=Dense(polynomials),Dense(physical_polys)
    r=n._dense_minima(first,0.,1.,roots,first(0.))
    q=n._dense_minima(second,0.,1.,linear,second(0.))
    assert np.allclose(r[0],q[0],rtol=0.,atol=1e-10)
    assert np.allclose(r[2],q[2],rtol=0.,atol=1e-12)
    grid=np.linspace(0.,1.,1001)
    sampled=np.array([n._log_totals(roots.decode(first(t))[1]) for t in grid])
    assert np.all(r[0]<=sampled.min(axis=0)+1e-12)
    assert np.all(sampled.min(axis=0)-r[0]<1e-5)


def test_positive_coordinates_match_independent_physical_radau_flow():
    base=h.Habitats(patches=(h.Patch("bulk",.98),h.Patch("warm",.02,"buffered",286.)),dispersal_yr=.001)
    p=d.Dormancy(base,epsilon=.003)
    y=d.reference_state(h.embed_single([30.,3e-4,4e-4,1e-4,.195],base),p)
    y[p.dormant_indices]=[[1e-5,2e-5],[3e-5,1e-5]]
    result=n.integrate_finite(y,p,3.,n.Census(minimum_cells=0.,census_yr=.5),sample_every_censuses=1)
    independent=solve_ivp(lambda t,y:d.rhs(y,p,trial_extension=True),(0.,3.),y,method="Radau",rtol=2e-10,
        atol=np.r_[np.tile([1e-9,1e-15,1e-15,1e-15,1e-15,1e-15],2),1e-13],t_eval=result.t)
    assert independent.success
    assert np.allclose(result.y,independent.y,rtol=2e-6,atol=2e-11)
