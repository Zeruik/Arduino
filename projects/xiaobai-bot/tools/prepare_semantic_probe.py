"""Paired wording ablation using answers already authored BEFORE independent testing."""
import json,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1]
owned=[json.loads(x) for x in (root/'data/curated.jsonl').read_text().splitlines()]
lookup={r['question']:r for r in owned}
# Canonical question, two semantic rewrites, held-out rewrite. Answers are copied,
# never inferred from a development/independent model response or test key.
rows='''你是谁|能介绍一下你这个助手吗|别人应该怎么称呼这个聊天助手|你的身份是什么，简单介绍一下
谁训练了你|这个小白助手由谁继续训练|你的后续压缩训练是谁负责的|请说明小白的开发署名
你需要联网吗|没有互联网也能和你聊天吗|部署好后是否还依赖云端聊天服务|这个助手断网后可不可以用
你什么都会吗|你的知识有没有局限|复杂的问题你有可能答错吗|应不应该把你的所有回答都当成正确的
地球为什么有昼夜|一天里天亮天黑怎样形成|地球自转和白天黑夜有什么联系|为什么同一地方会交替经历白天和夜晚
月亮自己发光吗|晚上看到的月光从哪里来|月球可见的亮光是它自己产生的吗|月面为什么会在夜空中显得明亮
空气主要由什么组成|干燥空气中最多的两种气体是什么|空气中氮气和氧气大致占多少|通常干空气的主要成分有哪些
植物如何制造养分|绿色植物靠什么过程制造有机物|植物如何利用光和水制造养料|绿色植物通过哪种过程把光能用于合成养分
力的单位是什么|国际单位制用什么单位表示力|测力计读数一般用什么单位|牛顿是用来计量哪种物理量的
质量和重量一样吗|物体的质量与重力有什么差别|千克和牛顿表示的是同一个量吗|质量能不能直接当成物体受到的重力
什么是惯性|为什么物体倾向于保持原来的运动状态|物体质量大时惯性会怎样|惯性描述了物体哪一种性质
什么是摩擦力|接触面为何会阻碍相对滑动|两个物体有相对运动趋势时会出现什么力|请解释接触面上的摩擦现象
什么是杠杆|绕一个支点转动的杆是什么简单机械|杠杆平衡时力和力臂有什么关系|杠杆的支点和力臂如何影响平衡
什么是密度|单位体积的质量叫什么|知道质量与体积后怎样求密度|密度表示材料的什么特征
什么是电流|电荷定向移动的快慢用什么量描述|电流用哪种单位来计量|安培对应哪一种电学量
什么是电压|电路中两点的电势差叫什么|电压的单位是什么|伏特表示的是什么物理量
什么是电阻|用什么量描述导体对电流的阻碍|欧姆是计量什么的单位|导体的电阻描述什么性质
二极管有什么用|二极管一般利用哪种导电特点|为什么二极管可用于整流|普通二极管在电路里能起什么作用
三极管有什么用|三极管能否用作电子开关|放大信号时可以使用什么半导体器件|电子电路中三极管常承担哪些任务
PWM是什么|如何通过脉冲占空比控制平均输出|脉冲宽度调制有什么常见用途|PWM调光主要改变脉冲的哪个参数
UART是什么|异步串口中的TX和RX分别做什么|串口双方需要约定哪些通信参数|UART怎样发送和接收数据
传感器为什么需要标定|怎样把传感器读数与真实量建立关系|校准传感器的目的是什么|标定在传感器测量中起什么作用
齿轮有什么作用|啮合的齿轮可以传递什么|用齿轮机构可以调整哪些运动量|机械系统为什么使用齿轮传动
什么是反馈控制|控制器如何利用实际输出纠正误差|把输出与目标比较再调整属于什么控制|闭环控制为什么要测量实际输出'''
train_fixed=[];train_diverse=[];val=[];families=[]
for i,line in enumerate(rows.splitlines()):
 qs=line.split('|');base=lookup[qs[0]]
 for j,q in enumerate(qs[:3]):
  train_diverse.append(dict(base,question=q,concept=i,provenance_question=qs[0]))
  train_fixed.append(dict(base,concept=i,provenance_question=qs[0]))
 val.append(dict(base,question=qs[3],concept=i,provenance_question=qs[0],role='held-out wording of trained fact; not independent facts'))
 families.append({'concept':i,'canonical':qs[0],'train_questions':qs[:3],'val_question':qs[3]})
# Same rehearsal, same sample count in both branches; exclude selected canonicals
# to keep the exact same per-concept weight.
selected={f['canonical'] for f in families}
rehearsal=[r for r in owned if r['question'] not in selected]
train_fixed+=rehearsal;train_diverse+=rehearsal
blocked=set()
for f in ['data/test.jsonl','data/val.jsonl','data/val-v2.jsonl','eval/independent-round1-frozen.jsonl']:
 blocked.update(json.loads(x)['question'] for x in (root/f).read_text().splitlines())
assert not blocked & {r['question'] for r in train_diverse+val}
assert not {r['question'] for r in train_diverse} & {r['question'] for r in val}
manifest={'facts':len(families),'train_rows_each':len(train_fixed),'val_rows':len(val),'source_answers_sha256':hashlib.sha256((root/'data/curated.jsonl').read_bytes()).hexdigest(),'answer_origin':'existing curated-v1, predates round1 independent test; unchanged answers','independent_accuracy':False,'families':families,'files':{}}
for name,data in [('train-fixed-round3',train_fixed),('train-semantic-round3',train_diverse),('val-semantic-round3',val)]:
 p=root/f'data/{name}.jsonl';p.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in data));manifest['files'][name]=hashlib.sha256(p.read_bytes()).hexdigest()
(root/'eval/round3-curriculum-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print({k:v for k,v in manifest.items() if k not in ['families','files']})
