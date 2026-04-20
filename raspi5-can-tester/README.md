# CAN Tester — 树莓派 5 版

[English](#can-tester-for-raspberry-pi-5) | 中文

基于 **MCP2515** CAN 控制器的 **树莓派 5** CAN 总线测试工具（Python）。  
从 Flipper Zero 版本移植，使用同一个 **CAN Hack 模块**。

## 功能特性

- **环回自测（Loopback）** — MCP2515 内部环回模式，无需外部 CAN 总线。用于验证 SPI 接线和 MCP2515 是否正常工作。
- **普通模式（Normal）** — 在真实 CAN 总线上以 500 kbps 收发 CAN 帧。用于验证与外部设备（如 USB-CAN 分析仪）的通信。
- **实时显示** — 终端上实时显示 TX/RX 计数器、错误计数、最后接收的 CAN ID、数据长度和十六进制数据。
- **关于页面** — 显示应用版本和说明信息。

## 硬件需求

| 组件 | 说明 |
|------|------|
| [Raspberry Pi 5](https://www.raspberrypi.com/) | 运行 Raspberry Pi OS (Bookworm+) |
| CAN Hack 模块 | MCP2515 + TJA1050，8 MHz 晶振（原来插在 Flipper Zero 上的同一个模块） |
| 杜邦线 × 6 | 母对母，连接模块排针到 RPi5 GPIO |

### 接线方式（CAN Hack 模块 ↔ 树莓派 5）

CAN Hack 模块的排针对应 Flipper Zero GPIO 排针位置。用杜邦线从模块排针连接到树莓派 5：

**Flipper Zero 排针定义（正面朝上，从左到右）：**
```
上排:  [3V3] [SWC] [PA7] [PA6] [PA4] [PB3] [PB2] [GND]
        Pin1  Pin2  Pin3  Pin4  Pin5  Pin6  Pin7  Pin8

功能:   VCC   --   MOSI  MISO   CS   SCK   --    GND
```

**接线表：**

| CAN Hack 模块引脚 (Flipper 排针) | 信号 | RPi5 GPIO | RPi5 物理引脚 |
|----------------------------------|------|-----------|--------------|
| Pin 1 (3V3)                      | VCC  | 3.3V      | Pin 1        |
| Pin 8 (GND)                      | GND  | GND       | Pin 6        |
| Pin 6 (PB3 / SCK)                | SCK  | GPIO 11 (SPI0_SCLK) | Pin 23 |
| Pin 3 (PA7 / MOSI)               | MOSI | GPIO 10 (SPI0_MOSI) | Pin 19 |
| Pin 4 (PA6 / MISO)               | MISO | GPIO 9 (SPI0_MISO)  | Pin 21 |
| Pin 5 (PA4 / CS)                  | CS   | GPIO 8 (SPI0_CE0)   | Pin 24 |

**接线示意图：**
```
CAN Hack 模块                      树莓派 5
(Flipper GPIO 排针)                (GPIO 排针)

Pin 1 (3V3/VCC) ──────────────── Pin 1  (3.3V)
Pin 3 (PA7/MOSI) ─────────────── Pin 19 (GPIO10/SPI0_MOSI)
Pin 4 (PA6/MISO) ─────────────── Pin 21 (GPIO9/SPI0_MISO)
Pin 5 (PA4/CS)   ─────────────── Pin 24 (GPIO8/SPI0_CE0)
Pin 6 (PB3/SCK)  ─────────────── Pin 23 (GPIO11/SPI0_SCLK)
Pin 8 (GND)      ─────────────── Pin 6  (GND)
```

**树莓派 5 GPIO 引脚图（★ = 需要连接的引脚）：**
```
     ┌─────────────────────────┐
   ★ │  3V3  (1)    (2) 5V    │
     │  GPIO2 (3)    (4) 5V   │
     │  GPIO3 (5)   ★(6) GND  │
     │  GPIO4 (7)    (8) TX   │
     │  GND   (9)   (10) RX   │
     │  GPIO17(11)  (12)GPIO18│
     │  GPIO27(13)  (14) GND  │
     │  GPIO22(15)  (16)GPIO23│
     │  3V3   (17)  (18)GPIO24│
   ★ │  GPIO10(19)  (20) GND  │  ← MOSI
   ★ │  GPIO9 (21)  (22)GPIO25│  ← MISO
   ★ │  GPIO11(23) ★(24)GPIO8 │  ← SCK, CS
     │  GND   (25)  (26)GPIO7 │
     └─────────────────────────┘
```

> **注意：** 关于供电 —— Loopback 自测模式用 3.3V 即可。Normal 模式如果无法正常通信，尝试将 VCC 改接 RPi5 的 5V (Pin 2)，因为 TJA1050 CAN 收发器通常需要 5V。

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

## 快速部署

```bash
# 1. 一键安装（启用 SPI + 安装依赖）
chmod +x install.sh
./install.sh

# 2. 重启（如果 SPI 刚启用）
sudo reboot

# 3. 运行
sudo python3 can_tester.py
```

### 手动部署

```bash
# 启用 SPI
sudo raspi-config nonint do_spi 0
sudo reboot

# 安装 Python 依赖
pip3 install -r requirements.txt

# 运行（需要 SPI 权限）
sudo python3 can_tester.py

# 或者将用户加入 spi 组后免 sudo
sudo usermod -aG spi $USER
# 重新登录后
python3 can_tester.py
```

## 项目结构

```
raspi5-can-tester/
├── can_tester.py      # 主程序入口 + curses 交互 UI
├── mcp2515.py         # MCP2515 CAN 控制器驱动（从 C 移植）
├── requirements.txt   # Python 依赖
├── install.sh         # 一键部署脚本
└── README.md          # 本文档
```

## 使用方法

1. 用杜邦线将 CAN Hack 模块连接到树莓派 5（参见上方接线表）。
2. 运行 `sudo python3 can_tester.py`。
3. 从主菜单选择测试模式：
   - **Loopback Self-Test**：测试 MCP2515 + SPI 接线，无需外部 CAN 总线。TX 和 RX 计数器应同时递增。
   - **Normal Mode (CAN Bus)**：将 CAN_H / CAN_L 连接到外部 CAN 设备。将以 500 kbps 发送 TX 帧，并显示接收到的帧。
4. 观察屏幕上的 TX/RX 计数器和数据实时更新。
5. 按 **Q** 或 **Backspace** 停止测试并返回菜单。

## 故障排查

| 现象 | 可能原因 |
|------|---------| 
| `SPI 设备不存在` | SPI 未启用 — 运行 `sudo raspi-config nonint do_spi 0` 并重启 |
| `没有权限访问 SPI` | 需要 sudo 或加入 spi 组 |
| `Init: FAIL` | MCP2515 未连接、SPI 接线错误、或晶振频率不匹配 |
| TX 递增但 RX 为 0（环回模式） | SPI 问题 — 检查 MISO/MOSI/CS 接线是否正确 |
| TX 递增但 RX 为 0（普通模式） | 无外部设备响应、CAN_H/CAN_L 未连接、缺少终端电阻 |
| ERR 计数递增 | 总线错误 — 检查波特率是否匹配、接线、终端电阻 |
| Normal 模式通信异常 | TJA1050 需要 5V — 尝试 VCC 改接 RPi5 Pin 2 (5V) |

## 许可证

MIT License — 详见 [LICENSE](../LICENSE)。

## 作者

**dashuai**

---

# CAN Tester for Raspberry Pi 5

[中文](#can-tester--树莓派-5-版) | English

A CAN bus testing tool for **Raspberry Pi 5** using the **MCP2515** CAN controller module (Python).  
Ported from the Flipper Zero version, using the same **CAN Hack module**.

## Features

- **Loopback Self-Test** — MCP2515 internal loopback mode, no external CAN bus needed.
- **Normal Mode** — Send and receive CAN frames on a real CAN bus at 500 kbps.
- **Real-time Display** — Live TX/RX counters, error counts, last received CAN ID, and hex data dump in terminal.
- **About Screen** — Shows app version and description.

## Hardware Requirements

| Component | Description |
|-----------|-------------|
| [Raspberry Pi 5](https://www.raspberrypi.com/) | Running Raspberry Pi OS (Bookworm+) |
| CAN Hack Module | MCP2515 + TJA1050, 8 MHz crystal (same module previously used with Flipper Zero) |
| Jumper Wires × 6 | Female-to-female, connect module header to RPi5 GPIO |

### Wiring (CAN Hack Module ↔ Raspberry Pi 5)

| CAN Hack Module Pin (Flipper Header) | Signal | RPi5 GPIO | RPi5 Physical Pin |
|---------------------------------------|--------|-----------|-------------------|
| Pin 1 (3V3)                           | VCC    | 3.3V      | Pin 1             |
| Pin 8 (GND)                           | GND    | GND       | Pin 6             |
| Pin 6 (PB3 / SCK)                     | SCK    | GPIO 11 (SPI0_SCLK) | Pin 23 |
| Pin 3 (PA7 / MOSI)                    | MOSI   | GPIO 10 (SPI0_MOSI) | Pin 19 |
| Pin 4 (PA6 / MISO)                    | MISO   | GPIO 9 (SPI0_MISO)  | Pin 21 |
| Pin 5 (PA4 / CS)                      | CS     | GPIO 8 (SPI0_CE0)   | Pin 24 |

> **Note:** For Normal mode, if CAN bus communication fails, try connecting VCC to RPi5 5V (Pin 2) instead, as the TJA1050 transceiver typically requires 5V.

## Quick Setup

```bash
# 1. One-click install (enables SPI + installs deps)
chmod +x install.sh
./install.sh

# 2. Reboot if SPI was just enabled
sudo reboot

# 3. Run
sudo python3 can_tester.py
```

## Usage

1. Connect CAN Hack module to Raspberry Pi 5 via jumper wires (see wiring table above).
2. Run `sudo python3 can_tester.py`.
3. Select a test mode from the menu:
   - **Loopback Self-Test**: Tests MCP2515 + SPI wiring without external CAN bus. TX and RX counters should both increment.
   - **Normal Mode (CAN Bus)**: Connect CAN_H / CAN_L to an external CAN device. TX frames will be sent at 500 kbps.
4. Watch the live display for TX/RX counters and data.
5. Press **Q** or **Backspace** to stop and return to menu.

## License

MIT License — see [LICENSE](../LICENSE) for details.

## Author

**dashuai**
