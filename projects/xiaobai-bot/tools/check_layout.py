import csv,json,struct,argparse,hashlib
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--model',required=True);ap.add_argument('--profile',choices=['n16','n32'],required=True);ap.add_argument('--firmware');ap.add_argument('--out',required=True);a=ap.parse_args()
root=Path(__file__).resolve().parents[1];d=Path(a.model);rows=[]
for line in (root/f'firmware/partitions_{a.profile}.csv').read_text().splitlines():
    if not line.strip() or line.startswith('#'):continue
    name,kind,sub,off,size=next(csv.reader([line]));rows.append(dict(name=name,offset=int(off,0),size=int(size,0)))
rows.sort(key=lambda r:r['offset']);last=0
for r in rows:
    assert r['offset']>=last;last=r['offset']+r['size']
assert last<= (16 if a.profile=='n16' else 32)*1024*1024
parts={r['name']:r for r in rows};files={}
for name,filename in [('model','model.bin'),('tokdata','tokenizer.bin')]:
    b=(d/filename).read_bytes();assert len(b)<=parts[name]['size'];files[filename]={'size':len(b),'sha256':hashlib.sha256(b).hexdigest(),'offset':parts[name]['offset']}
assert parts['model']['offset']+parts['model']['size']<=0x1000000,'模型跨越当前 mmap 布局边界'
if a.firmware:
    size=Path(a.firmware).stat().st_size;assert size<=parts['factory']['size'];files['firmware.bin']={'size':size,'offset':parts['factory']['offset']}
report={'profile':a.profile,'partitions':rows,'files':files,'layout_pass':True,'physical_board_test':False}
Path(a.out).write_text(json.dumps(report,indent=2));print(report)
