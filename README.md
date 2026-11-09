# 宇树 G1 机器人二次开发学习框架

这是一个面向机器人学习者和开发者的开源框架：在厂商提供的硬件、固件与接口基础上，按 **设备接入 → 感知 → 决策 → 执行 → 反馈 → 部署维护** 完成一套可验证的二次开发流程。

项目提供方法、接口约定、最小示例和验收思路，不替学习者决定具体实现。你可以替换传感器、算法、通信协议和执行器，并用相同的结构记录设计与验证结果。宇树 G1 是主要适配对象，但方法本身可迁移到其他机器人。

## 学习框架

| 环节 | 学习入口 | 交付物 |
| --- | --- | --- |
| 设备接入 | [01 设备接入](docs/framework/01-access.md) | 设备清单、环境报告、通信契约 |
| 感知 | [02 感知](docs/framework/02-perception.md) | 带时间、来源与置信信息的观测 |
| 决策 | [03 决策](docs/framework/03-decision.md) | 可拒绝、可取消、可追踪的任务计划 |
| 执行 | [04 执行](docs/framework/04-execution.md) | 受约束的执行接口与结果语义 |
| 反馈 | [05 反馈](docs/framework/05-feedback.md) | 可解释的状态、故障与操作反馈 |
| 部署维护 | [06 部署维护](docs/framework/06-operations.md) | 可复现、可诊断、可回退的交付 |

先读[完整框架](docs/learning-framework.md)，再按[学习路线](docs/learning-path.md)完成 14 篇[实践教程](docs/tutorials/README.md)。所有教程统一使用“目标、前置条件、输入输出、最小实践、扩展方向、验证方法”的模板。

## 五分钟开始

需要 Python 3.10 或更高版本。以下命令只运行本机检查与回环模拟，不会连接或控制机器人：

```bash
python tools/check_environment.py --profile pc
python g1.py demo
python tools/verify_learning.py
```

真实设备接入前，请先完成[安全说明](docs/safety.md)、[配置说明](docs/configuration.md)和[上线前检查](docs/preflight.md)。仓库中的参考适配器只用于说明接口契约，不会自动初始化厂商 SDK 或发送运动命令。

## 仓库内容

- `docs/`：学习框架、教程、专题与项目模板。
- `g1devkit/`：配置、校验、模拟状态、协议和命令行工具。
- `examples/`：可以在电脑上独立运行的最小实验。
- `adapters/reference/`：设备适配器的静态契约示例。
- `configs/`：不含设备身份和凭证的示例配置。
- `tests/`、`tools/`：自动测试、文档检查和公开发布检查。

进一步阅读：[系统架构](docs/architecture.md) · [仓库地图](docs/repository-map.md) · [扩展专题](docs/topics/README.md) · [贡献指南](CONTRIBUTING.md)。

项目采用 [Apache License 2.0](LICENSE) 开源。宇树及其他项目名称和商标归各自权利人所有。

> 本项目不是宇树官方产品，不附带厂商 SDK、固件、模型、动作资产或设备凭证。真实机器人操作具有风险，必须由具备现场安全条件的人员完成。
