"""Dormancy experiments with a restricted Newton matrix at zero linear allocations."""

import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import platform
from types import FunctionType

from . import dormancy_experiments as base
from . import dormancy_face_integration as numerical
from . import dormancy_stage_experiments as stage_runner
from . import dormancy_stage_integration as stages
from . import dormancy_chemical_experiments as chemical_runner
from . import dormancy_chemical_integration as chemical
from . import dormancy_progress_integration as progress
from . import dormancy_jacobian_integration as matrix
from . import dormancy_trial_integration as guard

RAW=base.RAW


def sources():
    paths=(Path(__file__),Path(numerical.__file__),Path(guard.__file__),Path(matrix.__file__),Path(progress.__file__),Path(chemical_runner.__file__),Path(chemical.__file__),Path(stage_runner.__file__),Path(stages.__file__))
    return base.sources()|{str(p.relative_to(base.e.ROOT)):sha256(p.read_bytes()).hexdigest() for p in paths}


def _copy(function,namespace):
    copied=FunctionType(function.__code__,namespace,function.__name__,function.__defaults__,function.__closure__)
    copied.__kwdefaults__=function.__kwdefaults__
    return copied


def identity(case,mode="uncensored"):
    if mode not in ("census","uncensored"):raise ValueError("Unknown dormancy recording mode")
    namespace=base.identity.__globals__.copy();namespace["sources"]=sources
    _,protocol=_copy(base.identity,namespace)(case,mode)
    protocol.update(solver="analytic_dormancy_zero_face_newton",architecture=platform.machine(),operating_system=platform.system())
    return sha256(base.e.dumps(protocol).encode()).hexdigest(),protocol


def read_record(case,mode="uncensored",raw=RAW):
    namespace=base.read_record.__globals__.copy();namespace["identity"]=identity
    return _copy(base.read_record,namespace)(case,mode,raw)


def run(case,mode="uncensored",raw=RAW,expected_sources=None):
    namespace=base.run.__globals__.copy()
    namespace.update(identity=identity,read_record=read_record,sources=sources,integrate_finite=numerical.integrate_finite)
    return _copy(base.run,namespace)(case,mode,raw,expected_sources)


def _worker(task):
    case,mode,raw,frozen=task
    try:return case.case_id,run(case,mode,raw,frozen),None
    except Exception as error:return case.case_id,None,repr(error)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode",choices=("census","uncensored"),default="uncensored")
    parser.add_argument("--years",type=float)
    parser.add_argument("--workers",type=int,default=4)
    parser.add_argument("--max-step",type=float,default=10.)
    parser.add_argument("--rtol",type=float,default=2e-8)
    parser.add_argument("--case-id",action="append")
    parser.add_argument("--epsilon",type=float)
    parser.add_argument("--raw-dir",type=Path,default=RAW)
    args=parser.parse_args()
    years=args.years or (100000. if args.mode=="census" else 30000.)
    cases=[replace(c,max_step_yr=args.max_step,rtol=args.rtol) for c in base.design(years)]
    if args.case_id:
        cases=[c for c in cases if c.case_id in args.case_id]
        if len(cases)!=len(args.case_id):raise ValueError("Unknown case selection")
    if args.epsilon is not None:
        if not args.case_id:raise ValueError("Select base cases for an epsilon refinement")
        cases=[replace(c,case_id=f"{c.case_id}_eps{args.epsilon:g}",epsilon=args.epsilon) for c in cases]
    frozen=sources();results=[];failures=[]
    with ProcessPoolExecutor(args.workers) as pool:
        tasks=[pool.submit(_worker,(c,args.mode,args.raw_dir,frozen)) for c in cases]
        for i,future in enumerate(as_completed(tasks),1):
            key,record,error=future.result()
            if error:
                failures.append(dict(case_id=key,error=error));print("FAILED",key,error,flush=True)
            else:results.append(record);print(i,len(cases),key,flush=True)
    suffix=sha256(base.e.dumps(sorted(identity(c,args.mode)[0] for c in cases)).encode()).hexdigest()[:16]
    ledger=dict(completed=len(results),requested=len(cases),mode=args.mode,failures=failures,source_sha256=frozen,
                architecture=platform.machine(),operating_system=platform.system(),
                receipts=[{k:r[k] for k in ("fingerprint","raw_file","raw_sha256")} for r in results])
    args.raw_dir.mkdir(parents=True,exist_ok=True)
    (args.raw_dir/f"prefix_batch_{suffix}.json").write_text(base.e.dumps(ledger)+"\n")
    if failures:raise RuntimeError(f"{len(failures)} dormancy runs failed; see batch ledger")


if __name__=="__main__":main()
