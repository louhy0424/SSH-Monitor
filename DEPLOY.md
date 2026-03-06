# Deployment Guide / 部署指南

[English](#english-deployment-guide) | [中文](#中文部署指南)

---

<a name="english-deployment-guide"></a>
## 🇬🇧 English Deployment Guide

### Quick Deploy

```bash
# 1. Clone repository
git clone <your-repo-url>
cd sshd-monitor

# 2. Run installer
sudo bash install.sh

# 3. Check status
sudo systemctl status sshd_monitor
```

### Manual Install

```bash
# Create directory
sudo mkdir -p /opt/sshd_monitor

# Copy files
sudo cp sshd_monitor.py /opt/sshd_monitor/
sudo cp sshd_monitor.service /etc/systemd/system/

# Start service
sudo systemctl daemon-reload
sudo systemctl enable --now sshd_monitor
```

### View Logs

```bash
# Real-time logs
sudo journalctl -u sshd_monitor -f

# Recent 100 lines
sudo journalctl -u sshd_monitor -n 100

# Today's logs
sudo journalctl -u sshd_monitor --since today
```

### Common Commands

```bash
sudo systemctl status sshd_monitor   # Check status
sudo systemctl stop sshd_monitor     # Stop service
sudo systemctl restart sshd_monitor  # Restart
sudo systemctl disable sshd_monitor  # Disable auto-start
```

### Configuration

Edit `/opt/sshd_monitor/sshd_monitor.py`:

```python
POLL_INTERVAL = 10          # Polling interval (seconds)
LOG_FILE = "/var/log/sshd_monitor.log"
LOG_LEVEL = logging.INFO    # DEBUG, INFO, WARNING, ERROR
LOG_RETENTION_DAYS = 7      # Log retention period (days)
```

### Log Rotation

The script automatically rotates logs daily and retains the most recent 7 days:
- Rotates at midnight every day
- Archives as `sshd_monitor.log.YYYY-MM-DD`
- Deletes logs older than 7 days automatically

---

<a name="中文部署指南"></a>
## 🇨🇳 中文部署指南

### 快速部署

```bash
# 1. 克隆仓库
git clone <你的仓库地址>
cd sshd-monitor

# 2. 运行安装脚本
sudo bash install.sh

# 3. 检查状态
sudo systemctl status sshd_monitor
```

### 手动安装

```bash
# 创建目录
sudo mkdir -p /opt/sshd_monitor

# 复制文件
sudo cp sshd_monitor.py /opt/sshd_monitor/
sudo cp sshd_monitor.service /etc/systemd/system/

# 启动服务
sudo systemctl daemon-reload
sudo systemctl enable --now sshd_monitor
```

### 查看日志

```bash
# 实时日志
sudo journalctl -u sshd_monitor -f

# 最近 100 行
sudo journalctl -u sshd_monitor -n 100

# 今天的日志
sudo journalctl -u sshd_monitor --since today
```

### 常用命令

```bash
sudo systemctl status sshd_monitor   # 查看状态
sudo systemctl stop sshd_monitor     # 停止服务
sudo systemctl restart sshd_monitor  # 重启服务
sudo systemctl disable sshd_monitor  # 禁用自启
```

### 配置说明

编辑 `/opt/sshd_monitor/sshd_monitor.py`：

```python
POLL_INTERVAL = 10          # 轮询间隔（秒）
LOG_FILE = "/var/log/sshd_monitor.log"
LOG_LEVEL = logging.INFO    # DEBUG, INFO, WARNING, ERROR
LOG_RETENTION_DAYS = 7      # 日志保留天数（自动清理）
```

### 日志轮转

脚本内置自动日志轮转功能：
- 每天午夜自动创建新日志文件
- 自动保留最近 **7 天**的日志
- 超过保留天数的旧日志会被**自动删除**
- 轮转后的日志文件格式：`sshd_monitor.log.2026-03-06`

---

## GitHub Upload Guide / GitHub 上传指南

### Step 1: Create Repository / 创建仓库

1. Go to [GitHub](https://github.com) and log in / 登录 GitHub
2. Click "New Repository" / 点击"新建仓库"
3. Name: `sshd-monitor` / 仓库名
4. Choose "Public" or "Private" / 选择公开或私有
5. Don't initialize with README (we already have one) / 不要勾选初始化 README
6. Click "Create repository" / 点击创建

### Step 2: Upload Files / 上传文件

```bash
# Navigate to project directory / 进入项目目录
cd sshd-monitor

# Initialize git / 初始化 git
git init

# Add all files / 添加所有文件
git add .

# Commit / 提交
git commit -m "Initial commit: SSH connection monitor with systemd support

Features:
- Real-time SSH connection monitoring
- Login/logout notifications
- Systemd service integration
- Log rotation (7 days retention)"

# Add remote (replace with your URL) / 添加远程仓库
# HTTPS:
git remote add origin https://github.com/YOUR_USERNAME/sshd-monitor.git
# or SSH:
git remote add origin git@github.com:YOUR_USERNAME/sshd-monitor.git

# Push / 推送
git branch -M main
git push -u origin main
```

### Step 3: Verify / 验证

Visit `https://github.com/YOUR_USERNAME/sshd-monitor` to see your code!

---

## Troubleshooting / 故障排查

### Service won't start / 服务无法启动

```bash
# Check detailed error / 查看详细错误
sudo systemctl status sshd_monitor -l
sudo journalctl -u sshd_monitor -n 50
```

### Permission denied / 权限问题

```bash
# Fix log file permissions / 修复日志权限
sudo chown root:root /var/log/sshd_monitor.log
sudo chmod 644 /var/log/sshd_monitor.log
```

### Test manually / 手动测试

```bash
# Run script manually / 手动运行
sudo python3 /opt/sshd_monitor/sshd_monitor.py
```

---

## Uninstall / 卸载

```bash
# Stop and disable / 停止并禁用
sudo systemctl stop sshd_monitor
sudo systemctl disable sshd_monitor

# Remove files / 删除文件
sudo rm /etc/systemd/system/sshd_monitor.service
sudo rm -rf /opt/sshd_monitor
sudo rm /var/log/sshd_monitor.log*

# Reload systemd / 重载配置
sudo systemctl daemon-reload
```
