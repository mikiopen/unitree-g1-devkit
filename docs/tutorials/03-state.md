# 第 03 章：模拟状态与只读DDS

> 环节E · 反馈。本章成果：标明数据来源的状态日志。

## 能力目标

先读取合成状态并解释字段；条件齐备后再使用同一示例做只读DDS订阅。

- 识别数据来源、时间戳、关节角和角速度。
- 区分接收时间与采样时间。
- 知道读取状态与发布控制是不同接口。

## 前置条件

| 项目 | 内容 |
| --- | --- |
| 所属环节 | 反馈 |
| 学习类型 | 电脑实验，含设备扩展 |
| 必需环境 | Python3.10+；电脑主任务无需SDK或机器人。 |
| 可选条件 | DDS扩展需G1、Linux、匹配SDK、网络和完整设备基线。 |
| 前置章节 | [01 环境](01-environment.md)；DDS扩展另需[02 网络](02-network.md)。 |
| 接口依据 | [独立状态读取示例](../../examples/03-state-reader/read_state.py)；DDS分支需与实际固件/SDK匹配。 |
| 验证状态 | 模拟主任务由自动检查覆盖；DDS 分支未做真机验证。见[验证说明](../validation.md)。 |

### 准备与配置

电脑端在仓库根目录运行。设备扩展先填写型号、自由度、固件、SDK提交、网卡和话题；不要将关节数组长度直接当作有效自由度。

## 输入输出与接口

输入状态 → 有界队列 → 主循环输出JSON。示例读取首个消息槽的q/dq；不创建运动发布器、不切换模式。队列可能丢弃新样本，因此日志条数不能直接测量总线频率。

| 边界 | 约定 |
| --- | --- |
| 输入 | 模拟参数，或明确选择的DDS接口与主题 |
| 输出 | source、received_at、joint_index、q_rad与dq_rad_s |
| 错误边界 | 时长非法或缺SDK/接口应失败；无DDS状态给出诊断 |

## 最小示例

### 主任务

1. 短时读取合成状态：

   ```text
   python examples/03-state-reader/read_state.py --duration 2
   ```

2. 找到source、received_at、joint_index、q_rad、dq_rad_s，说明每项含义。
3. 将duration改为非法值观察拒绝提示，再恢复正数。到时自动退出，也可Ctrl+C结束。

### 条件扩展：只读DDS

1. 按匹配的[官方SDK说明](https://github.com/unitreerobotics/unitree_sdk2_python)准备Linux环境。
2. 用02章记录的实际接口替换示例enp2s0，并核对固件话题；以下命令在具备SDK的Linux设备运行：

   ```text
   python examples/03-state-reader/read_state.py --mode dds --interface enp2s0 --topic rt/lowstate --duration 10
   ```

3. 程序使用unitree_hg的LowState_、DDS域0；部分配套使用rt/lf/lowstate，须按匹配资料选择。记录source=dds的日志及环境；无数据返回1。退出时关闭订阅。

## 可修改与扩展点

增加电池、IMU或关节字段时说明来源、单位和有效性；received_at是接收时间，不能代替传感器采集时间。

### 实践成果

保存一段日志，标注数据来源和三个时间概念。交付状态日志及字段说明。对应工作：机器人数据接口、反馈处理与控制基础。

## 验证方法

| 检查项 | 预期结果 | 提交证据 |
| --- | --- | --- |
| 电脑状态 | 至少一行source=synthetic，q/dq单位明确 | 一段状态JSON |
| 时间解释 | received_at是电脑接收时钟 | 采样/接收/显示时间对比 |
| 设备扩展 | 仅实测后才记录source=dds及槽位映射 | 条件具备时的基线和DDS日志 |

### 常见问题

| 现象 | 检查与处理 |
| --- | --- |
| 没有DDS数据 | 核对接口、话题、域、SDK和防火墙；模拟通过不能证明DDS可达。 |
| 输出始终为0 | 默认是合成数据；先看source，不据此判断电机。 |
| 日志频率比预期低 | 示例队列与显示循环有限，不用于测量原始采样频率。 |

### 下一步与参考

- 上一章：[02 网络、SSH与文件传输](02-network.md)
- 下一章：[04 控制命令的生命周期](04-control.md)
- 学习框架：[六环节框架](../learning-framework.md) · [完整章节目录](README.md)
- 必要参考：[状态示例](../../examples/03-state-reader/read_state.py) · [官方订阅器](https://github.com/unitreerobotics/unitree_sdk2_python/blob/master/unitree_sdk2py/core/channel.py)
- 所属环节：[反馈](../framework/05-feedback.md)
