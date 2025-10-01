#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能优化与监控系统
系统性能调优、内存管理、CPU优化、完整监控面板
"""

import asyncio
import logging
import time
import psutil
import gc
import threading
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from collections import deque
import json
import numpy as np
import os

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================================= 性能监控数据模型 =================================

@dataclass
class SystemMetrics:
    """系统性能指标"""
    timestamp: float
    
    # CPU指标
    cpu_percent: float
    cpu_count: int
    cpu_freq: float
    
    # 内存指标
    memory_total: float      # MB
    memory_used: float       # MB
    memory_percent: float
    memory_available: float  # MB
    
    # 进程指标
    process_cpu_percent: float
    process_memory_mb: float
    process_threads: int
    process_open_files: int
    
    # 磁盘指标
    disk_usage_percent: float
    disk_read_mb: float
    disk_write_mb: float
    
    # 网络指标
    network_sent_mb: float
    network_recv_mb: float

@dataclass
class ApplicationMetrics:
    """应用程序性能指标"""
    timestamp: float
    
    # 延迟指标
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    max_latency_ms: float
    
    # 吞吐量指标
    requests_per_second: float
    data_processing_rate: float
    
    # 错误指标
    error_rate: float
    success_rate: float
    
    # 队列指标
    queue_size: int
    queue_wait_time_ms: float
    
    # 缓存指标
    cache_hit_rate: float
    cache_size_mb: float
    
    # 垃圾回收指标
    gc_collections: int
    gc_time_ms: float

@dataclass
class PerformanceAlert:
    """性能警报"""
    timestamp: float
    alert_type: str        # WARNING, CRITICAL
    metric_name: str
    current_value: float
    threshold_value: float
    message: str
    severity: int          # 1-10

# ================================= 性能监控引擎 =================================

class PerformanceMonitor:
    """性能监控引擎"""
    
    def __init__(self, monitoring_interval: float = 1.0):
        """初始化性能监控"""
        self.monitoring_interval = monitoring_interval
        self.is_running = False
        
        # 监控数据
        self.system_metrics_history: deque = deque(maxlen=3600)  # 1小时数据
        self.app_metrics_history: deque = deque(maxlen=3600)
        self.alerts: deque = deque(maxlen=1000)
        
        # 性能阈值
        self.thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'process_memory_mb': 500.0,
            'avg_latency_ms': 200.0,
            'error_rate': 0.05,
            'queue_size': 1000
        }
        
        # 应用指标收集器
        self.latency_samples: deque = deque(maxlen=1000)
        self.request_counter = 0
        self.error_counter = 0
        self.last_request_time = time.time()
        
        # 回调函数
        self.alert_callbacks: List[Callable] = []
        
        # 进程信息
        self.process = psutil.Process()
        self.start_time = time.time()
        
        logger.info("✅ 性能监控引擎初始化完成")
    
    async def start(self):
        """启动性能监控"""
        if self.is_running:
            logger.warning("⚠️ 性能监控已在运行")
            return
        
        self.is_running = True
        
        # 启动监控任务
        system_monitor_task = asyncio.create_task(self._system_monitoring_loop())
        app_monitor_task = asyncio.create_task(self._app_monitoring_loop())
        alert_task = asyncio.create_task(self._alert_monitoring_loop())
        
        logger.info("🚀 性能监控引擎启动成功")
        
        # 等待任务完成
        await asyncio.gather(system_monitor_task, app_monitor_task, alert_task)
    
    async def stop(self):
        """停止性能监控"""
        self.is_running = False
        logger.info("🛑 性能监控引擎已停止")
    
    # ================================= 系统监控 =================================
    
    async def _system_monitoring_loop(self):
        """系统性能监控循环"""
        logger.info("📊 系统性能监控启动")
        
        while self.is_running:
            try:
                # 收集系统指标
                metrics = self._collect_system_metrics()
                self.system_metrics_history.append(metrics)
                
                # 检查系统级警报
                self._check_system_alerts(metrics)
                
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"系统监控错误: {e}")
                await asyncio.sleep(5.0)
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """收集系统性能指标"""
        try:
            # CPU指标
            cpu_percent = psutil.cpu_percent(interval=None)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq().current if psutil.cpu_freq() else 0.0
            
            # 内存指标
            memory = psutil.virtual_memory()
            memory_total = memory.total / (1024 * 1024)  # MB
            memory_used = memory.used / (1024 * 1024)
            memory_percent = memory.percent
            memory_available = memory.available / (1024 * 1024)
            
            # 进程指标
            process_cpu = self.process.cpu_percent()
            process_memory = self.process.memory_info().rss / (1024 * 1024)  # MB
            process_threads = self.process.num_threads()
            
            try:
                process_files = len(self.process.open_files())
            except:
                process_files = 0
            
            # 磁盘指标
            disk_usage = psutil.disk_usage('/')
            disk_percent = disk_usage.percent
            
            disk_io = psutil.disk_io_counters()
            if disk_io:
                disk_read = disk_io.read_bytes / (1024 * 1024)
                disk_write = disk_io.write_bytes / (1024 * 1024)
            else:
                disk_read = disk_write = 0.0
            
            # 网络指标
            net_io = psutil.net_io_counters()
            if net_io:
                network_sent = net_io.bytes_sent / (1024 * 1024)
                network_recv = net_io.bytes_recv / (1024 * 1024)
            else:
                network_sent = network_recv = 0.0
            
            return SystemMetrics(
                timestamp=time.time(),
                cpu_percent=cpu_percent,
                cpu_count=cpu_count,
                cpu_freq=cpu_freq,
                memory_total=memory_total,
                memory_used=memory_used,
                memory_percent=memory_percent,
                memory_available=memory_available,
                process_cpu_percent=process_cpu,
                process_memory_mb=process_memory,
                process_threads=process_threads,
                process_open_files=process_files,
                disk_usage_percent=disk_percent,
                disk_read_mb=disk_read,
                disk_write_mb=disk_write,
                network_sent_mb=network_sent,
                network_recv_mb=network_recv
            )
            
        except Exception as e:
            logger.error(f"系统指标收集失败: {e}")
            # 返回默认值
            return SystemMetrics(
                timestamp=time.time(),
                cpu_percent=0.0, cpu_count=1, cpu_freq=0.0,
                memory_total=0.0, memory_used=0.0, memory_percent=0.0, memory_available=0.0,
                process_cpu_percent=0.0, process_memory_mb=0.0, process_threads=1, process_open_files=0,
                disk_usage_percent=0.0, disk_read_mb=0.0, disk_write_mb=0.0,
                network_sent_mb=0.0, network_recv_mb=0.0
            )
    
    # ================================= 应用监控 =================================
    
    async def _app_monitoring_loop(self):
        """应用性能监控循环"""
        logger.info("⚡ 应用性能监控启动")
        
        while self.is_running:
            try:
                # 收集应用指标
                metrics = self._collect_app_metrics()
                self.app_metrics_history.append(metrics)
                
                # 检查应用级警报
                self._check_app_alerts(metrics)
                
                await asyncio.sleep(self.monitoring_interval * 5)  # 5秒间隔
                
            except Exception as e:
                logger.error(f"应用监控错误: {e}")
                await asyncio.sleep(10.0)
    
    def _collect_app_metrics(self) -> ApplicationMetrics:
        """收集应用性能指标"""
        try:
            current_time = time.time()
            
            # 延迟指标
            latencies = list(self.latency_samples)
            if latencies:
                avg_latency = np.mean(latencies)
                p95_latency = np.percentile(latencies, 95)
                p99_latency = np.percentile(latencies, 99)
                max_latency = np.max(latencies)
            else:
                avg_latency = p95_latency = p99_latency = max_latency = 0.0
            
            # 吞吐量指标
            time_window = current_time - self.last_request_time
            if time_window > 0:
                rps = self.request_counter / max(1, time_window)
            else:
                rps = 0.0
            
            # 错误率
            total_requests = max(1, self.request_counter)
            error_rate = self.error_counter / total_requests
            success_rate = 1.0 - error_rate
            
            # 垃圾回收指标
            gc_stats = gc.get_stats()
            gc_collections = sum(stat['collections'] for stat in gc_stats)
            
            return ApplicationMetrics(
                timestamp=current_time,
                avg_latency_ms=avg_latency,
                p95_latency_ms=p95_latency,
                p99_latency_ms=p99_latency,
                max_latency_ms=max_latency,
                requests_per_second=rps,
                data_processing_rate=rps * 1000,  # 假设每请求1KB
                error_rate=error_rate,
                success_rate=success_rate,
                queue_size=0,  # 待实现
                queue_wait_time_ms=0.0,  # 待实现
                cache_hit_rate=0.95,  # 假设值
                cache_size_mb=10.0,  # 假设值
                gc_collections=gc_collections,
                gc_time_ms=0.0  # 待实现
            )
            
        except Exception as e:
            logger.error(f"应用指标收集失败: {e}")
            # 返回默认值
            return ApplicationMetrics(
                timestamp=time.time(),
                avg_latency_ms=0.0, p95_latency_ms=0.0, p99_latency_ms=0.0, max_latency_ms=0.0,
                requests_per_second=0.0, data_processing_rate=0.0,
                error_rate=0.0, success_rate=1.0,
                queue_size=0, queue_wait_time_ms=0.0,
                cache_hit_rate=1.0, cache_size_mb=0.0,
                gc_collections=0, gc_time_ms=0.0
            )
    
    # ================================= 性能记录 =================================
    
    def record_request_latency(self, latency_ms: float):
        """记录请求延迟"""
        self.latency_samples.append(latency_ms)
        self.request_counter += 1
        self.last_request_time = time.time()
    
    def record_error(self):
        """记录错误"""
        self.error_counter += 1
    
    def record_success(self):
        """记录成功"""
        # success已在request_counter中统计
        pass
    
    # ================================= 警报检查 =================================
    
    def _check_system_alerts(self, metrics: SystemMetrics):
        """检查系统警报"""
        alerts = []
        
        # CPU警报
        if metrics.cpu_percent > self.thresholds['cpu_percent']:
            alerts.append(PerformanceAlert(
                timestamp=metrics.timestamp,
                alert_type="WARNING",
                metric_name="cpu_percent",
                current_value=metrics.cpu_percent,
                threshold_value=self.thresholds['cpu_percent'],
                message=f"CPU使用率过高: {metrics.cpu_percent:.1f}%",
                severity=7 if metrics.cpu_percent > 90 else 5
            ))
        
        # 内存警报
        if metrics.memory_percent > self.thresholds['memory_percent']:
            alerts.append(PerformanceAlert(
                timestamp=metrics.timestamp,
                alert_type="CRITICAL" if metrics.memory_percent > 95 else "WARNING",
                metric_name="memory_percent",
                current_value=metrics.memory_percent,
                threshold_value=self.thresholds['memory_percent'],
                message=f"内存使用率过高: {metrics.memory_percent:.1f}%",
                severity=9 if metrics.memory_percent > 95 else 6
            ))
        
        # 进程内存警报
        if metrics.process_memory_mb > self.thresholds['process_memory_mb']:
            alerts.append(PerformanceAlert(
                timestamp=metrics.timestamp,
                alert_type="WARNING",
                metric_name="process_memory_mb",
                current_value=metrics.process_memory_mb,
                threshold_value=self.thresholds['process_memory_mb'],
                message=f"进程内存使用过高: {metrics.process_memory_mb:.1f}MB",
                severity=6
            ))
        
        # 保存和处理警报
        for alert in alerts:
            self.alerts.append(alert)
            self._handle_alert(alert)
    
    def _check_app_alerts(self, metrics: ApplicationMetrics):
        """检查应用警报"""
        alerts = []
        
        # 延迟警报
        if metrics.avg_latency_ms > self.thresholds['avg_latency_ms']:
            alerts.append(PerformanceAlert(
                timestamp=metrics.timestamp,
                alert_type="WARNING",
                metric_name="avg_latency_ms",
                current_value=metrics.avg_latency_ms,
                threshold_value=self.thresholds['avg_latency_ms'],
                message=f"平均延迟过高: {metrics.avg_latency_ms:.1f}ms",
                severity=7 if metrics.avg_latency_ms > 500 else 5
            ))
        
        # 错误率警报
        if metrics.error_rate > self.thresholds['error_rate']:
            alerts.append(PerformanceAlert(
                timestamp=metrics.timestamp,
                alert_type="CRITICAL" if metrics.error_rate > 0.1 else "WARNING",
                metric_name="error_rate",
                current_value=metrics.error_rate,
                threshold_value=self.thresholds['error_rate'],
                message=f"错误率过高: {metrics.error_rate:.1%}",
                severity=8 if metrics.error_rate > 0.1 else 6
            ))
        
        # 保存和处理警报
        for alert in alerts:
            self.alerts.append(alert)
            self._handle_alert(alert)
    
    def _handle_alert(self, alert: PerformanceAlert):
        """处理警报"""
        # 输出警报
        alert_emoji = "🚨" if alert.alert_type == "CRITICAL" else "⚠️"
        logger.warning(f"{alert_emoji} {alert.message}")
        
        # 触发回调
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"警报回调失败: {e}")
    
    # ================================= 警报监控 =================================
    
    async def _alert_monitoring_loop(self):
        """警报监控循环"""
        while self.is_running:
            try:
                # 自动优化建议
                await self._auto_optimization()
                
                # 每30秒检查一次
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"警报监控错误: {e}")
                await asyncio.sleep(30)
    
    async def _auto_optimization(self):
        """自动优化建议"""
        try:
            if not self.system_metrics_history:
                return
            
            latest_metrics = self.system_metrics_history[-1]
            
            # 内存优化
            if latest_metrics.process_memory_mb > 400:
                logger.info("💡 优化建议: 考虑执行垃圾回收")
                gc.collect()
            
            # CPU优化
            if latest_metrics.cpu_percent > 85:
                logger.info("💡 优化建议: CPU使用率过高，考虑减少并发任务")
            
        except Exception as e:
            logger.error(f"自动优化失败: {e}")
    
    # ================================= 回调管理 =================================
    
    def add_alert_callback(self, callback: Callable):
        """添加警报回调"""
        self.alert_callbacks.append(callback)
    
    # ================================= 状态查询 =================================
    
    def get_performance_summary(self) -> Dict:
        """获取性能摘要"""
        try:
            current_time = time.time()
            uptime = current_time - self.start_time
            
            # 最新指标
            latest_sys = self.system_metrics_history[-1] if self.system_metrics_history else None
            latest_app = self.app_metrics_history[-1] if self.app_metrics_history else None
            
            # 最近警报
            recent_alerts = [asdict(alert) for alert in list(self.alerts)[-10:]]
            
            # 统计信息
            total_requests = self.request_counter
            total_errors = self.error_counter
            success_rate = (total_requests - total_errors) / max(1, total_requests)
            
            return {
                'uptime_seconds': uptime,
                'uptime_human': self._format_uptime(uptime),
                'monitoring_active': self.is_running,
                
                # 系统状态
                'system_status': {
                    'cpu_percent': latest_sys.cpu_percent if latest_sys else 0,
                    'memory_percent': latest_sys.memory_percent if latest_sys else 0,
                    'process_memory_mb': latest_sys.process_memory_mb if latest_sys else 0,
                    'process_threads': latest_sys.process_threads if latest_sys else 0
                } if latest_sys else {},
                
                # 应用状态
                'app_status': {
                    'avg_latency_ms': latest_app.avg_latency_ms if latest_app else 0,
                    'requests_per_second': latest_app.requests_per_second if latest_app else 0,
                    'error_rate': latest_app.error_rate if latest_app else 0,
                    'success_rate': latest_app.success_rate if latest_app else 1
                } if latest_app else {},
                
                # 统计信息
                'statistics': {
                    'total_requests': total_requests,
                    'total_errors': total_errors,
                    'success_rate': success_rate,
                    'metrics_collected': len(self.system_metrics_history),
                    'alerts_generated': len(self.alerts)
                },
                
                # 最近警报
                'recent_alerts': recent_alerts,
                
                # 性能评分
                'performance_score': self._calculate_performance_score(latest_sys, latest_app)
            }
            
        except Exception as e:
            logger.error(f"性能摘要生成失败: {e}")
            return {'error': str(e)}
    
    def _format_uptime(self, seconds: float) -> str:
        """格式化运行时间"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def _calculate_performance_score(self, sys_metrics, app_metrics) -> int:
        """计算性能评分 (0-100)"""
        try:
            score = 100
            
            if sys_metrics:
                # CPU评分 (权重: 20%)
                if sys_metrics.cpu_percent > 80:
                    score -= 20
                elif sys_metrics.cpu_percent > 60:
                    score -= 10
                
                # 内存评分 (权重: 25%)
                if sys_metrics.memory_percent > 90:
                    score -= 25
                elif sys_metrics.memory_percent > 75:
                    score -= 15
                
                # 进程内存评分 (权重: 15%)
                if sys_metrics.process_memory_mb > 500:
                    score -= 15
                elif sys_metrics.process_memory_mb > 300:
                    score -= 8
            
            if app_metrics:
                # 延迟评分 (权重: 20%)
                if app_metrics.avg_latency_ms > 500:
                    score -= 20
                elif app_metrics.avg_latency_ms > 200:
                    score -= 10
                
                # 错误率评分 (权重: 20%)
                if app_metrics.error_rate > 0.1:
                    score -= 20
                elif app_metrics.error_rate > 0.05:
                    score -= 10
            
            return max(0, score)
            
        except:
            return 50  # 默认评分
    
    def print_performance_dashboard(self):
        """打印性能仪表板"""
        summary = self.get_performance_summary()
        
        print("\n" + "="*60)
        print("📊 性能监控仪表板")
        print("="*60)
        
        # 基本信息
        print(f"🕐 运行时间: {summary.get('uptime_human', 'N/A')}")
        print(f"📈 性能评分: {summary.get('performance_score', 0)}/100")
        print(f"🔄 监控状态: {'✅ 活跃' if summary.get('monitoring_active', False) else '❌ 停止'}")
        
        # 系统状态
        sys_status = summary.get('system_status', {})
        if sys_status:
            print(f"\n💻 系统状态:")
            print(f"   CPU使用率: {sys_status.get('cpu_percent', 0):.1f}%")
            print(f"   内存使用率: {sys_status.get('memory_percent', 0):.1f}%")
            print(f"   进程内存: {sys_status.get('process_memory_mb', 0):.1f}MB")
            print(f"   线程数: {sys_status.get('process_threads', 0)}")
        
        # 应用状态
        app_status = summary.get('app_status', {})
        if app_status:
            print(f"\n⚡ 应用状态:")
            print(f"   平均延迟: {app_status.get('avg_latency_ms', 0):.2f}ms")
            print(f"   请求速率: {app_status.get('requests_per_second', 0):.1f}/s")
            print(f"   错误率: {app_status.get('error_rate', 0):.1%}")
            print(f"   成功率: {app_status.get('success_rate', 1):.1%}")
        
        # 统计信息
        stats = summary.get('statistics', {})
        print(f"\n📊 统计信息:")
        print(f"   总请求数: {stats.get('total_requests', 0)}")
        print(f"   总错误数: {stats.get('total_errors', 0)}")
        print(f"   成功率: {stats.get('success_rate', 1):.1%}")
        print(f"   警报数: {stats.get('alerts_generated', 0)}")
        
        # 最近警报
        recent_alerts = summary.get('recent_alerts', [])
        if recent_alerts:
            print(f"\n⚠️ 最近警报:")
            for alert in recent_alerts[-3:]:  # 显示最近3个警报
                alert_time = datetime.fromtimestamp(alert['timestamp']).strftime('%H:%M:%S')
                print(f"   [{alert_time}] {alert['message']}")
        
        print("="*60)

