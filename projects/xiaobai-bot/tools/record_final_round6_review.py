"""Record an already completed assistant review of the sealed raw answers.

Labels are explicitly authored case IDs, NOT keyword matching or an automatic
factual grader. This is a post-hoc single-assistant review, not human/independent
adjudication. Do not reuse these annotations to grade new generations.
"""
import collections
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
criteria = [
    ['吸气降低口腔/吸管内压力，外部大气压推动液体上升','湿巾中的水传热及蒸发带走热量，条件会影响凉感','通常不会持续降低整个封闭房间温度；电机耗电最终发热','温度下降使蒸发减弱；可见白汽为凝结小液滴，不等于气态水可见','是，气味分子扩散到鼻部','空气/气体','不是，是熔化','减慢散热保温，不是自行产热','加入水带来质量','列出任务便于厘清优先级、估时和安排'],
    ['自称小白Bot/小白，项目负责人理工阿白菌/TechABJ，区分底座贡献','同一项目负责人的中文网名和英文署名','小白Bot/小白','部署后推理在板上，不需云端聊天API','需要区分并注明上游开源底座和后续适配训练','本方案不需外置SD，权重在板载Flash','不能保证全部可靠，应核实不确定内容','ESP32-S3，两种Flash/PSRAM配置','主要面向现代中文','不可以，仅电脑检查不能替代真实板端证据'],
    ['赤道','一年','不是，中国在亚洲、法国本土在欧洲；海外领土不使二者同洲','地中海','地表海洋面积更大','大西洋','本初子午线/零度经线','通常更低','不是，太平洋最大','受光面白天、背光面夜晚'],
    ['改变，速度是矢量','位移为零，该推力机械功为零','2千克物体惯性更大；同条件质量越大惯性越大','重力势能增大','不是，温度与质量不同物理量','需要传播介质，真空不能传播声音','折射','100厘米','焦耳','弹性形变产生恢复力并储存弹性势能'],
    ['不同，O2只有氧；H2O含氢和氧','可以，温和蒸发可留下糖；过热分解另论','碳和氧，两种元素','通常有，锈蚀属于化学变化','正电','常规过滤不能去除溶解盐离子','不是，单纯撕纸为物理变化','不会，物态变化不改变元素种类','质子数/原子序数','不能，O2与CO2不同'],
    ['光合作用吸收光能','动物呼吸通常获取氧气','主要经根吸水','不一样，真菌异养，不作通常绿色植物式光合作用','是，传粉有助有性繁殖','是，会生长','推动/泵送血液','会相互影响','错误前提：反光不需叶片；月球反射太阳光','通常需要水与二氧化碳进行光合作用'],
    ['加倍，I=U/R','欧姆','相同','不合适，应限流避免损坏','理想断开电流为零','不能，储能有限','增大，同R时P=I平方R','必须注意极性和连接','单向导电','不是，这是短路，可能过流损坏'],
    ['不能凭减速提高功率；理想守恒、实际有损耗','力相同且力臂增大，力矩增大','是，用于支撑/引导并承载，常减摩擦','可以，把旋转转成直线运动','通常是，同变形下刚度越大需力越大','不能，刚度与强度/疲劳/断裂不同','通常是，TPU常比PLA柔韧；受牌号和结构影响','不是，通常逐层挤出堆积','应考虑接触摩擦','可以传递运动和转矩'],
    ['普通RAM数据易失，断电通常丢失','不同，Flash非易失保存固件，RAM临时工作','ADC/模数转换','可以，合理上下拉和电平条件','TX发送','SDA数据、SCL时钟','是，CS为片选','不是，频率为周期速率，占空比为高电平时间比例','不证明，校准需实物参考和测量','不能保证，未持久保存的历史可能丢失'],
    ['不能从缺失证据知道眼前准确阻值，应读取标识或测量','不能保证最新新闻，离线知识有限','不编造，比较证据并说明冲突/不确定','不能精确定位未见源码的错误行，需源码和日志','应明确不确定并说明核实/补充证据','不能保证，需重复和误差分析','不能确认，需真实冷启动/运行证据','不等于所有新问法正确','先测量或索要尺寸，不编数字','需要与可靠资料交叉核实'],
]

def ids(values):
    return {'f6-'+v for v in values.split()}

