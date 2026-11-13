# 第6轮最终下载清单

**六轮结束并暂停。所有模型仍为研究候选，综合知识、身份及通用多轮未通过，实体板与Windows交互未验收。** 不按最终测试选新默认；共同保留第3、5轮，旧版不删除。

| 型号 | 训练阶段 | FP32主权重 | Q4+固件 |
|---|---|---|---|
| N16R8 | 第3轮语义候选 | [下载](https://chatgpt.com/library?file_id=libfile_4ea78b0d99b0819191c4ecab9de5691e&account_id=personal) | [下载](https://chatgpt.com/library?file_id=libfile_b108dceb2750819193513ef82fe52e78&account_id=personal) |
| N16R8 | 第5轮记录候选 | [下载](https://chatgpt.com/library?file_id=libfile_30ee98f9f99c81918db94f6fea53a332&account_id=personal) | [下载](https://chatgpt.com/library?file_id=libfile_04395787a7708191871e2484ca90ed3e&account_id=personal) |
| N32R16 | 第3轮语义候选 | [下载](https://chatgpt.com/library?file_id=libfile_0fb2aad6c80c8191895cc39f5b2bb0d3&account_id=personal) | [下载](https://chatgpt.com/library?file_id=libfile_bffa6d5bcd688191926d690906da7f06&account_id=personal) |
| N32R16 | 第5轮记录候选 | [下载](https://chatgpt.com/library?file_id=libfile_d8d556dab57c819190420b027e29cb12&account_id=personal) | [下载](https://chatgpt.com/library?file_id=libfile_44929a8e0f108191be77f02c8e2eb513&account_id=personal) |

最终R3 Q4包保留R3原模型，配第4轮修复后的固件，与第5轮包使用同一固件hash；对应FP32主权重与原R3包一致。FP32用于恢复/研究，不是现有板端默认运行格式，且包内无优化器。

| 交付 | 文件 | 下载 |
|---|---|---|
| Windows安装器 | XiaobaiBot-Setup-round4-ci.exe | [下载](https://chatgpt.com/library?file_id=libfile_7506265abc048191b8edadf089a637ab&account_id=personal) |
| 原始Windows CI产物 | XiaobaiBot-Windows-Setup-round4-ci.zip | [下载](https://chatgpt.com/library?file_id=libfile_db93fedefa9881919ab0e8fba8902998&account_id=personal) |
| 最终完整源码与复现数据 | XiaobaiBot-final-source-round6.zip | [下载](https://chatgpt.com/library?file_id=libfile_a1ba4593d5c481919c179c0cc01834cc&account_id=personal) |
| 六轮原始评测/日志/报告 | XiaobaiBot-final-evidence-round6.zip | [下载](https://chatgpt.com/library?file_id=libfile_e4bcf6467a708191ae09e78b8a6f4ca8&account_id=personal) |

Windows包来源为已验证run43415308564，安装器未做GUI/真实串口实测；后续同源码提交run43424746000构建也成功、训练job跳过。最终源码/证据是上传前快照，精确下载ID和暂停记录保存在本GitHub提交，避免归档自身循环引用。

## 字节数与SHA-256

| 文件 | 字节数 | SHA-256 |
|---|---:|---|
| XiaobaiBot-N16R8-v0.2-dev-final-round6-R3.zip | 12769917 | 3ae55b43938d41fec89067fa304b6fc187b650ea036f5766375190ab57624f6e |
| XiaobaiBot-N32R16-v0.2-dev-final-round6-R3.zip | 14159256 | 3a5818c6d32480b494c56da96bfc61c9083f19b934f587286f37f2688ffef7b6 |
| XiaobaiBot-final-source-round6.zip | 14316807 | 148aec615f0f1c8d77ec1efc1edb00f03ebadf8e1bd54db2a3d0a7ed96e3c2b3 |
| XiaobaiBot-final-evidence-round6.zip | 1657836 | 252786e317542cd84bbcbd30b8a817677d8473c1c7bf721ec647dbe1dd02daaa |
| XiaobaiBot-N16R8-v0.2-dev-round3-FP32.zip | 95950859 | e9098ec9a6a3fd2092d77ece04ae79e621553deaffd7a5369d922c346e73b656 |
| XiaobaiBot-N32R16-v0.2-dev-round3-FP32.zip | 109786388 | 3c0bc4a50ee434510808dc5498eb53bdb3509d8da8171d4d8b3defc6f380be75 |
| XiaobaiBot-N16R8-v0.2-dev-round5.zip | 12769977 | 9711483127873d1f42d905c851f1b0c934a6078ff3cb22dc960c5df79572745c |
| XiaobaiBot-N16R8-v0.2-dev-round5-FP32.zip | 95949202 | 52689f0e62ba9fa095db7f63dd067d05fb2283b077688378e13cd82abe45a933 |
| XiaobaiBot-N32R16-v0.2-dev-round5.zip | 14159517 | 96236a5ea2e52a7b3996095e3f82f0c6416649ce1dec8193e29d2950e7711ae7 |
| XiaobaiBot-N32R16-v0.2-dev-round5-FP32.zip | 109786692 | a5b9878c8ee09f3e39530dff70b8e4dca40d8ccbd1cb222a2b22c3fc74523dfa |
| XiaobaiBot-Setup-round4-ci.exe | 26737365 | 225893f8e16d21b303a139ee5d40081198fd4312ef7d8ff8539ebf89bd567679 |
| XiaobaiBot-Windows-Setup-round4-ci.zip | 26190203 | 7a509ca05e0af03b72125de622d74b8e967f3ddf4cc5172285bd601adedbdb71 |
| XiaobaiBot-round5-evidence-source.zip | 14688741 | 3e60e0f8e8953191120958b026279016e37fd5be08156d2aa8bed4b17fab6440 |

[最终对比与遗留问题](FINAL_DELIVERY_ROUND6.md) · [逐条原始回答](FINAL_RAW_ANSWERS_ROUND6.md) · [架构研究](FINAL_RESEARCH_ROUND6.md)

历史候选及证据：[第1轮](ROUND_1_20261113.md)、[第3轮](ROUND_3_DOWNLOADS.md)、[第4轮](ROUND_4_DOWNLOADS.md)、[第5轮](ROUND_5_DOWNLOADS.md)。不把历史包误称最新固件。
