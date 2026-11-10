from hashlib import sha256

import numpy as np

from terra_prisca.haze_world import dormancy as model
from terra_prisca.haze_world import dormancy_jacobian_integration as frozen
from terra_prisca.haze_world import dormancy_progress_integration as progress
from terra_prisca.haze_world import habitat_coupling as h


def setup():
    p=model.Dormancy(h.Habitats(),epsilon=.1)
    initial=model.reference_state([30.,3e-4,4e-4,1e-4,.195],p)
    return p,initial


def test_ordinary_flow_census_and_minima_match_frozen_bitwise():
    p,initial=setup()
    process=progress.Census(minimum_cells=0.,census_yr=.25)
    a=frozen.integrate_finite(initial,p,2.,process,sample_every_censuses=1,max_step=1.)
    b=progress.integrate_finite(initial,p,2.,process,sample_every_censuses=1,max_step=1.)
    for name in ("t","y","log_biomass","log_active","log_dormant","log_acetate",
                 "global_continuous_min_log_biomass","global_continuous_min_times_yr","census_times","census_activity"):
        assert np.array_equal(getattr(a,name),getattr(b,name))
    for name in a.ledger:assert np.array_equal(a.ledger[name],b.ledger[name])
    assert a.extinction_events==b.extinction_events
    assert b.metadata["native_zero_time_retries"]==0
    assert b.metadata["native_zero_time_events"]==[]


def test_injected_zero_time_uses_rollback_refinement_and_restores_ceiling(monkeypatch):
    original=frozen._GuardedLSODA.step
    fired=[];ceilings=[]
    def stalled(self):
        if self.t>.0001 and not fired:
            initial=self.y.copy()
            self.fun(self.t+.25,self.y)
            fired.append((float(self.t),sha256(initial.tobytes()).hexdigest(),float(self._last_trial_time)))
            self.t_old=float(self.t)
            return None
        return original(self)
    class Observed(progress._ProgressLSODA):
        def __init__(self,*args,**kwargs):
            ceilings.append(kwargs["max_step"])
            super().__init__(*args,**kwargs)
    p,initial=setup();process=progress.Census(minimum_cells=0.,census_yr=.25)
    reference=frozen.integrate_finite(initial,p,1.,process,sample_every_censuses=1,max_step=1.)
    monkeypatch.setattr(frozen._GuardedLSODA,"step",stalled)
    monkeypatch.setattr(progress,"_ProgressLSODA",Observed)
    result=progress.integrate_finite(initial,p,1.,process,sample_every_censuses=1,max_step=1.)
    assert result.status=="completed" and len(fired)==1
    event=result.metadata["native_zero_time_events"][0]
    assert event["accepted_time_yr"]==fired[0][0]
    assert event["accepted_coordinate_sha256"]==fired[0][1]
    assert event["actual_rhs_trial_time_yr"]==fired[0][2]
    assert event["accepted_coordinate_sha256"]==event["returned_coordinate_sha256"]
    assert event["native_reported_step_size_yr"]==0.
    assert event["driver_retry_representable"]
    reduced=next(i for i,value in enumerate(ceilings) if value<1.)
    assert 1. in ceilings[reduced+1:]
    assert result.metadata["solver_failure_retries"]==1
    assert np.allclose(result.y,reference.y,rtol=3e-6,atol=2e-11)
    assert np.all(result.y>=0.)
    assert np.max([abs(model.redox_residual(y,p)) for y in result.y.T])<1e-16


def solver(start,bound):
    p,initial=setup();coords=frozen._Coordinates(initial,p);internal=coords.encode(initial)
    events=[]
    return progress._ProgressLSODA(coords.derivative,start,internal,bound,
        nominal_max_step=1.,events=[],progress_events=events,max_step=1.,rtol=2e-8,atol=1e-8),events


def test_terminal_zero_time_notification_is_unchanged():
    instance,events=solver(1.,1.)
    assert instance.step() is None
    assert instance.status=="finished" and instance.t==1.
    assert events==[]


def test_unrepresentable_retry_is_reported_without_inventing_trial_time(monkeypatch):
    instance,events=solver(128.,130.)
    def zero_step(self):
        self.fun(np.nextafter(self.t,np.inf),self.y)
        self.t_old=self.t
    monkeypatch.setattr(frozen._GuardedLSODA,"step",zero_step)
    instance.step()
    assert instance.status=="failed" and len(events)==1
    event=events[0]
    assert event["actual_rhs_trial_time_yr"]==np.nextafter(128.,np.inf)
    assert event["driver_retry_limit_yr"]==(np.nextafter(128.,np.inf)-128.)/2
    assert not event["driver_retry_representable"]
    assert instance.t==128.


def test_failed_refinement_retains_actual_zero_time_event(monkeypatch):
    import pytest

    def zero_step(self):
        self.fun(np.nextafter(self.t,np.inf),self.y)
        self.t_old=self.t
    monkeypatch.setattr(frozen._GuardedLSODA,"step",zero_step)
    p,initial=setup()
    with pytest.raises(RuntimeError,match="cannot advance") as error:
        progress.integrate_finite(initial,p,1.,progress.Census(minimum_cells=0.,census_yr=.25),max_step=1.)
    events=error.value.native_zero_time_events
    assert len(events)==1
    assert events[0]["actual_rhs_trial_time_yr"]==np.nextafter(0.,np.inf)
    assert not events[0]["driver_retry_representable"]


def test_nonzero_census_removal_and_inventory_match_frozen_bitwise():
    p,initial=setup();process=progress.Census(census_yr=.25)
    conversion=p.coupled.habitat_l_cm2*process.surface_cm2/process.cell_mass_gdw
    initial[1]=.5/conversion;initial[4]=.4/conversion
    a=frozen.integrate_finite(initial,p,.5,process,sample_every_censuses=1,max_step=.25)
    b=progress.integrate_finite(initial,p,.5,process,sample_every_censuses=1,max_step=.25)
    assert a.extinction_events and a.extinction_events==b.extinction_events
    assert np.array_equal(a.y,b.y)
    assert np.array_equal(a.census_activity,b.census_activity)
    assert np.array_equal(a.global_continuous_min_log_biomass,b.global_continuous_min_log_biomass)
    for name in a.ledger:assert np.array_equal(a.ledger[name],b.ledger[name])
    assert b.metadata["native_zero_time_events"]==[]
