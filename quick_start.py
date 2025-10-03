#!/usr/bin/env python3
"""
🚀 超简单量化交易 - 一键启动
专为新手设计，无需复杂配置！
"""

import os
import sys

def run_easy_command(description, command):
    """运行简单命令"""
    print(f"\n🔧 {description}")
    print(f"💻 执行: {command}")
    print("-" * 50)
    
    result = os.system(command)
    if result == 0:
        print("✅ 成功完成")
    else:
        print("❌ 执行出错")
    return result == 0

def main():
    print("=" * 60)
    print("🚀 超简单量化交易系统")  
    print("=" * 60)
    print("💡 让量化交易变得简单 - 为初学者设计")
    print("")
    
    while True:
        print("🎯 选择你想要的功能:")
        print("")
        print("   1. 🚀 一键启动自动交易监控")
        print("   2. 📊 查看我的自选股票")
        print("   3. 🔍 快速分析某只股票")
        print("   4. 📈 查看系统状态")
        print("   5. 📚 查看使用教程")
        print("   0. 🚪 退出")
        print("")
        
        choice = input("请输入数字选择 (0-5): ").strip()
        
        if choice == '1':
            print("\n🚀 启动自动交易监控...")
            print("💡 这会监控热门股票并显示实时交易信号")
            confirm = input("确认启动吗？(y/n): ").lower()
            if confirm == 'y':
                success = run_easy_command(
                    "启动实时交易监控", 
                    "python3 demo_auto_trading.py"
                )
                if not success:
                    print("💡 备用方案：使用基础监控模式")
                    run_easy_command(
                        "启动基础监控",
                        "python3 main.py trade monitor"
                    )
            
        elif choice == '2':
            run_easy_command(
                "查看自选股票池",
                "python3 main.py watchlist list"
            )
            
        elif choice == '3':
            stock = input("请输入股票代码 (如 AAPL): ").strip().upper()
            if stock:
                run_easy_command(
                    f"分析股票 {stock}",
                    f"python3 main.py strategy test RSI {stock}"
                )
            else:
                print("❌ 股票代码不能为空")
                
        elif choice == '4':
            run_easy_command(
                "检查系统状态",
                "python3 system_status_check.py"
            )
            
        elif choice == '5':
            print("\n📚 使用教程")
            print("=" * 40)
            print("🎯 新手快速上手:")
            print("1. 选择功能1 - 启动自动监控")
            print("2. 系统会自动分析热门股票")
            print("3. 观察实时交易信号")
            print("4. 学习信号含义和策略")
            print("")
            print("📊 股票分析:")
            print("• BUY = 买入信号")
            print("• SELL = 卖出信号") 
            print("• HOLD = 持有/观望")
            print("")
            print("⚠️  安全提醒:")
            print("• 这是模拟系统，不会实际交易")
            print("• 投资有风险，请谨慎决策")
            print("• 建议先学习再实践")
            print("")
            print("📖 详细文档: AUTO_TRADING_GUIDE.md")
            
        elif choice == '0':
            print("\n👋 谢谢使用！")
            print("💡 随时回来继续学习量化交易")
            break
            
        else:
            print("❌ 无效选择，请输入 0-5 的数字")
            
        input("\n按回车键继续...")
        print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 程序已退出")
    except Exception as e:
        print(f"\n❌ 程序出错: {e}")
        print("💡 请尝试重新运行或查看帮助文档")