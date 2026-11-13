# 六轮结束时的架构与训练路线筛选（2026-11-13）

结论：保留已实现的11层、hidden448、7头MHA、共享embedding、Q4权重/INT8 KV候选作为工程研究基线。本轮没有足以替换基线的小规模质量证据，没有启动从零训练。以下预算是计算或源码推断，不是实体板速度/峰值内存测量。

## 当前预算

| 项目 | N16R8 | N32R16 |
|---|---:|---:|
| 标称Flash/PSRAM | 16/8 MiB | 32/16 MiB |
| 参数 | 25,759,168 | 29,429,184 |
| 实际Q4文件 | 13,710,208 B | 15,659,904 B |
| tokenizer | 184,996 B | 423,154 B |
| 当前模型分区剩余 | 445,568 B | 3,200 B |
| ctx / INT8 KV分配 | 512 / 5,203,968 B | 1024 / 10,407,936 B |
| 同ctx主机FP32 KV | 20,185,088 B | 40,370,176 B |

KV不是全部PSRAM：还需激活、tokenizer索引、Wi-Fi/HTTP、任务栈、分配开销。权重通过Flash映射读取；Flash分区剩余也不等于可用虚拟映射空间。不能用上述静态布局推出真板内存峰值通过。乐鑫说明ESP32-S3外部PSRAM使用有限的虚拟地址空间，最终要核对实际SDK、模块、电气模式和mmap/heap日志：[官方外部RAM文档](https://docs.espressif.com/projects/esp-idf/en/v5.5/esp32s3/api-guides/external-ram.html)。

## 各路线结论

| 路线 | 原论文/作者开源实现 | 迁移、算子及预算判断 | 本轮决策 |
|---|---|---|---|
| 深窄Transformer、跨层共享 | [MobileLLM](https://arxiv.org/abs/2402.14905)、[作者仓库](https://github.com/facebookresearch/MobileLLM) | 当前已经深窄并共享输入/输出embedding。论文125M/350M证据不能外推到26M；125M即使全部理想4bit也需62.5 MB，超过32MiB Flash。重复块会改变计算与能力，不能直接把独立层平均当等价转换。当前作者README许可为FAIR NC，不能无条件当Apache中文迁移底座。 | 研究结构，不引入大权重，不重开预训练 |
| GQA/MQA | [GQA](https://arxiv.org/abs/2305.13245)；本工程tools/probe_mqa.py及第1轮日志 | 当前7个query头只有7/1个KV头可整除分组。MQA理论KV主体降至1/7；512时主体从5,046,272降至720,896 B，不含scale等。须转换投影并训练恢复，修改C/导出格式并对拍。第1轮同200步探针MQA验证loss5.732，MHA1.736，不能把节省内存当质量通过。 | 未替换；短训失败不证明永远不可行 |
| embedding共享 | MobileLLM；当前config.json tie_word_embeddings=true | 已在基线中使用，不能重复宣称为新增收益。N16词表裁剪与N32不同，不能直接互换token ID/权重。 | 保持 |
| 蒸馏、可信数据与表达多样性 | [Distilling Step-by-Step](https://arxiv.org/abs/2305.02301)、[作者实现](https://github.com/google-research/distilling-step-by-step) | 作者实现是标签/理由的多任务训练；本工程没有教师logits/KL或该多任务损失。小QA人工编写/回放SFT不能冒称实现logits蒸馏。第3轮同事实多问法有验证改善，但最终新100题仍失败。未经核实的历史教师输出不能自动变成可靠知识。 | 保留有证据的局部改善，不称综合成功 |
| 回放与遗忘控制 | [Replaying pre-training data improves fine-tuning，2026-03-05](https://arxiv.org/abs/2603.04964)、[作者固定版本实现](https://github.com/marin-community/marin/blob/bfbc4492aefe50291829e2ceebf1b3b94186da9c/experiments/two_stage/continual_pretraining.py) | 原证据涉及150M/8B和真正通用预训练数据。第5轮496行旧QA回放不是同样实验；没有比例/预训练数据对照，不能将保留或退化归因于回放单因素。 | 不再加epoch，封存失败证据 |
| 混合精度、PTQ与QAT | [GPTQ](https://arxiv.org/abs/2210.17323)；本工程export_model.py/train.py | 当前是自有分块Q4导出与Q4-aware训练，不是GPTQ复现。较敏感矩阵升精度必须重算分区/映射/算子；N32当前模型分区仅余3200 B。第6轮INT8/FP32 KV同答362/400，换FP32 KV仍大面积错误，不能只怪KV；这不等于证明Q4主权重无损。 | Q4+INT8维持；Q2因退化拒绝；FP32主权重保存，最终100问未全跑FP32主权重 |
| RWKV及常数状态 | [RWKV-7](https://arxiv.org/abs/2503.14456)、[NumPy原始推理](https://github.com/BlinkDL/RWKV-LM/blob/main/RWKV-v7/rwkv_v7_numpy.py)、[当前RWKV-8设计笔记](https://github.com/BlinkDL/RWKV-LM/blob/main/RWKV-8.md) | NumPy实现展示归一化、指数/门控、矩阵状态的衰减/低秩更新；C可研究实现但不是当前Transformer权重的无损换层。论文最小0.19B全部理想4bit仍95 MB，远超本板。常数状态不意味着无矩阵运算/零状态开销；最新设计笔记不是可直接移植的已验收小中文权重。 | 不更换；未找到并验证预算内的可用替代权重 |
| 状态空间/Mamba | [Mamba](https://arxiv.org/abs/2312.00752)、[作者单步源码](https://github.com/state-spaces/mamba/blob/main/mamba_ssm/modules/mamba_simple.py)、[Mamba-3，2026-03-16](https://arxiv.org/abs/2603.15569) | 单步需卷积状态、指数/softplus、选择性状态更新和投影；可写标量C但官方加速不是ESP32算子。Mamba-3增加复状态/MIMO，1.5B证据不能外推到30M；C实现和中文权重迁移尚缺，不因其状态跟踪论文表现就替换。 | 仅研究，未新训/未部署 |
| 无矩阵乘/三值 | [Scalable MatMul-free Language Modeling，v7](https://arxiv.org/abs/2406.02528)、[作者实现](https://github.com/ridgerchu/matmulfreellm) | 实现依赖PyTorch/Triton，公开表最小370M；即使所有参数用理想三值编码约73.3 MB，仍超32MiB，实际还需高精度部分/scale。三值加减核和循环状态需专门C实现，不能把GPU或神经形态多芯片数据当ESP32速度。 | 不引入大模型，不从零训练 |

以上是对当前已读论文与开源实现的筛选，不声称穷尽所有公开小模型。小规模验证只支持具体设置中的观察；没有发现足以保证“纯板端通用中文综合知识可靠”的路线。所有旧候选保留，后续研究如重新授权应使用新训练集/新独立验收，不用最终100题的答案训练。

## 原始事实核验

最终语义评阅由单一助手完成，事后制定最低要求，未独立人工复核；不是认证准确率。重点抽核的原始教材/厂商资料：

- [OpenStax功与能量](https://openstax.org/books/college-physics-2e/pages/7-section-summary)：机械功取决于位移，能量单位焦耳。
- [OpenStax力矩](https://openstax.org/books/college-physics-2e/pages/9-section-summary)：固定垂直力时，增大力臂增大力矩。
- [OpenStax原子与元素](https://openstax.org/books/chemistry-2e/pages/2-summary)：质子正电，原子序数决定元素种类。
- [OpenStax光合作用](https://openstax.org/books/biology-2e/pages/8-1-overview-of-photosynthesis)：植物/藻类/部分细菌光合；动物、真菌为异养，不能套用光合模板。
- [NOAA海洋](https://www.noaa.gov/jetstream/ocean)：地表海洋覆盖占多数，太平洋最大。
- [乐鑫ADC](https://docs.espressif.com/projects/esp-idf/en/v5.5/esp32s3/api-reference/peripherals/adc_oneshot.html)、[UART](https://docs.espressif.com/projects/esp-idf/en/v5.5/esp32s3/api-reference/peripherals/uart.html)、[LEDC](https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/api-reference/peripherals/ledc.html)：区分模拟转换、串口发送接收及PWM频率/占空比。

这些核验只用于判断原回答，未写回训练。全部100问最低语义要求、800条回答与评阅来源hash在eval/round6-semantic-review.json；原样保留错误、遗漏和不确定表述。
