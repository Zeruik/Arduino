# 持续研发交接

用户明确要求：质量优先，可以持续数天；不能把能生成字的模型当作已成功。
目标：小白Bot（简称小白），理工阿白菌 / TechABJ；ESP32-S3 N16R8 与 N32R16，全离线、无 SD、串口与热点网页聊天，现代中文、约 4000 常用汉字可编码，尽可能广泛的日常和基础科普。

## 已做与未做

- 调研 DaveBben、slvDev 与 feng-30m，选择后者作为开源迁移底座；不是从零预训练。
- 本地两种规格都已完成 2000 步 SFT、6000 步加权 SFT、2000 步权重量化感知训练。
- 主权重 FP32 与板端 Q4 已导出，C / 反量化 HF logits 对照通过，最大误差约 1.4e-5。
- 4000 汉字 HF/C tokenizer token ID 与往返一致，不能据此声称掌握所有知识。
- Q2 KV 导致语言明显退化，最终工程默认改为 INT8 KV。N16 ctx512，KV 5203968 B；N32 ctx1024，KV 10407936 B。
- 两种 Arduino 固件均在本地交叉编译成功。N16 app 974240 B、N32 app 974832 B；布局检查通过。
- 实际 HTTP 服务提交、真实模型回答、重置通过；受 sandbox Unix socket 限制，Chromium 视觉验收未完成。
- GitHub Windows job 构建了真实 Inno Setup exe，但未做安装器交互实测。
- **知识与泛化未通过**：换问法时仍把电压表接法说错、GPIO 等问题答偏，N32 某些问法还沿用旧身份。v0.1 包只作研发候选，不能宣称成功。
- **没有实体板日志**，不能宣称已验证在真板冷启动/断网运行，更不能套用上游速度。

## 存储和代码位置

GitHub：`Zeruik/Arduino` 的 `xiaobai-bot` 分支，代码目录 `projects/xiaobai-bot`。
不修改 master。主机工作目录可能过期，优先恢复 GitHub 与保存的训练包。
本轮工作目录 `/workspace/scratch/4cf03e477896/xiaobai-bot`。
原始 GitHub Actions run `43377448937`，Windows artifact `14014748923`；该 run 使用最初 Q2 配置，产物不得当成最终 INT8 验收。

## 进行中的 v4

`models/n16-full-v4` 和 `models/n32-full-v4`：从各自 v3 FP32 主权重出发，全部 11 个 Transformer 层做 Q4-aware 训练，目标 16000 步、单段最多 180 分钟；
学习率 3e-6、seq384、threads4，每 200 步保存，使用扩大的 `train-full-v4.jsonl`，验证 `val-v2.jsonl`。
启动命令见下。进程只是当前云端会话进程；未来运行必须检查真实进度，不假定它一直活着。

```bash
python tools/prepare_data.py
python tools/prepare_full_data.py
python tools/train.py --model models/n16-qat-v3/final --out models/n16-full-v4 --data data/train-full-v4.jsonl --val data/val-v2.jsonl --layers 11 --seq 384 --steps 16000 --minutes 180 --threads 4 --lr 0.000003 --save-every 200 --qat --resume
```

N32 同样替换 n16 为 n32。模型与 tokenizer、学习率、词表等配置不能在 resume 时变更。
新阶段使用新目录，不覆盖已完成版本。v3 FP32 zip 可恢复成 `models/n16-qat-v3/final` 等。

## 下一步

1. 获取当前本地/CI 原始日志与产物。能恢复时续训，不能恢复时从持久化 v3 主权重开始新版本，明确缺失步数。
2. 修复泛化的核心是更多、经过核实、表达多样的数据和正确容量分配，不是盲目加 epoch。
3. 单独冻结新的独立测试集，分日常、身份、地理、物理、化学、生物、电路、机械、嵌入式、不确定性；每类至少 10 题。现有 20 题已用于开发，不能再称无偏盲测。
4. 保留每道题原始回答，人工检查事实。关键词只能当提示，不输出为准确率。不要从独立测试生成训练答案。
5. 继续做浮点→Q4→INT8 KV 对比，数值对拍与语言质量均要过；单点 fp32 KV parity 不能替代 INT8 功能验收。
6. 每次稳定候选都打包 FP32、Q4+固件、Arduino 源码引用与校验清单，更新中英简介、许可和真实评测；保存检查点。
7. 最后再向用户要实际开发板型号照片/串口日志或已授权连接的硬件。这是实体板验收必需条件，不能用模拟代替。

## 工程注意

- PIO 平台固定 55.03.37 / Arduino3.3.7 / GCC14.2。临时构建盘从 `/home/agent` tmpfs 迁到 workspace，避免工具链安装双份时爆盘。
- 临时构建环境证书与 uv 依赖安装曾失败。未关闭 TLS；本地用系统 CA，并安装了已列明的 penv 依赖。
- Windows 安装器仅打包、编译通过；后续还要测安装目录、串口枚举、包损坏拒绝、错误型号拒绝和退出状态。
- N32 Flash 默认按 OPI/OPI（WROOM-2 N32R16V），用户实际模块不同时要调整。
- 源码/模型/教师资料保留 Apache-2.0 和上游来源，不把底座开发者工作冒充 TechABJ 原创。
