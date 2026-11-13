"""候选版打包；不把没有实机日志的交付标记为已通过实机。"""
import argparse,json,hashlib,shutil,zipfile
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--profile',choices=['N16R8','N32R16'],required=True);ap.add_argument('--hf',required=True);ap.add_argument('--q4',required=True);ap.add_argument('--tag',required=True);a=ap.parse_args()
root=Path(__file__).resolve().parents[1];dist=root/'dist';dist.mkdir(exist_ok=True)
folder=dist/f'XiaobaiBot-{a.profile}-{a.tag}';folder.mkdir(exist_ok=True)
pio=root/'firmware/.pio/build'/('n16r8' if a.profile=='N16R8' else 'n32r16')
mo,to=(0x200000,0xf80000) if a.profile=='N16R8' else (0x110000,0x1000000)
items=[(Path(a.q4)/'model.bin','model.bin',mo),(Path(a.q4)/'tokenizer.bin','tokenizer.bin',to),(pio/'bootloader.bin','bootloader.bin',0),(pio/'partitions.bin','partitions.bin',0x8000),(pio/'firmware.bin','firmware.bin',0x10000)]
manifest={'profile':a.profile,'tag':a.tag,'status':'candidate','physical_board_test':False,'files':[]}
for src,name,offset in items:
    if not src.exists():raise FileNotFoundError(f'没有编译产物，不能生成可烧录包：{src}')
    shutil.copy2(src,folder/name);b=src.read_bytes();manifest['files'].append({'name':name,'offset':offset,'size':len(b),'sha256':hashlib.sha256(b).hexdigest()})
for name in ['LICENSE','NOTICE']:
    shutil.copy2(root/name,folder/name);b=(root/name).read_bytes();manifest['files'].append({'name':name,'sha256':hashlib.sha256(b).hexdigest()})
(folder/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
shutil.make_archive(str(folder),'zip',folder)
hf=Path(a.hf);target=dist/f'XiaobaiBot-{a.profile}-{a.tag}-FP32.zip'
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=3) as z:
    for p in hf.rglob('*'):
        if p.is_file() and p.name!='trainer.pt':z.write(p,str(p.relative_to(hf)))
    for name in ['LICENSE','NOTICE']:z.write(root/name,name)
print(folder.with_suffix('.zip'));print(target)
