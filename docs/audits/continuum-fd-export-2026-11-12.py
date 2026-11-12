"""Repair only the finite-input export; preserve the original calculation epoch."""

import ast
from hashlib import sha256
import itertools
import json
from pathlib import Path

from terra_prisca.haze_world import continuum_experiments as runs

root=runs.ROOT
epoch=root/'local/haze/continuum_source_epochs/export_before_fd_fix'
old=epoch/'continuum_experiments.py'
before=json.loads((epoch/'manifest.json').read_text())
old_sources=before['source_sha256']
producer='src/terra_prisca/haze_world/continuum_experiments.py'
assert runs.digest(old)==old_sources[producer]
for name,digest in old_sources.items():
    if name!=producer:assert runs.digest(root/name)==digest,name


def without_flat(path):
    tree=ast.parse(path.read_text())
    tree.body=[node for node in tree.body if not isinstance(node,ast.FunctionDef) or node.name!='flat']
    return ast.dump(tree,include_attributes=False)


assert without_flat(old)==without_flat(root/producer),'Only the output flattening function may change'
stamp=sha256(json.dumps(old_sources,sort_keys=True).encode()).hexdigest()[:20]
cache=root/'local/haze/continuum_habitats'
c0_path=cache/f'c0-{stamp}.json'
c0=json.loads(c0_path.read_text())
settings=list(itertools.product(('fixed','products'),(0.,.5),(1.,3.,6.),(1e-4,1e-3,1e-2,1e-1),(.3,)))
settings+=list(itertools.product(('fixed','products'),(0.,.5),(3.,),(1e-4,1e-3,1e-2,1e-1),(.24,.36)))
c1=[];inputs={str(c0_path.relative_to(root)):runs.digest(c0_path)}
for setting in settings:
    path=cache/(sha256(json.dumps([stamp,setting]).encode()).hexdigest()[:24]+'.json')
    value=json.loads(path.read_text())
    assert tuple(value[k] for k in ('chemistry','fraction','sigma_k','dispersal_yr','nominal_potential'))==setting
    c1.append(value);inputs[str(path.relative_to(root))]=runs.digest(path)
c1.sort(key=lambda r:tuple(str(r[k]) for k in ('chemistry','fraction','sigma_k','dispersal_yr','nominal_potential')))
manifest=runs.write_tables(runs.OUTPUT,c0,c1,old_sources)
receipt=dict(calculation_source_sha256=old_sources[producer],export_source_sha256=runs.digest(root/producer),
             exporter_sha256=runs.digest(Path(__file__)),all_other_producer_AST_unchanged=True,
             frozen_cache_sha256=inputs,
             change='Export the qualified fine perturbation when used; retain coarse value and expose the step. No equation, state, slope, gain or spectrum changed.')
manifest['finite_input_export_correction']=receipt
(runs.OUTPUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k!='frozen_cache_sha256'},indent=2))
