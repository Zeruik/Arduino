"""下载固定版本的中文底座，并保留可闭合的 BPE 前缀词表。"""
import argparse, json, shutil, urllib.request
from pathlib import Path
import torch
from safetensors.torch import load_file, save_file
from tokenizers import Tokenizer

REV = 'a9709020bb00b6fb60e616cce8fa487e30b961a6'
ap = argparse.ArgumentParser()
ap.add_argument('--vocab', type=int, choices=[8192,16384], default=8192)
ap.add_argument('--out', required=True)
a = ap.parse_args()
root = Path(__file__).resolve().parents[1]
src = root/'upstream-model'; src.mkdir(exist_ok=True)
out = Path(a.out)
if out.exists(): raise SystemExit('输出目录已存在，请换一个版本目录。')
for name in ['model.safetensors','config.json','tokenizer.json','tokenizer_config.json','chat_template.jinja','generation_config.json']:
    dest = src/name
    if not dest.exists():
        tmp = dest.with_suffix(dest.suffix+'.part')
        urllib.request.urlretrieve(f'https://huggingface.co/jiaheng0815/feng-30m/resolve/{REV}/{name}',tmp)
        tmp.replace(dest)
j = json.loads((src/'tokenizer.json').read_text())
v = {s:i for s,i in j['model']['vocab'].items() if i<a.vocab}
j['model']['vocab'] = v
j['model']['merges'] = [m for m in j['model']['merges'] if (''.join(m) if isinstance(m,list) else m.replace(' ','')) in v]
# 按原 token ID 的前缀裁剪：保留字节 fallback 与全部 merge 依赖，不重编号。
for m in j['model']['merges']:
    x,y=m if isinstance(m,list) else m.split(' ')
    assert x in v and y in v
Tokenizer.from_str(json.dumps(j))
out.mkdir(parents=True)
(out/'tokenizer.json').write_text(json.dumps(j,ensure_ascii=False))
for name in ['tokenizer_config.json','chat_template.jinja','generation_config.json']:
    shutil.copy2(src/name,out/name)
c=json.loads((src/'config.json').read_text()); c['vocab_size']=a.vocab
(out/'config.json').write_text(json.dumps(c,indent=2))
sd=load_file(str(src/'model.safetensors'))
for k in ['model.embed_tokens.weight','lm_head.weight']:
    if k in sd: sd[k]=sd[k][:a.vocab].contiguous()
save_file(sd,str(out/'model.safetensors'),metadata={'format':'pt'})
(out/'provenance.json').write_text(json.dumps({'base':'jiaheng0815/feng-30m','revision':REV,'vocab':a.vocab,'method':'BPE prefix pruning, then supervised fine-tuning','author':'TechABJ / 理工阿白菌'},ensure_ascii=False,indent=2))
print('已准备',out, sum(t.numel() for t in sd.values()))
