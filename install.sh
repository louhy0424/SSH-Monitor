#!/bin/bash
# SSH 连接监控脚本 - 一键安装脚本
# 使用方法: sudo bash install.sh

set -e  # 遇到错误立即退出

echo "=========================================="
echo "  SSH 连接监控脚本 - 安装程序"
echo "=========================================="

# 检查是否为 root 用户
if [ "$EUID" -ne 0 ]; then 
    echo "错误: 请使用 root 用户运行此脚本"
    echo "示例: sudo bash install.sh"
    exit 1
fi

# 检查 Python3 是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: Python3 未安装，请先安装 Python3"
    exit 1
fi

echo ""
echo "[1/6] 检查环境..."
echo "  Python 版本: $(python3 --version)"
echo "  Systemd 版本: $(systemctl --version | head -n1)"

# 创建部署目录
echo ""
echo "[2/6] 创建部署目录..."
INSTALL_DIR="/opt/sshd_monitor"
mkdir -p "$INSTALL_DIR"
echo "  目录: $INSTALL_DIR"

# 复制脚本文件
echo ""
echo "[3/6] 安装 Python 脚本..."
cp sshd_monitor.py "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/sshd_monitor.py"
echo "  已安装: $INSTALL_DIR/sshd_monitor.py"

# 创建日志文件
echo ""
echo "[4/6] 配置日志文件..."
LOG_FILE="/var/log/sshd_monitor.log"
touch "$LOG_FILE"
chmod 644 "$LOG_FILE"
echo "  日志文件: $LOG_FILE"

# 安装 systemd 服务
echo ""
echo "[5/6] 安装 systemd 服务..."
cp sshd_monitor.service /etc/systemd/system/
systemctl daemon-reload
echo "  服务文件: /etc/systemd/system/sshd_monitor.service"

# 启用并启动服务
echo ""
echo "[6/6] 启用并启动服务..."
systemctl enable sshd_monitor.service
systemctl start sshd_monitor.service

# 等待服务启动
sleep 2

# 检查服务状态
if systemctl is-active --quiet sshd_monitor; then
    echo ""
    echo "=========================================="
    echo "  ✓ 安装成功！"
    echo "=========================================="
    echo ""
    echo "服务状态: $(systemctl is-active sshd_monitor)"
    echo "开机自启: $(systemctl is-enabled sshd_monitor)"
    echo ""
    echo "常用命令:"
    echo "  查看状态: sudo systemctl status sshd_monitor"
    echo "  查看日志: sudo journalctl -u sshd_monitor -f"
    echo "  停止服务: sudo systemctl stop sshd_monitor"
    echo "  重启服务: sudo systemctl restart sshd_monitor"
    echo ""
else
    echo ""
    echo "=========================================="
    echo "  ⚠ 服务启动失败，请检查日志"
    echo "=========================================="
    echo ""
    echo "查看错误信息:"
    echo "  sudo systemctl status sshd_monitor -l"
    echo "  sudo journalctl -u sshd_monitor -n 50"
    echo ""
    exit 1
fi
