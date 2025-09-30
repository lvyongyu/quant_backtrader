"""
FastAPI实时监控仪表板
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import json
import asyncio
from datetime import datetime
from typing import List, Dict
import backtrader as bt


app = FastAPI(title="Backtrader Trading Monitor", version="1.0.0")

# 活跃连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                pass

manager = ConnectionManager()

@app.get("/")
async def dashboard():
    """主仪表板页面"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>📈 Backtrader Trading Monitor</title>
        <meta charset="utf-8">
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 0; padding: 20px; background: #f5f5f7; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { text-align: center; margin-bottom: 30px; }
            .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
            .stat-card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
            .chart-container { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px; }
            .status-indicator { width: 12px; height: 12px; border-radius: 50%; display: inline-block; margin-right: 8px; }
            .online { background: #34c759; }
            .offline { background: #ff3b30; }
            .metric-value { font-size: 24px; font-weight: 600; margin-bottom: 5px; }
            .metric-label { color: #666; font-size: 14px; }
            .positive { color: #34c759; }
            .negative { color: #ff3b30; }
        </style>
    </head>
    <body>
        <div id="app" class="container">
            <div class="header">
                <h1>📈 Backtrader Trading Monitor</h1>
                <div>
                    <span class="status-indicator" :class="connected ? 'online' : 'offline'"></span>
                    {{ connected ? '实时连接' : '连接断开' }}
                </div>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="metric-value" :class="stats.totalReturn > 0 ? 'positive' : 'negative'">
                        {{ stats.totalReturn > 0 ? '+' : '' }}{{ stats.totalReturn }}%
                    </div>
                    <div class="metric-label">总收益率</div>
                </div>
                
                <div class="stat-card">
                    <div class="metric-value">{{ stats.winRate }}%</div>
                    <div class="metric-label">胜率</div>
                </div>
                
                <div class="stat-card">
                    <div class="metric-value">{{ stats.totalTrades }}</div>
                    <div class="metric-label">总交易数</div>
                </div>
                
                <div class="stat-card">
                    <div class="metric-value">${{ stats.currentValue.toLocaleString() }}</div>
                    <div class="metric-label">当前价值</div>
                </div>
            </div>
            
            <div class="chart-container">
                <div id="performance-chart" style="height: 400px;"></div>
            </div>
            
            <div class="chart-container">
                <div id="trades-chart" style="height: 300px;"></div>
            </div>
        </div>
        
        <script>
            const { createApp } = Vue;
            
            createApp({
                data() {
                    return {
                        connected: false,
                        stats: {
                            totalReturn: 0,
                            winRate: 0,
                            totalTrades: 0,
                            currentValue: 100000
                        },
                        performanceData: [],
                        tradesData: []
                    }
                },
                mounted() {
                    this.initWebSocket();
                    this.initCharts();
                },
                methods: {
                    initWebSocket() {
                        const ws = new WebSocket('ws://localhost:8000/ws');
                        
                        ws.onopen = () => {
                            this.connected = true;
                        };
                        
                        ws.onclose = () => {
                            this.connected = false;
                        };
                        
                        ws.onmessage = (event) => {
                            const data = JSON.parse(event.data);
                            this.updateDashboard(data);
                        };
                    },
                    
                    initCharts() {
                        // 性能图表
                        Plotly.newPlot('performance-chart', [{
                            x: [],
                            y: [],
                            type: 'scatter',
                            mode: 'lines',
                            name: '组合价值',
                            line: { color: '#007AFF' }
                        }], {
                            title: '组合价值走势',
                            xaxis: { title: '时间' },
                            yaxis: { title: '价值 ($)' }
                        });
                        
                        // 交易图表
                        Plotly.newPlot('trades-chart', [{
                            x: [],
                            y: [],
                            type: 'bar',
                            name: '每日交易',
                            marker: { color: '#34C759' }
                        }], {
                            title: '每日交易统计',
                            xaxis: { title: '日期' },
                            yaxis: { title: '交易数量' }
                        });
                    },
                    
                    updateDashboard(data) {
                        this.stats = data.stats;
                        
                        // 更新性能图表
                        Plotly.extendTraces('performance-chart', {
                            x: [[data.timestamp]],
                            y: [[data.stats.currentValue]]
                        }, [0]);
                        
                        // 更新交易图表
                        if (data.newTrade) {
                            Plotly.extendTraces('trades-chart', {
                                x: [[data.timestamp]],
                                y: [[1]]
                            }, [0]);
                        }
                    }
                }
            }).mount('#app');
        </script>
    </body>
    </html>
    """)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket连接处理"""
    await manager.connect(websocket)
    try:
        while True:
            # 模拟实时数据推送
            data = {
                "timestamp": datetime.now().isoformat(),
                "stats": {
                    "totalReturn": 12.45,
                    "winRate": 75,
                    "totalTrades": 23,
                    "currentValue": 112450
                },
                "newTrade": False
            }
            await websocket.send_text(json.dumps(data))
            await asyncio.sleep(1)  # 每秒更新
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/api/stats")
async def get_stats():
    """获取策略统计数据"""
    return {
        "totalReturn": 12.45,
        "winRate": 75,
        "totalTrades": 23,
        "currentValue": 112450,
        "sharpeRatio": 1.85,
        "maxDrawdown": -5.2
    }

@app.post("/api/strategy/start")
async def start_strategy():
    """启动策略"""
    return {"status": "started", "message": "策略已启动"}

@app.post("/api/strategy/stop") 
async def stop_strategy():
    """停止策略"""
    return {"status": "stopped", "message": "策略已停止"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 启动交易监控仪表板...")
    print("📊 访问: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)