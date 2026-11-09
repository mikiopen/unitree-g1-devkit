# 上线前检查

预检用于发现配置缺失、端口冲突、动作格式和接口契约问题；它不替代真实设备验收。

```bash
python g1.py plan
python g1.py preflight
python g1.py preflight --actions-dir adapters/reference/actions --report .local/reports/preflight.json
```

默认示例故意缺少机器人型号、自由度、固件、网卡和 SDK 版本，因此预检应返回阻止上线的结果。请只在本机 `.local/devkit.json` 中填写真实值。

## 检查范围

- 配置字段与路径是否完整。
- 三个教学端口是否冲突。
- 订阅端与动作端的静态常量、转发端口和动作映射是否一致。
- 动作 JSON 是否为有限数值、合法宽度和正持续时间。
- 适配器是否声明 SDK 初始化位置；预检不会导入或运行它。

单独检查动作数据：

```bash
python g1.py inspect-action adapters/reference/actions/init.json --dof 29
python g1.py inspect-action adapters/reference/actions/init.json --dof 23
```

通过预检只表示“静态契约可继续验证”，不表示机器人安全、SDK 兼容或动作可执行。真实设备还需验证急停、限幅、超时、模式切换、断连和状态回读。
