from hashlib import sha256

import numpy as np

from terra_prisca.haze_world import dormancy_experiments as base
from terra_prisca.haze_world import dormancy_predictor_experiments as numerical


def test_zero_stage_predictor_protocol_preserves_physics_and_recording_and_isolates_native_cache(tmp_path):
    case=base.design(.25)[0]
    frozen=base.identity(case,"census")
    for mode in ("census","uncensored"):
        fingerprint,protocol=numerical.identity(case,mode)
        _,native=base.identity(case,mode)
        assert protocol["parameters"]==native["parameters"]
        assert protocol["census"]==native["census"]
        assert protocol["solver"]=="radau_dormancy_zero_stage_predictor"
        assert protocol["architecture"] and protocol["operating_system"]
        assert set(protocol["source_sha256"])-set(native["source_sha256"])=={
            "src/terra_prisca/haze_world/dormancy_predictor_experiments.py",
            "src/terra_prisca/haze_world/dormancy_conditioned_experiments.py",
            "src/terra_prisca/haze_world/dormancy_radau_experiments.py",
            "src/terra_prisca/haze_world/dormancy_predictor_integration.py",
            "src/terra_prisca/haze_world/dormancy_conditioned_integration.py",
            "src/terra_prisca/haze_world/dormancy_radau_integration.py",
            "src/terra_prisca/haze_world/dormancy_face_experiments.py",
            "src/terra_prisca/haze_world/dormancy_face_integration.py",
            "src/terra_prisca/haze_world/dormancy_stage_experiments.py",
            "src/terra_prisca/haze_world/dormancy_stage_integration.py",
            "src/terra_prisca/haze_world/dormancy_chemical_experiments.py",
            "src/terra_prisca/haze_world/dormancy_chemical_integration.py",
            "src/terra_prisca/haze_world/dormancy_progress_integration.py",
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

