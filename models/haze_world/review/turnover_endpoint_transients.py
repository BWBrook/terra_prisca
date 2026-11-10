"""Check the slowly damped T2 mixed-community transients against local spectra.

    uv run python models/haze_world/review/turnover_endpoint_transients.py

Requires the frozen 100k census receipts/payloads in local/haze/turnover.
This assesses late relaxation within those recorded paths, not global basins.
"""

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from scipy.signal import find_peaks

from terra_prisca.haze_world import buffered_experiments as formatting
from terra_prisca.haze_world import habitat_equilibria as equilibrium
from terra_prisca.haze_world import turnover_experiments as experiments
from terra_prisca.haze_world import turnover_survival as profiles


def baseline(case_id):
    paths=list(experiments.RAW.glob(case_id+"_census_t100000-*.receipt.json"))
    if len(paths)!=1:raise RuntimeError("Expected one frozen baseline for "+case_id)
    record=json.loads(paths[0].read_text())
    assert sha256(formatting.dumps(record["protocol"]).encode()).hexdigest()==record["fingerprint"]
    return record,profiles.load(record,experiments.RAW)


def main():
    rows=[];sources=experiments.sources()
    for case_id,seed_id in (("refuges_0115",None),("refuges_0119",None),
                            ("refuges_0146","refuges_0148"),("refuges_0174","refuges_0176")):
        record,data=baseline(case_id)
        assert record["protocol"]["source_sha256"]==sources
        p=experiments.parameters(experiments.Case(**record["protocol"]["case"]))
        initial=data["y"][:,-1] if seed_id is None else baseline(seed_id)[1]["y"][:,-1]
        rates=[p.dispersal_yr] if seed_id is None else np.geomspace(.001,p.dispersal_yr,13)
        for rate in rates:
            root=equilibrium.refine(initial,replace(p,dispersal_yr=float(rate)))
            if root is None:raise RuntimeError("Mixed-root continuation failed: "+case_id)
            initial=root["y"]
        eigenvalues=np.asarray(root["eigenvalues"]);mode=eigenvalues[np.argmax(eigenvalues.real)]
        assert mode.real<0 and abs(mode.imag)>0
        late=data["t"]>=80000.;time=data["t"][late]
        deviation=data["y"][1,late]-root["y"][1]
        peaks,_=find_peaks(deviation,height=0.,prominence=float(max(abs(deviation)))*.005)
        peaks=peaks[deviation[peaks]>root["y"][1]*1e-9]
        assert len(peaks)>20
        period=float(np.polyfit(np.arange(len(peaks)),time[peaks],1)[0])
        slope=float(np.polyfit(time[peaks],np.log(deviation[peaks]),1)[0]);assert slope<0
        damping=-1/slope;predicted_period=2*np.pi/abs(mode.imag);predicted_damping=-1/mode.real
        rows.append(dict(case_id=case_id,source_raw_file=record["raw_file"],source_raw_sha256=record["raw_sha256"],
            root_y=root["y"].tolist(),root_max_scaled_residual=root["max_scaled_residual"],
            leading_eigenvalue_real_yr=float(mode.real),leading_eigenvalue_imag_yr=float(mode.imag),
            spectrum_period_yr=float(predicted_period),spectrum_damping_yr=float(predicted_damping),
            fitted_period_yr=period,fitted_damping_yr=damping,peaks=len(peaks),
            period_relative_error=float(period/predicted_period-1),damping_relative_error=float(damping/predicted_damping-1),
            root_seed_case=seed_id or case_id,dispersal_continuation_yr=np.asarray(rates).tolist()))
    assert experiments.sources()==sources
    result=dict(source_sha256=sources,checker_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
        interval_yr=[80000.,100000.],observable="Bulk acetogen biomass minus the refined mixed equilibrium",
        method="Positive peak timing and log-amplitude regression on 10-year samples; final100k state seeds the root, or13-step dispersal continuation from the matching1e-3 reference",
        scope="Late damped transients on the recorded census paths. Spectra are local and do not establish global attractor uniqueness.",rows=rows)
    target=Path(__file__).with_suffix(".json");target.write_text(json.dumps(result,indent=2)+"\n")
    for row in rows:
        print(row["case_id"],row["fitted_period_yr"],row["spectrum_period_yr"],row["fitted_damping_yr"],row["spectrum_damping_yr"],flush=True)


if __name__=="__main__":main()
