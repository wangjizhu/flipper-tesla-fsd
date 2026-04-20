# CAN Tester — Flipper Zero CAN 总线测试工具

[English](#can-tester-for-flipper-zero) | 中文

一个基于 **MCP2515** CAN 控制器模块的 **Flipper Zero** 独立 CAN 总线测试应用。用于验证 CAN 总线接线和与 USB-CAN 分析仪（如 CANalyst-II）的通信。

## 功能特性

- **环回自测（Loopback）** — MCP2515 内部环回模式，无需外部 CAN 总线。用于验证 SPI 接线和 MCP2515 是否正常工作。
- **普通模式（Normal）** — 在真实 CAN 总线上以 500 kbps 收发 CAN 帧。用于验证与外部设备（如 USB-CAN 分析仪）的通信。
- **实时显示** — Flipper 屏幕上实时显示 TX/RX 计数器、错误计数、最后接收的 CAN ID、数据长度和十六进制数据。
- **关于页面** — 显示应用版本和说明信息。

## 硬件需求

| 组件 | 说明 |
|------|------|
| Flipper Zero | 运行 OFW / Momentum / Unleashed / RogueMaster 固件 |
| MCP2515 CAN 模块 | SPI 接口 CAN 控制器，8 MHz 晶振 |
| CAN 收发器 | TJA1050 或类似（通常已集成在 MCP2515 模块上） |

### 接线方式（Flipper Zero ↔ MCP2515 模块）

| Flipper Zero 引脚 | MCP2515 引脚 |
|-------------------|-------------|
| 3V3               | VCC         |
| GND               | GND         |
| SCK (PB3)         | SCK         |
| MOSI (PB15)       | SI          |
| MISO (PC11)       | SO          |
| CS (PA4)          | CS          |

> **注意：** 本应用未使用 MCP2515 的 INT 引脚，采用轮询方式接收帧。

## CAN 总线参数

| 参数 | 值 |
|------|-----|
| 波特率 | 500 kbps |
| 时钟 | 8 MHz |
| 发送帧 ID | `0x7E0` |
| 数据长度 | 8 字节 |
| 发送间隔 | 500 ms |

### 发送帧格式

| Byte 0 | Byte 1–6 | Byte 7 |
|--------|----------|--------|
| 递增计数器（0x00–0xFF） | `DE AD BE EF CA FE` | 校验和（Byte 0–6 之和） |

## 编译

本应用使用 [ufbt](https://github.com/flipperdevices/flipperzero-ufbt)（micro Flipper Build Tool）编译。

```bash
# 安装 ufbt（如未安装）
pip install ufbt

# 编译应用
ufbt

# 通过 USB 刷入 Flipper Zero
ufbt launch
```

## 项目结构

```
.
├── application.fam          # Flipper 应用清单
├── can_tester_app.c         # 应用入口，分配/释放，主循环
├── can_tester_app.h         # 应用结构体、枚举、版本定义
├── icon.png                 # 应用图标（10x10，1-bit）
├── assets/
│   └── demo.gif             # 演示动画
├── libraries/
│   ├── mcp_can_2515.c/.h    # MCP2515 CAN 控制器驱动
│   ├── Spi_lib.c/.h         # Flipper Zero SPI 总线抽象
│   └── log_user.h           # 调试日志宏
├── scenes/
│   ├── main_menu.c          # 主菜单：环回 / 普通 / 关于
│   ├── can_test.c           # CAN 测试工作线程 + 实时 UI
│   └── about.c              # 关于页面
└── scenes_config/
    ├── app_scene_config.h    # 场景注册宏
    ├── app_scene_functions.c # 场景处理函数表
    └── app_scene_functions.h # 场景处理函数声明
```

## 使用方法

1. 通过 SPI 将 MCP2515 模块连接到 Flipper Zero（参见上方接线表）。
2. 在 Flipper Zero 上安装并启动 **CAN Tester** 应用。
3. 从主菜单选择测试模式：
   - **Loopback Self-Test**：测试 MCP2515 + SPI 接线，无需外部 CAN 总线。TX 和 RX 计数器应同时递增。
   - **Normal Mode (CAN Bus)**：将 CAN_H / CAN_L 连接到外部 CAN 设备。将以 500 kbps 发送 TX 帧，并显示接收到的帧。
4. 观察屏幕上的 TX/RX 计数器和数据实时更新。
5. 按 **BACK** 键停止测试并返回菜单。

## 故障排查

| 现象 | 可能原因 |
|------|---------|
| 屏幕显示 `Init: FAIL` | MCP2515 未连接、SPI 接线错误、或晶振频率不匹配 |
| TX 递增但 RX 为 0（环回模式） | MCP2515 SPI 问题 — 检查 MISO/MOSI/CS 接线 |
| TX 递增但 RX 为 0（普通模式） | 无外部设备响应、CAN_H/CAN_L 未连接、缺少终端电阻 |
| `ERR` 计数递增 | 总线错误 — 检查波特率是否匹配、接线、终端电阻 |

## 许可证

MIT License — 详见 [LICENSE](LICENSE)。

## 作者

**dashuai**

---

# CAN Tester for Flipper Zero

[中文](#can-tester--flipper-zero-can-总线测试工具) | English

A standalone CAN bus testing application for **Flipper Zero** using the **MCP2515** CAN controller module. Designed for verifying CAN bus wiring and communication with USB-CAN analyzers (e.g. CANalyst-II).

## Features

- **Loopback Self-Test** — MCP2515 internal loopback mode, no external CAN bus needed. Verifies SPI wiring and MCP2515 functionality.
- **Normal Mode** — Send and receive CAN frames on a real CAN bus at 500 kbps. Useful for verifying communication with external devices (e.g. USB-CAN analyzers).
- **Real-time Display** — Live TX/RX counters, error counts, last received CAN ID, data length, and hex data dump on the Flipper screen.
- **About Screen** — Shows app version and description.

## Hardware Requirements

| Component | Description |
|-----------|-------------|
| Flipper Zero | Running OFW / Momentum / Unleashed / RogueMaster firmware |
| MCP2515 CAN Module | SPI-based CAN controller, 8 MHz crystal oscillator |
| CAN Transceiver | TJA1050 or similar (usually integrated on MCP2515 module) |

### Wiring (Flipper Zero ↔ MCP2515 Module)

| Flipper Zero Pin | MCP2515 Pin |
|------------------|-------------|
| 3V3              | VCC         |
| GND              | GND         |
| SCK (PB3)        | SCK         |
| MOSI (PB15)      | SI          |
| MISO (PC11)      | SO          |
| CS (PA4)         | CS          |

> **Note:** The INT pin of MCP2515 is not used in this application — the app polls for received frames.

## CAN Bus Parameters

| Parameter | Value |
|-----------|-------|
| Bit Rate  | 500 kbps |
| Clock     | 8 MHz |
| Frame ID (TX) | `0x7E0` |
| Data Length | 8 bytes |
| TX Interval | 500 ms |

### TX Frame Format

| Byte 0 | Byte 1–6 | Byte 7 |
|--------|----------|--------|
| Counter (0x00–0xFF, incrementing) | `DE AD BE EF CA FE` | Checksum (sum of bytes 0–6) |

## Building

This app is built using [ufbt](https://github.com/flipperdevices/flipperzero-ufbt) (micro Flipper Build Tool).

```bash
# Install ufbt (if not already installed)
pip install ufbt

# Build the app
ufbt

# Flash to Flipper Zero via USB
ufbt launch
```

## Project Structure

```
.
├── application.fam          # Flipper app manifest
├── can_tester_app.c         # App entry point, alloc/free, main loop
├── can_tester_app.h         # App struct, enums, version definition
├── icon.png                 # App icon (10x10, 1-bit)
├── assets/
│   └── demo.gif             # Demo animation
├── libraries/
│   ├── mcp_can_2515.c/.h    # MCP2515 CAN controller driver
│   ├── Spi_lib.c/.h         # SPI bus abstraction for Flipper Zero
│   └── log_user.h           # Debug logging macros
├── scenes/
│   ├── main_menu.c          # Main menu: Loopback / Normal / About
│   ├── can_test.c           # CAN test worker thread + live UI
│   └── about.c              # About screen
└── scenes_config/
    ├── app_scene_config.h    # Scene registration macros
    ├── app_scene_functions.c # Scene handler tables
    └── app_scene_functions.h # Scene handler declarations
```

## Usage

1. Connect MCP2515 module to Flipper Zero via SPI (see wiring table above).
2. Install and launch the **CAN Tester** app on Flipper Zero.
3. Select a test mode from the main menu:
   - **Loopback Self-Test**: Tests MCP2515 + SPI wiring without external CAN bus. TX and RX counters should both increment.
   - **Normal Mode (CAN Bus)**: Connect CAN_H / CAN_L to an external CAN device. TX frames will be sent at 500 kbps, and any received frames will be displayed.
4. Watch the live display for TX/RX counters and data.
5. Press **BACK** to stop the test and return to the menu.

## Troubleshooting

| Symptom | Possible Cause |
|---------|---------------|
| `Init: FAIL` on screen | MCP2515 not connected, bad SPI wiring, or wrong crystal frequency |
| TX increments but RX stays 0 (Loopback) | MCP2515 SPI issue — check MISO/MOSI/CS wiring |
| TX increments but RX stays 0 (Normal) | No external device responding, CAN_H/CAN_L not connected, termination resistor missing |
| `ERR` counter increments | Bus error — check baud rate match, wiring, termination |

## License

MIT License — see [LICENSE](LICENSE) for details.

## Author

**dashuai**
