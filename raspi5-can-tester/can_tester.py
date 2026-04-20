#!/usr/bin/env python3
"""
CAN Tester — Raspberry Pi 5 Edition

A terminal-based CAN bus testing tool using MCP2515 via SPI.
Ported from the Flipper Zero C implementation.

Features:
  - Loopback self-test (no external CAN bus needed)
  - Normal mode (real CAN bus at 500 kbps)
  - Real-time TX/RX counters, error counts, hex data display

Usage:
  sudo python3 can_tester.py

Author: dashuai
License: MIT
"""

import sys
import os
import time
import threading
import curses
import signal

from mcp2515 import MCP2515, CANFrame, Mode, BitRate, Clock, Error

# ---------------------------------------------------------------------------
#  Configuration  (matches Flipper Zero version)
# ---------------------------------------------------------------------------

VERSION = "1.0.0"

CAN_TEST_TX_ID       = 0x7E0
CAN_TEST_INTERVAL_S  = 0.5      # 500 ms
CAN_TEST_POLL_S      = 0.002    # 2 ms

SPI_BUS    = 0
SPI_DEVICE = 0
SPI_SPEED  = 8_000_000   # 8 MHz (match Flipper)

CAN_CLOCK   = Clock.MHZ_8
CAN_BITRATE = BitRate.CAN_500KBPS


# ---------------------------------------------------------------------------
#  Test State (shared between worker thread and UI)
# ---------------------------------------------------------------------------

class TestState:
    def __init__(self):
        self.tx_count    = 0
        self.rx_count    = 0
        self.err_count   = 0
        self.tx_counter  = 0       # rolling 0x00-0xFF
        self.last_rx_id  = 0
        self.last_rx_len = 0
        self.last_rx_data = bytearray(8)
        self.running     = False
        self.init_ok     = False
        self.init_msg    = ""
        self.mode_name   = ""
        self.stop_event  = threading.Event()
        self.lock        = threading.Lock()


# ---------------------------------------------------------------------------
#  Worker Thread  (from scenes/can_test.c  can_test_worker)
# ---------------------------------------------------------------------------

def can_test_worker(state: TestState, mode: int):
    """Background thread that sends/receives CAN frames."""
    mcp = None
    try:
        mcp = MCP2515(bus=SPI_BUS, device=SPI_DEVICE,
                       clock=CAN_CLOCK, bitrate=CAN_BITRATE,
                       spi_speed=SPI_SPEED)

        err = mcp.init(mode=mode)
        if err != Error.OK:
            with state.lock:
                state.init_ok = False
                state.init_msg = f"MCP2515 Init FAILED (error={err})"
            return

        # Clear all masks/filters — accept everything
        mcp.set_mask(0, 0x000)
        mcp.set_mask(1, 0x000)
        for i in range(6):
            mcp.set_filter(i, 0x000)

        with state.lock:
            state.init_ok = True
            state.init_msg = "Init OK"

        last_tx_time = 0.0
        state.running = True

        while not state.stop_event.is_set():
            now = time.monotonic()

            # --- TX: send test frame periodically ---
            if (now - last_tx_time) >= CAN_TEST_INTERVAL_S:
                with state.lock:
                    counter = state.tx_counter

                data = bytearray(8)
                data[0] = counter & 0xFF
                data[1] = 0xDE
                data[2] = 0xAD
                data[3] = 0xBE
                data[4] = 0xEF
                data[5] = 0xCA
                data[6] = 0xFE
                data[7] = sum(data[:7]) & 0xFF  # checksum

                frame = CANFrame(can_id=CAN_TEST_TX_ID, data=bytes(data))

                result = mcp.send_frame(frame)
                with state.lock:
                    if result == Error.OK:
                        state.tx_count += 1
                        state.tx_counter = (state.tx_counter + 1) & 0xFF
                    else:
                        state.err_count += 1

                last_tx_time = now

            # --- RX: check for incoming frames ---
            if mcp.check_receive() == Error.OK:
                err_code, rx_frame = mcp.read_message()
                if err_code == Error.OK and rx_frame is not None:
                    with state.lock:
                        state.rx_count += 1
                        state.last_rx_id = rx_frame.can_id
                        state.last_rx_len = rx_frame.dlc
                        for i in range(min(rx_frame.dlc, 8)):
                            state.last_rx_data[i] = rx_frame.data[i]

            time.sleep(CAN_TEST_POLL_S)

    except Exception as e:
        with state.lock:
            state.init_ok = False
            state.init_msg = f"Error: {e}"
    finally:
        state.running = False
        if mcp:
            try:
                mcp.close()
            except Exception:
                pass


# ---------------------------------------------------------------------------
#  Curses UI
# ---------------------------------------------------------------------------

def draw_box(win, y, x, h, w, title=""):
    """Draw a box with optional title."""
    # Top border
    win.addstr(y, x, "┌" + "─" * (w - 2) + "┐")
    # Sides
    for i in range(1, h - 1):
        win.addstr(y + i, x, "│" + " " * (w - 2) + "│")
    # Bottom border
    win.addstr(y + h - 1, x, "└" + "─" * (w - 2) + "┘")
    # Title
    if title:
        win.addstr(y, x + 2, f" {title} ", curses.A_BOLD)


