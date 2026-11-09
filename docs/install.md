# 安装与开始

## 电脑教学环境

需要 Python 3.10 或更高版本，仓库核心检查只依赖标准库。

```bash
git clone <your-repository-url>
cd unitree-g1-devkit
python tools/check_environment.py --profile pc
python g1.py doctor
python g1.py demo
python tools/verify_learning.py
```

`demo` 使用本机回环地址运行两个模拟端，不连接真实机器人。可选能力（例如离线语音识别）按对应教程单独安装依赖和模型，资源放在被忽略的 `.local/` 中。

## 配置

复制示例配置到本地私有目录：

```bash
python g1.py plan
```

先阅读[配置说明](configuration.md)。示例中的机器人型号、自由度、固件、网卡和 SDK 版本故意留空；未补齐时，上线前检查必须阻止真实设备阶段。

## 真实设备适配

1. 根据设备型号和固件选择厂商官方 SDK。
2. 在你自己的适配层实现状态读取、命令发送、错误映射和生命周期管理。
3. 把设备身份、密钥、网络地址和现场配置留在仓库外。
4. 先做只读状态验证，再做受约束的单关节或官方安全动作测试。
5. 完成[上线前检查](preflight.md)并保留现场验收记录。

本仓库不分发厂商 SDK，也不保证任何接口与特定固件兼容。
