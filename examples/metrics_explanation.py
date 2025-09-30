#!/usr/bin/env python3
"""
量化交易关键指标解释和可视化
Key Metrics Explanation and Visualization

详细解释最大回撤和夏普比率的含义，并提供可视化示例
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import math

def generate_sample_returns():
    """生成示例收益数据"""
    
    # 设置随机种子确保结果可重现
    np.random.seed(42)
    
    # 生成252个交易日的数据（一年）
    days = 252
    dates = pd.date_range(start='2024-01-01', periods=days, freq='B')
    
    # 模拟策略收益率（日收益率）
    # 假设年化收益18%，日收益约0.071%，波动率15%
    daily_return_mean = 0.18 / 252  # 年化18%转日收益
    daily_volatility = 0.15 / math.sqrt(252)  # 年化波动15%转日波动
    
    # 生成正态分布的日收益率
    daily_returns = np.random.normal(daily_return_mean, daily_volatility, days)
    
    # 添加一些市场冲击模拟
    # 在第100天和第180天模拟市场下跌
    daily_returns[100:105] = [-0.03, -0.025, -0.02, -0.015, -0.01]  # 连续下跌
    daily_returns[180:185] = [-0.025, -0.02, -0.018, -0.012, -0.008]  # 另一次下跌
    
    return dates, daily_returns

def calculate_performance_metrics(returns):
    """计算性能指标"""
    
    # 转换为累计收益
    cumulative_returns = (1 + pd.Series(returns)).cumprod()
    cumulative_pct = (cumulative_returns - 1) * 100
    
    # 计算最大回撤
    peak = cumulative_returns.expanding().max()
    drawdown = (cumulative_returns - peak) / peak
    max_drawdown = drawdown.min() * 100  # 转换为百分比
    
    # 计算夏普比率
    annual_return = (cumulative_returns.iloc[-1] ** (252/len(returns)) - 1) * 100
    annual_volatility = pd.Series(returns).std() * math.sqrt(252) * 100
    risk_free_rate = 3.0  # 假设无风险利率3%
    sharpe_ratio = (annual_return - risk_free_rate) / annual_volatility
    
    # 其他指标
    total_return = (cumulative_returns.iloc[-1] - 1) * 100
    win_rate = (pd.Series(returns) > 0).mean() * 100
    
    return {
        'cumulative_returns': cumulative_returns,
        'cumulative_pct': cumulative_pct,
        'drawdown': drawdown * 100,
        'max_drawdown': max_drawdown,
        'annual_return': annual_return,
        'annual_volatility': annual_volatility,
        'sharpe_ratio': sharpe_ratio,
        'total_return': total_return,
        'win_rate': win_rate
    }

def explain_maximum_drawdown():
    """解释最大回撤"""
    
    print("📊 最大回撤 (Maximum Drawdown) 详解")
    print("=" * 60)
    
    print("\n🔍 定义:")
    print("最大回撤是投资组合从历史最高点到随后最低点的最大跌幅")
    
    print("\n💡 计算公式:")
    print("最大回撤 = (峰值净值 - 谷底净值) / 峰值净值 × 100%")
    
    print("\n📈 示例:")
    example_data = [
        ("2024-01-01", 100000, 0, "初始资金"),
        ("2024-03-15", 115000, 15.0, "盈利15%"),
        ("2024-06-20", 125000, 25.0, "创新高，盈利25%"),
        ("2024-08-10", 118000, 18.0, "回调，仍盈利18%"),
        ("2024-09-05", 115000, 15.0, "继续回调"),
        ("2024-10-01", 122000, 22.0, "重新上涨")
    ]
    
    print("   日期      |   账户价值  |  收益率  |    说明")
    print("   " + "-" * 50)
    for date, value, return_pct, desc in example_data:
        print(f"   {date}  |  ${value:,}  |  {return_pct:+5.1f}%  |  {desc}")
    
    print(f"\n   峰值: $125,000 (6月20日)")
    print(f"   谷底: $115,000 (9月5日)")
    print(f"   最大回撤: ($125,000 - $115,000) / $125,000 = 8.0%")
    
    print("\n⚠️ 重要意义:")
    print("• 风险控制: 回撤<8%说明在最坏情况下损失有限")
    print("• 心理承受: 帮助投资者了解可能面临的最大亏损")
    print("• 策略评估: 优秀策略通常最大回撤<10%")
    print("• 资金管理: 回撤小意味着资金保护能力强")

def explain_sharpe_ratio():
    """解释夏普比率"""
    
    print("\n📊 夏普比率 (Sharpe Ratio) 详解")
    print("=" * 60)
    
    print("\n🔍 定义:")
    print("夏普比率衡量每单位风险所获得的超额收益，反映风险调整后的收益水平")
    
    print("\n💡 计算公式:")
    print("夏普比率 = (策略年化收益率 - 无风险利率) / 策略收益率标准差")
    
    print("\n📈 示例计算:")
    strategies = [
        ("保守策略", 8, 2, 5),
        ("平衡策略", 15, 3, 10),
        ("激进策略", 25, 3, 20),
        ("优质策略", 18, 3, 10)
    ]
    
    print("   策略类型    |  年化收益  |  无风险利率  |  波动率  |  夏普比率  |  评级")
    print("   " + "-" * 70)
    
    for name, annual_return, risk_free, volatility in strategies:
        sharpe = (annual_return - risk_free) / volatility
        
        if sharpe >= 2.0:
            rating = "卓越⭐⭐⭐⭐⭐"
        elif sharpe >= 1.5:
            rating = "优秀⭐⭐⭐⭐"
        elif sharpe >= 1.0:
            rating = "良好⭐⭐⭐"
        elif sharpe >= 0.5:
            rating = "一般⭐⭐"
        else:
            rating = "较差⭐"
        
        print(f"   {name:8}  |    {annual_return:2d}%    |     {risk_free}%      |   {volatility:2d}%   |   {sharpe:4.2f}    |  {rating}")
    
    print("\n📊 夏普比率分级:")
    print("• < 0.5  : 较差，风险调整后收益不理想")
    print("• 0.5-1.0: 一般，收益勉强覆盖风险")
    print("• 1.0-1.5: 良好，较好的风险收益比")
    print("• 1.5-2.0: 优秀，高风险调整后收益")
    print("• > 2.0  : 卓越，极少策略能达到")
    
    print("\n🎯 实际意义:")
    print("• 夏普比率>1.5意味着每承担1单位风险，获得1.5单位以上超额收益")
    print("• 考虑了风险因素，比单纯看收益率更全面")
    print("• 便于不同策略之间的比较")
    print("• 是机构投资者评估策略的重要指标")

def visualize_performance_metrics():
    """可视化性能指标"""
    
    print("\n📈 性能指标可视化")
    print("=" * 60)
    
    # 生成示例数据
    dates, returns = generate_sample_returns()
    metrics = calculate_performance_metrics(returns)
    
    # 创建图表
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('量化交易策略性能分析', fontsize=16, fontweight='bold')
    
    # 1. 累计收益曲线
    ax1.plot(dates, metrics['cumulative_pct'], 'b-', linewidth=2, label='策略收益')
    ax1.axhline(y=0, color='k', linestyle='--', alpha=0.5)
    ax1.set_title('累计收益率曲线')
    ax1.set_ylabel('收益率 (%)')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # 2. 回撤曲线
    ax2.fill_between(dates, metrics['drawdown'], 0, alpha=0.3, color='red', label='回撤区域')
    ax2.plot(dates, metrics['drawdown'], 'r-', linewidth=1)
    ax2.axhline(y=metrics['max_drawdown'], color='darkred', linestyle='--', 
                label=f'最大回撤: {metrics["max_drawdown"]:.1f}%')
    ax2.set_title('回撤分析')
    ax2.set_ylabel('回撤 (%)')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # 3. 收益分布直方图
    ax3.hist(np.array(returns) * 100, bins=30, alpha=0.7, color='blue', edgecolor='black')
    ax3.axvline(x=np.mean(returns) * 100, color='red', linestyle='--', 
                label=f'平均日收益: {np.mean(returns)*100:.3f}%')
    ax3.set_title('日收益率分布')
    ax3.set_xlabel('日收益率 (%)')
    ax3.set_ylabel('频数')
    ax3.grid(True, alpha=0.3)
    ax3.legend()
    
    # 4. 关键指标总结
    ax4.axis('off')
    
    # 准备指标文本
    metrics_text = f"""