def draw_main_menu(stdscr, selected):
    """Draw the main menu screen."""
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    # Title
    title = "╔═══════════════════════════════════════╗"
    title2 = "║       CAN Tester  —  Raspberry Pi 5  ║"
    title3 = "╚═══════════════════════════════════════╝"
    cx = max(0, (w - len(title)) // 2)
    cy = 2
    stdscr.addstr(cy, cx, title, curses.color_pair(1) | curses.A_BOLD)
    stdscr.addstr(cy + 1, cx, title2, curses.color_pair(1) | curses.A_BOLD)
    stdscr.addstr(cy + 2, cx, title3, curses.color_pair(1) | curses.A_BOLD)

    # Subtitle
    sub = f"MCP2515 CAN Bus Test Tool  v{VERSION}"
    stdscr.addstr(cy + 4, max(0, (w - len(sub)) // 2), sub, curses.color_pair(3))

    # Menu items
    menu_items = [
        ("1", "Loopback Self-Test", "MCP2515 内部环回，验证 SPI 接线"),
        ("2", "Normal Mode (CAN Bus)", "500 kbps 真实 CAN 总线收发"),
        ("3", "About", "版本与说明信息"),
        ("4", "Exit", "退出程序"),
    ]

    menu_y = cy + 7
    for i, (key, label, desc) in enumerate(menu_items):
        prefix = "  ▸ " if i == selected else "    "
        attr = curses.color_pair(2) | curses.A_BOLD if i == selected else curses.color_pair(0)
        line = f"{prefix}[{key}] {label}"
        mx = max(0, (w - 50) // 2)
        stdscr.addstr(menu_y + i * 2, mx, line, attr)
        if i == selected:
            stdscr.addstr(menu_y + i * 2 + 1, mx + 6, desc, curses.color_pair(3))

    # Footer
    footer = "↑/↓ 选择  |  Enter 确认  |  Q 退出"
    stdscr.addstr(h - 2, max(0, (w - len(footer)) // 2), footer, curses.color_pair(3))

    stdscr.refresh()


def draw_test_screen(stdscr, state: TestState):
    """Draw the real-time CAN test display."""
    h, w = stdscr.getmaxyx()
    stdscr.erase()

    with state.lock:
        tx_count    = state.tx_count
        rx_count    = state.rx_count
        err_count   = state.err_count
        init_ok     = state.init_ok
        init_msg    = state.init_msg
        mode_name   = state.mode_name
        last_rx_id  = state.last_rx_id
        last_rx_len = state.last_rx_len
        last_rx_data = bytes(state.last_rx_data)
        running     = state.running

    box_w = min(56, w - 4)
    box_x = max(0, (w - box_w) // 2)
    box_y = 1

    # Title bar
    title = f"CAN Test [{mode_name}]"
    stdscr.addstr(box_y, max(0, (w - len(title)) // 2), title,
                  curses.color_pair(1) | curses.A_BOLD)

    # Status
    box_y += 2
    status_color = curses.color_pair(4) if init_ok else curses.color_pair(5)
    status_str = f"  Status: {'● RUNNING' if running else '○ STOPPED'}  |  Init: {'OK ✓' if init_ok else 'FAIL ✗'}"
    stdscr.addstr(box_y, box_x, status_str, status_color)

    if not init_ok and init_msg:
        stdscr.addstr(box_y + 1, box_x + 2, init_msg, curses.color_pair(5))

    # CAN params
    box_y += 3
    stdscr.addstr(box_y, box_x, "  ── CAN Parameters ──", curses.color_pair(3))
    box_y += 1
    stdscr.addstr(box_y, box_x, f"  Bitrate: 500 kbps  |  Clock: 8 MHz  |  TX ID: 0x{CAN_TEST_TX_ID:03X}", curses.color_pair(0))

    # TX info
    box_y += 2
    stdscr.addstr(box_y, box_x, "  ── Transmit ──", curses.color_pair(3))
    box_y += 1
    tx_line = f"  TX Count: {tx_count}"
    stdscr.addstr(box_y, box_x, tx_line, curses.color_pair(4))
    err_line = f"  ERR Count: {err_count}"
    err_color = curses.color_pair(5) if err_count > 0 else curses.color_pair(0)
    stdscr.addstr(box_y + 1, box_x, err_line, err_color)

    # RX info
    box_y += 3
    stdscr.addstr(box_y, box_x, "  ── Receive ──", curses.color_pair(3))
    box_y += 1
    if rx_count > 0:
        rx_line = f"  RX Count: {rx_count}  |  Last ID: 0x{last_rx_id:03X}  [{last_rx_len}]"
        stdscr.addstr(box_y, box_x, rx_line, curses.color_pair(4))

        # Hex dump
        hex_str = " ".join(f"{last_rx_data[i]:02X}" for i in range(min(last_rx_len, 8)))
        stdscr.addstr(box_y + 1, box_x, f"  Data: {hex_str}", curses.color_pair(2) | curses.A_BOLD)
    else:
        stdscr.addstr(box_y, box_x, "  RX Count: 0  (waiting...)", curses.color_pair(3))
        stdscr.addstr(box_y + 1, box_x, "  Data: -- -- -- -- -- -- -- --", curses.color_pair(3))

    # Footer
    footer = "按 Q 或 Backspace 停止测试并返回菜单"
    stdscr.addstr(h - 2, max(0, (w - len(footer)) // 2), footer, curses.color_pair(3))

    stdscr.refresh()


def draw_about_screen(stdscr):
    """Draw the about screen."""
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    lines = [
        ("CAN Tester", curses.A_BOLD | curses.color_pair(1)),
        ("", 0),
        (f"Version: {VERSION}", curses.color_pair(0)),
        ("Platform: Raspberry Pi 5", curses.color_pair(0)),
        ("", 0),
        ("MCP2515 CAN bus loopback", curses.color_pair(3)),
        ("tester for verifying", curses.color_pair(3)),
        ("wiring with USB-CAN", curses.color_pair(3)),
        ("analyzers (CANalyst-II)", curses.color_pair(3)),
        ("", 0),
        ("Ported from Flipper Zero", curses.color_pair(3)),
        ("Author: dashuai", curses.color_pair(2)),
        ("", 0),
        ("Press any key to return...", curses.color_pair(3)),
    ]

    start_y = max(0, (h - len(lines)) // 2)
    for i, (line, attr) in enumerate(lines):
        x = max(0, (w - len(line)) // 2)
        stdscr.addstr(start_y + i, x, line, attr)

    stdscr.refresh()
    stdscr.nodelay(False)
    stdscr.getch()


def run_test(stdscr, mode: int, mode_name: str):
    """Run the CAN test with live UI updates."""
    state = TestState()
    state.mode_name = mode_name

    # Start worker thread
    worker = threading.Thread(target=can_test_worker, args=(state, mode), daemon=True)
    worker.start()

    stdscr.nodelay(True)
    stdscr.timeout(300)  # refresh every 300ms

    try:
        while True:
            draw_test_screen(stdscr, state)

            key = stdscr.getch()
            if key in (ord('q'), ord('Q'), curses.KEY_BACKSPACE, 127, 8, 27):
                break

            # Check if worker died
            if not worker.is_alive() and not state.running and state.init_msg:
                # Show error for a moment then let user exit
                draw_test_screen(stdscr, state)
                stdscr.nodelay(False)
                stdscr.timeout(-1)
                stdscr.getch()
                break
    finally:
        state.stop_event.set()
        worker.join(timeout=3.0)


def main(stdscr):
    """Main curses application loop."""
    # Init colors
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN, -1)     # title
    curses.init_pair(2, curses.COLOR_GREEN, -1)     # selected / data
    curses.init_pair(3, curses.COLOR_YELLOW, -1)    # subtitle / dim
    curses.init_pair(4, curses.COLOR_GREEN, -1)     # ok / running
    curses.init_pair(5, curses.COLOR_RED, -1)       # error / fail
    curses.curs_set(0)

    selected = 0
    num_items = 4

    while True:
        draw_main_menu(stdscr, selected)

        stdscr.nodelay(False)
        stdscr.timeout(-1)
        key = stdscr.getch()

        if key == curses.KEY_UP:
            selected = (selected - 1) % num_items
        elif key == curses.KEY_DOWN:
            selected = (selected + 1) % num_items
        elif key in (curses.KEY_ENTER, 10, 13):
            if selected == 0:
                run_test(stdscr, Mode.LOOPBACK, "LOOPBACK")
            elif selected == 1:
                run_test(stdscr, Mode.NORMAL, "NORMAL")
            elif selected == 2:
                draw_about_screen(stdscr)
            elif selected == 3:
                break
        elif key == ord('1'):
            run_test(stdscr, Mode.LOOPBACK, "LOOPBACK")
        elif key == ord('2'):
            run_test(stdscr, Mode.NORMAL, "NORMAL")
        elif key == ord('3'):
            draw_about_screen(stdscr)
        elif key in (ord('4'), ord('q'), ord('Q')):
            break


# ---------------------------------------------------------------------------
#  Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Check SPI device exists
    spi_dev = f"/dev/spidev{SPI_BUS}.{SPI_DEVICE}"
    if not os.path.exists(spi_dev):
        print(f"错误: SPI 设备 {spi_dev} 不存在!")
        print()
        print("请确认:")
        print("  1. 已启用 SPI: sudo raspi-config nonint do_spi 0")
        print("  2. 重启后生效: sudo reboot")
        print(f"  3. 设备存在:   ls -la {spi_dev}")
        print()
        print("或者将用户加入 spi 组: sudo usermod -aG spi $USER")
        sys.exit(1)

    # Check permissions
    if not os.access(spi_dev, os.R_OK | os.W_OK):
        print(f"错误: 没有权限访问 {spi_dev}")
        print()
        print("请使用 sudo 运行:")
        print(f"  sudo python3 {sys.argv[0]}")
        print()
        print("或者将用户加入 spi 组: sudo usermod -aG spi $USER")
        sys.exit(1)

    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
    finally:
        print("CAN Tester 已退出。")
