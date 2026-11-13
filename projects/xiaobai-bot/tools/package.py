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
readme=f'''小白Bot / Xiaobai Bot · {a.profile} · {a.tag}
作者：理工阿白菌 / TechABJ；底座与共享引擎：feng-30m，Apache-2.0。
研发候选：已做主机数值、分区和编译检查，尚未做实体板验收。知识问答仍会出现错误。

Windows：安装 XiaobaiBot-Setup.exe，选择安装目录，再选择本包 manifest.json。
核对板上实际型号、USB 串口，确认后烧录。不要把 N16 包烧入 N32 配置或反之。

手工烧录（需要 Python 和 esptool 5）：
python -m esptool --chip esp32s3 --port COMx --baud 460800 write-flash --flash-size {'16MB' if a.profile=='N16R8' else '32MB'} 0x0 bootloader.bin 0x8000 partitions.bin 0x10000 firmware.bin {hex(mo)} model.bin {hex(to)} tokenizer.bin

完成后打开 115200 波特率 UTF-8 串口，或连接热点 XiaobaiBot（密码 xiaobai2026），访问 http://192.168.4.1。
无需外置 SD 卡或聊天 API。网页和模型均在开发板内运行。/reset 清空上下文。
源码及持续验证：https://github.com/Zeruik/Arduino/tree/xiaobai-bot/projects/xiaobai-bot
'''
(folder/'README.txt').write_text(readme)
for src in [folder/'README.txt',root/'docs/THIRD_PARTY.md']:
    if src.exists():
        dest=folder/src.name
        if src.resolve()!=dest.resolve():shutil.copy2(src,dest)
        manifest['files'].append({'name':dest.name,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
(folder/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
shutil.make_archive(str(folder),'zip',folder)
hf=Path(a.hf);target=dist/f'XiaobaiBot-{a.profile}-{a.tag}-FP32.zip'
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=3) as z:
    for p in hf.rglob('*'):
        if p.is_file() and p.name!='trainer.pt':z.write(p,str(p.relative_to(hf)))
    for name in ['LICENSE','NOTICE']:z.write(root/name,name)
    z.writestr('MODEL_CARD.md',f'# Xiaobai Bot {a.profile}\nFP32 master weights corresponding to candidate Q4 export.\nDerived from feng-30m with vocabulary adaptation, SFT and Q4-aware training.\nNot an original pretrained foundation model. Physical-board acceptance pending.\nAuthor: TechABJ / 理工阿白菌. Base: jiaheng0815/feng-30m, Apache-2.0.\n')
print(str(folder)+'.zip');print(target)
