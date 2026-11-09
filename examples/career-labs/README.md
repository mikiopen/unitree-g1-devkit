# 职业分支的可运行起点

本目录补充 [职业任务书](../../docs/tracks/career-labs.md)。程序可以提供设计/模拟证据；实际板卡固件、RTOS 调度测量、BSP 移植和 PCB 制作仍由对应设备实验提供证据。

| 分支 | 已提供源文件 | 运行 |
| --- | --- | --- |
| MCU 通信 | serial/protocol.c、protocol.h、host_test.c 与 Python 分帧接收器 | `python examples/career-labs/serial/receiver.py` |
| Linux/BSP | 只读 sysfs 类与内核清单 | `python examples/career-labs/linux_inspect.py` |
| 控制 | 单关节离散 PD、力矩限幅、误差/超调/RMSE、可导出 CSV | `python examples/career-labs/control_sim.py --kd 4` |
| App/集成 | 根目录 g1.py、g1devkit 的完整双设备链路与 Tkinter UI | `python g1.py demo` / `python g1.py gui` |

串口协议为 8 字节：A5 5A 01、uint8 序号、uint16 小端采样值、uint8 按键、CRC8。CRC 多项式 0x07、初值 0、不反射、无末尾 XOR，覆盖前 7 字节；不是 Unitree 通信协议。Python 接收器演示噪声、截断和 CRC 错误后的重同步。

有主机 C 编译器时：`cc -std=c99 -Wall -Wextra -Werror serial/protocol.c serial/host_test.c -o host_test`，然后运行 host_test。选择真实 MCU 后，只需把 frame_encode 的结果交给该板的 HAL UART；该调用及 RTOS 任务必须按具体板卡补充，当前没有虚构可烧录固件。不要直接连接机器人内部总线。

控制实验的单位惯量、阻尼0.2与限幅5是明确的教学假设。比较 `--kd 0` 与 `--kd 4` 的结果；不是 G1 整机动力学或训练策略。CSV 用 `--output .local/control.csv` 导出，若已有文件拒绝覆盖。

硬件分支先做独立3.3V按键输入板：需求、接口、拉电阻、限流/去耦、原理图、PCB、BOM与测量按任务书交付。没有实际选板和数据手册确认，当前不冒充完成 PCB/电气验证。
