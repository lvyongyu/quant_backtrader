#!/usr/bin/env python3
"""
🔧 后端API服务器 - 量化交易系统
专注于API逻辑，前后端分离架构
"""

import os
import sys
import json
import threading
import webbrowser
import argparse
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class APIHandler(BaseHTTPRequestHandler):
    """API处理器 - 专注于后端逻辑"""
    
    def log_message(self, format, *args):
        """自定义日志"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {format % args}")
    
    def do_GET(self):
        """处理GET请求"""
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            
            # 静态文件路由
            if path.startswith('/static/'):
                self.serve_static_file(path)
            # 页面路由
            elif path == '/':
                self.serve_template('index.html')
            elif path == '/stocks':
                self.serve_template('stocks.html')
            elif path == '/backtest':
                self.serve_template('backtest.html')
            elif path == '/auto_trade':
                self.serve_template('auto_trade.html')
            elif path == '/monitoring':
                self.serve_template('monitoring.html')
            elif path == '/reports':
                self.serve_template('reports.html')
            # API路由
            elif path == '/api/status':
                self.api_system_status()
            elif path == '/api/stocks':
                self.api_stocks_data()
            elif path == '/api/backtest':
                self.api_run_backtest(parse_qs(parsed_url.query))
            elif path == '/api/auto_trade/start':
                self.api_start_auto_trade()
            elif path == '/api/auto_trade/stop':
                self.api_stop_auto_trade()
            elif path == '/api/watchlist':
                self.api_get_watchlist()
            elif path.startswith('/api/watchlist/'):
                symbol = path.split('/')[-1]
                self.api_get_stock_info(symbol)
            else:
                self.send_error(404)
        except Exception as e:
            print(f"❌ API错误: {e}")
            self.send_error(500, str(e))
    
    def do_POST(self):
        """处理POST请求"""
        try:
            # 安全地获取Content-Length
            content_length = self.headers.get('Content-Length')
            if content_length:
                content_length = int(content_length)
                post_data = self.rfile.read(content_length)
                
                # 尝试解析JSON数据，如果失败则使用空字典
                try:
                    data = json.loads(post_data.decode('utf-8'))
                except:
                    data = {}
            else:
                data = {}
            
            if self.path == '/api/backtest':
                self.api_run_backtest_post(data)
            elif self.path == '/api/auto_trade/start':
                self.api_start_auto_trade()
            elif self.path == '/api/auto_trade/stop':
                self.api_stop_auto_trade()
            elif self.path == '/api/auto_trade/config':
                self.api_update_trade_config(data)
            elif self.path == '/api/watchlist/add':
                self.api_add_to_watchlist(data)
            elif self.path == '/api/watchlist/remove':
                self.api_remove_from_watchlist(data)
            else:
                self.send_error(404)
        except Exception as e:
            print(f"❌ POST错误: {e}")
            self.send_error(500, str(e))
    
    def serve_static_file(self, path):
        """提供静态文件服务"""
        file_path = os.path.join(os.path.dirname(__file__), '..', path[1:])  # 移除开头的 /
        
        if not os.path.exists(file_path):
            self.send_error(404)
            return
        
        # 根据文件扩展名设置Content-Type
        if path.endswith('.css'):
            content_type = 'text/css'
        elif path.endswith('.js'):
            content_type = 'application/javascript'
        elif path.endswith('.html'):
            content_type = 'text/html'
        else:
            content_type = 'application/octet-stream'
        
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-type', content_type + '; charset=utf-8')
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            print(f"❌ 静态文件错误: {e}")
            self.send_error(500)
    
    def serve_template(self, template_name):
        """提供HTML模板服务"""
        template_path = os.path.join(os.path.dirname(__file__), '..', 'templates', template_name)
        
        if not os.path.exists(template_path):
            self.send_error(404, f"模板文件不存在: {template_name}")
            return
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        except Exception as e:
            print(f"❌ 模板错误: {e}")
            self.send_error(500)
    
    # ===================
    # API接口实现
    # ===================
    
    def api_system_status(self):
        """系统状态API - 返回真实系统状态"""
        try:
            # 尝试获取真实系统信息
            memory_info = self._get_memory_info()
            cpu_info = self._get_cpu_info()
            disk_info = self._get_disk_info()
            
            # 检查核心组件状态
            components_status = self._check_components_status()
            
            # 检查网络连接
            network_status = self._check_network_status()
            
            # 检查数据文件状态
            data_files_status = self._check_data_files_status()
            
            status = {
                "system": "online",
                "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "uptime": self._get_system_uptime(),
                "memory": memory_info,
                "cpu": cpu_info,
                "disk": disk_info,
                "network": network_status,
                "components": components_status,
                "data_files": data_files_status,
                "api_server": {
                    "status": "running",
                    "host": "localhost",
                    "port": 8000,
                    "requests_handled": getattr(self, '_request_count', 0)
                }
            }
        except Exception as e:
            # 如果获取真实状态失败，返回基础状态
            status = {
                "system": "online",
                "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "memory": {"status": "unknown", "error": str(e)},
                "network": "unknown",
                "components": {
                    "data_engine": "unknown",
                    "strategy_engine": "unknown", 
                    "risk_engine": "unknown",
                    "trading_engine": "unknown"
                },
                "error": f"系统状态检查失败: {str(e)}"
            }
        
        self.send_json_response(status)
    
    def _get_memory_info(self):
        """获取内存信息"""
        try:
            import psutil
            memory_info = psutil.virtual_memory()
            return {
                "usage_percent": round(memory_info.percent, 1),
                "available_gb": round(memory_info.available / (1024**3), 1),
                "total_gb": round(memory_info.total / (1024**3), 1),
                "status": "normal" if memory_info.percent < 80 else "warning" if memory_info.percent < 90 else "critical"
            }
        except ImportError:
            # 备用方法：使用系统命令
            try:
                import subprocess
                result = subprocess.run(['vm_stat'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return {"status": "normal", "source": "system_command"}
                else:
                    return {"status": "unknown", "source": "fallback"}
            except Exception:
                return {"status": "unknown", "source": "fallback"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _get_cpu_info(self):
        """获取CPU信息"""
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=1)
            return {
                "usage_percent": round(cpu_percent, 1),
                "status": "normal" if cpu_percent < 70 else "warning" if cpu_percent < 85 else "critical"
            }
        except ImportError:
            return {"status": "unknown", "source": "psutil_unavailable"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _get_disk_info(self):
        """获取磁盘信息"""
        try:
            import psutil
            disk_info = psutil.disk_usage('/')
            return {
                "usage_percent": round(disk_info.percent, 1),
                "free_gb": round(disk_info.free / (1024**3), 1),
                "total_gb": round(disk_info.total / (1024**3), 1),
                "status": "normal" if disk_info.percent < 80 else "warning" if disk_info.percent < 90 else "critical"
            }
        except ImportError:
            return {"status": "unknown", "source": "psutil_unavailable"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _check_components_status(self):
        """检查系统组件状态"""
        components = {}
        
        try:
            # 检查主要Python模块是否可导入
            modules_to_check = [
                ('data_engine', 'src.data'),
                ('strategy_engine', 'src.strategies'), 
                ('risk_engine', 'src.risk'),
                ('analytics_engine', 'src.portfolio_analytics')
            ]
            
            for component, module in modules_to_check:
                try:
                    __import__(module)
                    components[component] = "available"
                except ImportError:
                    components[component] = "unavailable"
                except Exception:
                    components[component] = "error"
            
            # 检查数据文件访问
            data_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
            if os.path.exists(data_dir) and os.access(data_dir, os.R_OK | os.W_OK):
                components['data_storage'] = "accessible"
            else:
                components['data_storage'] = "inaccessible"
                
            # 检查交易引擎状态
            components['trading_engine'] = "standby"  # 默认待机状态
            
        except Exception as e:
            components = {
                "data_engine": "error",
                "strategy_engine": "error",
                "risk_engine": "error", 
                "trading_engine": "error",
                "error": str(e)
            }
        
        return components
    
    def _check_network_status(self):
        """检查网络连接状态"""
        try:
            import urllib.request
            # 测试网络连接
            urllib.request.urlopen('https://finance.yahoo.com', timeout=5)
            return "connected"
        except Exception:
            return "disconnected"
    
    def _check_data_files_status(self):
        """检查数据文件状态"""
        data_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
        files_status = {}
        
        critical_files = [
            'watchlist.json',
            'portfolio.json', 
            'transactions.json',
            'strategy_configs.json'
        ]
        
        for filename in critical_files:
            file_path = os.path.join(data_dir, filename)
            if os.path.exists(file_path):
                try:
                    # 检查文件大小和修改时间
                    stat = os.stat(file_path)
                    files_status[filename] = {
                        "status": "ok",
                        "size_kb": round(stat.st_size / 1024, 1),
                        "modified": datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    }
                except Exception as e:
                    files_status[filename] = {"status": "error", "error": str(e)}
            else:
                files_status[filename] = {"status": "missing"}
        
        return files_status
    
    def _get_system_uptime(self):
        """获取系统运行时间"""
        try:
            import psutil
            boot_time = psutil.boot_time()
            uptime_seconds = datetime.now().timestamp() - boot_time
            hours = int(uptime_seconds // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
        except ImportError:
            # 备用方法：使用系统命令
            try:
                import subprocess
                if sys.platform == "darwin":  # macOS
                    result = subprocess.run(['uptime'], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        return result.stdout.strip().split('up')[1].split(',')[0].strip()
                return "unknown"
            except Exception:
                return "unknown"
        except Exception:
            return "unknown"
    
    def api_stocks_data(self):
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
        self.send_json_response(stocks_data)
    
    def api_run_backtest(self, params):
        """回测API - GET方式"""
        # 这里可以调用实际的回测引擎
        result = {
            "status": "success",
            "message": "回测任务已启动",
            "taskId": f"backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
        self.send_json_response(result)
    
    def api_run_backtest_post(self, data):
        """回测API - POST方式"""
        # 这里可以接收完整的回测参数并调用回测引擎
        result = {
            "status": "success",
            "strategy": data.get("strategy", "unknown"),
            "symbol": data.get("symbol", "unknown"),
            "period": data.get("period", "1y"),
            "result": {
                "totalReturn": 0.15,
                "annualizedReturn": 0.12,
                "maxDrawdown": -0.08,
                "sharpeRatio": 1.25
            }
        }
        self.send_json_response(result)
    
    def api_start_auto_trade(self):
        """启动自动交易API"""
        # 这里可以调用实际的自动交易引擎
        result = {
            "status": "success",
            "message": "自动交易已启动",
            "timestamp": datetime.now().isoformat()
        }
        self.send_json_response(result)
    
    def api_stop_auto_trade(self):
        """停止自动交易API"""
        result = {
            "status": "success",
            "message": "自动交易已停止",
            "timestamp": datetime.now().isoformat()
        }
        self.send_json_response(result)
    
    def api_update_trade_config(self, data):
        """更新交易配置API"""
        result = {
            "status": "success",
            "message": "交易配置已更新",
            "config": data
        }
        self.send_json_response(result)
    
    def api_get_watchlist(self):
        """获取自选股列表API"""
        try:
            # 尝试从数据文件读取
            watchlist_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'watchlist.json')
            if os.path.exists(watchlist_file):
                with open(watchlist_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # 兼容不同的数据格式
                    if isinstance(data, dict):
                        if 'stocks' in data:
                            # 新格式: {"stocks": ["AAPL", "TSLA"]}
                            if isinstance(data['stocks'], list):
                                watchlist = data['stocks']
                            else:
                                # 旧格式: {"stocks": {"AAPL": {...}, "TSLA": {...}}}
                                watchlist = list(data['stocks'].keys())
                        else:
                            # 直接是股票字典: {"AAPL": {...}, "TSLA": {...}}
                            watchlist = list(data.keys())
                    elif isinstance(data, list):
                        # 简单数组格式: ["AAPL", "TSLA"]
                        watchlist = data
                    else:
                        watchlist = ['AAPL', 'TSLA', 'NVDA', 'MSFT', 'GOOGL']
            else:
                # 默认自选股列表
                watchlist = ['AAPL', 'TSLA', 'NVDA', 'MSFT', 'GOOGL']
            
            result = {
                "success": True,
                "data": watchlist,
                "total": len(watchlist),
                "lastUpdate": datetime.now().isoformat()
            }
        except Exception as e:
            result = {
                "success": False,
                "error": str(e),
                "data": ['AAPL', 'TSLA', 'NVDA', 'MSFT', 'GOOGL']  # 备用数据
            }
        
        self.send_json_response(result)
    
    def api_add_to_watchlist(self, data):
        """添加股票到自选股API"""
        symbol = data.get('symbol', '').upper().strip()
        
        if not symbol:
            result = {
                "success": False,
                "error": "股票代码不能为空"
            }
            self.send_json_response(result)
            return
        
        try:
            # 读取现有自选股列表
            watchlist_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'watchlist.json')
            
            if os.path.exists(watchlist_file):
                with open(watchlist_file, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                    
                    # 兼容不同格式
                    if isinstance(file_data, dict):
                        if 'stocks' in file_data:
                            if isinstance(file_data['stocks'], list):
                                # 新简单格式
                                watchlist = file_data['stocks']
                                use_simple_format = True
                            else:
                                # 旧复杂格式
                                watchlist = list(file_data['stocks'].keys())
                                use_simple_format = False
                                original_stocks_data = file_data['stocks']
                        else:
                            # 直接是股票字典
                            watchlist = list(file_data.keys())
                            use_simple_format = False
                            original_stocks_data = file_data
                    else:
                        # 简单数组
                        watchlist = file_data
                        use_simple_format = True
            else:
                watchlist = []
                use_simple_format = True
                file_data = {}
            
            # 检查是否已存在
            if symbol in watchlist:
                result = {
                    "success": False,
                    "error": f"股票 {symbol} 已在自选股列表中"
                }
            else:
                # 添加到列表
                watchlist.append(symbol)
                
                # 根据格式保存
                if use_simple_format:
                    save_data = {
                        "stocks": watchlist,
                        "lastUpdate": datetime.now().isoformat()
                    }
                else:
                    # 保持原有复杂格式，只添加新股票
                    if 'stocks' in file_data:
                        file_data['stocks'][symbol] = {
                            "last_score": 0,
                            "price": 0,
                            "added_at": datetime.now().isoformat()
                        }
                    else:
                        file_data[symbol] = {
                            "last_score": 0,
                            "price": 0,
                            "added_at": datetime.now().isoformat()
                        }
                    save_data = file_data
                
                # 确保目录存在
                os.makedirs(os.path.dirname(watchlist_file), exist_ok=True)
                
                # 保存到文件
                with open(watchlist_file, 'w', encoding='utf-8') as f:
                    json.dump(save_data, f, ensure_ascii=False, indent=2)
                
                result = {
                    "success": True,
                    "message": f"成功添加 {symbol} 到自选股",
                    "data": watchlist
                }
        
        except Exception as e:
            result = {
                "success": False,
                "error": f"添加失败: {str(e)}"
            }
        
        self.send_json_response(result)
    
    def api_remove_from_watchlist(self, data):
        """从自选股移除股票API"""
        symbol = data.get('symbol', '').upper().strip()
        
        if not symbol:
            result = {
                "success": False,
                "error": "股票代码不能为空"
            }
            self.send_json_response(result)
            return
        
        try:
            # 读取现有自选股列表
            watchlist_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'watchlist.json')
            
            if os.path.exists(watchlist_file):
                with open(watchlist_file, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                    
                    # 兼容不同格式
                    if isinstance(file_data, dict):
                        if 'stocks' in file_data:
                            if isinstance(file_data['stocks'], list):
                                # 新简单格式
                                watchlist = file_data['stocks']
                                use_simple_format = True
                            else:
                                # 旧复杂格式
                                watchlist = list(file_data['stocks'].keys())
                                use_simple_format = False
                        else:
                            # 直接是股票字典
                            watchlist = list(file_data.keys())
                            use_simple_format = False
                    else:
                        # 简单数组
                        watchlist = file_data
                        use_simple_format = True
            else:
                watchlist = []
                use_simple_format = True
                file_data = {}
            
            # 检查是否存在
            if symbol not in watchlist:
                result = {
                    "success": False,
                    "error": f"股票 {symbol} 不在自选股列表中"
                }
            else:
                # 从列表移除
                watchlist.remove(symbol)
                
                # 根据格式保存
                if use_simple_format:
                    save_data = {
                        "stocks": watchlist,
                        "lastUpdate": datetime.now().isoformat()
                    }
                else:
                    # 保持原有复杂格式，删除对应股票
                    if 'stocks' in file_data:
                        if symbol in file_data['stocks']:
                            del file_data['stocks'][symbol]
                    else:
                        if symbol in file_data:
                            del file_data[symbol]
                    save_data = file_data
                
                # 保存到文件
                with open(watchlist_file, 'w', encoding='utf-8') as f:
                    json.dump(save_data, f, ensure_ascii=False, indent=2)
                
                result = {
                    "success": True,
                    "message": f"成功从自选股移除 {symbol}",
                    "data": watchlist
                }
        
        except Exception as e:
            result = {
                "success": False,
                "error": f"移除失败: {str(e)}"
            }
        
        self.send_json_response(result)
    
    def api_get_stock_info(self, symbol):
        """获取单个股票信息API"""
        try:
            # 这里可以调用实际的股票数据获取逻辑
            # 目前使用模拟数据
            price = round(50 + (hash(symbol) % 400), 2)
            change = round((hash(symbol) % 21 - 10) / 10, 2)
            change_percent = round(change / price * 100, 2)
            
            result = {
                "success": True,
                "data": {
                    "symbol": symbol,
                    "name": f"{symbol} Inc.",
                    "price": price,
                    "change": change,
                    "changePercent": change_percent,
                    "volume": hash(symbol) % 10000000,
                    "lastUpdate": datetime.now().isoformat()
                }
            }
        except Exception as e:
            result = {
                "success": False,
                "error": f"获取股票信息失败: {str(e)}"
            }
        
        self.send_json_response(result)
    
    def send_json_response(self, data):
        """发送JSON响应"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')  # 允许跨域
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

