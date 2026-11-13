"""可恢复的 CPU/GPU SFT。训练目标只计算 assistant token，独立验证集选型。"""
import argparse,json,random,time,os,shutil,hashlib
from pathlib import Path
import torch
from transformers import AutoTokenizer, Qwen3ForCausalLM

ap=argparse.ArgumentParser()
ap.add_argument('--model',required=True); ap.add_argument('--out',required=True)
ap.add_argument('--data',default='data/train.jsonl'); ap.add_argument('--val',default='data/val.jsonl')
ap.add_argument('--steps',type=int,default=2000); ap.add_argument('--minutes',type=float,default=180)
ap.add_argument('--lr',type=float,default=8e-6); ap.add_argument('--threads',type=int,default=4)
ap.add_argument('--layers',type=int,default=2); ap.add_argument('--resume',action='store_true')
ap.add_argument('--seq',type=int,default=192); ap.add_argument('--save-every',type=int,default=100)
ap.add_argument('--qat',action='store_true',help='Q4 block64 量化感知训练')
a=ap.parse_args(); torch.set_num_threads(a.threads); random.seed(20261113); torch.manual_seed(20261113)
out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
if (out/'final').exists(): raise SystemExit('已完成，拒绝覆盖；请新建版本目录。')
state_path=out/'rolling'/'trainer.pt'
source=str(out/'rolling') if a.resume and state_path.exists() else a.model
if source!=a.model and (Path(source)/'checkpoint_meta.json').exists():
    meta=json.loads((Path(source)/'checkpoint_meta.json').read_text())
    expected={'data_sha256':hashlib.sha256(Path(a.data).read_bytes()).hexdigest(),'qat':a.qat,'seq':a.seq,'layers':a.layers,'lr':a.lr}
    if any(meta[k]!=v for k,v in expected.items()):
        raise SystemExit('Resume configuration/data changed; use a new version directory.')
tok=AutoTokenizer.from_pretrained(source)
model=Qwen3ForCausalLM.from_pretrained(source,dtype=torch.float32)
device='cuda' if torch.cuda.is_available() else 'cpu'; model.to(device)
for p in model.parameters():p.requires_grad_(False)
for layer in model.model.layers[-a.layers:]:
    for p in layer.parameters():p.requires_grad_(True)
for p in model.model.norm.parameters():p.requires_grad_(True)
opt=torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],lr=a.lr,weight_decay=0.01)
if a.qat:
    from torch.nn.utils import parametrize
    class Q4(torch.nn.Module):
        def __init__(self):super().__init__();self.cached=None
        def forward(self,w):
            if not w.requires_grad and self.cached is not None:return self.cached
            shape=w.shape;b=w.reshape(-1,64)
            s=(b.detach().abs().amax(-1,keepdim=True)/7).clamp(min=1e-8)
            q=torch.round(b/s).clamp(-8,7)
            dq=(q*s.half().float()).reshape(shape)
            if not w.requires_grad:self.cached=dq.detach();return self.cached
            return w+(dq-w).detach()
    # frozen 参数直接反量化一次；可训练 Linear 用 STE，每步重新量化。
    for module in model.modules():
        if isinstance(module,(torch.nn.Linear,torch.nn.Embedding)) and module.weight.shape[-1]%64==0:
            parametrize.register_parametrization(module,'weight',Q4())
start_step=0
if source!=a.model:
    state=torch.load(state_path,map_location=device,weights_only=False)
    opt.load_state_dict(state['optimizer']);start_step=state['step'];random.setstate(state['random'])

def load(path):
    rows=[]
    for line in Path(path).read_text().splitlines():
        r=json.loads(line); q=r['question']; ans=r['answer']
        prefix=f'<|im_start|>user\n{q}<|im_end|>\n<|im_start|>assistant\n'
        ids=tok.encode(prefix,add_special_tokens=False)
        tail=tok.encode(ans+'<|im_end|>\n',add_special_tokens=False)
        if len(ids)+len(tail)>a.seq:continue
        x=ids+tail; lab=[-100]*len(ids)+tail
        rows.append((torch.tensor([x],device=device),torch.tensor([lab],device=device)))
    if not rows:raise ValueError('没有可用数据')
    return rows
train=load(a.data); val=load(a.val)
def validate():
    model.eval()
    with torch.no_grad(): losses=[model(input_ids=x,labels=y,use_cache=False).loss.item() for x,y in val]
    model.train(); return sum(losses)/len(losses)
def save(target,step,with_opt=False):
    temp=out/(target+'.tmp');temp.mkdir(exist_ok=True)
    if a.qat:
        # 存储 HF 标准权重名；保存的是浮点主权重，量化由 exporter 完成。
        sd={}
        for key,value in model.state_dict().items():
            key=key.replace('.parametrizations.weight.original','.weight')
            sd[key]=value
        model.save_pretrained(temp,state_dict=sd)
    else:model.save_pretrained(temp)
    tok.save_pretrained(temp)
    (temp/'checkpoint_meta.json').write_text(json.dumps({'step':step,'data_sha256':hashlib.sha256(Path(a.data).read_bytes()).hexdigest(),'qat':a.qat,'seq':a.seq,'layers':a.layers,'lr':a.lr}))
    if with_opt:torch.save({'optimizer':opt.state_dict(),'step':step,'random':random.getstate()},temp/'trainer.pt')
    dest=out/target
    old=out/(target+'.previous')
    if old.exists():shutil.rmtree(old)
    if dest.exists():dest.rename(old)
    temp.rename(dest)
    if old.exists():shutil.rmtree(old)

t0=time.monotonic(); initial=validate(); best=initial
# Preserve the best candidate across bounded resume segments.
previous_summary=out/'summary.json'
if source!=a.model and previous_summary.exists() and (out/'best/model.safetensors').exists():
    best=min(initial,float(json.loads(previous_summary.read_text())['best_val_loss']))
    if initial < float(json.loads(previous_summary.read_text())['best_val_loss']):
        save('best',start_step)
else:
    save('best',start_step)
log=open(out/'train_log.jsonl','a',buffering=1)
print(json.dumps({'device':device,'train_rows':len(train),'val_rows':len(val),'initial_val_loss':initial,'trainable_params':sum(p.numel() for p in model.parameters() if p.requires_grad)},ensure_ascii=False),flush=True)
step=start_step
try:
    for step in range(start_step+1,a.steps+1):
        model.train();x,y=random.choice(train)
        loss=model(input_ids=x,labels=y,use_cache=False).loss
        if not torch.isfinite(loss): raise RuntimeError('非有限损失，停止训练')
        opt.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.0);opt.step()
        record={'step':step,'loss':loss.item(),'elapsed_seconds':round(time.monotonic()-t0,2)}
        if step%a.save_every==0:
            vl=validate();record['val_loss']=vl
            if vl<best:best=vl;save('best',step)
            save('rolling',step,True)
        log.write(json.dumps(record)+'\n')
        if step%10==0:print(json.dumps(record),flush=True)
        if time.monotonic()-t0>a.minutes*60:break
finally:
    save('rolling',step,True)
    summary={'step':step,'initial_val_loss':initial,'best_val_loss':best,'seconds':time.monotonic()-t0,'complete':step>=a.steps,'train_rows':len(train),'val_rows':len(val),'base':a.model,'trainable_layers':a.layers,'data_sha256':hashlib.sha256(Path(a.data).read_bytes()).hexdigest()}
    (out/'summary.json').write_text(json.dumps(summary,indent=2))
if step>=a.steps:
    shutil.copytree(out/'best',out/'final')
print(json.dumps(summary),flush=True)
