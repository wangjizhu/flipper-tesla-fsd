#!/bin/bash
# CAN Tester — Raspberry Pi 5 一键部署脚本
# Usage: chmod +x install.sh && ./install.sh

set -e

echo "╔═══════════════════════════════════════╗"
echo "║  CAN Tester — Raspberry Pi 5 Setup    ║"
echo "╚═══════════════════════════════════════╝"
echo ""

# 1. Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi\|BCM27\|BCM28" /proc/cpuinfo 2>/dev/null; then
    echo "⚠  警告: 未检测到树莓派硬件，继续安装..."
fi

# 2. Enable SPI if not already enabled
echo "► 检查 SPI 状态..."
if [ -e /dev/spidev0.0 ]; then
    echo "  ✓ SPI 已启用 (/dev/spidev0.0)"
else
    echo "  ✗ SPI 未启用，正在启用..."
    sudo raspi-config nonint do_spi 0
    echo "  ✓ SPI 已启用（可能需要重启生效）"
    NEED_REBOOT=1
fi

# 3. Install Python dependencies
echo ""
echo "► 安装 Python 依赖..."
pip3 install -r requirements.txt
echo "  ✓ 依赖安装完成"

# 4. Add current user to spi group (optional, avoids sudo)
echo ""
echo "► 将用户加入 spi 组（避免每次 sudo）..."
sudo usermod -aG spi "$USER" 2>/dev/null || true
echo "  ✓ 用户已加入 spi 组（重新登录后生效）"

# 5. Done
echo ""
echo "════════════════════════════════════════"
echo "  ✓ 安装完成！"
echo ""
echo "  运行方式:"
echo "    sudo python3 can_tester.py"
echo ""
echo "  或重新登录后（spi 组生效）:"
echo "    python3 can_tester.py"
echo "════════════════════════════════════════"

if [ "${NEED_REBOOT:-0}" = "1" ]; then
    echo ""
    echo "⚠  SPI 刚启用，请先重启: sudo reboot"
fi
