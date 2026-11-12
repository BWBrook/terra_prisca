"""Archive owned D1/D2 replay evidence with full readback; no deposition."""

from hashlib import sha256
import gzip
import json
from pathlib import Path
import tarfile

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'local/haze/graded-dials-archive-20261112'
OUT.mkdir(parents=True,exist_ok=True)
archive=OUT/'haze-graded-dials-20261112.tar.gz'
if archive.exists():raise FileExistsError('Preserve existing archives; choose a fresh output')
paths=set()
for folder in ('local/haze/graded_dials','local/haze/graded_thresholds',
               'models/haze_world/figures/graded_dials','src/terra_prisca'):
    for path in (ROOT/folder).rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts and not path.name.endswith('.partial.json'):
            if path.suffix in ('.py','.json','.csv','.md','.png','.toml','.lock'):
                paths.add(path.relative_to(ROOT))
for pattern in ('graded-dial-*-2026-11-12.*','package-graded-dials-2026-11-12.py'):
    paths.update(p.relative_to(ROOT) for p in (ROOT/'docs/audits').glob(pattern))
paths.update(p.relative_to(ROOT) for p in (ROOT/'tests').glob('test_graded*.py'))
paths.update(Path(name) for name in ('pyproject.toml','uv.lock','LICENSE','LICENSE-CONTENT',
    'models/haze_world/graded-dial-spec.md','models/haze_world/graded-dial-methods.md'))
entries=[]
for relative in sorted(paths):
    path=ROOT/relative
    entries.append(dict(path=str(relative),sha256=sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size))
index=dict(scope='Owned D1/D2 numerical evidence, source epochs and audits; no third-party PDFs; not a release.',
           files=entries,file_count=len(entries),payload_bytes=sum(r['bytes'] for r in entries))
index_path=OUT/'members.json';index_path.write_text(json.dumps(index,indent=2)+'\n')
with archive.open('wb') as stream,gzip.GzipFile(filename='',mode='wb',fileobj=stream,mtime=0) as compressed,tarfile.open(fileobj=compressed,mode='w|') as tar:
    for row in entries:
        path=ROOT/row['path'];info=tar.gettarinfo(str(path),arcname=row['path'])
        info.uid=info.gid=0;info.uname=info.gname='';info.mode=0o644;info.mtime=0
        with path.open('rb') as data:tar.addfile(info,data)
with tarfile.open(archive,'r:gz') as tar:
    members=tar.getmembers()
    if [r.name for r in members]!=[r['path'] for r in entries]:raise ArithmeticError('Archive membership differs')
    for member,row in zip(members,entries):
        if sha256(tar.extractfile(member).read()).hexdigest()!=row['sha256']:raise ArithmeticError('Archive readback failed')
receipt=dict(archive_name=archive.name,archive_sha256=sha256(archive.read_bytes()).hexdigest(),
    archive_bytes=archive.stat().st_size,members_sha256=sha256(index_path.read_bytes()).hexdigest(),
    payload_files=len(entries),payload_bytes=index['payload_bytes'],local_full_member_readback=True,
    publication_status='Prepared working evidence; not deposited or publicly released',
    packager_sha256=sha256(Path(__file__).read_bytes()).hexdigest())
(OUT/'archive_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
