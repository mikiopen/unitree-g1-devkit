# 验证说明

## 自动检查

```bash
python tools/verify_learning.py
python tools/check_upload_credentials.py
python tools/check_publication.py
```

`verify_learning.py` 检查 Markdown 本地链接、Python 语法、课程结构、电脑示例和单元测试。`check_upload_credentials.py` 启发式查找凭证字面量；`check_publication.py` 检查公开树边界、个人路径、邮箱和公网地址。

这些检查不访问真实设备、不运行参考适配器、不发送运动命令，也不能证明第三方许可或真实系统安全。

## 真实设备验收

设备验收应单独记录硬件、固件、SDK、网络、急停、限幅、断连、模式切换、状态回读和现场人员。任何“命令已发送”都不能等同于“动作已安全完成”。
