"""较广泛的短中文教师语料回放；保留验证问题与开发测试隔离。"""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1];p=root/'data'
if not (p/'upstream_teacher.jsonl').exists():raise SystemExit('先运行 tools/prepare_data.py')
raw=[json.loads(x) for x in (p/'upstream_teacher.jsonl').read_text().splitlines()]
rows=[];seen=set();ban=['feng','jiaheng','chatgpt','通义','你是谁','古诗','文言','扮演']
blocked={json.loads(x)['question'] for name in ['test.jsonl','val.jsonl'] for x in (p/name).read_text().splitlines()}
for r in raw:
    if r.get('kind')!='single':continue
    q=r.get('prompt','').strip();ans=r.get('response','').strip()
    if not q or not ans or len(q)>100 or len(ans)>240 or q in blocked or q in seen:continue
    if any(s in (q+ans).lower() for s in ban):continue
    seen.add(q);rows.append({'question':q,'answer':ans,'source':'feng-v4-teacher-Apache-2.0'})
owned=[json.loads(x) for x in (p/'curated.jsonl').read_text().splitlines()]
rows+=owned*25
(p/'train-full-v4.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
print('Full curriculum:',len(rows))