# These labels were assigned after reading every full INT8 answer.
labels = {
    'n16-round3': {
        'C': ids('02-07 02-09 03-09 04-05 06-01 06-10 07-09 08-10 09-05 09-06 10-02 10-05 10-10'),
        'P': ids('01-09 02-01 03-05 04-03 05-07 07-02 07-03 07-08 08-09 09-08 10-01 10-03 10-04'),
    },
    'n32-round3': {
        'C': ids('02-07 06-01 06-10 07-02 07-09 08-03 08-09 08-10 09-05 10-07'),
        'P': ids('02-01 02-09 03-01 06-06 07-03 09-06 09-07 09-08 09-09 10-03 10-04'),
    },
    'n16-round5': {
        'C': ids('02-07 02-09 03-09 04-05 06-01 06-10 07-09 08-10 09-06 10-10'),
        'P': ids('01-09 02-01 03-05 04-03 07-02 07-03 09-08 09-10 10-01 10-03 10-04 10-05 10-07'),
    },
    'n32-round5': {
        'C': ids('02-07 06-01 06-10 07-04 07-09 07-10 08-03 08-09 08-10 09-05 09-06'),
        'P': ids('01-09 02-01 07-02 07-03 07-06 09-07 09-08 09-09 10-03 10-04 10-08'),
    },
}
# All 38 changed FP32-KV answers were separately read. Unlisted changed answers
# retain the same grade; exact-identical answers inherit their INT8 annotation.
fp32_changes = {
    'n16-round3': {'f6-01-10':'P', 'f6-03-05':'W'},
    'n16-round5': {'f6-08-09':'P', 'f6-09-05':'C'},
    'n32-round3': {},
    'n32-round5': {'f6-07-04':'W'},
}
expected_hashes = {
    'n16-round3':'dffaa2f16813560eca47104702379416ffaa23c2f85010dd8d1a5cd44764fd21',
    'n32-round3':'cdde403054f9cfcc8938b0c4fc22d759c62df07a1e0d3a2451462a2adf847221',
    'n16-round5':'eb99c32480f1e5a0247fe65587238d0d658dee7b09829738edfd9aee378378bd',
    'n32-round5':'ff58d5aebf608d9ca4a132272cbd83cebea1457f5544c1928730019f8636d24f',
}
manifest=json.loads((ROOT/'eval/final-round6-manifest.json').read_text())
output = {
    'reviewer':'single assistant semantic review; NOT independent human adjudication',
    'rubric_timing':'post-hoc after seeing raw answers; not a preregistered blinded benchmark',
    'C':'answers the actual question sufficiently, no material false claim; minor fluency fragments tolerated',
    'P':'relevant true fragment or warranted caution, but missing requested relation/field/conclusion; not counted complete',
    'W':'false, unrelated, incoherent, unsupported refusal, or does not answer; a correct keyword does not rescue a materially false explanation',
    'accuracy_claim':False,
    'training_use_forbidden':True,
    'groups':{},
}
for group, annotation in labels.items():
    assert not annotation['C'] & annotation['P']
    base = json.loads((ROOT/f'eval/round6-{group}-int8.json').read_text())
    lookup = {r['id']:r for r in base['rows']}
    assert annotation['C'] | annotation['P'] <= lookup.keys()
    for kv in ['int8','fp32kv']:
        path=ROOT/f'eval/round6-{group}-{kv}.json'
        result=json.loads(path.read_text())
        assert result['model_sha256']==expected_hashes[group]
        assert result['suite_sha256']==manifest['sha256']
        reviewed=[]
        for row in result['rows']:
            i,j=map(int,row['id'].split('-')[1:])
            label='C' if row['id'] in annotation['C'] else 'P' if row['id'] in annotation['P'] else 'W'
            changed = row['answer'] != lookup[row['id']]['answer']
            if kv=='fp32kv' and row['id'] in fp32_changes[group]:
                assert changed
                label=fp32_changes[group][row['id']]
            reviewed.append({
                'id':row['id'],'category':row['category'],'question':row['question'],
                'answer':row['answer'],'answer_sha256':hashlib.sha256(row['answer'].encode()).hexdigest(),
                'minimum_semantic_requirement':criteria[i-1][j-1],'review_label':label,
                'basis':'full response semantic review' if kv=='int8' or changed else 'identical full answer to reviewed INT8 response',
            })
        output['groups'][group+'-'+kv]={
            'raw_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'counts':dict(collections.Counter(r['review_label'] for r in reviewed)),
            'by_category':{c:dict(collections.Counter(r['review_label'] for r in reviewed if r['category']==c)) for c in dict.fromkeys(r['category'] for r in reviewed)},
            'rows':reviewed,
        }
(ROOT/'eval/round6-semantic-review.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v['counts'] for k,v in output['groups'].items()},ensure_ascii=False))
