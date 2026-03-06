#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSH 连接监控脚本
功能：定时轮询系统命令，监控 SSH 连接的上线/下线状态,程序存活检测
版本：1.1.0
"""

import subprocess
import time
import re
import logging
import logging.handlers
import signal
import sys
from dataclasses import dataclass, field
from typing import Dict, Set, Optional
from datetime import datetime


# ==================== 配置区域 ====================
POLL_INTERVAL = 10  # 轮询间隔（秒）
LOG_FILE = "/var/log/sshd_monitor.log"  # 日志文件路径
LOG_LEVEL = logging.INFO  # 日志级别: DEBUG, INFO, WARNING, ERROR
LOG_RETENTION_DAYS = 7  # 日志保留天数，超过后自动覆盖
# ==================================================


@dataclass
class SSHSession:
    """SSH 会话数据类"""
    username: str
    terminal: str
    login_time: str
    ip: str
    pid: Optional[str] = None  # SSHD 进程 PID
    
    @property
    def session_id(self) -> str:
        """生成唯一会话标识：用户名@终端"""
        return f"{self.username}@{self.terminal}"
    
    def __hash__(self):
        return hash(self.session_id)
    
    def __eq__(self, other):
        if isinstance(other, SSHSession):
            return self.session_id == other.session_id
        return False
    
    def __repr__(self):
        return f"SSHSession({self.session_id}, IP={self.ip}, Time={self.login_time})"


class SSHMonitor:
    """SSH 连接监控器"""
    
    def __init__(self):
        self.current_sessions: Dict[str, SSHSession] = {}
        self.running = False
        self.logger = self._setup_logger()
        
        # 注册信号处理，确保优雅退出
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _setup_logger(self) -> logging.Logger:
        """配置日志记录器，支持自动轮转（保留最近 N 天）"""
        logger = logging.getLogger("SSHDMonitor")
        logger.setLevel(LOG_LEVEL)
        
        # 清除已有的处理器（避免重复）
        logger.handlers.clear()
        
        # 定义统一的日志格式
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台输出
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 文件输出（带轮转功能）
        try:
            # 使用 TimedRotatingFileHandler 实现按时间轮转
            # when='midnight': 每天午夜创建新日志
            # interval=1: 每 1 天
            # backupCount=LOG_RETENTION_DAYS: 保留最近 N 天的日志文件
            # 超过 backupCount 的旧日志会被自动删除
            file_handler = logging.handlers.TimedRotatingFileHandler(
                LOG_FILE,
                when='midnight',
                interval=1,
                backupCount=LOG_RETENTION_DAYS,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            
            # 设置轮转后缀格式（让日志文件名更易读）
            file_handler.suffix = "%Y-%m-%d"
            
            logger.addHandler(file_handler)
            logger.info(f"日志轮转已启用: 保留最近 {LOG_RETENTION_DAYS} 天")
        except PermissionError:
            logger.warning(f"无法写入日志文件 {LOG_FILE}，将仅输出到控制台")
        except Exception as e:
            logger.warning(f"配置日志轮转失败: {e}，将使用普通文件日志")
            # 降级为普通文件处理器
            try:
                file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            except Exception as e2:
                logger.warning(f"无法写入日志文件: {e2}")
        
        return logger
    
    def _signal_handler(self, signum, frame):
        """处理终止信号，实现优雅退出"""
        signame = signal.Signals(signum).name
        self.logger.info(f"收到信号 {signame}，正在停止监控...")
        self.running = False
    
    def _run_command(self, command: list) -> str:
        """
        执行系统命令并返回输出
        
        Args:
            command: 命令列表，如 ['who', '-u']
        
        Returns:
            命令的标准输出字符串
        
        Raises:
            subprocess.SubprocessError: 命令执行失败时抛出
        """
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                timeout=5,  # 设置超时避免卡死
                check=False  # 不自动抛出异常，我们自己处理
            )
            
            # 手动解码，使用 errors='replace' 处理非 UTF-8 字符
            # 这会将无法解码的字节替换为 � 符号，避免程序崩溃
            stdout = result.stdout.decode('utf-8', errors='replace')
            stderr = result.stderr.decode('utf-8', errors='replace')
            
            if result.returncode != 0:
                self.logger.warning(f"命令执行返回非零状态: {' '.join(command)}")
                if stderr:
                    self.logger.debug(f"命令错误输出: {stderr.strip()}")
            
            return stdout
        except subprocess.TimeoutExpired:
            self.logger.error(f"命令执行超时: {' '.join(command)}")
            return ""
        except FileNotFoundError:
            self.logger.error(f"命令不存在: {command[0]}")
            return ""
        except Exception as e:
            self.logger.error(f"执行命令时发生异常: {e}")
            return ""
    
    def _parse_who_output(self, output: str) -> Dict[str, SSHSession]:
        """
        解析 who 命令的输出
        
        who -u 输出格式示例：
        user1    pts/0        2024-01-15 09:30 00:01       12345 (192.168.1.100)
        user2    pts/1        2024-01-15 10:15 00:23       12346 (192.168.1.101)
        """
        sessions = {}
        
        # 按行解析
        for line in output.strip().split('\n'):
            if not line.strip():
                continue
            
            try:
                # 使用正则表达式匹配 who 输出
                # 格式：用户名 终端 日期 时间 [空闲时间] PID (IP)
                # 注意：空闲时间可能不存在，IP可能显示为 :0 或 域名
                pattern = r'(\S+)\s+(\S+)\s+(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})\s+(?:\S+\s+)?(\d+)\s*\(([^)]+)\)'
                match = re.search(pattern, line)
                
                if match:
                    username = match.group(1)
                    terminal = match.group(2)
                    date = match.group(3)
                    login_time = match.group(4)
                    pid = match.group(5)
                    ip_raw = match.group(6).strip()
                    
                    # 处理 IP 显示格式
                    ip = self._normalize_ip(ip_raw)
                    
                    # 只处理 pts 终端（SSH 登录通常是 pts）
                    if terminal.startswith('pts/'):
                        session = SSHSession(
                            username=username,
                            terminal=terminal,
                            login_time=f"{date} {login_time}",
                            ip=ip,
                            pid=pid
                        )
                        sessions[session.session_id] = session
                        
            except Exception as e:
                self.logger.debug(f"解析行失败: {line} - {e}")
                continue
        
        return sessions
    
    def _parse_ss_output(self, output: str) -> Dict[str, str]:
        """
        解析 ss 命令输出，辅助获取更准确的 IP 信息
        
        ss -tnpa | grep sshd 输出示例：
        LISTEN  0  128  0.0.0.0:22  0.0.0.0:*  users:(("sshd",pid=1234,fd=3))
        ESTAB   0  0  192.168.1.10:22  192.168.1.100:54321  users:(("sshd",pid=12345,fd=3),("sshd",pid=12346,fd=3))
        """
        pid_to_ip = {}
        
        for line in output.strip().split('\n'):
            if 'ESTAB' not in line or 'sshd' not in line:
                continue
            
            try:
                # 提取客户端 IP
                # 格式：ESTAB ... 本地IP:22  远程IP:端口 ...
                parts = line.split()
                if len(parts) >= 5:
                    local_addr = parts[4]  # 本地地址
                    remote_addr = parts[5]  # 远程地址
                    
                    # 提取远程 IP（去掉端口）
                    remote_ip = remote_addr.rsplit(':', 1)[0]
                    
                    # 提取所有相关 PID
                    pid_matches = re.findall(r'pid=(\d+)', line)
                    for pid in pid_matches:
                        pid_to_ip[pid] = remote_ip
                        
            except Exception as e:
                self.logger.debug(f"解析 ss 输出失败: {line} - {e}")
                continue
        
        return pid_to_ip
    
    def _normalize_ip(self, ip_str: str) -> str:
        """
        规范化 IP 地址显示
        
        Args:
            ip_str: 原始 IP 字符串（可能是 :0、域名、IPv4/IPv6 等）
        
        Returns:
            规范化后的 IP 字符串
        """
        ip_str = ip_str.strip()
        
        # 处理本地显示
        if ip_str == ':0' or ip_str == '::':
            return 'localhost'
        
        # 处理 IPv6 本地地址
        if ip_str == '::1':
            return '127.0.0.1'
        
        # 如果是 IPv4 映射的 IPv6 地址，转换为 IPv4
        if ip_str.startswith('::ffff:'):
            return ip_str[7:]
        
        return ip_str
    
    def _get_current_sessions(self) -> Dict[str, SSHSession]:
        """
        获取当前活跃的 SSH 会话
        
        Returns:
            以 session_id 为键的会话字典
        """
        # 1. 执行 who 命令获取基础会话信息
        who_output = self._run_command(['who', '-u'])
        sessions = self._parse_who_output(who_output)
        
        # 2. 执行 ss 命令获取更精确的网络连接信息
        ss_output = self._run_command(['ss', '-tnpa'])
        ss_output_filtered = '\n'.join(line for line in ss_output.split('\n') if 'sshd' in line)
        pid_to_ip = self._parse_ss_output(ss_output_filtered)
        
        # 3. 用 ss 的信息补充/修正 who 的结果
        for session_id, session in sessions.items():
            if session.pid and session.pid in pid_to_ip:
                # 如果 ss 检测到的 IP 与 who 不同，优先使用 ss 的（更准确）
                ss_ip = pid_to_ip[session.pid]
                if ss_ip != session.ip and ss_ip not in ['0.0.0.0', '::']:
                    session.ip = ss_ip
        
        return sessions
    
    def _compare_sessions(self, old: Dict[str, SSHSession], new: Dict[str, SSHSession]):
        """
        比较两次轮询的会话状态，检测上下线事件
        
        Args:
            old: 上一次轮询的会话字典
            new: 当前轮询的会话字典
        """
        old_keys = set(old.keys())
        new_keys = set(new.keys())
        
        # 检测新上线
        connected = new_keys - old_keys
        for session_id in connected:
            session = new[session_id]
            self.logger.info(
                f"【上线通知】用户 {session.username} 从 IP {session.ip} 登录 "
                f"(终端: {session.terminal}, 时间: {session.login_time})"
            )
        
        # 检测已下线
        disconnected = old_keys - new_keys
        for session_id in disconnected:
            session = old[session_id]
            self.logger.info(
                f"【下线通知】用户 {session.username} 从 IP {session.ip} 断开 "
                f"(终端: {session.terminal}, 登录时间: {session.login_time})"
            )
        
        # 统计信息
        if connected or disconnected:
            self.logger.info(
                f"当前在线会话数: {len(new)} "
                f"(新增: {len(connected)}, 断开: {len(disconnected)})"
            )
    
    def run(self):
        """启动监控主循环"""
        self.logger.info("=" * 60)
        self.logger.info("SSH 连接监控服务启动")
        self.logger.info(f"轮询间隔: {POLL_INTERVAL} 秒")
        self.logger.info(f"日志文件: {LOG_FILE}")
        self.logger.info("=" * 60)
        
        self.running = True
        
        # 首次运行，获取初始状态（不触发通知）
        try:
            self.current_sessions = self._get_current_sessions()
            self.logger.info(f"初始会话数: {len(self.current_sessions)}")
            for session in self.current_sessions.values():
                self.logger.info(f"  - 当前在线: {session.username}@{session.ip} ({session.terminal})")
        except Exception as e:
            self.logger.error(f"获取初始会话失败: {e}")
            self.current_sessions = {}
        
        # 主循环
        loop_count = 0
        while self.running:
            try:
                time.sleep(POLL_INTERVAL)
                
                if not self.running:
                    break
                
                loop_count += 1
                self.logger.debug(f"第 {loop_count} 次轮询开始...")
                
                # 获取最新会话状态
                new_sessions = self._get_current_sessions()
                
                # 对比并检测变化
                self._compare_sessions(self.current_sessions, new_sessions)
                
                # 更新当前状态
                self.current_sessions = new_sessions
                
                # 每 6 次轮询（约 60 秒）输出一次心跳信息
                if loop_count % 6 == 0:
                    self.logger.info(f"[心跳] 监控运行中，当前在线会话数: {len(self.current_sessions)}")
                
            except Exception as e:
                self.logger.error(f"监控循环发生异常: {e}", exc_info=True)
                # 短暂暂停后继续，避免疯狂重试
                time.sleep(1)
        
        self.logger.info("SSH 连接监控服务已停止")


def main():
    """入口函数"""
    # 检查运行权限
    import os
    if os.geteuid() != 0:
        print("警告: 建议以 root 用户运行此脚本，否则可能无法获取完整的 SSH 连接信息")
    
    monitor = SSHMonitor()
    monitor.run()


if __name__ == "__main__":
    main()
