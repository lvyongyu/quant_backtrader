#!/usr/bin/env python3
"""
Advanced Multi-Dimensional Signal Web Dashboard
高级多维度信号实时监控面板
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import json
import asyncio
import datetime
import requests
import math
from typing import List, Dict

app = FastAPI(title="多维度交易信号监控")

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

def get_enhanced_stock_data(symbol: str) -> Dict:
    """获取增强股票数据"""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data['chart']['result'] and len(data['chart']['result']) > 0:
                result = data['chart']['result'][0]
                meta = result['meta']
                
                current_price = meta.get('regularMarketPrice', 0)
                prev_close = meta.get('previousClose', current_price)
                
                quotes = result['indicators']['quote'][0]
                closes = [p for p in quotes.get('close', []) if p is not None][-30:]
                volumes = [p for p in quotes.get('volume', []) if p is not None][-30:]
                
                return {
                    'symbol': symbol,
                    'current_price': current_price,
                    'prev_close': prev_close,
                    'closes': closes,
                    'volumes': volumes,
                    'success': True
                }
        
        return {'success': False, 'error': 'No data found'}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def calculate_multi_signals(stock_data: Dict) -> Dict:
    """计算多维度信号"""
    
    if not stock_data.get('success'):
        return {}
    
    closes = stock_data['closes']
    volumes = stock_data['volumes']
    current_price = stock_data['current_price']
    
    if len(closes) < 20:
        return {}
    
    signals = {'current_price': current_price}
    
    # 1. 趋势指标
    sma_5 = sum(closes[-5:]) / 5
    sma_10 = sum(closes[-10:]) / 10
    sma_20 = sum(closes[-20:]) / 20
    
    # EMA计算
    def ema(prices, period):
        multiplier = 2 / (period + 1)
        ema_val = sum(prices[:period]) / period
        for price in prices[period:]:
            ema_val = (price * multiplier) + (ema_val * (1 - multiplier))
        return ema_val
    
    ema_12 = ema(closes, 12)
    ema_26 = ema(closes, 26)
    macd_line = ema_12 - ema_26
    
    # 趋势评分
    trend_score = 0
    if sma_5 > sma_10: trend_score += 1
    if sma_10 > sma_20: trend_score += 1
    if current_price > sma_20: trend_score += 1
    if macd_line > 0: trend_score += 1
    
    signals['trend_score'] = trend_score
    signals['sma_5'] = sma_5
    signals['sma_20'] = sma_20
    
    # 2. 动量指标
    def rsi(prices, period=14):
        if len(prices) < period + 1:
            return 50
        gains = [max(prices[i] - prices[i-1], 0) for i in range(1, len(prices))]
        losses = [max(prices[i-1] - prices[i], 0) for i in range(1, len(prices))]
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        if avg_loss == 0: return 100
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    rsi_val = rsi(closes)
    
    momentum_score = 0
    if 30 < rsi_val < 70: momentum_score += 2
    elif rsi_val < 30: momentum_score += 3  # 超卖，看多
    else: momentum_score = 0  # 超买，看空
    
    signals['momentum_score'] = momentum_score
    signals['rsi'] = rsi_val
    
    # 3. 成交量指标
    volume_sma = sum(volumes[-10:]) / 10
    volume_ratio = volumes[-1] / volume_sma if volume_sma > 0 else 1
    
    volume_score = 0
    if volume_ratio > 1.5: volume_score += 2
    elif volume_ratio > 1.2: volume_score += 1
    
    signals['volume_score'] = volume_score
    signals['volume_ratio'] = volume_ratio
    
    # 4. 波动率指标
    variance = sum((p - sma_20) ** 2 for p in closes[-20:]) / 20
    std_dev = math.sqrt(variance)
    bb_upper = sma_20 + (2 * std_dev)
    bb_lower = sma_20 - (2 * std_dev)
    bb_position = (current_price - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5
    
    volatility_score = 0
    if bb_position < 0.2: volatility_score += 3  # 接近下轨
    elif bb_position > 0.8: volatility_score = 0  # 接近上轨
    else: volatility_score += 1
    
    signals['volatility_score'] = volatility_score
    signals['bb_position'] = bb_position
    
    # 综合评分
    total_score = trend_score + momentum_score + volume_score + volatility_score
    max_possible = 10  # 4+3+2+3的最大值调整
    normalized_score = min(10, max(1, round((total_score / max_possible) * 9 + 1)))
    
    signals['total_score'] = normalized_score
    
    # 信号分类
    if normalized_score >= 8:
        signals['signal'] = 'STRONG_BUY'
        signals['color'] = '#22c55e'
    elif normalized_score >= 6:
        signals['signal'] = 'BUY'
        signals['color'] = '#84cc16'
    elif normalized_score <= 3:
        signals['signal'] = 'STRONG_SELL'
        signals['color'] = '#ef4444'
    elif normalized_score <= 5:
        signals['signal'] = 'SELL'
        signals['color'] = '#f97316'
    else:
        signals['signal'] = 'NEUTRAL'
        signals['color'] = '#64748b'
    
    return signals

@app.get("/")
async def get():
    return HTMLResponse(content="""
