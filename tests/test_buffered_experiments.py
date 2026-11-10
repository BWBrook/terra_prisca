from dataclasses import replace
import numpy as np

from terra_prisca.haze_world import buffered_experiments as e


def test_approved_design_counts_and_unique_protocols():
    for stage,n in (("main",96),("sensitivity",72),("controls",24),("pilot",6)):
        rows=e.design(stage)
        assert len(rows)==len(set(rows))==n
        assert len({r.case_id for r in rows})==n
    assert {c.dispersal_yr for c in e.design("controls")}=={0.}


def test_zero_refuges_preserve_active_bulk_and_global_inoculum_dose():
    for configuration in ("none","warm","cold","both"):
        c=replace(e.design()[0],configuration=configuration)
        p=e.parameters(c);y=np.zeros(p.state_size);y[1:3]=.001
        seeded=e.seed_state(y,p,"A_into_M")
        assert np.isclose(p.weights@seeded[p.biomass_indices[:,0]],1e-12,rtol=1e-15,atol=0.)
        for j,w in enumerate(p.weights):
            if not w:assert np.all(seeded[4*j:4*j+4]==0)


def test_identity_changes_with_the_scientific_protocol():
    c=e.design()[0]
    baseline=e.identity(c)[0]
    for other in (replace(c,warm_k=292.),replace(c,activity="products"),replace(c,census_yr=1.),replace(c,years=200000.)):
        assert e.identity(other)[0]!=baseline
