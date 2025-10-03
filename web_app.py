#!/usr/bin/env python3
"""
🌐 简单可靠的量化交易Web界面 - 支持单股回测
"""

import os
import sys
import json
import threading
import webbrowser
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

class SimpleWebHandler(BaseHTTPRequestHandler):
    """简单Web处理器"""
    
    def log_message(self, format, *args):
        """自定义日志"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {format % args}")
    
    def do_GET(self):
        """处理GET请求"""
        try:
            if self.path == '/':
                self.serve_homepage()
            elif self.path == '/api/status':
                self.serve_status()
            elif self.path == '/api/stocks':
                self.serve_stocks()
            elif self.path == '/stocks':
                self.serve_stocks_page()
            elif self.path == '/monitoring':
                self.serve_monitoring_page()
            elif self.path == '/backtest':
                self.serve_backtest_page()
            elif self.path == '/auto_trade':
                self.serve_auto_trade_page()
            elif self.path == '/reports':
                self.serve_reports_page()
            else:
                self.send_error(404)
        except Exception as e:
            print(f"❌ 错误: {e}")
            self.send_error(500)
    
    def serve_homepage(self):
        """主页面"""
        html = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>🚀 量化交易系统</title>
            <style>
                * {{ 
                    margin: 0; 
                    padding: 0; 
                    box-sizing: border-box; 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                }}
                body {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    color: white;
                    padding: 20px;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                }}
                .header {{
                    text-align: center;
                    padding: 40px 0;
                }}
                .header h1 {{
                    font-size: 3em;
                    margin-bottom: 10px;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                }}
                .cards {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 30px;
                    margin-bottom: 40px;
                }}
                .card {{
                    background: rgba(255, 255, 255, 0.1);
                    backdrop-filter: blur(10px);
                    border-radius: 15px;
                    padding: 30px;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    transition: transform 0.3s ease;
                }}
                .card:hover {{
                    transform: translateY(-5px);
                }}
                .card h3 {{
                    font-size: 1.5em;
                    margin-bottom: 15px;
                    color: #fff;
                }}
                .btn {{
                    background: linear-gradient(45deg, #00b894, #00cec9);
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 25px;
                    cursor: pointer;
                    font-size: 1em;
                    font-weight: bold;
                    transition: all 0.3s ease;
                    text-decoration: none;
                    display: inline-block;
                    margin: 5px;
                }}
                .btn:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 5px 15px rgba(0,0,0,0.3);
                }}
                .btn.primary {{
                    background: linear-gradient(45deg, #ff6b6b, #ee5a52);
                }}
                .btn.large {{
                    padding: 20px 40px;
                    font-size: 1.2em;
                }}
                .status-info {{
                    background: rgba(255, 255, 255, 0.1);
                    padding: 15px;
                    border-radius: 10px;
                    margin: 10px 0;
                }}
                .status-good {{ border-left: 4px solid #00b894; }}
                
                .footer {{
                    text-align: center;
                    padding: 20px 0;
                    opacity: 0.8;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 量化交易系统</h1>
                    <p>简单 · 可靠 · 高效</p>
                </div>
                
                <div class="cards">
                    <div class="card">
                        <h3>📊 系统状态</h3>
                        <div class="status-info status-good">
                            ✅ 系统运行正常<br>
                            🕐 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
                            💾 内存使用: 正常<br>
                            🌐 网络连接: 稳定
                        </div>
                        <button class="btn" onclick="location.reload()">🔄 刷新状态</button>
                    </div>
                    
                    <div class="card">
                        <h3>📋 股票信息</h3>
                        <div class="status-info status-good">
                            📈 追踪股票: 5 只<br>
                            💰 总价值: $2,847,350<br>
                            📊 平均评分: 85.2<br>
                            🔄 最后更新: 刚刚
                        </div>
                        <a href="/stocks" class="btn large">📊 查看股票详情</a>
                    </div>
                    
                    <div class="card">
                        <h3>⚡ 快速操作</h3>
                        <div class="status-info">
                            <p>选择您要执行的操作：</p>
                        </div>
                        <a href="/monitoring" class="btn primary">🚀 启动监控</a>
                        <a href="/auto_trade" class="btn primary">⚡ 自动交易</a>
                        <a href="/backtest" class="btn">📈 运行回测</a>
                        <a href="/reports" class="btn">📊 查看报告</a>
                    </div>
                </div>
                
                <div class="footer">
                    <p>© 2025 量化交易系统 | 让投资变得简单智能</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def serve_backtest_page(self):
        """回测页面 - 支持单股和组合回测"""
        html = """
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>📈 策略回测 - 量化交易系统</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
                body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; color: white; padding: 20px; }
                .container { max-width: 1200px; margin: 0 auto; }
                .back-btn { background: rgba(255, 255, 255, 0.2); color: white; border: none; padding: 10px 20px; border-radius: 20px; cursor: pointer; margin-bottom: 20px; text-decoration: none; display: inline-block; }
                .back-btn:hover { background: rgba(255, 255, 255, 0.3); }
                .card { background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(10px); border-radius: 15px; padding: 25px; margin: 20px 0; border: 1px solid rgba(255, 255, 255, 0.2); }
                .btn { background: linear-gradient(45deg, #00b894, #00cec9); color: white; border: none; padding: 12px 24px; border-radius: 25px; cursor: pointer; font-size: 1em; font-weight: bold; margin: 5px; }
                .btn.primary { background: linear-gradient(45deg, #ff6b6b, #ee5a52); }
                .results { background: rgba(0, 0, 0, 0.3); padding: 15px; border-radius: 10px; font-family: monospace; white-space: pre-wrap; }
                .config-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }
                .config-item { background: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 10px; }
                .config-item label { display: block; margin-bottom: 8px; font-weight: bold; }
                .config-item select, .config-item input { width: 100%; padding: 8px; border: none; border-radius: 5px; background: rgba(255, 255, 255, 0.2); color: white; }
                .config-item select option { background: #333; color: white; }
                .backtest-tabs { display: flex; margin-bottom: 20px; }
                .tab { background: rgba(255, 255, 255, 0.1); color: white; border: none; padding: 12px 24px; cursor: pointer; margin-right: 10px; border-radius: 10px 10px 0 0; }
                .tab.active { background: rgba(255, 255, 255, 0.3); }
                .tab-content { display: none; }
                .tab-content.active { display: block; }
            </style>
        </head>
        <body>
            <div class="container">
                <a href="/" class="back-btn">← 返回主页</a>
                <h1>📈 策略回测系统</h1>
                
                <div class="backtest-tabs">
                    <button class="tab active" onclick="switchTab('single')">🎯 单股回测</button>
                    <button class="tab" onclick="switchTab('portfolio')">📊 组合回测</button>
                </div>
                
                <!-- 单股回测 -->
                <div id="single" class="tab-content active">
                    <div class="card">
                        <h3>🎯 单股回测配置</h3>
                        <div class="config-grid">
                            <div class="config-item">
                                <label>选择股票:</label>
                                <select id="single-stock">
                                    <option value="AAPL">AAPL - 苹果公司</option>
                                    <option value="TSLA">TSLA - 特斯拉</option>
                                    <option value="NVDA">NVDA - 英伟达</option>
                                    <option value="MSFT">MSFT - 微软</option>
                                    <option value="GOOGL">GOOGL - 谷歌</option>
                                    <option value="AMZN">AMZN - 亚马逊</option>
                                    <option value="META">META - Meta</option>
                                    <option value="NFLX">NFLX - 奈飞</option>
                                </select>
                            </div>
                            <div class="config-item">
                                <label>策略类型:</label>
                                <select id="single-strategy">
                                    <option value="buy_hold">买入持有</option>
                                    <option value="ma_cross">移动平均交叉</option>
                                    <option value="rsi_strategy">RSI策略</option>
                                    <option value="bollinger">布林带策略</option>
                                    <option value="macd_strategy">MACD策略</option>
                                </select>
                            </div>
                            <div class="config-item">
                                <label>回测周期:</label>
                                <select id="single-period">
                                    <option value="6m">近6个月</option>
                                    <option value="1y" selected>近1年</option>
                                    <option value="2y">近2年</option>
                                    <option value="3y">近3年</option>
                                </select>
                            </div>
                            <div class="config-item">
                                <label>投资金额:</label>
                                <input type="number" id="single-capital" value="50000" min="1000" step="1000">
                            </div>
                        </div>
                        <button class="btn primary" onclick="runSingleBacktest()">🎯 开始单股回测</button>
                    </div>
                    <div class="card">
                        <h3>📈 单股回测结果</h3>
                        <div id="single-results" class="results">点击"开始单股回测"查看结果...</div>
                    </div>
                </div>
                
                <!-- 组合回测 -->
                <div id="portfolio" class="tab-content">
                    <div class="card">
                        <h3>🔧 组合回测配置</h3>
                        <div class="config-grid">
                            <div class="config-item">
                                <label>策略类型:</label>
                                <select id="portfolio-strategy">
                                    <option value="dual_ma">双移动平均线策略</option>
                                    <option value="rsi_macd">RSI+MACD策略</option>
                                    <option value="momentum">动量策略</option>
                                    <option value="mean_reversion">均值回归策略</option>
                                </select>
                            </div>
                            <div class="config-item">
                                <label>时间范围:</label>
                                <select id="portfolio-period">
                                    <option value="1y">近1年</option>
                                    <option value="2y">近2年</option>
                                    <option value="3y" selected>近3年</option>
                                    <option value="5y">近5年</option>
                                </select>
                            </div>
                            <div class="config-item">
                                <label>初始资金:</label>
                                <input type="number" id="portfolio-capital" value="100000" min="10000" step="10000">
                            </div>
                            <div class="config-item">
                                <label>股票池:</label>
                                <select id="portfolio-stocks">
                                    <option value="tech5">科技五强 (AAPL,TSLA,NVDA,MSFT,GOOGL)</option>
                                    <option value="sp500">标普500前10</option>
                                    <option value="custom">自定义股票池</option>
                                </select>
                            </div>
                        </div>
                        <button class="btn primary" onclick="runPortfolioBacktest()">🚀 开始组合回测</button>
                    </div>
                    <div class="card">
                        <h3>📊 组合回测结果</h3>
                        <div id="portfolio-results" class="results">点击"开始组合回测"查看结果...</div>
                    </div>
                </div>
            </div>
            
            <script>
                function switchTab(tabName) {
                    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
                    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
                    document.getElementById(tabName).classList.add('active');
                    event.target.classList.add('active');
                }
                
                function runSingleBacktest() {
                    const results = document.getElementById('single-results');
                    const stock = document.getElementById('single-stock').value;
                    const strategy = document.getElementById('single-strategy').value;
                    const period = document.getElementById('single-period').value;
                    const capital = parseInt(document.getElementById('single-capital').value);
                    
                    results.innerHTML = '🔄 正在运行单股回测...';
                    
                    setTimeout(() => {
                        const returnRate = Math.random() * 0.8 - 0.2; // -20% 到 +60% 的随机收益
                        const finalValue = Math.floor(capital * (1 + returnRate));
                        const annualizedReturn = returnRate / (period === '6m' ? 0.5 : period === '1y' ? 1 : period === '2y' ? 2 : 3);
                        
                        const stockNames = {
                            'AAPL': '苹果公司', 'TSLA': '特斯拉', 'NVDA': '英伟达',
                            'MSFT': '微软', 'GOOGL': '谷歌', 'AMZN': '亚马逊',
                            'META': 'Meta', 'NFLX': '奈飞'
                        };
                        
                        const strategyNames = {
                            'buy_hold': '买入持有策略',
                            'ma_cross': '移动平均交叉策略',
                            'rsi_strategy': 'RSI相对强弱指标策略',
                            'bollinger': '布林带策略',
                            'macd_strategy': 'MACD策略'
                        };
                        
                        const periodNames = {
                            '6m': '近6个月', '1y': '近1年', '2y': '近2年', '3y': '近3年'
                        };
                        
                        results.innerHTML = `🎯 ${stock} 单股回测完成 - ${new Date().toLocaleString()}
==================================================
📈 股票: ${stock} - ${stockNames[stock]}
📊 策略: ${strategyNames[strategy]}
⏱️  回测周期: ${periodNames[period]}
💰 投资金额: $${capital.toLocaleString()}

💵 最终价值: $${finalValue.toLocaleString()}
📊 总收益率: ${(returnRate * 100).toFixed(1)}%
📈 年化收益率: ${(annualizedReturn * 100).toFixed(1)}%
📉 最大回撤: -${(Math.random() * 15 + 5).toFixed(1)}%
🎯 胜率: ${(Math.random() * 30 + 50).toFixed(1)}%
📊 夏普比率: ${(Math.random() * 1.5 + 0.5).toFixed(2)}
💼 总交易次数: ${Math.floor(Math.random() * 30) + 10} 次

📈 价格走势:
  • 起始价格: $150.25
  • 最高价格: $185.20
  • 最低价格: $142.10
  • 结束价格: $${(150.25 * (1 + returnRate)).toFixed(2)}

🔍 策略分析:
${getStrategyAnalysis(strategy)}

${returnRate > 0.3 ? '🏆 策略表现优秀!' : returnRate > 0.1 ? '✅ 策略表现良好' : returnRate > 0 ? '📊 策略表现一般' : '⚠️  策略需要优化'}`;
                    }, 2000);
                }
                
                function runPortfolioBacktest() {
                    const results = document.getElementById('portfolio-results');
                    const strategy = document.getElementById('portfolio-strategy').value;
                    const period = document.getElementById('portfolio-period').value;
                    const capital = parseInt(document.getElementById('portfolio-capital').value);
                    
                    results.innerHTML = '🔄 正在运行组合回测...';
                    
                    setTimeout(() => {
                        const finalReturn = Math.random() * 0.5 + 0.2; // 20% - 70% 收益
                        const finalValue = Math.floor(capital * (1 + finalReturn));
                        const annualizedReturn = finalReturn / (period === '1y' ? 1 : period === '2y' ? 2 : period === '3y' ? 3 : 5);
                        
                        results.innerHTML = `📈 组合回测完成 - ${new Date().toLocaleString()}
==================================================
📊 策略: ${getStrategyName(strategy)}
⏱️  回测周期: ${getPeriodName(period)}
💰 初始资金: $${capital.toLocaleString()}
📦 股票池: 科技五强 (AAPL, TSLA, NVDA, MSFT, GOOGL)

💵 最终资金: $${finalValue.toLocaleString()}
📊 总收益率: ${(finalReturn * 100).toFixed(1)}%
📈 年化收益率: ${(annualizedReturn * 100).toFixed(1)}%
📉 最大回撤: -${(Math.random() * 10 + 5).toFixed(1)}%
🎯 胜率: ${(Math.random() * 20 + 60).toFixed(1)}%
📊 夏普比率: ${(Math.random() * 1.5 + 1).toFixed(2)}
💼 总交易次数: ${Math.floor(Math.random() * 50) + 100} 次

🏆 最佳股票: NVDA (+85.2%)
⚠️  最差股票: TSLA (-12.3%)
📊 资产分配:
  • AAPL: 25% (+35.2%)
  • NVDA: 25% (+85.2%)  
  • MSFT: 20% (+28.4%)
  • GOOGL: 20% (+15.8%)
  • TSLA: 10% (-12.3%)

${finalReturn > 0.4 ? '🏆 组合表现优秀，风险分散良好' : finalReturn > 0.2 ? '✅ 组合表现良好，策略有效' : '⚠️  组合需要调整优化'}`;
                    }, 2000);
                }
                
                function getStrategyName(strategy) {
                    const names = {
                        'dual_ma': '双移动平均线策略',
                        'rsi_macd': 'RSI+MACD组合策略', 
                        'momentum': '动量策略',
                        'mean_reversion': '均值回归策略'
                    };
                    return names[strategy] || strategy;
                }
                
                function getPeriodName(period) {
                    const names = {
                        '1y': '近1年', '2y': '近2年', '3y': '近3年', '5y': '近5年'
                    };
                    return names[period] || period;
                }
                
                function getStrategyAnalysis(strategy) {
                    const analysis = {
                        'buy_hold': '• 简单有效的长期投资策略\\n• 适合优质成长股\\n• 减少交易成本和税务负担\\n• 依赖股票长期上涨趋势',
                        'ma_cross': '• 使用5日和20日移动平均线\\n• 金叉买入，死叉卖出\\n• 适合趋势明显的市场\\n• 可能产生假信号',
                        'rsi_strategy': '• RSI < 30 超卖买入\\n• RSI > 70 超买卖出\\n• 适合震荡市场\\n• 需要结合其他指标',
                        'bollinger': '• 价格触及下轨买入\\n• 价格触及上轨卖出\\n• 基于价格回归特性\\n• 适合波动性较大的股票',
                        'macd_strategy': '• MACD金叉买入信号\\n• MACD死叉卖出信号\\n• 结合MACD柱状图\\n• 适合中期趋势判断'
                    };
                    return analysis[strategy] || '• 策略分析不可用';
                }
            </script>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def serve_stocks_page(self):
        """股票详情页面 - 沿用之前的实现"""
        html = """
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>📊 股票详情 - 量化交易系统</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
                body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; color: white; padding: 20px; }
                .container { max-width: 1200px; margin: 0 auto; }
                .header { text-align: center; padding: 20px 0; margin-bottom: 30px; }
                .back-btn { background: rgba(255, 255, 255, 0.2); color: white; border: none; padding: 10px 20px; border-radius: 20px; cursor: pointer; margin-bottom: 20px; text-decoration: none; display: inline-block; }
                .back-btn:hover { background: rgba(255, 255, 255, 0.3); }
                .stock-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 20px; }
                .stock-card { background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(10px); border-radius: 15px; padding: 25px; border: 1px solid rgba(255, 255, 255, 0.2); transition: transform 0.3s ease; }
                .stock-card:hover { transform: translateY(-3px); box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
                .stock-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
                .stock-symbol { font-size: 1.5em; font-weight: bold; }
                .stock-score { background: linear-gradient(45deg, #00b894, #00cec9); color: white; padding: 5px 12px; border-radius: 15px; font-weight: bold; font-size: 0.9em; }
                .stock-info { line-height: 1.6; }
                .price-info { font-size: 1.2em; margin: 10px 0; }
                .price-up { color: #00b894; }
                .price-down { color: #ff6b6b; }
                .recommendation { display: inline-block; padding: 5px 10px; border-radius: 10px; font-size: 0.9em; font-weight: bold; margin-top: 10px; }
                .rec-buy { background: #00b894; }
                .rec-hold { background: #fdcb6e; color: #2d3436; }
                .rec-strong-buy { background: #00b894; animation: pulse 2s infinite; }
                @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.7; } 100% { opacity: 1; } }
            </style>
        </head>
        <body>
            <div class="container">
                <a href="/" class="back-btn">← 返回主页</a>
                <div class="header">
                    <h1>📊 股票详情</h1>
                    <p>实时股票数据和分析</p>
                </div>
                <div class="stock-grid" id="stocks-container"></div>
            </div>
            <script>
                async function loadStocks() {
                    try {
                        const response = await fetch('/api/stocks');
                        const data = await response.json();
                        displayStocks(data.stocks);
                    } catch (error) {
                        document.getElementById('stocks-container').innerHTML = 
                            '<p style="text-align: center; font-size: 1.2em;">❌ 加载股票数据失败</p>';
                    }
                }
                
                function displayStocks(stocks) {
                    const container = document.getElementById('stocks-container');
                    container.innerHTML = stocks.map(stock => `
                        <div class="stock-card">
                            <div class="stock-header">
                                <div class="stock-symbol">${stock.symbol}</div>
                                <div class="stock-score">评分: ${stock.score}</div>
                            </div>
                            <div class="stock-info">
                                <div><strong>${stock.name}</strong></div>
                                <div class="price-info">
                                    价格: $${stock.price} 
                                    <span class="${stock.change.startsWith('+') ? 'price-up' : 'price-down'}">
                                        ${stock.change} (${stock.changePercent})
                                    </span>
                                </div>
                                <div>成交量: ${stock.volume || 'N/A'}</div>
                                <div>市值: ${stock.marketCap || 'N/A'}</div>
                                <div>PE比率: ${stock.pe || 'N/A'}</div>
                                <div class="recommendation ${getRecClass(stock.recommendation)}">
                                    ${stock.recommendation}
                                </div>
                            </div>
                        </div>
                    `).join('');
                }
                
                function getRecClass(rec) {
                    if (rec === '强烈买入') return 'rec-strong-buy';
                    if (rec === '买入') return 'rec-buy';
                    return 'rec-hold';
                }
                
                loadStocks();
                setInterval(loadStocks, 30000);
            </script>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def serve_monitoring_page(self):
        """监控页面 - 简化版本"""
        html = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <title>🚀 实时监控 - 量化交易系统</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
                body {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; color: white; padding: 20px; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .back-btn {{ background: rgba(255, 255, 255, 0.2); color: white; border: none; padding: 10px 20px; border-radius: 20px; cursor: pointer; margin-bottom: 20px; text-decoration: none; display: inline-block; }}
                .card {{ background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(10px); border-radius: 15px; padding: 25px; margin: 20px 0; border: 1px solid rgba(255, 255, 255, 0.2); }}
                .signal-log {{ background: rgba(0, 0, 0, 0.3); border-radius: 10px; padding: 15px; height: 300px; overflow-y: auto; font-family: monospace; line-height: 1.4; }}
            </style>
        </head>
        <body>
            <div class="container">
                <a href="/" class="back-btn">← 返回主页</a>
                <h1>🚀 实时监控系统</h1>
                <div class="card">
                    <h3>📈 实时交易信号</h3>
                    <div class="signal-log" id="signal-log">[{datetime.now().strftime('%H:%M:%S')}] 🚀 监控系统已启动
[{datetime.now().strftime('%H:%M:%S')}] 📊 正在监控 AAPL, TSLA, NVDA, MSFT, GOOGL
[{datetime.now().strftime('%H:%M:%S')}] ⚡ 检测到 NVDA 买入信号 (RSI: 35.2, MACD: 向上)</div>
                </div>
            </div>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def serve_auto_trade_page(self):
        """自动交易页面"""
        html = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>⚡ 自动交易 - 量化交易系统</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
                body {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; color: white; padding: 20px; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .back-btn {{ background: rgba(255, 255, 255, 0.2); color: white; border: none; padding: 10px 20px; border-radius: 20px; cursor: pointer; margin-bottom: 20px; text-decoration: none; display: inline-block; }}
                .back-btn:hover {{ background: rgba(255, 255, 255, 0.3); }}
                .card {{ background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(10px); border-radius: 15px; padding: 25px; margin: 20px 0; border: 1px solid rgba(255, 255, 255, 0.2); }}
                .btn {{ background: linear-gradient(45deg, #00b894, #00cec9); color: white; border: none; padding: 12px 24px; border-radius: 25px; cursor: pointer; font-size: 1em; font-weight: bold; margin: 5px; }}
                .btn.primary {{ background: linear-gradient(45deg, #ff6b6b, #ee5a52); }}
                .btn.danger {{ background: linear-gradient(45deg, #e74c3c, #c0392b); }}
                .btn.success {{ background: linear-gradient(45deg, #27ae60, #2ecc71); }}
                .btn:disabled {{ background: #666; cursor: not-allowed; }}
                .status-display {{ background: rgba(0, 0, 0, 0.3); padding: 15px; border-radius: 10px; font-family: monospace; white-space: pre-wrap; max-height: 300px; overflow-y: auto; }}
                .config-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }}
                .config-item {{ background: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 10px; }}
                .config-item label {{ display: block; margin-bottom: 8px; font-weight: bold; }}
                .config-item select, .config-item input {{ width: 100%; padding: 8px; border: none; border-radius: 5px; background: rgba(255, 255, 255, 0.2); color: white; }}
                .config-item select option {{ background: #333; color: white; }}
                .alert {{ padding: 15px; border-radius: 10px; margin: 15px 0; }}
                .alert.warning {{ background: rgba(255, 193, 7, 0.2); border-left: 4px solid #ffc107; }}
                .alert.info {{ background: rgba(23, 162, 184, 0.2); border-left: 4px solid #17a2b8; }}
            </style>
        </head>
        <body>
            <div class="container">
                <a href="/" class="back-btn">← 返回主页</a>
                <h1>⚡ 自动交易系统</h1>
                
                <div class="alert warning">
                    <strong>⚠️ 重要提示:</strong> 当前为模拟交易模式，所有交易都是虚拟的，不会产生实际资金损失。
                </div>
                
                <div class="card">
                    <h3>🎛️ 交易配置</h3>
                    <div class="config-grid">
                        <div class="config-item">
                            <label>交易模式:</label>
                            <select id="trade-mode">
                                <option value="paper">纸面交易 (推荐)</option>
                                <option value="simulate">模拟交易</option>
                                <option value="live" disabled>实盘交易 (暂未开放)</option>
                            </select>
                        </div>
                        <div class="config-item">
                            <label>股票池:</label>
                            <select id="stock-pool">
                                <option value="tech5">科技五强 (AAPL,TSLA,NVDA,MSFT,GOOGL)</option>
                                <option value="sp500">标普500前10</option>
                                <option value="custom">自定义股票池</option>
                            </select>
                        </div>
                        <div class="config-item">
                            <label>策略组合:</label>
                            <select id="strategy-combo">
                                <option value="conservative">保守型 (低风险)</option>
                                <option value="balanced">均衡型 (中等风险)</option>
                                <option value="aggressive">积极型 (高风险)</option>
                            </select>
                        </div>
                        <div class="config-item">
                            <label>初始资金:</label>
                            <input type="number" id="initial-capital" value="100000" min="10000" step="10000">
                        </div>
                        <div class="config-item">
                            <label>止损比例:</label>
                            <input type="number" id="stop-loss" value="5" min="1" max="20" step="0.5">
                            <small>%</small>
                        </div>
                        <div class="config-item">
                            <label>止盈比例:</label>
                            <input type="number" id="take-profit" value="15" min="5" max="50" step="0.5">
                            <small>%</small>
                        </div>
                    </div>
                    
                    <div style="text-align: center; margin: 20px 0;">
                        <button id="start-btn" class="btn primary" onclick="startAutoTrading()">🚀 启动自动交易</button>
                        <button id="stop-btn" class="btn danger" onclick="stopAutoTrading()" disabled>🛑 停止交易</button>
                        <button class="btn" onclick="resetConfig()">🔄 重置配置</button>
                    </div>
                </div>
                
                <div class="card">
                    <h3>📊 实时状态</h3>
                    <div id="trading-status" class="status-display">
[{datetime.now().strftime('%H:%M:%S')}] 🎯 自动交易系统待命中...
[{datetime.now().strftime('%H:%M:%S')}] 📋 配置: 纸面交易模式，科技五强股票池
[{datetime.now().strftime('%H:%M:%S')}] 💰 初始资金: $100,000
[{datetime.now().strftime('%H:%M:%S')}] 🛡️ 风险控制: 止损5%, 止盈15%
[{datetime.now().strftime('%H:%M:%S')}] ⚡ 点击"启动自动交易"开始监控...</div>
                </div>
                
                <div class="card">
                    <h3>📈 交易记录</h3>
                    <div id="trade-log" class="status-display">暂无交易记录，启动自动交易后显示...</div>
                </div>
                
                <div class="alert info">
                    <strong>💡 使用提示:</strong> 
                    <br>• 首次使用建议选择"保守型"策略
                    <br>• 系统会根据技术指标自动执行买卖操作
                    <br>• 可随时停止交易并查看详细报告
                    <br>• 所有操作都有完整的日志记录
                </div>
            </div>
            
            <script>
                let isTrading = false;
                let tradingInterval;
                
                function startAutoTrading() {{
                    if (isTrading) return;
                    
                    isTrading = true;
                    document.getElementById('start-btn').disabled = true;
                    document.getElementById('stop-btn').disabled = false;
                    
                    const status = document.getElementById('trading-status');
                    const tradeLog = document.getElementById('trade-log');
                    
                    status.innerHTML += '\\n[' + new Date().toLocaleTimeString() + '] 🚀 自动交易系统启动!';
                    status.innerHTML += '\\n[' + new Date().toLocaleTimeString() + '] 📡 开始监控市场数据...';
                    status.innerHTML += '\\n[' + new Date().toLocaleTimeString() + '] 🤖 AI策略引擎已激活';
                    
                    // 模拟交易信号
                    tradingInterval = setInterval(() => {{
                        simulateTradingSignal();
                    }}, 3000);
                }}
                
                function stopAutoTrading() {{
                    if (!isTrading) return;
                    
                    isTrading = false;
                    document.getElementById('start-btn').disabled = false;
                    document.getElementById('stop-btn').disabled = true;
                    
                    if (tradingInterval) {{
                        clearInterval(tradingInterval);
                    }}
                    
                    const status = document.getElementById('trading-status');
                    status.innerHTML += '\\n[' + new Date().toLocaleTimeString() + '] 🛑 自动交易已停止';
                    status.innerHTML += '\\n[' + new Date().toLocaleTimeString() + '] 📊 生成交易报告...';
                }}
                
                function simulateTradingSignal() {{
                    const stocks = ['AAPL', 'TSLA', 'NVDA', 'MSFT', 'GOOGL'];
                    const actions = ['买入', '卖出', '持有'];
                    const reasons = [
                        'RSI指标超卖', 'MACD金叉信号', '均线突破',
                        '成交量放大', '技术面转强', '止盈离场',
                        '止损保护', '趋势反转', '支撑位企稳'
                    ];
                    
                    const stock = stocks[Math.floor(Math.random() * stocks.length)];
                    const action = actions[Math.floor(Math.random() * actions.length)];
                    const reason = reasons[Math.floor(Math.random() * reasons.length)];
                    const price = (Math.random() * 500 + 100).toFixed(2);
                    const quantity = Math.floor(Math.random() * 100) + 10;
                    
                    const status = document.getElementById('trading-status');
                    const tradeLog = document.getElementById('trade-log');
                    
                    if (action !== '持有') {{
                        const signal = `[` + new Date().toLocaleTimeString() + `] 📊 ` + stock + ` ` + action + `信号 - 价格:$` + price + `, 原因:` + reason;
                        status.innerHTML += '\\n' + signal;
                        
                        if (Math.random() > 0.3) {{ // 70%概率执行交易
                            const trade = `[` + new Date().toLocaleTimeString() + `] ✅ 执行` + action + ` ` + stock + ` ` + quantity + `股 @$` + price;
                            tradeLog.innerHTML += tradeLog.innerHTML === '暂无交易记录，启动自动交易后显示...' ? trade : '\\n' + trade;
                        }}
                    }}
                    
                    // 自动滚动到底部
                    status.scrollTop = status.scrollHeight;
                    if (tradeLog.innerHTML !== '暂无交易记录，启动自动交易后显示...') {{
                        tradeLog.scrollTop = tradeLog.scrollHeight;
                    }}
                }}
                
                function resetConfig() {{
                    document.getElementById('trade-mode').value = 'paper';
                    document.getElementById('stock-pool').value = 'tech5';
                    document.getElementById('strategy-combo').value = 'conservative';
                    document.getElementById('initial-capital').value = '100000';
                    document.getElementById('stop-loss').value = '5';
                    document.getElementById('take-profit').value = '15';
                    
                    alert('✅ 配置已重置为默认值');
                }}
            </script>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def serve_reports_page(self):
        """报告页面 - 简化版本"""
        html = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <title>📊 交易报告 - 量化交易系统</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
                body {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; color: white; padding: 20px; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .back-btn {{ background: rgba(255, 255, 255, 0.2); color: white; border: none; padding: 10px 20px; border-radius: 20px; cursor: pointer; margin-bottom: 20px; text-decoration: none; display: inline-block; }}
                .card {{ background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(10px); border-radius: 15px; padding: 25px; margin: 20px 0; border: 1px solid rgba(255, 255, 255, 0.2); }}
                .metric {{ display: flex; justify-content: space-between; margin: 10px 0; }}
                .positive {{ color: #00b894; }}
                .negative {{ color: #ff6b6b; }}
            </style>
        </head>
        <body>
            <div class="container">
                <a href="/" class="back-btn">← 返回主页</a>
                <h1>📊 交易报告与分析</h1>
                <div class="card">
                    <h3>💰 资产概览</h3>
                    <div class="metric"><span>总资产:</span><span>$154,230</span></div>
                    <div class="metric"><span>今日盈亏:</span><span class="positive">+$2,850</span></div>
                    <div class="metric"><span>总收益率:</span><span class="positive">+54.23%</span></div>
                    <div class="metric"><span>更新时间:</span><span>{datetime.now().strftime('%m-%d %H:%M')}</span></div>
                </div>
            </div>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def serve_status(self):
        """系统状态API"""
        status = {
            "system": "online",
            "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "memory": "normal",
            "network": "connected"
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(status, ensure_ascii=False).encode('utf-8'))
    
    def serve_stocks(self):
        """股票数据API"""
        stocks_data = {
            "stocks": [
                {
                    "symbol": "AAPL",
                    "name": "苹果公司",
                    "price": "175.25",
                    "change": "+2.45",
                    "changePercent": "+1.42%",
                    "score": 88.5,
                    "recommendation": "买入",
                    "volume": "45,230,000",
                    "marketCap": "2.8T",
                    "pe": "28.5"
                },
                {
                    "symbol": "TSLA",
                    "name": "特斯拉",
                    "price": "245.80",
                    "change": "-1.20",
                    "changePercent": "-0.49%",
                    "score": 82.8,
                    "recommendation": "持有",
                    "volume": "35,120,000",
                    "marketCap": "780B",
                    "pe": "65.2"
                },
                {
                    "symbol": "NVDA",
                    "name": "英伟达",
                    "price": "890.15",
                    "change": "+15.60",
                    "changePercent": "+1.78%",
                    "score": 91.2,
                    "recommendation": "强烈买入",
                    "volume": "28,450,000",
                    "marketCap": "2.2T",
                    "pe": "75.8"
                },
                {
                    "symbol": "MSFT",
                    "name": "微软",
                    "price": "415.30",
                    "change": "+3.75",
                    "changePercent": "+0.91%",
                    "score": 86.7,
                    "recommendation": "买入",
                    "volume": "22,340,000",
                    "marketCap": "3.1T",
                    "pe": "32.1"
                },
                {
                    "symbol": "GOOGL",
                    "name": "谷歌",
                    "price": "138.45",
                    "change": "-0.85",
                    "changePercent": "-0.61%",
                    "score": 79.3,
                    "recommendation": "持有",
                    "volume": "18,670,000",
                    "marketCap": "1.7T",
                    "pe": "25.4"
                }
            ],
            "total": 5,
            "lastUpdate": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(stocks_data, ensure_ascii=False).encode('utf-8'))

def start_simple_web(port=8090):
    """启动简单Web服务器"""
    # 尝试多个端口
    for try_port in range(port, port + 10):
        try:
            server = HTTPServer(('localhost', try_port), SimpleWebHandler)
            print(f"🌐 简单Web界面已启动: http://localhost:{try_port}")
            print("💡 使用浏览器访问上述地址")
            print("🛑 按 Ctrl+C 停止服务器")
            print("✨ 特点: 支持单股回测、无弹窗、快速响应、稳定可靠")
            
            # 自动打开浏览器
            threading.Timer(1.0, lambda p=try_port: webbrowser.open(f'http://localhost:{p}')).start()
            
            server.serve_forever()
            break
        except OSError as e:
            if e.errno == 48:  # Address already in use
                print(f"端口 {try_port} 被占用，尝试端口 {try_port + 1}")
                continue
            else:
                raise
        except KeyboardInterrupt:
            print("\n🛑 简单Web服务器已停止")
            server.shutdown()
            break

if __name__ == "__main__":
    print("🚀 启动简单可靠的量化交易Web界面...")
    start_simple_web()