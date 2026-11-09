# 第 01 章：开发环境与依赖检查

> 环节A · 设备接入。本章成果：环境报告和运行记录。

## 能力目标

确认当前Python和工作目录，生成一份可复现的基础环境报告。

- 区分解释器、虚拟环境和工作目录。
- 读懂环境检查中的字段与退出码。
- 识别电脑主线与可选模块的依赖边界。

## 前置条件

| 项目 | 内容 |
| --- | --- |
| 所属环节 | 设备接入 |
| 学习类型 | 电脑实验 |
| 必需环境 | 开发电脑、终端、Python3.10+；已获取仓库。 |
| 可选条件 | Linux/SDK、Vosk、Flutter仅用于相应扩展检查。 |
| 前置章节 | [00 系统地图](00-overview.md)。 |
| 接口依据 | 维护的[环境检查工具](../../tools/check_environment.py)与g1.py doctor，不代表所有历史模块的运行环境。 |
| 验证状态 | 电脑实验由自动检查覆盖；设备兼容不能由依赖存在推断。见[验证说明](../validation.md)。 |

### 准备与配置

所有电脑命令从仓库根目录执行。基础实验使用标准库；不要先把所有历史requirements合并安装。下面的python可替换为虚拟环境解释器。

## 输入输出与接口

终端在工作目录中启动指定Python，Python再读取脚本和依赖。检查工具只报告环境，不导入或启动历史机器人服务。

| 边界 | 约定 |
| --- | --- |
| 输入 | Python环境、检查profile与配置 |
| 输出 | 环境报告及缺失依赖说明 |
| 错误边界 | 缺依赖与配置错误可定位，不自动安装设备服务 |

## 最小示例

1. 创建独立环境。Windows PowerShell：

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python.exe tools/check_environment.py --profile pc
   ```

   Linux/macOS：

   ```bash
   python3 -m venv .venv
   .venv/bin/python tools/check_environment.py --profile pc
   ```

2. 阅读executable、system、python和checks；解释当前使用哪个解释器。
3. 运行维护入口，并记录可选依赖是否存在：

   ```text
   python g1.py doctor
   ```

4. 如需某个方向，再分别运行相应检查；缺依赖返回1属于预期诊断：

   ```text
   python tools/check_environment.py --profile robot
   python tools/check_environment.py --profile voice
   python tools/check_environment.py --profile app
   ```

5. PowerShell用$LASTEXITCODE查看刚才Python命令的退出码，Linux用echo $?。程序检查后自行退出，无后台服务。

## 可修改与扩展点

增加一项依赖或设备能力检查，保持报告能区分必需、可选和缺失；不要把所有功能依赖变成入门必装。

### 实践成果

比较系统Python与.venv报告的executable。交付环境JSON、使用的命令和一次缺项说明。对应工作：Linux应用开发与环境交付。

## 验证方法

| 检查项 | 预期结果 | 提交证据 |
| --- | --- | --- |
| 基础环境 | python_3_10_plus=true，pc检查退出码0 | 解释器路径与环境JSON |
| 可选缺项 | 能说明robot/voice/app检查缺少什么 | 一份缺项记录或已具备说明 |
| 范围 | 知道包存在不证明驱动、模型或硬件可用 | 简短解释 |

### 常见问题

| 现象 | 检查与处理 |
| --- | --- |
| python指向系统别名 | 调用实际Python或.venv中的解释器，核对executable。 |
| 缺少SDK或Vosk | 先完成pc主线，进入设备或语音扩展时单独准备。 |
| 找不到脚本 | 回到包含g1.py的仓库根目录，不在历史模块目录运行主线命令。 |

### 下一步与参考

- 上一章：[00 机器人二次开发系统地图](00-overview.md)
- 下一章：[02 网络、SSH与文件传输](02-network.md)
- 学习框架：[六环节框架](../learning-framework.md) · [完整章节目录](README.md)
- 必要参考：[环境检查脚本](../../tools/check_environment.py) · [安装细节](../install.md)
- 所属环节：[设备接入](../framework/01-access.md)
