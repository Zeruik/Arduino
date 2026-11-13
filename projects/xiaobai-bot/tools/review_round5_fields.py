"""Post-hoc whole-reply schema diagnostic; primary strict-string metric is retained."""
import re,json,collections
from pathlib import Path
root=Path(__file__).resolve().parents[1]
pattern=re.compile(r'^代号[：:]?\s*([^；;，,。\s]+)\s*[；;，,]\s*色标[：:]?\s*([^；;，,。\s]+)\s*[。.]?$')
report={'primary_metric_unchanged':'strict whole-string equality','supplemental_posthoc':True,'rule':'entire final answer must parse as exactly two ordered fields; optional colons and terminal full-stop, no extra prose; compare BOTH values exactly','not_keyword_scoring':True,'not_knowledge_accuracy':True,'files':{}}
paths=sorted((root/'eval').glob('round5-*-context-*.json'))+sorted((root/'eval').glob('round5-*-counterfactual-int8.json'))
for p in paths:
 d=json.loads(p.read_text());rows=[];by=collections.defaultdict(lambda:[0,0])
 for r in d['rows']:
  ans=r['turns'][-1]['answer'].strip();m=pattern.fullmatch(ans);match=bool(m and m.group(1)==r['code'] and m.group(2)==r['color']);kind=r.get('kind','copy');by[kind][0]+=match;by[kind][1]+=1
  rows.append({'kind':kind,'answer':ans,'parse_valid':bool(m),'both_values_equal':match})
 report['files'][p.name]={'full_structured_matches':sum(x['both_values_equal'] for x in rows),'rows':len(rows),'by_kind':dict(by),'details':rows}
(root/'eval/round5-posthoc-field-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print({k:{x:v[x] for x in ['full_structured_matches','rows']} for k,v in report['files'].items()})