关键性能指标 (Key Metrics)

总收益率: {metrics['total_return']:.1f}%
年化收益率: {metrics['annual_return']:.1f}%
年化波动率: {metrics['annual_volatility']:.1f}%

最大回撤: {metrics['max_drawdown']:.1f}%
夏普比率: {metrics['sharpe_ratio']:.2f}
胜率: {metrics['win_rate']:.1f}%

策略评级: {'优秀⭐⭐⭐⭐' if metrics['sharpe_ratio'] > 1.5 and abs(metrics['max_drawdown']) < 8 else '良好⭐⭐⭐'}
风险等级: {'低风险' if abs(metrics['max_drawdown']) < 5 else '中风险' if abs(metrics['max_drawdown']) < 10 else '高风险'}
"""
    
    ax4.text(0.1, 0.9, metrics_text, transform=ax4.transAxes, fontsize=11,
             verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
    
    plt.tight_layout()
    
    # 保存图表
    try:
        plt.savefig('performance_metrics_analysis.png', dpi=300, bbox_inches='tight')
        print("📊 图表已保存为: performance_metrics_analysis.png")
    except Exception as e:
        print(f"⚠️ 图表保存失败: {e}")
    
    try:
        plt.show()
    except:
        print("ℹ️ 无法显示图表（可能是无GUI环境）")
    
    return metrics

def show_real_world_examples():
    """展示真实案例"""
    
    print("\n🌍 真实世界案例")
    print("=" * 60)
    
    famous_strategies = [
        {
            "名称": "巴菲特伯克希尔",
            "年化收益": "20.0%",
            "最大回撤": "54%",
            "夏普比率": "0.76",
            "评价": "长期优秀，但回撤较大"
        },
        {
            "名称": "桥水全天候",
            "年化收益": "7.7%", 
            "最大回撤": "3.9%",
            "夏普比率": "0.48",
            "评价": "低风险稳健策略"
        },
        {
            "名称": "量化对冲基金",
            "年化收益": "15.2%",
            "最大回撤": "6.8%",
            "夏普比率": "1.89",
            "评价": "优秀的风险调整收益"
        },
        {
            "名称": "市场指数SPY",
            "年化收益": "10.5%",
            "最大回撤": "33.7%",
            "夏普比率": "0.42",
            "评价": "市场基准表现"
        }
    ]
    
    print("策略/基金          | 年化收益 | 最大回撤 | 夏普比率 | 评价")
    print("-" * 65)
    
    for strategy in famous_strategies:
        print(f"{strategy['名称']:15} | {strategy['年化收益']:8} | {strategy['最大回撤']:8} | {strategy['夏普比率']:8} | {strategy['评价']}")
    
    print(f"\n💡 分析:")
    print("• 最大回撤<8%的策略风险控制优秀，能在市场动荡中保护资金")
    print("• 夏普比率>1.5的策略提供了出色的风险调整后收益")
    print("• 我们的目标(年化15-25%, 回撤<8%, 夏普>1.5)属于顶级水平")
    print("• 这样的指标在实际投资中非常难得，需要精心的策略设计")

def practical_implications():
    """实际应用含义"""
    
    print("\n💼 实际投资含义")
    print("=" * 60)
    
    print("🎯 对于投资者的意义:")
    print("• 最大回撤<8%: 即使在最坏情况下，资金损失也控制在8%以内")
    print("• 夏普比率>1.5: 承担的风险得到了充分的收益补偿")
    print("• 两者结合: 既有较高收益，又有较强的风险控制能力")
    
    print(f"\n💰 资金安全性:")
    print("• 如果投资$100,000，最大可能亏损约$8,000")
    print("• 相比股票指数30%+的回撤，这是非常保守的")
    print("• 适合风险厌恶但又希望获得超额收益的投资者")
    
    print(f"\n📊 与其他投资对比:")
    print("• 银行定存: 年化3-4%, 回撤0%, 夏普比率约0.5-1.0")
    print("• 股票指数: 年化8-12%, 回撤20-40%, 夏普比率约0.3-0.6")
    print("• 优秀量化策略: 年化15-25%, 回撤<8%, 夏普比率>1.5")
    print("• 可见量化策略在风险调整后的收益上有明显优势")
    
    print(f"\n⚠️ 注意事项:")
    print("• 历史表现不代表未来收益")
    print("• 量化策略可能在特定市场环境下失效")
    print("• 需要持续监控和适时调整")
    print("• 建议分散投资，不要把所有资金投入单一策略")

def main():
    """主函数"""
    
    print("📊 量化交易关键指标详解")
    print("🎯 最大回撤 vs 夏普比率")
    print("=" * 80)
    
    # 详细解释各个指标
    explain_maximum_drawdown()
    explain_sharpe_ratio()
    
    # 可视化演示
    metrics = visualize_performance_metrics()
    
    # 真实案例
    show_real_world_examples()
    
    # 实际应用含义
    practical_implications()
    
    print(f"\n" + "=" * 80)
    print("🎉 总结")
    print("=" * 80)
    
    print("🎯 最大回撤<8%的含义:")
    print("• 在最坏的市场情况下，账户价值从峰值下跌不超过8%")
    print("• 体现了优秀的风险控制能力和资金保护水平")
    print("• 让投资者能够承受市场波动，避免恐慌性操作")
    
    print(f"\n📊 夏普比率>1.5的含义:")
    print("• 每承担1单位风险，获得超过1.5单位的超额收益")
    print("• 在风险调整后仍能提供出色的投资回报")
    print("• 是机构级量化策略的重要评判标准")
    
    print(f"\n🚀 两者结合的优势:")
    print("• 高收益 + 低风险 = 优秀的投资策略")
    print("• 适合长期持有，复利效应显著")
    print("• 在各种市场环境下都能保持相对稳定的表现")
    print("• 是量化交易追求的理想目标!")

if __name__ == '__main__':
    main()