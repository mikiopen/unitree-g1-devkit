# 仓库地图

推荐路径：**框架 → 教程 → 最小示例 → 自己的适配器 → 验证记录**。

```text
unitree-g1-devkit/
├─ docs/
│  ├─ framework/          六阶段能力入口
│  ├─ tutorials/          统一模板的实践教程
│  ├─ topics/             可选扩展专题
│  └─ tracks/             不同学习目标的路线
├─ g1devkit/              教学工具与领域层代码
├─ examples/              本机可运行的最小实验
├─ adapters/reference/    不可直接部署的静态契约示例
├─ configs/               可公开的示例配置
├─ tests/                 单元测试
├─ tools/                 内容、隐私与发布检查
└─ third-party-notices/   外部引用说明
```

新增通用教学内容放在 `docs/` 或 `examples/`；真实设备实现建议放在独立项目仓库，避免把客户配置、凭证、日志和许可受限资源带入公共框架。
