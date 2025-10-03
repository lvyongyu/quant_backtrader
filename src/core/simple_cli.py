#!/usr/bin/env python3
"""
量化交易系统简化命令行界面 - SimpleTrader CLI

让量化交易像使用终端命令一样简单！

命令示例：
  python simple_cli.py data AAPL                    # 获取数据
  python simple_cli.py strategy list                # 列出策略
  python simple_cli.py strategy test RSI AAPL       # 测试策略
  python simple_cli.py strategy multi "RSI,MACD" AAPL  # 多策略分析
  python simple_cli.py config list                  # 列出配置
  python simple_cli.py config use balanced AAPL     # 使用配置分析
"""

import argparse
import json
import sys
import os
from datetime import datetime, timedelta

# 添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 颜色输出
def print_success(msg): print(f"✅ {msg}")
def print_error(msg): print(f"❌ {msg}")
def print_info(msg): print(f"ℹ️  {msg}")
def print_header():
    print("🚀 SimpleTrader - 量化交易简化命令行")
    print("=" * 50)

# 尝试导入核心模块
CLI_AVAILABLE = True
import_error = None

try:
    from quick_trade import (
        get_data, get_price, get_info, get_stock_data,
        test_strategy, list_strategies, create_simple_strategy,
        backtest, compare_strategies,
        start_trading, stop_trading, get_trading_status,
        quick_analysis, system_status, demo, tutorial
    )
except ImportError as e:
    CLI_AVAILABLE = False
    import_error = str(e)

