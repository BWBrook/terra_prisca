from dataclasses import replace

import numpy as np
import pytest

from terra_prisca.haze_world import evolved_kinetics as e
from terra_prisca.haze_world import population_coupling as core
from terra_prisca.haze_world import two_guilds as reference
from terra_prisca.haze_world import competitive_best_response as scan


@pytest.mark.parametrize('temperature_c',[4.,10.,11.37,25.,30.])
def test_identity_kinetic_position_preserves_reference_physiology(temperature_c):
    bio=core.reference().biology
    original=reference.guilds(temperature_c,bio)
    variant=e.guilds(temperature_c+273.15,bio,e.Traits((temperature_c,temperature_c),0.))
    for a,b in zip(original,variant):
        assert a.name==b.name and a.kinetics==b.kinetics
        for key in ('rate_scale','km_pa','threshold_pa','yield_g_mol','maintenance','assimilation_mol_g'):
            assert getattr(a,key)==pytest.approx(getattr(b,key),rel=2e-14)
        assert a.rstar(bio.loss_h)==pytest.approx(b.rstar(bio.loss_h),rel=2e-14)


def test_traits_change_kinetics_but_actual_temperature_controls_threshold_and_maintenance():
    bio=core.reference().biology
    t=278.
    actual=reference.guilds(t-273.15,bio)
    target=e.guilds(t,bio,e.Traits((10.,25.),.45))
    at_trait=[reference.guilds(u,bio)[i] for i,u in enumerate((10.,25.))]
    for i,g in enumerate(target):
        assert g.threshold_pa==actual[i].threshold_pa
        assert g.maintenance==actual[i].maintenance
        expected=at_trait[i].rate_scale*np.exp(-.45/e.KB_EV*(1/t-1/((10.,25.)[i]+273.15)))
        assert g.rate_scale==pytest.approx(expected,rel=1e-14)
        assert g.km_pa==at_trait[i].km_pa


def test_s2_freezes_are_independent_and_leave_selected_kinetics_unchanged():
    bio=core.reference().biology;t=278.
    plain=e.guilds(t,bio,e.Traits((10.,25.),.2))
    h=e.guilds(t,bio,e.Traits((10.,25.),.2,freeze_thresholds=True))
    m=e.guilds(t,bio,e.Traits((10.,25.),.2,freeze_maintenance=True))
    warm=reference.guilds(30.,bio)
    for i in (0,1):
        assert h[i].threshold_pa==warm[i].threshold_pa and h[i].maintenance==plain[i].maintenance
        assert m[i].maintenance==warm[i].maintenance and m[i].threshold_pa==plain[i].threshold_pa
        assert h[i].rate_scale==m[i].rate_scale==plain[i].rate_scale


def test_smooth_log_shape_preserves_measured_nodes_and_segment_ranges():
    bio=core.reference().biology
    v,k=e.shape(e.NODES_C,bio,'smooth_shape')
    expected=e.profiles(bio)
    assert np.allclose(v,expected[0],rtol=1e-14)
    assert np.allclose(k,expected[1],rtol=1e-14)
    for left,right in zip(e.NODES_C[:-1],e.NODES_C[1:]):
        points=np.linspace(left,right,31)
        vv,kk=e.shape(points,bio,'smooth_shape')
        for arr in (vv,kk):
            assert np.all(arr>=np.minimum(arr[:,[0]],arr[:,[-1]])*(1-1e-14))
            assert np.all(arr<=np.maximum(arr[:,[0]],arr[:,[-1]])*(1+1e-14))


def test_measured_trait_bound_rejects_the_preview_continuation():
    with pytest.raises(ValueError,match='measured'):
        e.Traits((-.15,10.),.45)
    with pytest.raises(ValueError,match='extrapolation'):
        e.shape([-.15,10.],core.reference().biology)


def test_best_response_passes_global_grid_mutant_check():
    bio=core.reference().biology;t=281.8682466844
    response=e.best_response(t,bio,.65)
    assert min(response['positions_c'])>=4 and max(response['positions_c'])<=30
    assert all(row['rstar_pa']<=row['grid_rstar_pa']+1e-10 for row in response['guild_results'])
    for i in (0,1):
        _,growth=e.uptake_grid(response['rstars_pa'][i],t,bio,.65)
        assert max(growth[i])<1e-10
        selected=e.guilds(t,bio,e.Traits(response['positions_c'],.65))[i]
        assert selected.net_growth(response['rstars_pa'][i],bio.loss_h)==pytest.approx(0.,abs=1e-14)


def test_infeasible_capacity_is_not_reported_as_a_crossing():
    bio=replace(core.reference().biology,loss_h=10.)
    response=e.best_response(280.,bio,0.)
    assert all(np.isinf(response['rstars_pa']))
    result=scan.crossings(bio,0.)
    assert result['crossings']==[] and result['sampled_both_viable']==0
    assert result['cold_end_winner']=='neither_viable'


def test_shared_reference_checkpoint_and_preview_bound_error():
    bio=core.reference().biology
    root=scan.crossings(bio,0.)['crossings'][0]
    assert root['temperature_k']==pytest.approx(277.9602210578,abs=1e-7)
    assert root['orientation']=='acetogen_cold'
    measured=scan.crossings(bio,.45)['crossings'][0]
    historical=scan.crossings(bio,.45,legacy_trait_min_c=-.15)['crossings'][0]
    assert measured['temperature_k']==pytest.approx(281.105494886,abs=1e-7)
    assert historical['temperature_k']-measured['temperature_k']>2.5
    assert historical['positions_c'][0]==-.15
