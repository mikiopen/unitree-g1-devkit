# 第 06 章：单设备UDP请求与回复

> 环节A · 设备接入。本章成果：一次请求、回复与超时记录。

## 能力目标

用两个电脑进程完成一次UDP请求、回复和超时实验。

- 识别IP、端口、目标与请求ID。
- 观察回声与缺失回复。
- 区分教学JSON协议和现有App文本协议。

## 前置条件

| 项目 | 内容 |
| --- | --- |
| 所属环节 | 设备接入 |
| 学习类型 | 电脑实验 |
| 必需环境 | Python3.10+、两个终端；仅使用IPv4回环网络。 |
| 可选条件 | 无；不需要机器人或局域网广播。 |
| 前置章节 | [01 环境](01-environment.md)和[05 数据格式](05-action-data.md)。 |
| 接口依据 | [独立UDP示例](../../examples/06-udp-demo/udp_demo.py)，协议g1-learning/v1，不与App或维护入口协议互换。 |
| 验证状态 | 本机通信及异常路径由自动测试覆盖。见[验证说明](../validation.md)。 |

### 准备与配置

两个终端都进入仓库根目录。使用未占用的19006端口；更改端口时两端保持一致。它不同于App的2006/3840文本服务，也不同于维护入口demo的g1devkit/mock/v1。

## 输入输出与接口

发送端编码JSON → 127.0.0.1接收端按target过滤 → 返回相同request_id → 发送端校验并收集。此独立实验使用g1-learning/v1，仅支持status、echo、stop_demo，单报文上限4096字节。

| 边界 | 约定 |
| --- | --- |
| 输入 | 回环目标、request_id、command和可选text |
| 输出 | 与请求关联的g1-learning/v1模拟回复 |
| 错误边界 | 未知协议、错误目标与超时分开处理 |

## 最小示例

1. 终端A启动模拟接收端，保持运行：

   ```text
   python examples/06-udp-demo/udp_demo.py serve --robot-id g1-a --port 19006
   ```

2. 终端B查询状态：

   ```text
   python examples/06-udp-demo/udp_demo.py send --endpoint 127.0.0.1:19006 --target g1-a --command status
   ```

3. 在终端B发送回声，检查文字是否一致：

   ```text
   python examples/06-udp-demo/udp_demo.py send --endpoint 127.0.0.1:19006 --target g1-a --command echo --text "你好"
   ```

4. 在A用Ctrl+C结束接收端，再执行查询观察超时与missing_endpoints。发送端收齐回复或超时后自行退出。
5. stop_demo只回复模拟结果，不关闭接收进程，也不是机器人急停。

## 可修改与扩展点

扩展通信适配层时保留请求关联、目标选择和超时语义；当前示例固定回环，真实网络需另建适配与验证。

### 实践成果

给记录加上发送和接收时刻，说明“发送成功”与“有效回复”的区别。交付正常、回声和超时三组结果。对应工作：Linux通信服务与协议调试。

## 验证方法

| 检查项 | 预期结果 | 提交证据 |
| --- | --- | --- |
| 正常请求 | replies含g1-a、result=simulated、motion_executed=false；退出0 | 请求与回复 |
| 回声 | 回复text与发送文字一致 | 回声结果 |
| 超时 | 接收端停止后missing_endpoints含19006；退出1 | 超时记录 |

### 常见问题

| 现象 | 检查与处理 |
| --- | --- |
| 端口占用 | 换一个端口并同时修改serve和send。 |
| 收不到回复 | 检查接收端、端口和target，确认双方都在回环地址。 |
| 非回环地址被拒绝 | 这是电脑实验范围；真机使用配套正式服务。 |

### 下一步与参考

- 上一章：[05 动作数据结构与校验](05-action-data.md)
- 下一章：[07 多设备与掉线诊断](07-fleet.md)
- 学习框架：[六环节框架](../learning-framework.md) · [完整章节目录](README.md)
- 必要参考：[独立UDP代码](../../examples/06-udp-demo/udp_demo.py) · [协议矩阵](../configuration.md)
- 所属环节：[设备接入](../framework/01-access.md)
