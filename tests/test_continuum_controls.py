from dataclasses import replace
import json

import numpy as np
import pytest

from terra_prisca.haze_world import continuum_controls as controls,continuum_core as weighted
from terra_prisca.haze_world import dynamic_core as original,population_coupling as core


def test_homogeneous_secondary_control_matches_original_root_and_slope():
    base=replace(core.reference(),enabled=(False,True))
    q=weighted.WeightedParams(base,'fixed')
    expected=next(r for r in original.equilibrium_states(original.DynamicParams(base)) if r['kind']=='methanogen')
    found=controls.matched(q,-2.)
    assert found['gain_status']=='defined'
    assert found['control_temperature_k']==pytest.approx(expected['t_k'],abs=1e-7)
    assert found['control_ratio']==pytest.approx(expected['r'],abs=1e-10)
    target=original.implicit_response(expected['y'],original.DynamicParams(base))['dtemperature_dlog_supply']
    assert found['control_slope_k']==pytest.approx(target,rel=1e-7)
    assert found['control_balance_residual_yr']<1e-7


def test_resource_and_weighted_immigration_balances_hold_for_pure_m():
    base=replace(core.reference(.24),enabled=(False,True))
    q=weighted.WeightedParams(base,'products',1.,weighted.gauss_mesh(1.),.01)
    y=controls.pure_resident(.19,q)
    assert y is not None
    local=weighted.physical_rhs(y,q)[:-1].reshape(q.n,4)
    assert max(abs(local[:,0]))<1e-6
    assert np.max(abs(weighted.per_capita(y,q)))<1e-7
    assert q.weights@y[:-1].reshape(q.n,4)[:,1]==0


def test_unsupported_geometry_does_not_acquire_a_fake_gain():
    q=weighted.WeightedParams(core.reference(),'fixed',3.,weighted.gauss_mesh(3.))
    result=controls.matched(q,-2.)
    assert result['gain_status']=='no_admissible_control_detected'
    assert result['gain'] is None
    assert result['supported_search_nodes']<result['search_nodes']


def test_flat_methanogen_control_has_undefined_ratio():
    q=weighted.WeightedParams(core.reference(.36),'fixed')
    result=controls.matched(q,-2.)
    assert result['gain_status']=='zero_control_slope'
    assert result['gain'] is None
    assert result['control_slope_k']==0


def test_scalar_search_keeps_exact_vertices_and_validates_solver_roots(monkeypatch):
    assert controls.scalar_roots(lambda x:x-.2,[0.,.2,.4])==[.2]
    monkeypatch.setattr(controls,'brentq',lambda *args,**kwargs:0.)
    assert controls.scalar_roots(lambda x:x-.2,[0.,.4])==[]


def test_frozen_cache_is_hash_checked_before_export(tmp_path,monkeypatch):
    manifest=tmp_path/'models/haze_world/figures/continuum_habitats/manifest.json'
    manifest.parent.mkdir(parents=True)
    source=tmp_path/'c0-cache.json';source.write_text('[]')
    manifest.write_text(json.dumps(dict(source_sha256={},finite_input_export_correction=dict(frozen_cache_sha256={'c0-cache.json':'0'*64}))))
    monkeypatch.setattr(controls,'ROOT',tmp_path)
    with pytest.raises(ValueError,match='Frozen cache identity changed'):
        controls.run(tmp_path)