# ================================= 全局监控实例 =================================

_global_performance_monitor: Optional[PerformanceMonitor] = None

def get_performance_monitor() -> PerformanceMonitor:
    """获取全局性能监控实例"""
    global _global_performance_monitor
    if _global_performance_monitor is None:
        _global_performance_monitor = PerformanceMonitor()
    return _global_performance_monitor

async def start_performance_monitoring():
    """启动全局性能监控"""
    monitor = get_performance_monitor()
    if not monitor.is_running:
        asyncio.create_task(monitor.start())
    return monitor

async def stop_performance_monitoring():
    """停止全局性能监控"""
    monitor = get_performance_monitor()
    await monitor.stop()

def print_performance_dashboard():
    """打印性能仪表板"""
    monitor = get_performance_monitor()
    monitor.print_performance_dashboard()

# ================================= 测试代码 =================================

async def test_performance_monitor():
    """测试性能监控系统"""
    print("🧪 开始测试性能监控系统...")
    
    # 创建监控器
    monitor = PerformanceMonitor(monitoring_interval=0.5)
    
    # 添加警报回调
    def alert_handler(alert):
        print(f"🚨 收到警报: {alert.message}")
    
    monitor.add_alert_callback(alert_handler)
    
    # 启动测试任务
    async def test_scenario():
        await asyncio.sleep(2)
        
        print("\n1. 模拟正常请求...")
        for i in range(20):
            monitor.record_request_latency(np.random.uniform(10, 50))
            await asyncio.sleep(0.1)
        
        print("\n2. 模拟高延迟请求...")
        for i in range(5):
            monitor.record_request_latency(np.random.uniform(200, 300))
            monitor.record_error()  # 模拟一些错误
            await asyncio.sleep(0.2)
        
        print("\n3. 等待监控数据收集...")
        await asyncio.sleep(3)
        
        # 打印性能仪表板
        print("\n4. 性能仪表板:")
        monitor.print_performance_dashboard()
        
        await monitor.stop()
    
    # 并行运行监控器和测试
    try:
        await asyncio.gather(
            monitor.start(),
            test_scenario()
        )
    except Exception as e:
        print(f"测试出错: {e}")
    
    print("\n✅ 性能监控系统测试完成")

if __name__ == "__main__":
    asyncio.run(test_performance_monitor())