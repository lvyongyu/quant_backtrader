#!/usr/bin/env python3
"""
量化交易系统 - 5分钟快速演示

展示新的组合策略和配置化分析功能
"""

import os
import sys

def demo_header():
    print("🚀 专业量化交易系统 - 快速演示")
    print("=" * 60)
    print()

def demo_1_list_configs():
    print("📋 1. 查看所有预设策略配置")
    print("-" * 40)
    os.system("python3 core/simple_cli.py config list")
    print()

def demo_2_balanced_analysis():
    print("⚖️ 2. 使用平衡配置分析AAPL（推荐新手）")
    print("-" * 40)
    os.system("python3 core/simple_cli.py config use balanced AAPL")
    print()

def demo_3_aggressive_analysis():
    print("⚡ 3. 使用激进配置分析TSLA")
    print("-" * 40)
    os.system("python3 core/simple_cli.py config use aggressive TSLA")
    print()

def demo_4_custom_config():
    print("🔧 4. 创建个人自定义配置")
    print("-" * 40)
    print("创建自定义配置：重点关注RSI的策略组合")
    os.system('python3 core/simple_cli.py config create demo_custom --strategies "RSI,MA_Cross,BollingerBands" --weights "[0.6,0.25,0.15]" --description "演示自定义配置"')
    print()

def demo_5_use_custom():
    print("🎯 5. 使用自定义配置分析")
    print("-" * 40)
    os.system("python3 core/simple_cli.py config use demo_custom AAPL")
    print()

def demo_6_manual_multi():
    print("🛠️ 6. 手动多策略组合（高级用法）")
    print("-" * 40)
    os.system('python3 core/simple_cli.py strategy multi "RSI,MACD,VolumeConfirmation" NVDA --weights "[0.5,0.3,0.2]"')
    print()

def demo_summary():
    print("📊 演示总结")
    print("=" * 60)
    print("✅ 核心优势:")
    print("  • 5种专业预设配置，开箱即用")
    print("  • 多策略组合，降低误判风险")
    print("  • 一键分析，操作简单高效")
    print("  • 个性化配置，满足不同需求")
    print()
    print("🎯 推荐使用流程:")
    print("  1. 新手使用 'balanced' 配置开始")
    print("  2. 根据市场环境选择合适配置")
    print("  3. 创建个人偏好的自定义配置")
    print("  4. 结合置信度进行投资决策")
    print()
    print("📚 更多功能请查看: README.md")
    print("🚀 让专业的量化交易变得像使用计算器一样简单！")

def cleanup():
    print("\n🧹 清理演示数据...")
    os.system("python3 core/simple_cli.py config delete demo_custom 2>/dev/null")
    print("✅ 演示完成！")

def main():
    try:
        demo_header()
        demo_1_list_configs()
        
        input("按回车键继续演示平衡配置分析...")
        demo_2_balanced_analysis()
        
        input("按回车键继续演示激进配置分析...")
        demo_3_aggressive_analysis()
        
        input("按回车键继续演示自定义配置创建...")
        demo_4_custom_config()
        
        input("按回车键继续演示自定义配置使用...")
        demo_5_use_custom()
        
        input("按回车键继续演示手动策略组合...")
        demo_6_manual_multi()
        
        demo_summary()
        
    except KeyboardInterrupt:
        print("\n\n演示已中断")
    finally:
        cleanup()

if __name__ == "__main__":
    main()