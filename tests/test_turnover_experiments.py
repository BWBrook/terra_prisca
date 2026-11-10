from collections import Counter

import numpy as np

from terra_prisca.haze_world import buffered_experiments as reference
from terra_prisca.haze_world import habitat_equilibria as equilibria
from terra_prisca.haze_world import turnover_experiments as runs
from terra_prisca.haze_world import turnover_starts as starts


def test_design_preserves_all_turnovers_directions_and_refuge_comparisons():
    cases=runs.design()
    assert len(cases)==196 and len({c.case_id for c in cases})==196
    assert Counter(c.layout for c in cases)==dict(none=28,both_absolute=56,both_relative=56,warm_relative=56)
    assert all(c.dispersal_yr==0 for c in cases if c.layout=="none")
    assert len({(c.loss_h,c.fraction,c.direction) for c in cases if c.layout=="none"})==28


def test_absolute_reference_and_relative_thermal_offsets():
    case=next(c for c in runs.design() if c.loss_h==1e-3 and c.fraction==.5 and c.layout=="both_absolute"
              and c.dispersal_yr==1e-6 and c.direction=="A_into_M")
    expected=reference.parameters(reference.Case("reference",.5,"both",1e-6,"A_into_M"))
    assert runs.parameters(case)==expected
    relative=next(c for c in runs.design() if c.loss_h==3e-3 and c.layout=="both_relative")
    p=runs.parameters(relative)
    switch=reference.core.switch_temperatures(p.base.biology)[0]
    assert p.patches[1].value==switch+4.465
    assert p.patches[2].value==switch-3.535


def test_conditional_start_can_support_a_nonviable_isolated_sink():
    case=next(c for c in runs.design() if c.loss_h==3e-3 and c.fraction==0 and c.layout=="both_absolute"
              and c.dispersal_yr==1e-6 and c.direction=="A_into_M")
    p=runs.parameters(case)
    assert equilibria.local_resident(.2,278.,p.base,1) is None
    result=starts.conditional_states(p,1)
    assert result["selected"] is not None
    selected=result["selected"];y=selected["y"]
    assert selected["stability"]=="stable" and y[10]>0
    assert selected["max_scaled_residual"]<1e-8
    flux=reference.model.fluxes(y,p)
    assert flux["local"][2]["net_growth_yr"][1]<0
    assert flux["exchange_gdw_l_yr"][2,1]>0
    assert np.isfinite(y).all()
