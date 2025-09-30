"""
实时风险监控系统

提供7×24小时实时风险监控，追踪日内亏损、最大回撤、连续亏损等
关键风险指标，设置日亏损<2%的硬限制，确保交易系统安全运行。

核心功能：
1. 实时风险指标监控
2. 自动风险预警机制
3. 紧急止损触发
4. 风险事件记录
5. 风险报告生成
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Tuple
import logging
import threading
import time
import json

from . import RiskLevel, RiskMetrics, RiskLimits


@dataclass
class RiskAlert:
    """风险警报数据类"""
    alert_id: str
    alert_type: str
    severity: RiskLevel
    message: str
    timestamp: datetime
    current_value: float
    threshold_value: float
    symbol: Optional[str] = None
    resolved: bool = False
    resolved_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'alert_id': self.alert_id,
            'alert_type': self.alert_type,
            'severity': self.severity.value,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'current_value': self.current_value,
            'threshold_value': self.threshold_value,
            'symbol': self.symbol,
            'resolved': self.resolved,
            'resolved_time': self.resolved_time.isoformat() if self.resolved_time else None
        }


@dataclass
class RiskEvent:
    """风险事件记录"""
    event_id: str
    event_type: str
    description: str
    timestamp: datetime
    risk_level: RiskLevel
    affected_positions: List[str] = field(default_factory=list)
    actions_taken: List[str] = field(default_factory=list)
    financial_impact: float = 0.0
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'description': self.description,
            'timestamp': self.timestamp.isoformat(),
            'risk_level': self.risk_level.value,
            'affected_positions': self.affected_positions,
            'actions_taken': self.actions_taken,
            'financial_impact': self.financial_impact
        }


class RiskMonitor:
    """
    实时风险监控器
    
    负责持续监控交易系统的风险状态，识别潜在风险，
    触发警报和自动保护机制，记录风险事件。
    """
    
    def __init__(self, risk_limits: RiskLimits = None, check_interval: int = 5):
        self.risk_limits = risk_limits or RiskLimits()
        self.check_interval = check_interval  # 检查间隔（秒）
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 监控状态
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # 风险数据
        self.current_metrics = RiskMetrics()
        self.risk_alerts: List[RiskAlert] = []
        self.risk_events: List[RiskEvent] = []
        
        # 回调函数
        self.alert_callbacks: List[Callable] = []
        self.emergency_callbacks: List[Callable] = []
        
        # 历史记录
        self.metrics_history: List[Tuple[datetime, RiskMetrics]] = []
        self.daily_start_value = 0.0
        self.session_start_time = datetime.now()
        
        # 统计数据
        self.total_alerts = 0
        self.resolved_alerts = 0
        self.emergency_stops = 0
        
        self.logger.info("风险监控器初始化完成")
    
    def start_monitoring(self):
        """启动风险监控"""
        if self.monitoring:
            self.logger.warning("风险监控已在运行中")
            return
        
        self.monitoring = True
        self.session_start_time = datetime.now()
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        self.logger.info("风险监控已启动")
    
    def stop_monitoring(self):
        """停止风险监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
        
        self.logger.info("风险监控已停止")
    
    def _monitoring_loop(self):
        """监控主循环"""
        while self.monitoring:
            try:
                self._check_risk_conditions()
                time.sleep(self.check_interval)
            except Exception as e:
                self.logger.error("监控循环错误: %s", e)
                time.sleep(self.check_interval)
    
    def update_metrics(self, new_metrics: RiskMetrics):
        """更新风险指标"""
        self.current_metrics = new_metrics
        
        # 记录历史
        self.metrics_history.append((datetime.now(), new_metrics))
        
        # 限制历史记录长度
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
        
        # 设置日开始价值
        if self.daily_start_value == 0:
            self.daily_start_value = new_metrics.account_value
    
    def _check_risk_conditions(self):
        """检查风险条件"""
        if not self.current_metrics:
            return
        
        # 检查日亏损限制
        self._check_daily_loss_limit()
        
        # 检查最大回撤
        self._check_max_drawdown()
        
        # 检查连续亏损
        self._check_consecutive_losses()
        
        # 检查仓位集中度
        self._check_position_concentration()
        
        # 检查账户价值
        self._check_account_value()
        
        # 检查VaR超限
        self._check_var_breach()
    
    def _check_daily_loss_limit(self):
        """检查日亏损限制"""
        if self.daily_start_value <= 0:
            return
        
        daily_loss_pct = abs(self.current_metrics.daily_pnl) / self.daily_start_value
        
        # 警告阈值：80%的限制
        warning_threshold = self.risk_limits.max_daily_loss_pct * 0.8
        if daily_loss_pct >= warning_threshold and daily_loss_pct < self.risk_limits.max_daily_loss_pct:
            self._create_alert(
                "daily_loss_warning",
                RiskLevel.HIGH,
                f"日亏损接近限制: {daily_loss_pct:.2%} (限制: {self.risk_limits.max_daily_loss_pct:.2%})",
                daily_loss_pct,
                self.risk_limits.max_daily_loss_pct
            )
        
        # 超限触发紧急停止
        elif daily_loss_pct >= self.risk_limits.max_daily_loss_pct:
            self._trigger_emergency_stop(
                "daily_loss_limit",
                f"日亏损超限: {daily_loss_pct:.2%}",
                daily_loss_pct
            )
    
    def _check_max_drawdown(self):
        """检查最大回撤"""
        max_drawdown_threshold = 0.05  # 5%最大回撤阈值
        
        if self.current_metrics.max_drawdown >= max_drawdown_threshold:
            self._create_alert(
                "max_drawdown",
                RiskLevel.HIGH,
                f"最大回撤过大: {self.current_metrics.max_drawdown:.2%}",
                self.current_metrics.max_drawdown,
                max_drawdown_threshold
            )
    
    def _check_consecutive_losses(self):
        """检查连续亏损"""
        if self.current_metrics.consecutive_losses >= self.risk_limits.max_consecutive_losses:
            self._trigger_emergency_stop(
                "consecutive_losses",
                f"连续亏损达到限制: {self.current_metrics.consecutive_losses}次",
                self.current_metrics.consecutive_losses
            )
        elif self.current_metrics.consecutive_losses >= self.risk_limits.max_consecutive_losses * 0.8:
            self._create_alert(
                "consecutive_losses_warning",
                RiskLevel.MODERATE,
                f"连续亏损较多: {self.current_metrics.consecutive_losses}次",
                self.current_metrics.consecutive_losses,
                self.risk_limits.max_consecutive_losses
            )
    
    def _check_position_concentration(self):
        """检查仓位集中度"""
        position_pct = self.current_metrics.position_value / self.current_metrics.account_value
        
        if position_pct > 0.9:  # 90%仓位警告
            self._create_alert(
                "high_position_concentration",
                RiskLevel.MODERATE,
                f"仓位集中度过高: {position_pct:.1%}",
                position_pct,
                0.9
            )
    
    def _check_account_value(self):
        """检查账户价值"""
        if self.current_metrics.account_value < self.risk_limits.min_account_value:
            self._trigger_emergency_stop(
                "low_account_value",
                f"账户价值过低: ${self.current_metrics.account_value:,.2f}",
                self.current_metrics.account_value
            )
    
    def _check_var_breach(self):
        """检查VaR超限"""
        if self.current_metrics.var_95 > 0:
            var_threshold = self.current_metrics.account_value * 0.03  # 3% VaR阈值
            
            if self.current_metrics.var_95 > var_threshold:
                self._create_alert(
                    "var_breach",
                    RiskLevel.HIGH,
                    f"VaR超限: ${self.current_metrics.var_95:,.2f} (阈值: ${var_threshold:,.2f})",
                    self.current_metrics.var_95,
                    var_threshold
                )
    
    def _create_alert(self, alert_type: str, severity: RiskLevel, message: str,
                     current_value: float, threshold_value: float, symbol: str = None):
        """创建风险警报"""
        alert_id = f"{alert_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        alert = RiskAlert(
            alert_id=alert_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            timestamp=datetime.now(),
            current_value=current_value,
            threshold_value=threshold_value,
            symbol=symbol
        )
        
        self.risk_alerts.append(alert)
        self.total_alerts += 1
        
        self.logger.warning("风险警报: %s", message)
        
        # 触发回调
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.logger.error("警报回调错误: %s", e)
    
    def _trigger_emergency_stop(self, event_type: str, description: str, impact_value: float):
        """触发紧急停止"""
        event_id = f"emergency_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        event = RiskEvent(
            event_id=event_id,
            event_type=event_type,
            description=description,
            timestamp=datetime.now(),
            risk_level=RiskLevel.CRITICAL,
            financial_impact=impact_value
        )
        
        self.risk_events.append(event)
        self.emergency_stops += 1
        
        self.logger.critical("紧急停止触发: %s", description)
        
        # 触发紧急回调
        for callback in self.emergency_callbacks:
            try:
                callback(event)
            except Exception as e:
                self.logger.error("紧急停止回调错误: %s", e)
    
    def resolve_alert(self, alert_id: str, resolution_note: str = ""):
        """解决风险警报"""
        for alert in self.risk_alerts:
            if alert.alert_id == alert_id and not alert.resolved:
                alert.resolved = True
                alert.resolved_time = datetime.now()
                self.resolved_alerts += 1
                
                self.logger.info("警报已解决: %s - %s", alert_id, resolution_note)
                return True
        
        return False
    
    def add_alert_callback(self, callback: Callable):
        """添加警报回调函数"""
        self.alert_callbacks.append(callback)
    
    def add_emergency_callback(self, callback: Callable):
        """添加紧急停止回调函数"""
        self.emergency_callbacks.append(callback)
    
    def get_active_alerts(self) -> List[RiskAlert]:
        """获取活跃警报"""
        return [alert for alert in self.risk_alerts if not alert.resolved]
    
    def get_risk_dashboard(self) -> Dict:
        """获取风险监控面板数据"""
        active_alerts = self.get_active_alerts()
        
        return {
            'monitoring_status': self.monitoring,
            'session_duration': (datetime.now() - self.session_start_time).total_seconds() / 3600,
            'current_risk_level': self.current_metrics.risk_level.value,
            'current_metrics': self.current_metrics.to_dict(),
            'active_alerts_count': len(active_alerts),
            'total_alerts': self.total_alerts,
            'resolved_alerts': self.resolved_alerts,
            'emergency_stops': self.emergency_stops,
            'active_alerts': [alert.to_dict() for alert in active_alerts[-10:]],  # 最近10个
            'risk_events': [event.to_dict() for event in self.risk_events[-5:]]    # 最近5个事件
        }
    
    def generate_risk_report(self, hours: int = 24) -> Dict:
        """生成风险报告"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # 筛选时间范围内的数据
        recent_alerts = [alert for alert in self.risk_alerts if alert.timestamp >= cutoff_time]
        recent_events = [event for event in self.risk_events if event.timestamp >= cutoff_time]
        recent_metrics = [m for t, m in self.metrics_history if t >= cutoff_time]
        
        # 计算统计数据
        if recent_metrics:
            max_account_value = max(m.account_value for m in recent_metrics)
            min_account_value = min(m.account_value for m in recent_metrics)
            max_drawdown = max(m.max_drawdown for m in recent_metrics)
            avg_daily_pnl = sum(m.daily_pnl for m in recent_metrics) / len(recent_metrics)
        else:
            max_account_value = min_account_value = max_drawdown = avg_daily_pnl = 0
        
        return {
            'report_period_hours': hours,
            'generated_time': datetime.now().isoformat(),
            'summary': {
                'total_alerts': len(recent_alerts),
                'resolved_alerts': len([a for a in recent_alerts if a.resolved]),
                'emergency_events': len(recent_events),
                'max_account_value': max_account_value,
                'min_account_value': min_account_value,
                'max_drawdown': max_drawdown,
                'avg_daily_pnl': avg_daily_pnl
            },
            'alerts_by_type': self._group_alerts_by_type(recent_alerts),
            'risk_level_distribution': self._analyze_risk_levels(recent_metrics),
            'recommendations': self._generate_recommendations()
        }
    
    def _group_alerts_by_type(self, alerts: List[RiskAlert]) -> Dict:
        """按类型分组警报"""
        groups = {}
        for alert in alerts:
            if alert.alert_type not in groups:
                groups[alert.alert_type] = []
            groups[alert.alert_type].append(alert.to_dict())
        return groups
    
    def _analyze_risk_levels(self, metrics: List[RiskMetrics]) -> Dict:
        """分析风险等级分布"""
        if not metrics:
            return {}
        
        level_counts = {}
        for metric in metrics:
            level = metric.risk_level.value
            level_counts[level] = level_counts.get(level, 0) + 1
        
        total = len(metrics)
        return {level: count/total for level, count in level_counts.items()}
    
    def _generate_recommendations(self) -> List[str]:
        """生成风险建议"""
        recommendations = []
        
        if self.current_metrics.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            recommendations.append("当前风险等级较高，建议减少仓位或暂停交易")
        
        if self.current_metrics.consecutive_losses >= 3:
            recommendations.append("连续亏损较多，建议检查策略有效性")
        
        if self.current_metrics.max_drawdown > 0.03:
            recommendations.append("回撤较大，建议调整止损策略")
        
        active_alerts = self.get_active_alerts()
        if len(active_alerts) > 5:
            recommendations.append("活跃警报较多，建议及时处理风险问题")
        
        return recommendations
    
    def export_risk_data(self, filename: str = None) -> str:
        """导出风险数据"""
        if not filename:
            filename = f"risk_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data = {
            'export_time': datetime.now().isoformat(),
            'current_metrics': self.current_metrics.to_dict(),
            'risk_limits': self.risk_limits.__dict__,
            'alerts': [alert.to_dict() for alert in self.risk_alerts],
            'events': [event.to_dict() for event in self.risk_events],
            'statistics': {
                'total_alerts': self.total_alerts,
                'resolved_alerts': self.resolved_alerts,
                'emergency_stops': self.emergency_stops,
                'session_duration_hours': (datetime.now() - self.session_start_time).total_seconds() / 3600
            }
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.logger.info("风险数据已导出到: %s", filename)
        return filename
    
    def reset_daily_monitoring(self):
        """重置日监控数据（每日开盘前调用）"""
        self.daily_start_value = self.current_metrics.account_value
        self.current_metrics.daily_pnl = 0.0
        
        # 解决所有日相关的警报
        for alert in self.risk_alerts:
            if not alert.resolved and 'daily' in alert.alert_type:
                alert.resolved = True
                alert.resolved_time = datetime.now()
                self.resolved_alerts += 1
        
        self.logger.info("日监控数据已重置")


# 使用示例
if __name__ == "__main__":
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🔍 实时风险监控系统演示")
    print("=" * 50)
    
    # 创建风险监控器
    risk_monitor = RiskMonitor(check_interval=1)  # 1秒检查间隔（演示用）
    
    # 添加回调函数
    def alert_handler(alert: RiskAlert):
        print(f"⚠️ 风险警报: {alert.message}")
    
    def emergency_handler(event: RiskEvent):
        print(f"🚨 紧急事件: {event.description}")
    
    risk_monitor.add_alert_callback(alert_handler)
    risk_monitor.add_emergency_callback(emergency_handler)
    
    # 启动监控
    risk_monitor.start_monitoring()
    
    # 模拟风险指标更新
    test_metrics = RiskMetrics(
        account_value=95000,  # 模拟亏损
        daily_pnl=-5000,     # 日亏损
        consecutive_losses=3,
        risk_level=RiskLevel.HIGH
    )
    
    risk_monitor.update_metrics(test_metrics)
    
    # 等待监控检查
    time.sleep(2)
    
    # 获取监控面板
    dashboard = risk_monitor.get_risk_dashboard()
    print(f"\\n监控状态: {'运行中' if dashboard['monitoring_status'] else '已停止'}")
    print(f"当前风险等级: {dashboard['current_risk_level']}")
    print(f"活跃警报数量: {dashboard['active_alerts_count']}")
    
    # 停止监控
    risk_monitor.stop_monitoring()
    
    print("\\n⚠️ 风险监控功能:")
    print("- 7×24小时实时监控")
    print("- 自动风险预警")
    print("- 紧急止损保护")
    print("- 风险事件记录")
    print("- 监控报告生成")