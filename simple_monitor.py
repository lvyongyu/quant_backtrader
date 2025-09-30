#!/usr/bin/env python3
"""
纯HTML版股票监控面板 - 无依赖版本
"""

import http.server
import socketserver
import json
import requests
import threading
import time
import datetime

# 全局股票数据存储
stock_data_global = {}

def get_stock_data(symbol: str) -> dict:
    """获取股票数据"""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data['chart']['result'] and len(data['chart']['result']) > 0:
                result = data['chart']['result'][0]
                meta = result['meta']
                
                current_price = meta.get('regularMarketPrice', 0)
                prev_close = meta.get('previousClose', current_price)
                
                # 获取历史数据用于技术指标
                quotes = result['indicators']['quote'][0]
                closes = [p for p in quotes.get('close', []) if p is not None][-20:]
                
                # 计算简单指标
                sma_5 = sum(closes[-5:]) / 5 if len(closes) >= 5 else current_price
                sma_20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else current_price
                
                # 简单RSI计算
                def simple_rsi(prices):
                    if len(prices) < 14:
                        return 50
                    gains = [max(prices[i] - prices[i-1], 0) for i in range(1, len(prices))]
                    losses = [max(prices[i-1] - prices[i], 0) for i in range(1, len(prices))]
                    avg_gain = sum(gains[-14:]) / 14
                    avg_loss = sum(losses[-14:]) / 14
                    if avg_loss == 0:
                        return 100
                    rs = avg_gain / avg_loss
                    return 100 - (100 / (1 + rs))
                
                rsi = simple_rsi(closes)
                
                # 简单信号评分
                score = 5  # 基础分
                if current_price > sma_5: score += 1
                if sma_5 > sma_20: score += 1
                if rsi < 30: score += 2
                elif rsi > 70: score -= 2
                
                signal = 'BUY' if score >= 7 else 'SELL' if score <= 4 else 'NEUTRAL'
                color = '#4CAF50' if signal == 'BUY' else '#f44336' if signal == 'SELL' else '#FFC107'
                
                return {
                    'symbol': symbol,
                    'current_price': current_price,
                    'prev_close': prev_close,
                    'sma_5': sma_5,
                    'sma_20': sma_20,
                    'rsi': rsi,
                    'score': score,
                    'signal': signal,
                    'color': color,
                    'success': True,
                    'timestamp': datetime.datetime.now().strftime('%H:%M:%S')
                }
        
        return {'success': False, 'error': 'No data found'}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def update_stock_data():
    """定期更新股票数据"""
    symbols = ['AAPL', 'MSTR', 'TSLA', 'NVDA', 'MSFT']
    
    while True:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 更新股票数据...")
        
        for symbol in symbols:
            data = get_stock_data(symbol)
            stock_data_global[symbol] = data
            
            if data.get('success'):
                print(f"  {symbol}: ${data['current_price']:.2f} ({data['signal']})")
            else:
                print(f"  {symbol}: 获取失败 - {data.get('error')}")
        
        time.sleep(10)  # 每10秒更新一次

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path.startswith('/?'):
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>📊 股票监控面板</title>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="10">
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            margin: 0; 
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
            color: white;
            min-height: 100vh;
        }}
        .container {{ 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 20px; 
        }}
        .header {{ 
            text-align: center; 
            margin-bottom: 30px; 
            padding: 20px;
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }}
        .header h1 {{ 
            margin: 0; 
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }}
        .timestamp {{
            margin-top: 10px;
            opacity: 0.8;
            font-size: 1.1em;
        }}
        .stock-grid {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); 
            gap: 20px; 
        }}
        .stock-card {{
            background: rgba(255,255,255,0.15);
            border-radius: 15px;
            padding: 25px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            transition: transform 0.3s ease;
        }}
        .stock-card:hover {{
            transform: translateY(-5px);
        }}
        .symbol {{ 
            font-size: 1.8em; 
            font-weight: bold; 
            margin-bottom: 15px;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
        }}
        .price {{ 
            font-size: 2.2em; 
            font-weight: bold; 
            margin: 15px 0;
        }}
        .change {{ 
            font-size: 1.2em;
            margin-bottom: 15px; 
        }}
        .signal {{
            font-size: 1.3em;
            font-weight: bold;
            padding: 10px 20px;
            border-radius: 25px;
            text-align: center;
            margin: 15px 0;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
        }}
        .indicators {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 15px;
        }}
        .indicator {{
            background: rgba(255,255,255,0.1);
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 0.9em;
            text-align: center;
        }}
        .positive {{ color: #4CAF50; }}
        .negative {{ color: #f44336; }}
        .error {{ 
            background: rgba(244, 67, 54, 0.2); 
            color: #ffcdd2;
            text-align: center;
            padding: 20px;
            border-radius: 10px;
            margin: 10px;
        }}
        .loading {{
            text-align: center;
            font-size: 1.2em;
            padding: 40px;
            opacity: 0.8;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 实时股票监控面板</h1>
            <div class="timestamp">最后更新: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </div>
        
        <div class="stock-grid">
"""
            
            # 添加股票卡片
            if not stock_data_global:
                html_content += '<div class="loading">🔄 正在加载股票数据...</div>'
            else:
                for symbol, data in stock_data_global.items():
                    if data.get('success'):
                        change = data['current_price'] - data['prev_close']
                        change_pct = (change / data['prev_close'] * 100)
                        change_class = 'positive' if change >= 0 else 'negative'
                        
                        html_content += f"""
            <div class="stock-card">
                <div class="symbol">{data['symbol']}</div>
                <div class="price">${data['current_price']:.2f}</div>
                <div class="change {change_class}">
                    {'+' if change >= 0 else ''}{change:.2f} ({change_pct:+.1f}%)
                </div>
                <div class="signal" style="background-color: {data['color']};">
                    {data['signal']} ({data['score']}/10)
                </div>
                <div class="indicators">
                    <div class="indicator">SMA5: ${data['sma_5']:.2f}</div>
                    <div class="indicator">SMA20: ${data['sma_20']:.2f}</div>
                    <div class="indicator">RSI: {data['rsi']:.1f}</div>
                    <div class="indicator">更新: {data['timestamp']}</div>
                </div>
            </div>
"""
                    else:
                        html_content += f"""
            <div class="stock-card error">
                <div class="symbol">{symbol}</div>
                <div>❌ 数据获取失败</div>
                <div>{data.get('error', '未知错误')}</div>
            </div>
"""
            
            html_content += """
        </div>
    </div>
</body>
</html>
"""
            
            self.wfile.write(html_content.encode('utf-8'))
            
        elif self.path == '/api/data':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(json.dumps(stock_data_global).encode('utf-8'))
        else:
            super().do_GET()

def main():
    PORT = 8002
    
    # 启动数据更新线程
    data_thread = threading.Thread(target=update_stock_data, daemon=True)
    data_thread.start()
    
    print("🚀 启动股票监控面板...")
    print(f"🌐 访问地址: http://localhost:{PORT}")
    print("📊 监控股票: AAPL, MSTR, TSLA, NVDA, MSFT")
    print("🔄 页面每10秒自动刷新")
    print("📈 ESC键或Ctrl+C退出")
    
    # 启动HTTP服务器
    with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 服务器已停止")

if __name__ == "__main__":
    main()