def start_api_server(host='localhost', port=8090, open_browser=True):
    """启动API服务器"""
    for try_port in range(port, port + 10):
        try:
            server = HTTPServer((host, try_port), APIHandler)
            print(f"🔧 后端API服务器已启动: http://{host}:{try_port}")
            print(f"🌐 前端页面: http://{host}:{try_port}/")
            print(f"📡 API端点: http://{host}:{try_port}/api/")
            print("🛑 按 Ctrl+C 停止服务器")
            print("✨ 特点: 前后端分离、RESTful API、模块化架构")
            
            # 自动打开浏览器
            if open_browser:
                threading.Timer(1.0, lambda: webbrowser.open(f'http://{host}:{try_port}')).start()
            
            server.serve_forever()
            break
        except OSError as e:
            if e.errno == 48:  # Address already in use
                print(f"端口 {try_port} 被占用，尝试端口 {try_port + 1}")
                continue
            else:
                raise
        except KeyboardInterrupt:
            print("\n🛑 API服务器已停止")
            server.shutdown()
            break

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='量化交易系统API服务器')
    parser.add_argument('--host', default='localhost', help='服务器地址 (默认: localhost)')
    parser.add_argument('--port', type=int, default=8000, help='服务器端口 (默认: 8000)')
    parser.add_argument('--no-browser', action='store_true', help='不自动打开浏览器')
    
    args = parser.parse_args()
    
    print("🚀 启动量化交易系统后端API服务器...")
    print(f"📡 服务器地址: http://{args.host}:{args.port}")
    
    start_api_server(host=args.host, port=args.port, open_browser=not args.no_browser)