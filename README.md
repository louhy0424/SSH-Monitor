# SSH Connection Monitor / SSH 连接监控工具

[English](#english) | [中文](#中文)

---

<a name="english"></a>
## 🇬🇧 English

A Python-based SSH connection monitoring tool that detects SSH login/logout events in real-time through periodic polling of system commands.

### Features

- ✅ **Real-time Monitoring**: Poll system status every 10 seconds
- ✅ **Login/Logout Notifications**: Automatically detect and log SSH connection events
- ✅ **Dual Data Source**: Combines `who` and `ss` commands for accurate information
- ✅ **Complete Logging**: Standard timestamp format, supports console and file output
- ✅ **Systemd Integration**: One-click installation as system service with auto-start
- ✅ **Log Rotation**: Automatic cleanup of logs older than 7 days
- ✅ **Zero Dependencies**: Uses only Python standard library

### Quick Start

```bash
# One-click installation
sudo bash install.sh

# View logs
sudo journalctl -u sshd_monitor -f
```

### Log Output Example

```
[2024-01-15 09:30:15] [INFO] [Login] User alice from IP 192.168.1.100 (pts/0)
[2024-01-15 10:15:23] [INFO] [Logout] User alice from IP 192.168.1.100 (pts/0)
```

---

<a name="中文"></a>
## 🇨🇳 中文

基于 Python 的 SSH 连接状态监控脚本，通过定时轮询系统命令实时检测用户的上线和下线事件。

### 功能特性

- ✅ **实时监控**: 每 10 秒轮询一次系统状态
- ✅ **上下线通知**: 自动检测并记录 SSH 登录/登出事件
- ✅ **双数据源验证**: 结合 `who` 和 `ss` 命令获取准确信息
- ✅ **完整日志**: 标准时间戳格式，支持控制台和文件双输出
- ✅ **日志轮转**: 自动清理超过 7 天的旧日志
- ✅ **Systemd 集成**: 一键安装为系统服务，支持开机自启
- ✅ **零依赖**: 仅使用 Python 标准库

### 快速开始

```bash
# 一键安装
sudo bash install.sh

# 查看日志
sudo journalctl -u sshd_monitor -f
```

### 日志输出示例

```
[2024-01-15 09:30:15] [INFO] 【上线通知】用户 alice 从 IP 192.168.1.100 登录
[2024-01-15 10:15:23] [INFO] 【下线通知】用户 alice 从 IP 192.168.1.100 断开
```

---

## System Requirements / 系统要求

| Item / 项目 | Requirement / 要求 |
|-------------|-------------------|
| OS / 操作系统 | Ubuntu 18.04+, Debian 9+, CentOS 7+ |
| Python | 3.6+ |
| Privilege / 权限 | root (required for full connection info) |

## Files / 文件说明

| File / 文件 | Description / 说明 |
|-------------|-------------------|
| `sshd_monitor.py` | Main Python script / Python 主程序 |
| `sshd_monitor.service` | systemd service config / systemd 服务配置 |
| `install.sh` | One-click installer / 一键安装脚本 |
| `DEPLOY.md` | Detailed deployment guide / 详细部署文档 |

## License / 许可证

MIT License
