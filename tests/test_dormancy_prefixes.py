from hashlib import sha256

import numpy as np

from terra_prisca.haze_world import dormancy_experiments as base
from terra_prisca.haze_world import dormancy_prefixes as prefix


def test_prefix_protocol_adds_only_declared_numerical_sources_without_mutating_census():
    case=base.design(1.)[0]
    before=base.identity(case,"census")
    old_id,old=base.identity(case,"uncensored")
    new_id,new=prefix.identity(case)
    assert base.identity(case,"census")==before
    assert new_id!=old_id and new["solver"]=="nonfinite_stage_trial_rejection"
    assert new["architecture"] and new["operating_system"]
    assert all(new["source_sha256"][k]==v for k,v in old["source_sha256"].items())
    extras=set(new["source_sha256"])-set(old["source_sha256"])
    assert extras=={"src/terra_prisca/haze_world/dormancy_prefixes.py",
                    "src/terra_prisca/haze_world/dormancy_trial_integration.py"}
    assert new_id==sha256(base.e.dumps(new).encode()).hexdigest()
    _,census=prefix.identity(case,"census")
    assert census["census"]==before[1]["census"]
    assert census["source_sha256"]==new["source_sha256"]


def test_prefix_runner_keeps_nonretry_physical_path_and_separates_cache(tmp_path):
    case=base.design(1.)[0]
    old=base.run(case,"uncensored",tmp_path)
    assert prefix.read_record(case,raw=tmp_path) is None
    new=prefix.run(case,raw=tmp_path,expected_sources=prefix.sources())
    assert new["fingerprint"]!=old["fingerprint"]
    for key in ("t","y","log_biomass","log_active","log_dormant","min_log_biomass","min_times"):
        with np.load(tmp_path/old["raw_file"]) as a,np.load(tmp_path/new["raw_file"]) as b:
            np.testing.assert_array_equal(a[key],b[key])
    assert prefix.read_record(case,raw=tmp_path)["fingerprint"]==new["fingerprint"]
