# 最小教学实验

从仓库根目录执行命令。电脑基础实验使用 Python 3.10+ 标准库；不需要安装历史模块的完整依赖。

| 实验 | 入口 | 默认行为 | 验证范围 |
| --- | --- | --- | --- |
| 环境 | [check_environment.py](../tools/check_environment.py) | 报告 Python 与选定依赖 | 电脑实测 |
| 状态 | [read_state.py](03-state-reader/read_state.py) | 生成合成状态 | 模拟实测；DDS 订阅待设备验证 |
| 动作数据 | [inspect_csv.py](05-action-data/inspect_csv.py) | 校验教学 CSV | 电脑实测；不执行动作 |
| UDP/群控 | [udp_demo.py](06-udp-demo/udp_demo.py) | 只接受本机回环地址 | 双进程实测；独立教学协议 |
| 音频 | [audio_file.py](08-audio-demo/audio_file.py) | 生成测试音或读取 WAV | 文件实测；不自动播放或合成语音 |
| ASR | [transcribe_file.py](09-asr-demo/transcribe_file.py) | 指定本地模型后转写 WAV | 可选依赖；[2026-10-07本地模型推理证据](../docs/validation.md)，不代表麦克风或真机验证 |
| 指令映射 | [route_text.py](10-command-router/route_text.py) | 输出允许或拒绝的计划 | 电脑实测；不发控制指令 |

运行 [第 13 章电脑组合项目](../docs/tutorials/13-delivery.md) 可将状态、文本映射与 UDP 回复串起来理解。独立实验不自动相互调用；教程明确传递哪些输入。

UDP 示例只处理 `status`、`echo`、`stop_demo`，回复全部为模拟结果。`stop_demo` 不结束接收进程，也不代表机器人停止；进程通过 Ctrl+C 退出。这里的 JSON 消息不能直接发给历史 App 订阅服务。

测试、资源与本地日志说明见 [验证记录](../docs/validation.md) 和 [资源声明](../third-party-notices/README.md)。


## 统一与职业分支入口

完整双设备链路用 `python g1.py demo`；界面用 `python g1.py gui`；文件ASR到模拟端用 `python g1.py voice --audio your.wav --model model-directory`，需要可选Vosk依赖。新增 [职业分支代码](career-labs/README.md) 包含UART C协议/接收器、Linux只读清单与控制仿真。
