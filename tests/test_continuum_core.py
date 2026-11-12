from dataclasses import replace

import numpy as np
import pytest

from terra_prisca.haze_world import continuum_core as weighted
from terra_prisca.haze_world import dynamic_core as original
from terra_prisca.haze_world import population_coupling as core


def example(chemistry='products',sigma=1.,n=5):
    p=original.DynamicParams(core.reference(),chemistry,sigma_k=sigma,n_habitats=n)
    y=original.equilibrium_states(p)[0]['y']
    q=weighted.WeightedParams(p.base,chemistry,sigma,weighted.midpoint_mesh(sigma,n))
    return y,p,q


def test_midpoint_case_reproduces_b1_rhs_and_jacobian():
    y,p,q=example()
    np.testing.assert_allclose(weighted.physical_rhs(y,q),original.physical_rhs(y,p),atol=1e-18,rtol=1e-12)
    scales=original.state_scales(y,p)
    expected=original.reduced_matrix(y,p)*scales[:,None]/scales[None,:]
    np.testing.assert_allclose(weighted.dense_matrix(y,q),expected,rtol=2e-11,atol=1e-8)
    assert weighted.slopes(y,q)['Sc']==pytest.approx(original.implicit_response(y,p)['dtemperature_dlog_supply'],rel=1e-8)


def test_gauss_panels_represent_uniform_measure_and_integrate_polynomials():
    mesh=weighted.gauss_mesh(3.,[-3.,-2.98,-.1,3.])
    x,w=np.array(mesh.nodes),np.array(mesh.weights)
    assert sum(w)==pytest.approx(1.)
    for degree in range(8):
        target=3.**degree/(degree+1) if degree%2==0 else 0.
        assert w@x**degree==pytest.approx(target,abs=1e-12,rel=1e-13)


def test_weighted_exchange_conserves_each_guild_total():
    q=weighted.WeightedParams(core.reference(),'fixed',1.,weighted.gauss_mesh(1.))
    base=original.DynamicParams(q.base)
    y0=next(r['y'] for r in original.equilibrium_states(base) if r['kind']=='mixed')
    y=np.r_[np.tile(y0[:4],q.n),y0[-1]]
    y[1:-1:4]*=np.linspace(.1,2.,q.n);y[2:-1:4]*=np.linspace(2.,.2,q.n)
    delta=(weighted.physical_rhs(y,q)-weighted.physical_rhs(y,replace(q,dispersal_yr=0)))[:-1].reshape(q.n,4)
    np.testing.assert_allclose(q.weights@delta[:,1:3],0.,atol=1e-18)


def test_schur_solve_and_scaled_shift_inverse_recover_full_operator():
    y,_,q=example('fixed')
    matrix=weighted.dense_matrix(y,q)
    scale=weighted.operator_scales(y,q)
    rhs=np.random.default_rng(4).normal(size=len(y))*scale
    got,_=weighted.block_solve(weighted.local_blocks(y,q),rhs[:-1].reshape(q.n,4),rhs[-1])
    scaled=matrix*scale[None,:]/scale[:,None]
    denominator=np.linalg.norm(scaled)*np.linalg.norm(got/scale)+np.linalg.norm(rhs/scale)
    assert np.linalg.norm((matrix@got-rhs)/scale)/denominator<1e-13
    for tau in (0.,3.):
        operator=weighted.scaled_operator(y,q,tau)
        inverse=weighted.scaled_operator(y,q,tau,shift=.03j)
        vector=np.random.default_rng(3).normal(size=operator.shape[0]).astype(complex)
        answer=inverse@vector
        assert np.linalg.norm(operator@answer-.03j*answer-vector)<2e-7


def test_frozen_jacobian_is_total_biomass_projection_of_original():
    y,_,q=example('products')
    _,expand,collapse=weighted.frozen_projection(y,q)
    e=np.zeros((4*q.n+1,3*q.n+1));j=np.zeros(e.T.shape)
    for n in range(q.n):
        e[n*4:n*4+4,n*3:n*3+3]=expand[n]
        j[n*3:n*3+3,n*4:n*4+4]=collapse[n]
    e[-1,-1]=j[-1,-1]=1
    expected=j@weighted.dense_matrix(y,q)@e
    actual=weighted.dense_matrix(y,q,blocks=weighted.frozen_blocks(y,q))
    np.testing.assert_allclose(actual,expected,rtol=1e-12,atol=1e-10)


def test_frozen_gain_matches_finite_supply_counterfactual():
    p=original.DynamicParams(core.reference(),'products')
    y=next(r['y'] for r in original.equilibrium_states(p) if r['kind']=='mixed')
    q=weighted.WeightedParams(p.base,'products')
    result=weighted.slopes(y,q)
    check=weighted.frozen_supply_check(y,q,step=5e-5)
    assert result['Sc']==pytest.approx(-1.87756715,abs=1e-7)
    assert result['S0']==pytest.approx(check['S0_finite_difference'],rel=1e-6)
    assert result['G_loc']<.05
    assert max(p['maximum_ratio_error'] for p in check['points'])<1e-14
    assert weighted.spectrum(y,q,blocks=weighted.frozen_blocks(y,q))['leading_real']<0


def test_plateau_has_no_defined_composition_gain():
    y,_,q=example('fixed',sigma=0,n=1)
    y[-1]=.5
    result=weighted.slopes(y,q)
    assert result['status']=='climate_insensitive'
    assert result['Sc']==result['S0']==0.
    assert result['G_loc'] is None


def test_adaptive_mesh_resolves_panel_endpoints_and_nodes():
    q=weighted.WeightedParams(core.reference(),'fixed',1.,weighted.gauss_mesh(1.),dispersal_yr=.01)
    result=weighted.adaptive_equilibrium(q)
    assert result['status']=='logit_resolved'
    assert result['history'][-1]['max_logit_change']<=1.
    assert np.max(abs(weighted.per_capita(result['y'],result['p'])))<1e-7
    mesh,info=weighted.refine_panels(result['y'],result['p'],force_mixed=True)
    assert len(mesh.nodes)>result['p'].n
    assert info['mixed_width_k']>0


def test_strong_product_feedback_mesh_step_uses_local_manifold_correction():
    q=weighted.WeightedParams(core.reference(),'products',6.,weighted.gauss_mesh(6.),dispersal_yr=.0001)
    result=weighted.adaptive_equilibrium(q,max_levels=2)
    assert result['status']!='refinement_root_unresolved'
    assert result['p'].n>16
    assert any(r.get('local_profile_correction_accepted') for r in result['history'])
    assert np.max(abs(weighted.per_capita(result['y'],result['p'])))<1e-8
