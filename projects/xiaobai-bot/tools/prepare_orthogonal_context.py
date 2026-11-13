"""Balanced procedural curriculum, no copied prior test questions/answers.
Every project identifier is paired with EVERY color, in each scenario class.
"""
import json,hashlib,random,collections
from pathlib import Path
root=Path(__file__).resolve().parents[1];colors=['红色','黄色','蓝色','绿色','白色','紫色']
# Distinct from all round4 names. Colors are fully crossed, never tied to a glyph.
names=[a+b for a in '春夏秋冬晨暮晴霜' for b in '帆泉谷桥']
rng=random.Random(51113)
def make(pool,split):
 out=[]
 for ni,name in enumerate(pool):
  for ci,color in enumerate(colors):
   for kind in ['keep','change_color','replace_record','other_person']:
    target_name,target_color=name,color
    other=pool[(ni+1)%len(pool)]
    if kind=='keep':middle='先保留这份记录，等会儿我会询问它。'
    elif kind=='change_color':
     # Each output color occurs once for every name within this class.
     target_color=colors[(ci+1)%6];middle=f'修改一下：色标换成{target_color}，代号仍按原记录。'
    elif kind=='replace_record':
     target_name=other;target_color=colors[(ci+2)%6];middle=f'旧记录作废，我这份的新代号为{target_name}，新色标为{target_color}。'
    else:
     distractor=colors[(ci+3)%6];middle=f'另外一人的代号是{other}，色标是{distractor}。那是对方的，不修改我的记录。'
    first=f'这是我自己的记录：代号{name}，色标{color}。请暂存。'
    question='请给出我的现行记录，严格使用“代号：名称；色标：颜色。”这个格式。' if split!='test' else '按“代号：名称；色标：颜色。”写出我目前这份记录，别填别人的。'
    messages=[{'role':'user','content':first},{'role':'assistant','content':'收到，我记下了。'},{'role':'user','content':middle},{'role':'assistant','content':'好的，按你的说明处理。'},{'role':'user','content':question},{'role':'assistant','content':f'代号：{target_name}；色标：{target_color}。'}]
    out.append({'messages':messages,'context_code':target_name,'context_color':target_color,'kind':kind,'loss_last_only':True,'source':'TechABJ procedural user-record curriculum; no external facts'})
 rng.shuffle(out);return out
train=make(names[:12],'train');val=make(names[12:16],'val');test=make(names[16:20],'test')
# Isolate paired counterfactual inputs: same name appears with all six colors.
audit={}
for split,rows in [('train',train),('val',val),('test',test)]:
 counts=collections.Counter((r['kind'],r['context_code'],r['context_color']) for r in rows)
 for kind in ['keep','change_color','replace_record','other_person']:
  pool={r['context_code'] for r in rows if r['kind']==kind}
  for n in pool:assert len({counts[kind,n,c] for c in colors})==1 and counts[kind,n,colors[0]]>0
 audit[split]={'rows':len(rows),'kind_counts':dict(collections.Counter(r['kind'] for r in rows)),'each_name_crossed_with_all_colors':True}
assert not set(names[:12])&set(names[12:20])
# Reuse only pre-test authored semantic QA; oversample equally to limit template spillover.
replay=[json.loads(x) for x in (root/'data/train-semantic-round3.jsonl').read_text().splitlines()]
train+=replay*4
blocked=set()
for f in ['eval/independent-round1-frozen.jsonl','eval/independent-round3-frozen.jsonl','eval/context-round4-challenge.jsonl']:
 for line in (root/f).read_text().splitlines():
  r=json.loads(line)
  if 'question' in r:blocked.add(r['question'])
  for m in r.get('messages',[]):
   if m['role']=='user':blocked.add(m['content'])
assert not blocked & {m['content'] for r in train for m in r.get('messages',[]) if m['role']=='user'}
manifest={'audit':audit,'replay_rows':len(replay)*4,'train_rows':len(train),'selection_loss':'final assistant turn only in multi-turn rows','known_limits':'procedural fixed response format; does not establish free-form conversation or science knowledge','hashes':{}}
for file,rows in [('data/train-orthogonal-round5.jsonl',train),('data/val-orthogonal-round5.jsonl',val),('eval/context-round5-frozen.jsonl',test)]:
 p=root/file;p.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows));manifest['hashes'][file]=hashlib.sha256(p.read_bytes()).hexdigest()
(root/'eval/round5-curriculum-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));print(manifest)
