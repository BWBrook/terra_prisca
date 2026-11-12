"""Prepare and read back owned Stage B′ evidence; never deposit or publish it."""

from hashlib import sha256
import gzip
import json
from pathlib import Path
import tarfile


ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'local/haze/stage-b-prime-archive-2026-11-12'
OUT.mkdir(parents=True,exist_ok=True)
ARCHIVE=OUT/'haze-stage-b-prime-20261112.tar.gz'
if ARCHIVE.exists():raise FileExistsError('Existing evidence archives are preserved; choose a fresh output')
selected={}


def include(relative,expected=None):
    path=Path(relative)
    if path.is_absolute() or '..' in path.parts:raise ValueError('Only repository-relative owned files')
    source=ROOT/path
    digest=sha256(source.read_bytes()).hexdigest()
    if expected is not None and expected!=digest:raise ArithmeticError(f'Input hash changed: {path}')
    selected[str(path)]=dict(path=str(path),sha256=digest,bytes=source.stat().st_size)


transients=ROOT/'models/haze_world/figures/dynamic_realisation/transient_archive_manifest.json'
canonical=json.loads(transients.read_text())
if len(canonical['receipts'])!=33:raise ArithmeticError('Expected29 main and4 tighter controls')
for entry in canonical['canonical_raw']+canonical['public_files']:
    include(entry['path'],entry['sha256'])
include(transients.relative_to(ROOT))
continuum=ROOT/'models/haze_world/figures/continuum_habitats'
manifest=json.loads((continuum/'manifest.json').read_text())
for name,digest in manifest['finite_input_export_correction']['frozen_cache_sha256'].items():include(name,digest)
for path in continuum.iterdir():
    if path.is_file() and path.name!='archive_receipt.json':include(path.relative_to(ROOT))
for folder in ('local/haze/continuum_source_epochs','local/haze/continuum_characteristic'):
    for path in (ROOT/folder).rglob('*'):
        if path.is_file() and path.suffix in ('.py','.json'):include(path.relative_to(ROOT))
for path in (ROOT/'src/terra_prisca').rglob('*.py'):include(path.relative_to(ROOT))
for name in ('pyproject.toml','uv.lock','LICENSE','LICENSE-CONTENT'):include(name)
for pattern in ('continuum*2026-11-12.*','homogeneous-transients-independent-2026-11-12.*','package-stage-b-prime-2026-11-12.py'):
    for path in (ROOT/'docs/audits').glob(pattern):include(path.relative_to(ROOT))
for path in (ROOT/'tests').glob('test_*'):
    if path.suffix=='.py' and any(term in path.name for term in ('continuum','dynamic_transient')):include(path.relative_to(ROOT))

entries=sorted(selected.values(),key=lambda r:r['path'])
index=dict(scope='Owned numerical evidence only; no third-party PDFs or publication deposit.',
           files=entries,file_count=len(entries),payload_bytes=sum(r['bytes'] for r in entries),
           canonical_transient_receipts=len(canonical['receipts']))
index_path=OUT/'members.json';index_path.write_text(json.dumps(index,indent=2)+'\n')
with ARCHIVE.open('wb') as stream,gzip.GzipFile(filename='',mode='wb',fileobj=stream,mtime=0) as compressed,tarfile.open(fileobj=compressed,mode='w|') as archive:
    for entry in entries:
        source=ROOT/entry['path'];info=archive.gettarinfo(str(source),arcname=entry['path'])
        info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0;info.mode=0o644
        with source.open('rb') as data:archive.addfile(info,data)
with tarfile.open(ARCHIVE,'r:gz') as archive:
    members=archive.getmembers()
    if [member.name for member in members]!=[entry['path'] for entry in entries]:raise ArithmeticError('Archive member identity differs')
    for member,entry in zip(members,entries):
        data=archive.extractfile(member)
        if data is None or sha256(data.read()).hexdigest()!=entry['sha256']:raise ArithmeticError(f'Readback failed: {member.name}')
receipt=dict(archive_name=ARCHIVE.name,archive_sha256=sha256(ARCHIVE.read_bytes()).hexdigest(),archive_bytes=ARCHIVE.stat().st_size,
             members_sha256=sha256(index_path.read_bytes()).hexdigest(),payload_files=len(entries),payload_bytes=index['payload_bytes'],
             canonical_transient_receipts=len(canonical['receipts']),local_full_member_readback=True,
             publication_status='Prepared evidence archive; not deposited or publicly released',
             packager_sha256=sha256(Path(__file__).read_bytes()).hexdigest())
(OUT/'archive_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