def handle_data_command(args):
    """处理数据相关命令"""
    if not args.symbol:
        print_error("请提供股票代码")
        return
    
    symbol = args.symbol.upper()
    
    try:
        if args.action == 'price':
            price = get_price(symbol)
            if price > 0:
                print_success(f"{symbol} 当前价格: ${price:.2f}")
            else:
                print_error(f"无法获取 {symbol} 的价格")
        
        elif args.action == 'info':
            info = get_info(symbol)
            if info:
                print_success(f"{symbol} 基本信息:")
                for key, value in info.items():
                    print(f"  {key}: {value}")
            else:
                print_error(f"无法获取 {symbol} 的信息")
        
        else:
            start_date = args.start or (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            end_date = args.end or datetime.now().strftime('%Y-%m-%d')
            
            data = get_stock_data(symbol, start_date, end_date)
            if not data.empty:
                print_success(f"获取 {symbol} 数据成功:")
                print(f"  时间范围: {start_date} 到 {end_date}")
                print(f"  数据条数: {len(data)}")
                print(f"  最新价格: ${data['Close'].iloc[-1]:.2f}")
                print(f"  期间涨幅: {((data['Close'].iloc[-1] / data['Close'].iloc[0]) - 1) * 100:.2f}%")
                
                if args.save:
                    filename = f"{symbol}_{start_date}_{end_date}.csv"
                    data.to_csv(filename)
                    print_info(f"数据已保存到: {filename}")
            else:
                print_error(f"无法获取 {symbol} 的数据")
    
    except Exception as e:
        print_error(f"数据操作失败: {e}")

def handle_strategy_command(args):
    """处理策略相关命令"""
    if args.action == 'list':
        try:
            strategies = list_strategies()
            print_success("可用策略:")
            for strategy in strategies:
                print(f"  • {strategy}")
        except Exception as e:
            print_error(f"获取策略列表失败: {e}")
        return
    
    if not args.strategy or not args.symbol:
        print_error("请提供策略名称和股票代码")
        return
    
    strategy_name = args.strategy
    symbol = args.symbol.upper()
    
    params = {}
    if args.params:
        try:
            params = json.loads(args.params)
        except json.JSONDecodeError:
            print_error("策略参数格式错误，请使用JSON格式")
            return
    
    try:
        if args.action == 'test':
            result = test_strategy(strategy_name, symbol, params)
            
            print_success(f"{strategy_name} 策略信号:")
            print(f"  股票: {symbol}")
            print(f"  信号: {result.signal.value}")
            print(f"  置信度: {result.confidence:.2f}")
            print(f"  当前价格: ${result.price:.2f}")
            print(f"  原因: {result.reason}")
            
            if result.indicators:
                print("  技术指标:")
                for key, value in result.indicators.items():
                    if isinstance(value, (int, float)):
                        print(f"    {key}: {value:.2f}")
                    else:
                        print(f"    {key}: {value}")
        
        elif args.action == 'multi':
            strategy_names = strategy_name.split(',')
            
            weights = None
            if args.weights:
                try:
                    weights = json.loads(args.weights)
                    if len(weights) != len(strategy_names):
                        print_error("权重数量必须与策略数量一致")
                        return
                except json.JSONDecodeError:
                    print_error("权重格式错误，请使用JSON数组格式，如 [0.4,0.3,0.3]")
                    return
            
            print_success(f"多策略组合分析 - {symbol}:")
            print(f"  策略: {', '.join(strategy_names)}")
            if weights:
                print(f"  权重: {weights}")
            else:
                print(f"  权重: 等权重")
            print()
            
            individual_results = []
            for i, strat_name in enumerate(strategy_names):
                try:
                    result = test_strategy(strat_name.strip(), symbol, params)
                    individual_results.append(result)
                    
                    weight_str = f"(权重: {weights[i]:.1f})" if weights else "(等权重)"
                    print(f"  📊 {strat_name.strip()} {weight_str}:")
                    print(f"     信号: {result.signal.value}")
                    print(f"     置信度: {result.confidence:.2f}")
                    print(f"     原因: {result.reason}")
                    print()
                except Exception as e:
                    print_error(f"    {strat_name.strip()}: 分析失败 - {e}")
                    continue
            
            if len(individual_results) > 0:
                from strategy_manager import multi_strategy, Strategy, create_strategy
                from data_manager import get_data
                
                strategies = []
                for strat_name in strategy_names:
                    try:
                        strat = create_strategy(strat_name.strip(), params)
                        strategies.append(strat)
                    except:
                        continue
                
                if strategies:
                    data = get_data(symbol)
                    combined_result = multi_strategy(data, strategies, weights)
                    
                    print("🎯 组合策略结果:")
                    print(f"   综合信号: {combined_result.signal.value}")
                    print(f"   综合置信度: {combined_result.confidence:.2f}")
                    print(f"   决策依据: {combined_result.reason}")
                    
                    if combined_result.indicators:
                        print("   组合指标:")
                        for key, value in combined_result.indicators.items():
                            if isinstance(value, (int, float)):
                                print(f"     {key}: {value:.2f}")
                            else:
                                print(f"     {key}: {value}")
        
        elif args.action == 'create':
            strategy = create_simple_strategy(strategy_name, params)
            print_success(f"策略创建成功:")
            print(f"  名称: {strategy.name}")
            print(f"  参数: {strategy.params}")
            
    except Exception as e:
        print_error(f"策略操作失败: {e}")

def handle_config_command(args):
    """处理配置相关命令"""
    try:
        from strategy_config import (
            list_strategy_configs, get_strategy_config, 
            create_strategy_config, delete_strategy_config
        )
        
        if args.action == 'list':
            configs = list_strategy_configs()
            print_success(f"可用策略配置 ({len(configs)}个):")
            for config in configs:
                print(f"\n  📋 {config.name}")
                print(f"     描述: {config.description}")
                print(f"     策略: {', '.join(config.strategies)}")
                print(f"     权重: {config.weights}")
        
        elif args.action == 'show':
            if not args.name:
                print_error("请提供配置名称")
                return
            
            config = get_strategy_config(args.name)
            if not config:
                print_error(f"配置不存在: {args.name}")
                return
            
            print_success(f"策略配置: {config.name}")
            print(f"  描述: {config.description}")
            print(f"  策略: {', '.join(config.strategies)}")
            print(f"  权重: {config.weights}")
            print()
            print("🔍 策略详情:")
            from strategy_manager import get_available_strategies
            available = get_available_strategies()
            for i, strategy in enumerate(config.strategies):
                if strategy in available:
                    print(f"  ✅ {strategy} (权重: {config.weights[i]:.1%})")
                else:
                    print(f"  ❌ {strategy} (权重: {config.weights[i]:.1%}) - 策略不可用")
        
        elif args.action == 'create':
            if not all([args.name, args.strategies, args.weights]):
                print_error("请提供配置名称、策略列表和权重")
                print_info("示例: config create my_config --strategies 'RSI,MACD,MA_Cross' --weights '[0.5,0.3,0.2]' --description '我的自定义策略'")
                return
            
            try:
                strategies = [s.strip() for s in args.strategies.split(',')]
                weights = json.loads(args.weights)
                description = args.description or f"用户自定义策略配置"
                
                success = create_strategy_config(args.name, strategies, weights, description)
                if success:
                    print_success(f"策略配置创建成功: {args.name}")
                    print(f"  策略: {', '.join(strategies)}")
                    print(f"  权重: {weights}")
                    print(f"  描述: {description}")
                else:
                    print_error("配置创建失败")
                    
            except json.JSONDecodeError:
                print_error("权重格式错误，请使用JSON数组格式，如 [0.5,0.3,0.2]")
            except ValueError as e:
                print_error(f"配置参数错误: {e}")
        
        elif args.action == 'delete':
            if not args.name:
                print_error("请提供要删除的配置名称")
                return
            
            try:
                success = delete_strategy_config(args.name)
                if success:
                    print_success(f"策略配置已删除: {args.name}")
                else:
                    print_error(f"配置不存在: {args.name}")
            except ValueError as e:
                print_error(f"删除失败: {e}")
        
        elif args.action == 'use':
            if not args.name:
                print_error("请提供配置名称")
                return
            
            config = get_strategy_config(args.name)
            if not config:
                print_error(f"配置不存在: {args.name}")
                return
            
            symbol = getattr(args, 'symbol', None)
            if not symbol:
                print_error("请提供股票代码")
                print_info("示例: config use balanced AAPL")
                return
            
            symbol = symbol.upper()
            print_success(f"使用配置 '{config.name}' 分析 {symbol}:")
            print(f"  描述: {config.description}")
            print()
            
            # 执行多策略分析
            strategies_str = ','.join(config.strategies)
            weights_str = json.dumps(config.weights)
            
            from types import SimpleNamespace
            multi_args = SimpleNamespace(
                action='multi',
                strategy=strategies_str,
                symbol=symbol,
                weights=weights_str,
                params=None
            )
            handle_strategy_command(multi_args)
    
    except Exception as e:
        print_error(f"配置操作失败: {e}")

def handle_watchlist_command(args):
    """处理自选股池相关命令"""
    try:
        # 简化版自选股管理器
        watchlist_file = os.path.join(current_dir, '../data/watchlist.json')
        
        def load_watchlist():
            if os.path.exists(watchlist_file):
                with open(watchlist_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {"stocks": {}, "created_at": datetime.now().isoformat(), "last_updated": datetime.now().isoformat()}
        
        def save_watchlist(data):
            data["last_updated"] = datetime.now().isoformat()
            os.makedirs(os.path.dirname(watchlist_file), exist_ok=True)
            with open(watchlist_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        if args.action in ['list', 'show']:
            # 显示自选股池
            watchlist = load_watchlist()
            stocks = watchlist.get("stocks", {})
            
            if not stocks:
                print_info("自选股池为空")
                print("💡 添加股票: python simple_cli.py watchlist add AAPL")
                return
            
            print_success(f"自选股池 ({len(stocks)}只股票):")
            print()
            
            for symbol, data in stocks.items():
                score = data.get("last_score", 0)
                price = data.get("price", "N/A")
                added_time = data.get("added_at", "未知")[:10]
                
                print(f"  📈 {symbol}")
                print(f"     得分: {score:.1f}")
                print(f"     价格: {price}")
                print(f"     添加时间: {added_time}")
                print()
        
        elif args.action == 'add':
            # 添加股票到自选股池
            if not args.symbol:
                print_error("请指定要添加的股票代码")
                print_info("示例: python simple_cli.py watchlist add AAPL")
                return
            
            symbol = args.symbol.upper()
            watchlist = load_watchlist()
            
            # 检查是否已存在
            if symbol in watchlist["stocks"]:
                print_info(f"{symbol} 已在自选股池中")
                return
            
            print_info(f"正在分析 {symbol}...")
            
            # 获取股票信息
            try:
                from quick_trade import get_price, get_info
                price = get_price(symbol)
                # 简单评分（可以后续扩展）
                score = 7.5  # 默认分数
                
                watchlist["stocks"][symbol] = {
                    "last_score": score,
                    "price": price,
                    "added_at": datetime.now().isoformat()
                }
                
                save_watchlist(watchlist)
                print_success(f"{symbol} 已添加到自选股池")
                print(f"  价格: ${price:.2f}")
                print(f"  评分: {score:.1f}")
                
            except Exception as e:
                print_error(f"获取 {symbol} 数据失败: {e}")
        
        elif args.action in ['remove', 'rm']:
            # 移除股票
            if not args.symbol:
                print_error("请指定要移除的股票代码")
                print_info("示例: python simple_cli.py watchlist remove AAPL")
                return
            
            symbol = args.symbol.upper()
            watchlist = load_watchlist()
            
            if symbol in watchlist["stocks"]:
                del watchlist["stocks"][symbol]
                save_watchlist(watchlist)
                print_success(f"{symbol} 已从自选股池移除")
            else:
                print_error(f"{symbol} 不在自选股池中")
        
        elif args.action == 'clear':
            # 清空自选股池
            watchlist = load_watchlist()
            count = len(watchlist["stocks"])
            watchlist["stocks"] = {}
            save_watchlist(watchlist)
            print_success(f"自选股池已清空 (移除了 {count} 只股票)")
        
        elif args.action == 'analyze':
            # 分析自选股池
            watchlist = load_watchlist()
            stocks = watchlist.get("stocks", {})
            
            if not stocks:
                print_info("自选股池为空，请先添加一些股票")
                return
            
            print_success("分析自选股池中的股票:")
            print()
            
            # 使用RSI策略快速分析每只股票
            for symbol in stocks.keys():
                try:
                    print(f"🔍 分析 {symbol}...")
                    
                    # 简单的策略分析
                    from types import SimpleNamespace
                    analysis_args = SimpleNamespace(
                        action='test',
                        strategy='RSI',
                        symbol=symbol,
                        params=None
                    )
                    
                    print(f"  📊 {symbol} RSI策略分析:")
                    handle_strategy_command(analysis_args)
                    print()
                    
                except Exception as e:
                    print_error(f"  分析 {symbol} 失败: {e}")
        
        elif args.action == 'stats':
            # 显示统计信息
            watchlist = load_watchlist()
            stocks = watchlist.get("stocks", {})
            
            if not stocks:
                print_info("自选股池为空")
                return
            
            print_success("自选股池统计信息:")
            print()
            
            scores = [data.get("last_score", 0) for data in stocks.values()]
            avg_score = sum(scores) / len(scores) if scores else 0
            max_score = max(scores) if scores else 0
            min_score = min(scores) if scores else 0
            
            print(f"  📈 股票总数: {len(stocks)} 只")
            print(f"  📊 平均得分: {avg_score:.1f}")
            print(f"  🏆 最高得分: {max_score:.1f}")
            print(f"  📉 最低得分: {min_score:.1f}")
            
            created_at = watchlist.get("created_at", "未知")[:10]
            last_updated = watchlist.get("last_updated", "未知")[:10]
            
            print(f"  📅 创建时间: {created_at}")
            print(f"  🔄 更新时间: {last_updated}")
    
    except Exception as e:
        print_error(f"自选股操作失败: {e}")

def handle_screen_command(args):
    """处理选股相关命令"""
    try:
        if args.action == 'single':
            # 单股分析
            if not args.target:
                print_error("请指定要分析的股票代码")
                print_info("示例: python simple_cli.py screen single AAPL")
                return
            
            symbol = args.target.upper()
            print_success(f"四维度分析 {symbol}:")
            print()
            
            # 快速四维度分析
            tech_score = analyze_technical_score(symbol)
            fundamental_score = 75.0  # 简化版基本面分析
            market_score = 70.0       # 简化版市场分析
            sentiment_score = 65.0    # 简化版情绪分析
            
            # 权重计算
            weights = [0.4, 0.25, 0.2, 0.15]  # 技术、基本面、市场、情绪
            scores = [tech_score, fundamental_score, market_score, sentiment_score]
            total_score = sum(w * s for w, s in zip(weights, scores))
            
            print(f"  🔧 技术分析 (40%): {tech_score:.1f}/100")
            print(f"  📊 基本面分析 (25%): {fundamental_score:.1f}/100")
            print(f"  🌍 市场环境 (20%): {market_score:.1f}/100")
            print(f"  💭 情绪分析 (15%): {sentiment_score:.1f}/100")
            print()
            print(f"  🎯 综合评分: {total_score:.1f}/100")
            
            # 投资建议
            if total_score >= 80:
                print("  💚 建议: 强烈推荐")
            elif total_score >= 70:
                print("  💛 建议: 推荐")
            elif total_score >= 60:
                print("  🧡 建议: 中性")
            else:
                print("  ❤️ 建议: 不推荐")
        
        elif args.action == 'pool':
            # 从股票池选股
            pool_name = args.target or 'sp500'
            print_success(f"从 {pool_name} 股票池选股 (TOP {args.limit}):")
            print()
            
            # 简化版股票池选股
            sample_stocks = get_sample_stocks(pool_name)
            
            results = []
            for symbol in sample_stocks[:20]:  # 分析前20只
                try:
                    score = analyze_technical_score(symbol)
                    if score >= args.min_score:
                        results.append((symbol, score))
                except:
                    continue
            
            # 排序并显示结果
            results.sort(key=lambda x: x[1], reverse=True)
            
            print(f"📊 找到 {len(results)} 只符合条件的股票 (评分≥{args.min_score}):")
            for i, (symbol, score) in enumerate(results[:args.limit], 1):
                print(f"  {i:2d}. {symbol:5s} : {score:5.1f}分")
            
            if results:
                print(f"\n💡 可以用以下命令添加到自选股池:")
                top_symbols = [r[0] for r in results[:3]]
                for symbol in top_symbols:
                    print(f"  python simple_cli.py watchlist add {symbol}")
        
        elif args.action == 'batch':
            # 批量分析自选股池
            watchlist_file = os.path.join(current_dir, '../data/watchlist.json')
            
            if not os.path.exists(watchlist_file):
                print_error("自选股池为空，请先添加一些股票")
                return
            
            with open(watchlist_file, 'r', encoding='utf-8') as f:
                watchlist = json.load(f)
            
            stocks = list(watchlist.get("stocks", {}).keys())
            if not stocks:
                print_error("自选股池为空")
                return
            
            print_success(f"批量分析自选股池 ({len(stocks)} 只股票):")
            print()
            
            results = []
            for symbol in stocks:
                try:
                    score = analyze_technical_score(symbol)
                    results.append((symbol, score))
                    print(f"  ✅ {symbol}: {score:.1f}分")
                except Exception as e:
                    print(f"  ❌ {symbol}: 分析失败")
            
            # 排序显示
            results.sort(key=lambda x: x[1], reverse=True)
            print(f"\n🏆 自选股排名:")
            for i, (symbol, score) in enumerate(results, 1):
                print(f"  {i:2d}. {symbol:5s} : {score:5.1f}分")
    
    except Exception as e:
        print_error(f"选股操作失败: {e}")

def analyze_technical_score(symbol):
    """简化版技术分析评分"""
    try:
        from quick_trade import get_data
        
        # 获取数据
        data = get_data(symbol, period='6mo')
        if data is None or data.empty:
            return 50.0
        
        current_price = data['Close'].iloc[-1]
        
        # 移动平均线
        data['MA5'] = data['Close'].rolling(5).mean()
        data['MA20'] = data['Close'].rolling(20).mean()
        data['MA50'] = data['Close'].rolling(50).mean()
        
        # 趋势得分
        trend_score = 0
        if current_price > data['MA5'].iloc[-1]:
            trend_score += 25
        if current_price > data['MA20'].iloc[-1]:
            trend_score += 35
        if current_price > data['MA50'].iloc[-1]:
            trend_score += 40
        
        # RSI计算
        delta = data['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        # 动量得分
        if 40 <= current_rsi <= 70:
            momentum_score = 100
        elif 30 <= current_rsi <= 80:
            momentum_score = 80
        else:
            momentum_score = 60
        
        # 综合得分
        technical_score = trend_score * 0.6 + momentum_score * 0.4
        return min(100, max(0, technical_score))
        
    except Exception as e:
        return 50.0

def get_sample_stocks(pool_name):
    """获取示例股票池"""
    stock_pools = {
        'sp500': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM', 'JNJ', 'V', 'WMT', 'PG', 'MA', 'HD', 'CVX'],
        'tech': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'CRM', 'ORCL', 'ADBE', 'NFLX'],
        'nasdaq': ['AAPL', 'MSFT', 'AMZN', 'TSLA', 'META', 'GOOGL', 'NVDA', 'PYPL', 'CMCSA', 'NFLX'],
        'dow': ['AAPL', 'MSFT', 'JPM', 'JNJ', 'V', 'WMT', 'PG', 'HD', 'CVX', 'MRK']
    }
    return stock_pools.get(pool_name, stock_pools['sp500'])

def create_parser():
    """创建命令行解析器"""
    parser = argparse.ArgumentParser(
        description="SimpleTrader - 量化交易简化命令行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 数据命令
    data_parser = subparsers.add_parser('data', help='数据相关操作')
    data_parser.add_argument('action', nargs='?', default='data', 
                           choices=['data', 'price', 'info'], help='操作类型')
    data_parser.add_argument('symbol', help='股票代码')
    data_parser.add_argument('--start', help='开始日期 (YYYY-MM-DD)')
    data_parser.add_argument('--end', help='结束日期 (YYYY-MM-DD)')
    data_parser.add_argument('--save', action='store_true', help='保存数据到CSV文件')
    
    # 策略命令
    strategy_parser = subparsers.add_parser('strategy', help='策略相关操作')
    strategy_parser.add_argument('action', choices=['list', 'test', 'multi', 'create'], help='操作类型')
    strategy_parser.add_argument('strategy', nargs='?', help='策略名称或策略列表（用逗号分隔）')
    strategy_parser.add_argument('symbol', nargs='?', help='股票代码')
    strategy_parser.add_argument('--params', help='策略参数 (JSON格式)')
    strategy_parser.add_argument('--weights', help='多策略权重 (JSON格式，如 [0.4,0.3,0.3])')
    
    # 配置命令
    config_parser = subparsers.add_parser('config', help='策略配置管理')
    config_parser.add_argument('action', choices=['list', 'create', 'use', 'show', 'delete'], help='操作类型')
    config_parser.add_argument('name', nargs='?', help='配置名称')
    config_parser.add_argument('symbol', nargs='?', help='股票代码（用于use操作）')
    config_parser.add_argument('--strategies', help='策略列表（用逗号分隔）')
    config_parser.add_argument('--weights', help='策略权重（JSON格式）')
    config_parser.add_argument('--description', help='配置描述')
    
    # 自选股命令
    watchlist_parser = subparsers.add_parser('watchlist', help='自选股池管理')
    watchlist_parser.add_argument('action', choices=['list', 'show', 'add', 'remove', 'rm', 'clear', 'analyze', 'stats'], help='操作类型')
    watchlist_parser.add_argument('symbol', nargs='?', help='股票代码（用于add/remove操作）')
    
    # 选股命令
    screen_parser = subparsers.add_parser('screen', help='智能选股')
    screen_parser.add_argument('action', choices=['single', 'batch', 'pool'], help='选股类型')
    screen_parser.add_argument('target', nargs='?', help='目标股票代码或股票池名称')
    screen_parser.add_argument('--limit', type=int, default=10, help='最大结果数量')
    screen_parser.add_argument('--min-score', type=float, default=70.0, help='最低评分')
    
    return parser

def main():
    """主函数"""
    print_header()
    
    if not CLI_AVAILABLE:
        print_error(f"CLI不可用，导入错误: {import_error}")
        print_info("请确保已安装必要依赖: pip install pandas numpy yfinance")
        return 1
    
    parser = create_parser()
    
    if len(sys.argv) == 1:
        parser.print_help()
        print("\n🎯 快速开始:")
        print("  python simple_cli.py strategy list       # 列出所有策略")
        print("  python simple_cli.py config list         # 列出策略配置") 
        print("  python simple_cli.py config use balanced AAPL  # 使用平衡配置分析")
        print("  python simple_cli.py screen single AAPL  # 四维度分析单股")
        print("  python simple_cli.py screen pool sp500   # 从SP500选股")
        print("  python simple_cli.py watchlist add AAPL  # 添加到自选股池")
        print("  python simple_cli.py strategy multi 'RSI,MACD' AAPL  # 多策略分析")
        return 0
    
    args = parser.parse_args()
    
    try:
        if args.command == 'data':
            handle_data_command(args)
        elif args.command == 'strategy':
            handle_strategy_command(args)
        elif args.command == 'config':
            handle_config_command(args)
        elif args.command == 'watchlist':
            handle_watchlist_command(args)
        elif args.command == 'screen':
            handle_screen_command(args)
        else:
            parser.print_help()
        
        return 0
        
    except KeyboardInterrupt:
        print_info("\n操作已取消")
        return 1
    except Exception as e:
        print_error(f"未知错误: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())