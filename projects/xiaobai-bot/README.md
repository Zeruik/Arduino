# 小白Bot / Xiaobai Bot

**ESP32-S3 中文本地极轻量语言模型 / Ultra-lightweight offline Chinese language model for ESP32-S3**

作者 / Author：**理工阿白菌 / TechABJ**。
小白以现代中文短对话和基础科普为目标，涉及日常、地理、自然科学、电路、机械与嵌入式。
权重保存在板载 Flash，推理在 ESP32-S3 本机完成，不需要 SD 卡或云端聊天 API。

Xiaobai targets short modern-Chinese conversations and elementary science, geography,
electronics and engineering. Model weights stay in onboard Flash; generation runs
on the ESP32-S3 itself, without an SD card or cloud chat API.

**状态 / Status（2026-11-13）：六轮研究结束并暂停。主机工程检查与Windows构建完成，综合知识、身份和通用多轮未通过，实体板与Windows交互仍未验收。**
**Six research rounds concluded and paused. Host engineering checks and Windows builds completed; general knowledge, consistent identity and conversation remain unaccepted. Physical-board and Windows interactive validation are pending.**

[最终对比与未通过项](docs/FINAL_DELIVERY_ROUND6.md) · [模型、源码、安装器及证据下载](docs/FINAL_DOWNLOADS_ROUND6.md) · [原始回答](docs/FINAL_RAW_ANSWERS_ROUND6.md) · [架构筛选](docs/FINAL_RESEARCH_ROUND6.md)

不能把“能运行”“4000 汉字可编码”或“数值一致”理解成通用知识可靠。
Running successfully, encoding 4000 Hanzi and numerical parity do not establish reliable general knowledge.

| 配置 / Profile | N16R8 | N32R16 |
|---|---:|---:|
| Flash / PSRAM | 16 / 8 MiB | 32 / 16 MiB |
| 参数 / Parameters | 25,759,168 | 29,429,184 |
| BPE vocabulary | 8192 | 16384 |
| Context configuration | 512 tokens | 1024 tokens |
| Weights / KV cache | Q4 / INT8 | Q4 / INT8 |

两种型号有不同的词表、上下文、分区与 Flash/PSRAM 电气配置；不仅是量化精度不同。
Profiles differ in vocabulary, context, partitions and memory configuration, rather than quantization alone.

## 来源 / Provenance

本项目**基于 [feng-30m](https://github.com/jiaheng0815/feng-30m) 开源中文底座继续训练**，
不是 TechABJ 从零预训练的底座。保留上游 Apache-2.0 许可及来源声明。
小白身份、N16 压缩适配、训练增补、网页与安装工具是本项目新增工作。

This project continues training the open-source feng-30m Chinese base. It does not
claim original pretraining by TechABJ. Upstream Apache-2.0 licensing and attribution
are preserved. See [NOTICE](NOTICE) and [research notes](docs/RESEARCH.md).

## 复现 / Reproduce

Python 3.12，GCC 14+，Arduino-ESP32 3.3.7；无 GPU 时可以进行 CPU 继续训练。
Python 3.12, GCC 14+, Arduino-ESP32 3.3.7. CPU fine-tuning is supported.

```bash
pip install torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
python tools/train_pipeline.py --profile n16 --steps 6000
python tools/train_pipeline.py --profile n32 --steps 6000
```

流水线下载固定版本与哈希的数据，训练、导出、验证、编译并输出候选包。
训练过程记录检查点和逐步日志；重复执行需要显式续训或新版本目录。
The pipeline downloads pinned inputs, trains, exports, checks, compiles and packages candidates.
It keeps checkpoints and logs. Additional iterations must resume explicitly or use new output directories.

## 网页验证 / Web verification

```bash
python tools/build_host.py
python tools/serve.py --model models/n16-q4-ci --port 8765
```

打开 `http://127.0.0.1:8765`。这里运行真实 Q4 C 引擎，页面标注“电脑验证”。
板端固件提供同一网页，热点 `XiaobaiBot`，密码 `xiaobai2026`，访问 `http://192.168.4.1`。
USB 串口为 115200，输入现代中文并回车；`/reset` 清空上下文。

The host page runs the actual Q4 C engine and labels itself as host verification.
Firmware serves the same page over its local Wi-Fi access point. Serial chat uses
115200 baud; `/reset` clears context. No CDN or chat API is used by the page.

## Arduino 与 Windows / Arduino and Windows

Arduino sketch: `firmware/XiaobaiBot/XiaobaiBot.ino`。
建议用附带 PlatformIO 配置编译同一 Arduino 程序；其 C23 编译参数和型号分区表已经显式配置。
直接 Arduino IDE 编译需要手工设置 C23 参数、复制网页头文件与对应分区表，不能只粘贴 ino。

Use the included PlatformIO profiles to compile the Arduino sketch, including its
C23 core and custom partition tables. Arduino IDE requires equivalent manual settings.

`desktop/wizard.py` 提供许可、选目录、导入校验包、型号和串口选择、烧录日志。
Windows CI 使用 PyInstaller 和 Inno Setup 构建安装器；仅有 Python 源码不代表已测试 Windows 安装体验。
烧录前向导会提示覆盖板上程序。下载与烧录需要电脑，完成后板端离线。

The desktop wizard offers license review, destination selection, package hash checks,
board/port selection and flashing logs. Windows CI builds an installer with PyInstaller
and Inno Setup. Source availability is not a Windows runtime acceptance test.

## 验证记录 / Verification

见 `eval/` 的原始输出、数值对拍和布局报告。初版含真实失败样本，保留用于对比。
模型短小，可能复读、答非所问和编造。后续版本按独立测试与实际板端日志验收。

See `eval/` for raw replies, numerical comparisons and layout reports. Initial failures
are preserved for comparison. Small models can repeat, drift or fabricate answers.
Final acceptance requires independent language tests and physical-board logs.
