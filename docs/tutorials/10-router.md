# 第 10 章：文本白名单与拒绝路径

> 环节C · 决策。本章成果：接受、未知与混合输入测试。

## 能力目标

为文字输入建立精确白名单，分别验证允许、未知与混合输入。

- 用明确配置解释命令来源。
- 在未知或混合输入时拒绝执行。
- 区分dry-run计划与实际操作。

## 前置条件

| 项目 | 内容 |
| --- | --- |
| 所属环节 | 决策 |
| 学习类型 | 电脑实验 |
| 必需环境 | Python3.10+；无需ASR、模型或机器人。 |
| 可选条件 | 可将09章text作为输入，或在.local维护自己的同义短句配置。 |
| 前置章节 | [05 数据格式](05-action-data.md)；语音输入另需[09 ASR](09-asr.md)。 |
| 接口依据 | [独立白名单路由器](../../examples/10-command-router/route_text.py)与显式mapping文件；历史语音原型映射单独保留。 |
| 验证状态 | 电脑白名单、非法配置与拒绝路径已验证。 |

### 准备与配置

使用[白名单模板](../../configs/command-map.example.json)，从仓库根目录运行。要改映射时复制到.local，通过--mapping显式指定。

## 输入输出与接口

文字去除两端空格 → 精确查表 → 返回允许/拒绝和命令计划。独立示例仅允许status/stop_demo，不做模糊包含、自动纠错、shell调用或SDK运动。

| 边界 | 约定 |
| --- | --- |
| 输入 | 文本与显式白名单mapping |
| 输出 | accepted、command、mode=dry-run、motion_executed=false |
| 错误边界 | 未知文本拒绝；非法mapping报错 |

## 最小示例

1. 检查允许输入：

   ```text
   python examples/10-command-router/route_text.py "查询状态"
   ```

2. 检查未知与混合输入：

   ```text
   python examples/10-command-router/route_text.py "向前走"
   python examples/10-command-router/route_text.py "查询状态并向前走"
   ```

3. 对照accepted、command、mode、motion_executed和退出码，写出每个结果的原因。
4. 在.local副本中添加一个精确同义短句，值仍为status或stop_demo，用--mapping指向该文件，再测试。
5. 程序打印后退出，没有后台服务。stop_demo是教学命令，不能证明机器人停止。

## 可修改与扩展点

修改白名单短语或另建意图识别模块，保留精确拒绝与输出校验；当前mapping仅支持status和stop_demo，新增技能需要实现独立执行适配。

### 实践成果

为“未知输入”写一条可理解的未执行提示。交付三组输入输出和一条自定义同义句。对应工作：AI任务边界、后端参数校验与机器人任务层。

## 验证方法

| 检查项 | 预期结果 | 提交证据 |
| --- | --- | --- |
| 允许 | 查询状态：accepted=true、command=status、mode=dry-run、退出0 | 允许结果 |
| 拒绝 | 未知句/混合句：accepted=false、command=null、退出1 | 两份拒绝结果 |
| 配置错误 | 非法映射值被拒绝，退出2 | 一份错误记录 |

### 常见问题

| 现象 | 检查与处理 |
| --- | --- |
| 识别到了但命令没执行 | 先看是否精确匹配；dry-run只生成计划，不调用机器人。 |
| 想让模型直接运行命令 | 模型输出先作为数据，目标、期限、状态、许可和反馈需要独立检查。 |
| 出现空格就无法匹配 | 独立示例只裁两端空格；g1.py voice的中文词间空格规范另有明确实现，不使用模糊包含。 |

### 下一步与参考

- 上一章：[09 语音文件转写](09-asr.md)
- 下一章：[11 广播与桥接的消息契约](11-broadcast.md)
- 学习框架：[六环节框架](../learning-framework.md) · [完整章节目录](README.md)
- 必要参考：[路由代码](../../examples/10-command-router/route_text.py) · [决策框架](../framework/03-decision.md)
- 所属环节：[决策](../framework/03-decision.md)
