"""Replay short ledger auditors with outputs redirected outside the checkout."""
from pathlib import Path
import contextlib
import importlib.util
import json
import traceback
import sys

repo=Path(sys.argv[1]).resolve()
out=Path(__file__).resolve().parent/'author_replays'
out.mkdir(exist_ok=True)
records=[]
for label in ['precursors','core','communities','turnover']:
    path=repo/f'models/haze_world/review/synthesis-{label}-audit-2026-11-11.py'
    spec=importlib.util.spec_from_file_location('replay_'+label,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.HERE=out
    rec={'audit':label,'input_script':str(path.relative_to(repo)),'output_redirected':True}
    with (out/f'{label}.log').open('w') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
        try:
            module.main()
            rec['status']='passed'
        except Exception as exc:
            rec.update(status='blocked_or_failed',exception=type(exc).__name__,message=str(exc))
            traceback.print_exc()
    records.append(rec)
    print(json.dumps(rec),flush=True)
(out/'replay_status.json').write_text(json.dumps(records,indent=2)+'\n')
