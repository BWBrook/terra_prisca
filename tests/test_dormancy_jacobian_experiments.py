from hashlib import sha256
import importlib.util
from pathlib import Path

import numpy as np
import pytest

from terra_prisca.haze_world import dormancy_experiments as base
from terra_prisca.haze_world import dormancy_jacobian_experiments as numerical
from terra_prisca.haze_world import dormancy_jacobian_integration as driver


def test_jacobian_protocol_preserves_physics_and_recording_and_isolates_native_cache(tmp_path):
    case=base.design(.25)[0]
    frozen=base.identity(case,"census")
    for mode in ("census","uncensored"):
        fingerprint,protocol=numerical.identity(case,mode)
        _,native=base.identity(case,mode)
        assert protocol["parameters"]==native["parameters"]
        assert protocol["census"]==native["census"]
        assert protocol["solver"]=="analytic_dormancy_switching_jacobian"
        assert protocol["architecture"] and protocol["operating_system"]
        assert set(protocol["source_sha256"])-set(native["source_sha256"])=={
            "src/terra_prisca/haze_world/dormancy_jacobian_experiments.py",
            "src/terra_prisca/haze_world/dormancy_jacobian_integration.py",
            "src/terra_prisca/haze_world/dormancy_trial_integration.py"}
        assert all(protocol["source_sha256"][k]==v for k,v in native["source_sha256"].items())
        assert fingerprint==sha256(base.e.dumps(protocol).encode()).hexdigest()
    assert base.identity(case,"census")==frozen
    original=base.run(case,"uncensored",tmp_path)
    assert numerical.read_record(case,raw=tmp_path) is None
    repeated=numerical.run(case,raw=tmp_path,expected_sources=numerical.sources())
    assert repeated["fingerprint"]!=original["fingerprint"]
    with np.load(tmp_path/original["raw_file"]) as a,np.load(tmp_path/repeated["raw_file"]) as b:
        np.testing.assert_allclose(a["y"],b["y"],rtol=3e-6,atol=1e-13)
        assert np.all(b["y"]>=0)
    assert numerical.read_record(case,raw=tmp_path)["fingerprint"]==repeated["fingerprint"]


@pytest.mark.parametrize("name",[
    "test_census_counts_both_stages_and_exports_their_combined_inventory",
    "test_global_minima_are_contemporaneous_sums_of_active_and_dormant_stocks",
    "test_local_census_loss_is_recolonized_only_from_existing_metapopulation",
    "test_positive_coordinates_match_independent_physical_radau_flow"])
def test_copied_driver_retains_frozen_accepted_flow_contract(name):
    spec=importlib.util.spec_from_file_location("isolated_driver_contract",Path(__file__).with_name("test_dormancy_integration.py"))
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.n=driver
    getattr(module,name)()