<!DOCTYPE html>
<html>
<head>
    <title>多维度交易信号监控</title>
    <meta charset="UTF-8">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body { 
            font-family: 'Segoe UI', Arial, sans-serif; 
            margin: 0; 
            background: #0f172a; 
            color: white;
        }
        .container { 
            max-width: 1400px; 
            margin: 0 auto; 
            padding: 20px; 
        }
        .header { 
            text-align: center; 
            margin-bottom: 30px; 
            border-bottom: 2px solid #1e293b;
            padding-bottom: 20px;
        }
        .header h1 { 
            color: #3b82f6; 
            margin: 0; 
            font-size: 2.5em;
        }
        .grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
            gap: 20px; 
            margin-bottom: 30px;
        }
        .card {
            background: #1e293b;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            border: 1px solid #334155;
            transition: transform 0.2s;
        }
        .card:hover { 
            transform: translateY(-2px);
        }
        .symbol { 
            font-size: 1.5em; 
            font-weight: bold; 
            margin-bottom: 15px;
        }
        .price { 
            font-size: 1.8em; 
            font-weight: bold; 
            margin-bottom: 10px;
        }
        .change { 
            margin-bottom: 15px;
        }
        .signal { 
            font-size: 1.2em; 
            font-weight: bold; 
            padding: 8px 16px; 
            border-radius: 20px; 
            text-align: center; 
            margin: 10px 0;
        }
        .score-bar {
            background: #374151;
            height: 20px;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        .score-fill {
            height: 100%;
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 0.9em;
        }
        .indicators {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 15px;
        }
        .indicator {
            background: #374151;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 0.9em;
        }
        .status { 
            margin: 20px 0; 
            text-align: center; 
            font-style: italic;
        }
        .positive { color: #22c55e; }
        .negative { color: #ef4444; }
        .chart-container {
            background: #1e293b;
            border-radius: 12px;
            padding: 20px;
            margin-top: 20px;
            border: 1px solid #334155;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 多维度交易信号监控面板</h1>
            <p>实时股票分析 | 多维度信号 | 智能决策</p>
        </div>
        
        <div class="status" id="status">🔄 连接中...</div>
        
        <div class="grid" id="stockGrid">
        </div>
        
        <div class="chart-container">
            <h3>📈 信号强度对比</h3>
            <div id="signalChart"></div>
        </div>
    </div>

    <script>
        const ws = new WebSocket("ws://localhost:8000/ws");
        const stockGrid = document.getElementById('stockGrid');
        const status = document.getElementById('status');
        
        let chartData = {
            symbols: [],
            scores: [],
            colors: []
        };

        ws.onopen = function(event) {
            status.innerHTML = "🟢 已连接 | 实时更新中";
            status.style.color = "#22c55e";
        };

        ws.onclose = function(event) {
            status.innerHTML = "🔴 连接断开 | 正在重连...";
            status.style.color = "#ef4444";
            setTimeout(() => location.reload(), 3000);
        };

        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            updateStockCards(data.stocks);
            updateChart(data.stocks);
        };

        function updateStockCards(stocks) {
            stockGrid.innerHTML = '';
            
            stocks.forEach(stock => {
                const card = createStockCard(stock);
                stockGrid.appendChild(card);
            });
        }

        function createStockCard(stock) {
            const card = document.createElement('div');
            card.className = 'card';
            
            const change = stock.current_price - stock.prev_close;
            const changePct = (change / stock.prev_close * 100);
            const changeClass = change >= 0 ? 'positive' : 'negative';
            
            card.innerHTML = `
                <div class="symbol">${stock.symbol}</div>
                <div class="price">$${stock.current_price.toFixed(2)}</div>
                <div class="change ${changeClass}">
                    ${change >= 0 ? '+' : ''}${change.toFixed(2)} (${changePct.toFixed(1)}%)
                </div>
                
                <div class="signal" style="background-color: ${stock.color}">
                    ${stock.signal}
                </div>
                
                <div class="score-bar">
                    <div class="score-fill" style="width: ${stock.total_score * 10}%; background-color: ${stock.color}">
                        ${stock.total_score}/10
                    </div>
                </div>
                
                <div class="indicators">
                    <div class="indicator">
                        📈 趋势: ${stock.trend_score}/4
                    </div>
                    <div class="indicator">
                        ⚡ 动量: ${stock.momentum_score}/3
                    </div>
                    <div class="indicator">
                        📊 成交量: ${stock.volume_score}/2
                    </div>
                    <div class="indicator">
                        📉 波动: ${stock.volatility_score}/3
                    </div>
                    <div class="indicator">
                        RSI: ${stock.rsi.toFixed(1)}
                    </div>
                    <div class="indicator">
                        成交量比: ${stock.volume_ratio.toFixed(2)}x
                    </div>
                </div>
            `;
            
            return card;
        }

        function updateChart(stocks) {
            const symbols = stocks.map(s => s.symbol);
            const scores = stocks.map(s => s.total_score);
            const colors = stocks.map(s => s.color);
            
            const trace = {
                x: symbols,
                y: scores,
                type: 'bar',
                marker: {
                    color: colors,
                    line: {
                        color: '#64748b',
                        width: 1
                    }
                },
                text: scores.map(s => `${s}/10`),
                textposition: 'auto',
                textfont: {
                    color: 'white'
                }
            };
            
            const layout = {
                paper_bgcolor: '#1e293b',
                plot_bgcolor: '#374151',
                font: { color: 'white' },
                xaxis: { 
                    title: '股票代码',
                    gridcolor: '#4b5563'
                },
                yaxis: { 
                    title: '信号强度',
                    range: [0, 10],
                    gridcolor: '#4b5563'
                },
                margin: { t: 20, r: 20, b: 50, l: 50 }
            };
            
            Plotly.newPlot('signalChart', [trace], layout, {responsive: true});
        }
    </script>
</body>
</html>
    """)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # 监控的股票列表
            symbols = ['AAPL', 'MSTR', 'TSLA', 'NVDA', 'MSFT', 'GOOGL']
            stock_data = []
            
            for symbol in symbols:
                data = get_enhanced_stock_data(symbol)
                if data.get('success'):
                    signals = calculate_multi_signals(data)
                    if signals:
                        stock_data.append({
                            'symbol': symbol,
                            'current_price': data['current_price'],
                            'prev_close': data['prev_close'],
                            **signals
                        })
            
            message = {
                'timestamp': datetime.datetime.now().isoformat(),
                'stocks': stock_data
            }
            
            await manager.broadcast(json.dumps(message))
            await asyncio.sleep(5)  # 每5秒更新一次
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    print("🚀 启动多维度交易信号监控面板...")
    print("📊 访问地址: http://localhost:8001")
    print("📈 监控股票: AAPL, MSTR, TSLA, NVDA, MSFT, GOOGL")
    uvicorn.run(app, host="0.0.0.0", port=8001)