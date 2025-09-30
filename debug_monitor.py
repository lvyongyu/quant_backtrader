#!/usr/bin/env python3
"""
简化版多维度交易信号监控面板 - 调试版
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import json
import asyncio
import datetime
import requests
import math

app = FastAPI(title="交易信号监控")

def get_stock_data_simple(symbol: str) -> dict:
    """简化版股票数据获取"""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
        
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            if data['chart']['result'] and len(data['chart']['result']) > 0:
                result = data['chart']['result'][0]
                meta = result['meta']
                
                current_price = meta.get('regularMarketPrice', 0)
                prev_close = meta.get('previousClose', current_price)
                
                return {
                    'symbol': symbol,
                    'current_price': current_price,
                    'prev_close': prev_close,
                    'success': True
                }
        
        return {'success': False, 'error': 'No data found'}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.get("/")
async def get():
    return HTMLResponse(content="""
<!DOCTYPE html>
<html>
<head>
    <title>交易信号监控 - 调试版</title>
    <meta charset="UTF-8">
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 20px; 
            background: #1a1a1a; 
            color: white;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 30px; }
        .status { 
            margin: 20px 0; 
            text-align: center; 
            padding: 10px;
            border-radius: 5px;
            background: #333;
        }
        .stock-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 15px; 
        }
        .stock-card {
            background: #2a2a2a;
            border-radius: 8px;
            padding: 15px;
            border: 1px solid #444;
        }
        .symbol { font-size: 1.3em; font-weight: bold; color: #4CAF50; }
        .price { font-size: 1.5em; font-weight: bold; margin: 10px 0; }
        .change { margin-bottom: 10px; }
        .positive { color: #4CAF50; }
        .negative { color: #f44336; }
        .error { color: #ff6b6b; }
        .success { color: #4CAF50; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 交易信号监控 - 调试版</h1>
        </div>
        
        <div class="status" id="status">🔄 初始化中...</div>
        
        <div class="stock-grid" id="stockGrid">
            <!-- 股票数据将在这里显示 -->
        </div>
    </div>

    <script>
        const status = document.getElementById('status');
        const stockGrid = document.getElementById('stockGrid');
        
        // WebSocket连接
        let ws;
        let reconnectAttempts = 0;
        const maxReconnectAttempts = 5;
        
        function connectWebSocket() {
            try {
                ws = new WebSocket("ws://localhost:8001/ws");
                
                ws.onopen = function(event) {
                    console.log("WebSocket连接成功");
                    status.innerHTML = "🟢 WebSocket已连接";
                    status.className = "status success";
                    reconnectAttempts = 0;
                };
                
                ws.onmessage = function(event) {
                    console.log("收到数据:", event.data);
                    try {
                        const data = JSON.parse(event.data);
                        updateDisplay(data);
                        status.innerHTML = `🟢 最后更新: ${new Date().toLocaleTimeString()}`;
                    } catch (error) {
                        console.error("解析数据错误:", error);
                        status.innerHTML = "❌ 数据解析错误";
                        status.className = "status error";
                    }
                };
                
                ws.onclose = function(event) {
                    console.log("WebSocket连接关闭:", event.code, event.reason);
                    status.innerHTML = `🔴 连接断开 (${event.code})`;
                    status.className = "status error";
                    
                    if (reconnectAttempts < maxReconnectAttempts) {
                        reconnectAttempts++;
                        console.log(`尝试重连 ${reconnectAttempts}/${maxReconnectAttempts}`);
                        setTimeout(connectWebSocket, 3000);
                    }
                };
                
                ws.onerror = function(error) {
                    console.error("WebSocket错误:", error);
                    status.innerHTML = "❌ WebSocket错误";
                    status.className = "status error";
                };
                
            } catch (error) {
                console.error("创建WebSocket连接失败:", error);
                status.innerHTML = "❌ 无法创建连接";
                status.className = "status error";
            }
        }
        
        function updateDisplay(data) {
            if (!data.stocks || !Array.isArray(data.stocks)) {
                stockGrid.innerHTML = '<div class="error">无效的数据格式</div>';
                return;
            }
            
            stockGrid.innerHTML = '';
            
            data.stocks.forEach(stock => {
                const card = document.createElement('div');
                card.className = 'stock-card';
                
                const change = stock.current_price - stock.prev_close;
                const changePct = (change / stock.prev_close * 100);
                const changeClass = change >= 0 ? 'positive' : 'negative';
                
                card.innerHTML = `
                    <div class="symbol">${stock.symbol}</div>
                    <div class="price">$${stock.current_price.toFixed(2)}</div>
                    <div class="change ${changeClass}">
                        ${change >= 0 ? '+' : ''}${change.toFixed(2)} (${changePct.toFixed(1)}%)
                    </div>
                `;
                
                stockGrid.appendChild(card);
            });
        }
        
        // 页面加载完成后连接WebSocket
        window.addEventListener('load', function() {
            console.log("页面加载完成，开始连接WebSocket");
            connectWebSocket();
        });
    </script>
</body>
</html>
    """)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("客户端WebSocket连接成功")
    
    try:
        while True:
            print("开始获取股票数据...")
            
            symbols = ['AAPL', 'MSTR', 'TSLA']
            stock_data = []
            
            for symbol in symbols:
                print(f"获取{symbol}数据...")
                data = get_stock_data_simple(symbol)
                
                if data.get('success'):
                    stock_data.append(data)
                    print(f"{symbol}: ${data['current_price']:.2f}")
                else:
                    print(f"{symbol}数据获取失败: {data.get('error')}")
            
            message = {
                'timestamp': datetime.datetime.now().isoformat(),
                'stocks': stock_data
            }
            
            print(f"发送数据给客户端: {len(stock_data)}只股票")
            await websocket.send_text(json.dumps(message))
            
            await asyncio.sleep(10)  # 10秒更新一次
            
    except WebSocketDisconnect:
        print("客户端WebSocket连接断开")
    except Exception as e:
        print(f"WebSocket错误: {e}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 启动简化版交易信号监控...")
    print("🌐 访问地址: http://localhost:8001")
    print("🔧 调试模式 - 查看控制台输出")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")