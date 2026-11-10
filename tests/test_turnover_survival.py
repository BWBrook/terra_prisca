from types import SimpleNamespace
from hashlib import sha256
import json

import numpy as np
import pytest

from terra_prisca.haze_world import turnover_survival as s


def test_first_window_does_not_select_later_ghost_minimum(monkeypatch):
    monkeypatch.setattr(s,"uptake_shares",lambda *args:(0.,0.))
    t=np.arange(9.)
    logs=np.log(1e16)+np.array([2.,-1.,-2.,1.,3.,-10.,-20.,-40.,1.])
    result=s.first_window(t,np.zeros((1,9)),logs,None,0)
    assert (result["lo"],result["hi"])==(0,3)
    assert result["rare"] and not result["terminal"]


def test_first_window_checks_local_linearity_and_keeps_terminal_horizon(monkeypatch):
    calls=[]
    def shares(y,p,g,indices,dormant):
        calls.append(list(indices))
        return (1e-5,0.) if len(calls)==1 else (0.,0.)
    monkeypatch.setattr(s,"uptake_shares",shares)
    t=np.arange(5.);logs=np.log(1e16)+np.array([2.,-1.,-3.,-5.,-8.])
    result=s.first_window(t,np.zeros((1,5)),logs,None,0)
    assert result["terminal"] and result["hi"]==4
    assert result["reductions"]==1
    assert result["threshold"]==pytest.approx(np.log(1e15))


def test_linearity_reduction_does_not_skip_first_shallow_dip(monkeypatch):
    monkeypatch.setattr(s,"uptake_shares",lambda *args:(1e-3,0.))
    t=np.arange(8.)
    total=np.log(1e16)+np.array([1.,-.2,1.,2.,-10.,-20.,-40.,1.])
    result=s.first_window(t,np.zeros((1,len(t))),total,None,0)
    assert (result["lo"],result["hi"],result["anchor"])==(0,2,1)
    assert result["status"]=="first_minimum_not_locally_linear"
    assert not result["rare"]


def test_first_minimum_stops_at_recovery_peak_inside_one_rare_episode(monkeypatch):
    monkeypatch.setattr(s,"uptake_shares",lambda *args:(0.,0.))
    t=np.arange(8.)
    total=np.log(1e16)+np.array([1.,-1.,-5.,-2.,-3.,-10.,-20.,1.])
    result=s.first_window(t,np.zeros((1,len(t))),total,None,0)
    assert result["anchor"]==2 and result["hi"]==3


def test_dormant_stage_counts_use_habitat_volumes_without_double_counting():
    p=SimpleNamespace(weights=np.array([.75,.25]))
    active=np.array([[[2.,3.],[5.,7.]],[[11.,13.],[17.,19.]]])
    dormant=active/2
    data=dict(metadata={"global_log_cell_conversion":np.log(10.)},
              log_active=np.log(active),log_dormant=np.log(dormant),log_biomass=np.log(active+dormant))
    total,types=s.counts(data,p,0,True)
    expected=10*(.75*(active[0,0]+dormant[0,0])+.25*(active[1,0]+dormant[1,0]))
    assert np.exp(total)==pytest.approx(expected)
    assert np.exp(types).sum(axis=1)==pytest.approx(expected)


def test_terminal_first_window_has_finite_horizon_survival_and_no_gaussian_width(monkeypatch):
    monkeypatch.setattr(s,"uptake_shares",lambda *args:(0.,0.))
    monkeypatch.setattr(s.branching,"per_cell_rates",
                        lambda *args:(np.array([0]),np.array([0.]),np.array([.1])))
    monkeypatch.setattr(s.branching,"migration_matrix",lambda p:np.zeros((1,1)))
    p=SimpleNamespace(weights=np.array([1.]))
    t=np.arange(101.)
    data=dict(t=t,y=np.zeros((5,len(t))),metadata={"global_log_cell_conversion":0.},
              log_biomass=np.stack((np.log(100.)-.1*t,np.zeros_like(t)))[None,:,:])
    row=s.analyze(data,p,0)
    assert row["terminal_window"]
    assert row["survival_probability"]==pytest.approx(-np.expm1(-100*np.exp(-10.)),rel=1e-7)
    assert row["gaussian_cells_for_half_survival"] is None


def test_select_longest_profile_before_rejecting_obsolete_pilot_source(tmp_path,monkeypatch):
    monkeypatch.setattr(s.e,"ROOT",tmp_path)
    physical=tmp_path/"physical.py";physical.write_text("frozen\n")
    for horizon,digest in ((1000.,"obsolete"),(100000.,sha256(physical.read_bytes()).hexdigest())):
        protocol=dict(case=dict(case_id="case",years=horizon,max_step_yr=10.),mode="census",
                      source_sha256={"physical.py":digest})
        record=dict(execution_status="complete",protocol=protocol,
                    fingerprint=sha256(s.e.dumps(protocol).encode()).hexdigest())
        (tmp_path/f"{horizon:g}.receipt.json").write_text(json.dumps(record))
    assert s.records(tmp_path,"census")["case"]["protocol"]["case"]["years"]==100000.
    physical.write_text("changed\n")
    with pytest.raises(RuntimeError,match="Physical source differs"):
        s.records(tmp_path,"census")
