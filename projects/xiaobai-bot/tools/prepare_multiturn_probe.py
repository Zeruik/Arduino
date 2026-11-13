"""Context copying experiment; no new factual/test answers are synthesized."""
import json,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1]
first=list('青白红绿蓝金银紫橙灰粉黑');second=list('松竹兰梅禾云雨风山海星月')
codes=[a+b for a in first for b in second if a!=b]
colors=['蓝色','白色','红色','绿色','紫色','黄色']
rows=[]
for i,code in enumerate(codes[:96]):
 color=colors[i%6]
 msgs=[{'role':'user','content':f'我们给这次方案起名为{code}，外壳选{color}。'}, {'role':'assistant','content':'好的，我记下了方案名称和外壳颜色。'}, {'role':'user','content':'后面还要讨论电路，先别忘记前面的安排。'}, {'role':'assistant','content':'好的，我们可以接着讨论。'}, {'role':'user','content':'请复述刚才约定的方案名称和外壳颜色。'}, {'role':'assistant','content':f'方案名称是{code}，外壳是{color}。'}]
 rows.append({'messages':msgs,'source':'TechABJ deterministic context-copy curriculum','context_code':code,'context_color':color,'loss_last_only':i>=64})
train=rows[:64]*4+[json.loads(x) for x in (root/'data/train-semantic-round3.jsonl').read_text().splitlines()]
val=rows[64:80]
# New combinations and different query phrasing, created before training/output.
held=rows[80:96]
for r in held:r['messages'][-2]['content']='方案叫哪个名字？外壳之前选了什么颜色？'
manifest={'train_dialogues':64,'val_dialogues':16,'heldout_dialogues':16,'facts':'only user-provided temporary names/colors, not external knowledge','val_loss':'final assistant turn only; earlier turns masked','hashes':{}}
for path,data in [('data/train-multiturn-round4.jsonl',train),('data/val-multiturn-round4.jsonl',val),('eval/context-round4-frozen.jsonl',held)]:
 p=root/path;p.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in data));manifest['hashes'][path]=hashlib.sha256(p.read_bytes()).hexdigest()
assert not {r['context_code'] for r in rows[:64]}&{r['context_code'] for r in rows[64:]}
(root/'eval/round4-curriculum-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print(manifest)
