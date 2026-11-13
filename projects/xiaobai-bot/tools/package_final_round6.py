"""Archive final sources and evidence without model weights or transient tools."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
TEXT={'.md','.txt','.json','.jsonl','.py','.c','.h','.cpp','.ino','.ini','.csv','.yml','.yaml','.iss','.html','.css','.js','.toml'}

def collect(folders):
    result=set()
    for folder in folders:
        for p in (ROOT/folder).rglob('*'):
            if p.is_file() and not any(x.startswith('.') or x=='__pycache__' for x in p.relative_to(ROOT).parts):
                if p.suffix.lower() in TEXT:
                    result.add(p)
    return result

def archive(name,files,extra=None):
    entries={str(p.relative_to(ROOT)):p.read_bytes() for p in sorted(files)}
    if extra:entries.update(extra)
    hashes={k:{'bytes':len(v),'sha256':hashlib.sha256(v).hexdigest()} for k,v in entries.items()}
    entries['ARCHIVE_CONTENTS_SHA256.json']=(json.dumps(hashes,ensure_ascii=False,indent=2)+'\n').encode()
    target=ROOT/'dist'/name
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for key,data in entries.items():z.writestr(key,data)
    return {'filename':name,'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'members':len(entries)}

base={ROOT/x for x in ['README.md','LICENSE','NOTICE','requirements.txt']}
source=base|collect(['docs','tools','desktop','firmware','tests','web','vendor','data'])
workflow=next(p for p in [ROOT/'.github/workflows/xiaobai-bot.yml',
                         ROOT.parents[1]/'.github/workflows/xiaobai-bot.yml',
                         ROOT.parent/'round5-workflow.yml'] if p.exists())
assert workflow.exists() and "if: github.event_name == 'workflow_dispatch'" in workflow.read_text()
result=[]
result.append(archive('XiaobaiBot-final-source-round6.zip',source,{'.github/workflows/xiaobai-bot.yml':workflow.read_bytes()}))
evidence=base|collect(['docs','eval'])
# Upload indices and the archive's own checks are published beside the ZIPs;
# excluding them avoids retaining a stale hash from a previous packaging pass.
evidence.difference_update(ROOT/'eval'/n for n in [
    'round6-archive-checks.json','round6-artifacts.json','round6-completion.json'])
# All raw logs, including earlier failed attempts, remain evidence.
evidence.update(q for q in (ROOT/'logs').glob('*') if q.is_file())
for folder in (ROOT/'models').iterdir():
    if not folder.is_dir():continue
    for name in ['summary.json','train_log.jsonl','final/checkpoint_meta.json','rolling/checkpoint_meta.json']:
        p=folder/name
        if p.exists():evidence.add(p)
result.append(archive('XiaobaiBot-final-evidence-round6.zip',evidence,{
    'SOURCE_ARCHIVE.json':(json.dumps(result[0],indent=2)+'\n').encode(),
    'SNAPSHOT_NOTE.txt':'Download IDs and task pause receipt are recorded in the final GitHub index/commit after uploading these snapshots. No weights or optimizer tensors are in this evidence ZIP.\n'.encode(),
}))
(ROOT/'eval/round6-archive-checks.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False))
