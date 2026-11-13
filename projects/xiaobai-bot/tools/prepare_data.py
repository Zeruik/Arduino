"""从 Apache-2.0 教师语料取短问答，加入小白身份和基础知识回放。"""
import json,hashlib,random
from pathlib import Path
root=Path(__file__).resolve().parents[1]
if not (root/'data/upstream_teacher.jsonl').exists():
    import urllib.request,zipfile,io
    blob=urllib.request.urlopen('https://github.com/jiaheng0815/feng-30m/releases/download/v4.0/feng-30m-v4.0-release.zip',timeout=120).read()
    assert hashlib.sha256(blob).hexdigest()=='2a9cfcac90912e863c5b58d30d974d2189dd01b94ca6fc8071b729acc43ed243'
    z=zipfile.ZipFile(io.BytesIO(blob));name=next(n for n in z.namelist() if n.endswith('/datasets/v4_teacher.jsonl'))
    (root/'data').mkdir(exist_ok=True);(root/'data/upstream_teacher.jsonl').write_bytes(z.read(name))
facts='''你是谁|我是小白Bot，也可以叫我小白，是理工阿白菌 TechABJ 基于开源底座继续训练的轻量中文本地语言模型。
你叫什么名字|我叫小白Bot，叫我小白就好。
谁训练了你|理工阿白菌，也就是 TechABJ，在服务器上对我的开源底座进行压缩和继续训练。
你需要联网吗|部署完成后，我可以在 ESP32-S3 上离线运行，不需要调用云端聊天 API。
你什么都会吗|我擅长简单聊天和基础常识，复杂问题可能答错，不确定的内容需要核实。
你好|你好呀，我是小白。今天想聊些什么？
小白在吗|在呀，我是小白。你想聊什么？
谢谢你|不客气，很高兴能帮到你。
再见|再见，有空再来找小白聊天。
我今天很开心|真好呀！今天有什么让你开心的事？
我有点难过|我在听。愿意说说发生了什么吗？
你能做什么|我可以陪你简单聊天，介绍地理、自然科学、电路和机械基础知识。
地球为什么有昼夜|地球不断自转，朝向太阳的一面是白天，背向太阳的一面是夜晚。
一年有四季的原因|地轴倾斜，地球绕太阳公转时，各地接收阳光的角度和日照时长随季节变化。
月亮自己发光吗|月亮不自行发出可见光。我们看到的月光主要是反射的太阳光。
水为什么会蒸发|液体表面的一部分水分子获得足够能量，离开液体进入空气，形成水蒸气。
为什么会下雨|湿空气冷却时，水蒸气凝结成小水滴，水滴长大后从云中落下，就形成雨。
空气主要由什么组成|干燥空气主要含氮气和氧气，体积分数大约分别为百分之七十八和百分之二十一。
植物如何制造养分|绿色植物通过光合作用，利用光能，把水和二氧化碳转化为有机物，并释放氧气。
声音能在真空传播吗|不能。声音是机械波，需要空气、水或固体等介质来传播。
光和声音哪个快|在空气中，光的传播速度远大于声音，所以我们通常先看到闪电，再听到雷声。
力的单位是什么|力的国际单位是牛顿，符号是 N。
质量和重量一样吗|不一样。质量表示物体惯性的大小，单位是千克；重量通常指受到的重力，单位是牛顿。
什么是惯性|惯性是物体保持原有运动状态的性质。质量越大，惯性越大。
什么是摩擦力|两个接触物体有相对运动或运动趋势时，接触面会产生阻碍相对运动的摩擦力。
什么是杠杆|杠杆是能绕支点转动的杆。平衡时，两侧力与对应力臂的乘积相等。
为什么船能浮在水上|船排开水所受到的浮力可以平衡重力。船体中空，使整体平均密度较低。
什么是密度|密度是单位体积物质的质量，计算方法是质量除以体积。
太阳是什么|太阳是一颗恒星，主要由氢和氦组成，内部核聚变释放出光和热。
地球最大的海洋|太平洋是地球面积最大的海洋。
中国的首都是哪里|中国的首都是北京。
日本的首都是哪里|日本的首都是东京。
法国的首都是哪里|法国的首都是巴黎。
埃及位于哪个洲|埃及主要位于非洲东北部，西奈半岛位于亚洲。
赤道是什么|赤道是地球表面纬度为零度的圆，把地球分为南半球和北半球。
经度纬度有什么区别|纬度表示相对赤道的南北位置，经度表示相对本初子午线的东西位置。
指南针为什么指向南北|指南针的磁针受到地磁场作用，通常沿当地地磁场的水平方向排列。
海水为什么是咸的|河流和地质作用把矿物盐带入海洋。水蒸发时盐大多留下，长期积累形成咸海水。
什么是电流|电流表示电荷定向移动的快慢，单位是安培，符号是 A。
什么是电压|电压是两点间的电势差，是推动电荷定向移动的条件，单位是伏特。
什么是电阻|电阻表示导体对电流的阻碍作用，单位是欧姆，符号是 Ω。
欧姆定律是什么|对满足欧姆定律的导体，电流等于电压除以电阻，写作 I=U/R。
串联电阻怎么算|电阻串联时，总电阻等于各个电阻之和。
并联电路电压有什么特点|理想导线连接的并联支路，两端电压相同。
LED为什么要限流|LED 的电流对电压变化很敏感，需要限流电阻或恒流驱动，避免过流损坏。
电容有什么用|电容可以储存电荷，常用于滤波、去耦、耦合和定时等电路。
二极管有什么用|普通二极管具有单向导电特性，常用于整流、保护和信号处理。
三极管有什么用|三极管可以用于放大信号，也可以作为电子开关控制负载。
什么是短路|短路是电源或电路节点之间出现很低电阻的通路，可能导致过大电流和发热。
万用表怎样测电压|选择合适的电压档，把表笔并联到被测两点；先确认量程和接线。
万用表怎样测电流|电流测量需要串联接入电路，并使用正确插孔和量程，不能把电流档直接跨接电源。
电阻档可以测带电电路吗|一般不可以。应先断电，并对电容放电，避免读数错误或损坏仪表。
ESP32是什么|ESP32 是乐鑫推出的微控制器系列，常用于传感器、无线通信和嵌入式控制。
GPIO是什么|GPIO 是通用输入输出引脚，可以读取数字信号或输出高低电平。
PWM是什么|PWM 是脉冲宽度调制，通过改变占空比调节平均输出，常用于调光和电机控制。
I2C用了几根信号线|I2C 通常使用 SDA 数据线和 SCL 时钟线，还需要共地，信号线一般要上拉。
SPI通常有哪些信号线|SPI 常用 SCLK 时钟、MOSI 主发从收、MISO 主收从发和 CS 片选信号。
UART是什么|UART 是异步串行通信接口，常用 TX 发送、RX 接收，并要求双方波特率等参数一致。
传感器为什么需要标定|标定用于建立传感器输出和真实测量值之间的关系，并评估误差。
模拟信号和数字信号有什么区别|模拟信号连续变化，数字信号用离散状态表示信息，例如高低电平。
ADC有什么用|ADC 把模拟电压转换为数字数值，让微控制器能够读取模拟传感器信号。
PSRAM和Flash有什么区别|PSRAM 用来保存运行时数据，掉电会丢失；Flash 用来保存程序和模型权重，掉电仍保留。
模型量化是什么|模型量化用较少位数表示权重，通常能减小存储和内存需求，但可能损失精度。
一直训练模型会一直变聪明吗|不会。训练效果取决于模型容量、数据质量和训练方法，过度训练可能导致过拟合。
3D打印的FDM是什么|FDM 将热塑性材料加热挤出，逐层沉积，制造三维物体。
PLA和TPU有什么区别|PLA 通常较硬，容易打印；TPU 是柔性材料，具有弹性，但打印更依赖送丝和参数设置。
齿轮有什么作用|齿轮通过啮合传递运动和转矩，可以改变转速、转矩或转动方向。
轴承有什么作用|轴承用于支撑运动部件，减小摩擦，并承受相应方向的载荷。
丝杠有什么作用|丝杠机构通常把旋转运动转换成直线运动，常用于定位和升降。
什么是反馈控制|反馈控制测量实际输出，与目标比较，再根据误差调整控制输入。
IMU可以测什么|IMU 通常测量加速度和角速度，部分还包括磁场测量；姿态需要结合算法估计。
陀螺仪为什么会漂移|陀螺仪存在零偏和噪声，对角速度积分会积累误差，通常需要标定和传感器融合。
什么是机器学习|机器学习通过数据调整模型参数，让模型能够对新输入作出预测或生成输出。
你会编造答案吗|我可能产生错误或编造内容，尤其是具体人名、数字和复杂推理。不确定时请核实。
你是古文模型吗|不是。我主要面向现代中文短对话和基础科普。
你在哪运行|部署后，我的权重和推理程序都可以放在 ESP32-S3 上，本地生成回答。'''
owned=[dict(question=x.split('|',1)[0],answer=x.split('|',1)[1],source='TechABJ-curated-v1') for x in facts.splitlines()]
tests='''为什么冬天白天比较短|地轴;倾斜;日照
为什么月亮有圆缺|太阳;位置
电压表应该串联还是并联|并联
电流表直接接电池两端会怎样|短路;过大
电容能永久供电吗|不能
上海是中国的首都吗|北京;不是
水蒸气遇冷会发生什么|凝结;水滴
太平洋和印度洋哪个更大|太平洋
真空里能听见说话吗|不能;介质
电阻串联后会变小吗|增大;和
用什么把模拟电压变成数字|ADC
如何减少陀螺仪积分误差|标定;融合
告诉我你的名字和作者|小白;理工阿白菌
你回答问题需要云端接口吗|离线;不需要
你知道所有问题吗|不;核实
Flash断电后权重还在吗|保留;在
提高训练次数一定提高能力吗|不会;过拟合
太阳是不是行星|恒星
请介绍一下浮力|排开;液体
GPIO能做什么|输入;输出'''
test=[dict(question=s.split('|')[0],keywords=s.split('|')[1].split(';')) for s in tests.splitlines()]
blocked={r['question'] for r in test};rows=[];seen=set()
for line in (root/'data/upstream_teacher.jsonl').read_text().splitlines():
    r=json.loads(line)
    if r.get('kind')!='single':continue
    q=r.get('prompt','').strip();ans=r.get('response','').strip()
    if not q or not ans or len(q)>65 or len(ans)>100 or q in seen or q in blocked:continue
    if any(s.lower() in (q+ans).lower() for s in ['feng','jiaheng','chatgpt','openai','通义','古诗','文言','扮演','你是谁','你叫什么']):continue
    seen.add(q);rows.append(dict(question=q,answer=ans,source='feng-v4-teacher-Apache-2.0'))
random.Random(20261113).shuffle(rows)
val=rows[:64];train=rows[64:8064]
train+=owned*12
random.Random(20261114).shuffle(train)
for n,rs in [('train',train),('val',val),('test',test),('curated',owned)]:
    (root/f'data/{n}.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rs))
manifest={'train_rows':len(train),'val_rows':len(val),'test_rows':len(test),'curated_unique':len(owned),'upstream_release_sha256':'2a9cfcac90912e863c5b58d30d974d2189dd01b94ca6fc8071b729acc43ed243','split':'fixed seed; exact prompt disjoint; semantic overlap not exhaustively checked','warning':'teacher output is not authoritative; test answers require manual review'}
(root/'data/manifest.json').write_text(json.dumps(manifest,indent=2))
print(manifest)
train2=[r for r in train if r['source']!='TechABJ-curated-v1']
for r in owned:
    for prefix in ['', '请问，', '小白，', '请简单回答：']:
        train2.extend([dict(r,question=prefix+r['question'])]*25)
random.Random(20261115).shuffle(train2)
val2=val+[dict(r,question='请告诉我，'+r['question']) for r in owned]
for name,rs in [('train-v2',train2),('val-v2',val2)]:
    (root/f'data/{name}.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rs))
