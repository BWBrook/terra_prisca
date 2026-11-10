"""Compare the new first-minimum rule with the accepted bottleneck pilot."""

from hashlib import sha256
from pathlib import Path
import csv
import json

import numpy as np

from terra_prisca.haze_world import bottleneck as old
from terra_prisca.haze_world import buffered_experiments as e
from terra_prisca.haze_world import turnover_survival as new


if __name__=="__main__":
    record=old._records()["main_0010_t100000"]
    data=old.load_npz(record)
    p=e.parameters(e.Case("main_0010_t100000",0.,"warm",1e-6,"A_into_M"))
    result=new.analyze(data,p,0)
    table=e.ROOT/"models/haze_world/figures/bottleneck/survival.csv"
    with table.open() as stream:
        accepted=next(v for v in csv.DictReader(stream) if v["case_id"]=="main_0010_t100000" and v["guild"]=="a")
    previous=float(accepted["first_window_survival_probability"])
    difference=result["survival_probability"]/previous-1
    assert abs(difference)<5e-5
    assert result["classification"]=="contingent"
    assert result["minimum_time_yr"]==1344.
    paths=(Path(__file__),Path(new.__file__))
    receipt=dict(control="Accepted warm-only f0,d1e-6 acetogen bottleneck; new first-minimum rule",
        source_raw_file=record["raw_file"],source_raw_sha256=record["raw_sha256"],
        inherited_archive_directory="bottleneck-66c46a2-20261110",
        accepted_survival_probability=previous,relative_probability_change=difference,
        accepted_table_sha256=sha256(table.read_bytes()).hexdigest(),
        source_sha256={str(v.relative_to(e.ROOT)):sha256(v.read_bytes()).hexdigest() for v in paths},
        interpretation="Reproduces the accepted approximately0.000265 conditional probability; not an independent stochastic ecosystem test",
        result=result)
    table=e.ROOT/"models/haze_world/figures/turnover/first_survival.json"
    if table.exists():
        from terra_prisca.haze_world import turnover_experiments as run
        checks=[]
        for row in json.loads(table.read_text()):
            if row["classification"]!="contingent" or row["local_census_removals"]==0:continue
            raw=run.RAW/row["source_raw_file"]
            source=json.loads(raw.with_suffix(".receipt.json").read_text())
            if source["raw_sha256"]!=row["source_raw_sha256"]:raise RuntimeError("Changed contingent source identity")
            data=new.load(source,run.RAW);p=run.parameters(run.Case(**source["protocol"]["case"]))
            guild=e.GUILDS.index(row["guild"])
            coarse=new.analyze(data,p,guild,rate_stride=2.,max_step=.5)
            t=data["t"];lo=int(np.searchsorted(t,row["start_yr"]));hi=int(np.searchsorted(t,row["end_yr"]))
            trim=max(1,(hi-lo)//10);lo+=trim;hi-=trim
            if not t[lo]<row["minimum_time_yr"]<t[hi]:raise RuntimeError("Cannot trim the first window safely")
            birth=[];death=[]
            for k in range(lo,hi+1):
                _,b,d=new.branching.per_cell_rates(data["y"][:,k],p,guild);birth.append(b);death.append(d)
            logu=new.branching.backward_survival(t[lo:hi+1],np.array(birth),np.array(death),
                new.branching.migration_matrix(p),max_step=.5)
            _,types=new.counts(data,p,guild)
            shorter=new.branching.lineages(types[lo],logu)
            values=dict(case_id=row["case_id"],guild=row["guild"],source_raw_sha256=source["raw_sha256"],
                baseline_log_lambda=row["log_lambda"],coarse_rate_log_lambda=coarse["log_lambda"],
                trimmed_window_log_lambda=shorter["log_lambda"],trimmed_start_yr=float(t[lo]),trimmed_end_yr=float(t[hi]),
                rate_grid_log_lambda_change=coarse["log_lambda"]-row["log_lambda"],
                window_trim_log_lambda_change=shorter["log_lambda"]-row["log_lambda"],
                classification_unchanged=coarse["classification"]==shorter["classification"]==row["classification"])
            checks.append(values)
        if any(not v["classification_unchanged"] or max(abs(v["rate_grid_log_lambda_change"]),abs(v["window_trim_log_lambda_change"]))>.01 for v in checks):
            raise RuntimeError("Contingent first-window grid/horizon control needs refinement")
        receipt["contingent_controls"]=dict(table_sha256=sha256(table.read_bytes()).hexdigest(),
            scope="Two-year rate grid with smaller probability steps; first-window entry/exit trimmed by10% while retaining its minimum; conditional classes must agree and log-intensity changes stay below0.01",checks=checks)
    Path(__file__).with_suffix(".json").write_text(e.dumps(receipt)+"\n")
