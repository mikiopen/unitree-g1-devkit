# 选择学习路线

能力结构采用[六环节框架](learning-framework.md)。本页按示例前置条件安排实践顺序，因此03只读状态可以在执行实践前完成；章节编号不代表环节编号。先理解六环节，再按自己的条件使用已有示例。

## 零基础

先完成[准备单元P1–P4](course-syllabus.md)：Python文件/字典/异常、终端与进程、基本网络、Git与实验记录。然后进入00、01，再选择下列路线。

## 只有电脑

[00 机器人二次开发系统地图](tutorials/00-overview.md) → [01 开发环境与依赖检查](tutorials/01-environment.md) → [03 模拟状态与只读DDS](tutorials/03-state.md) → [04 控制命令的生命周期](tutorials/04-control.md) → [05 动作数据结构与校验](tutorials/05-action-data.md) → [06 单设备UDP请求与回复](tutorials/06-udp.md) → [07 多设备与掉线诊断](tutorials/07-fleet.md) → [08 音频文件与TTS边界](tutorials/08-audio.md) → [10 文本白名单与拒绝路径](tutorials/10-router.md) → [11 广播与桥接的消息契约](tutorials/11-broadcast.md) → [12 界面与通信状态](tutorials/12-ui.md) → [13 完成可复现的项目交付](tutorials/13-delivery.md)

03只做模拟；04和11先做设计；12有Tkinter时运行界面，无桌面时运行demo并完成交互设计。09是模型条件具备后的选做实验。02的实际网络与SSH操作留待有设备后补做。

## 有G1并具备基础

[00 机器人二次开发系统地图](tutorials/00-overview.md) → [01 开发环境与依赖检查](tutorials/01-environment.md) → [02 网络、SSH与文件传输](tutorials/02-network.md) → [03 模拟状态与只读DDS](tutorials/03-state.md) → [04 控制命令的生命周期](tutorials/04-control.md) → [05 动作数据结构与校验](tutorials/05-action-data.md) → [06 单设备UDP请求与回复](tutorials/06-udp.md) → [07 多设备与掉线诊断](tutorials/07-fleet.md) → [08 音频文件与TTS边界](tutorials/08-audio.md) → [09 语音文件转写](tutorials/09-asr.md) → [10 文本白名单与拒绝路径](tutorials/10-router.md) → [11 广播与桥接的消息契约](tutorials/11-broadcast.md) → [12 界面与通信状态](tutorials/12-ui.md) → [13 完成可复现的项目交付](tutorials/13-delivery.md)

先做各章电脑主任务。02、03的DDS、04的真实控制按设备基线和停止证据逐层加入；有机器人并不自动满足09模型、11广播和12外部后台的条件。每章“前置条件”表是进入扩展的依据。

## 想了解职业方向

完成共同主线后，阅读[职业地图](career-map.md)，从[体验任务](tracks/career-labs.md)选择两个方向，用[作品模板](portfolio-template.md)比较兴趣、基础缺口与独立完成程度。已有[职业分支代码](../examples/career-labs/README.md)可作为起点，不能当作板卡固件、PCB或整机控制已完成。

## 每次学习只做四件事

1. 从[章节目录](tutorials/README.md)进入当前章。
2. 按统一六栏目完成主任务，扩展按条件加入。
3. 保留验收证据与一次失败记录。
4. 按章末导航继续；查源码时才打开[资料导航](README.md)。
