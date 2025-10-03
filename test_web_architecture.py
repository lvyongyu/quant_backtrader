#!/usr/bin/env python3
"""
Web架构测试脚本
测试新的前后端分离架构的各种功能
"""

import requests
import json
import time

def test_web_architecture():
    """测试Web架构的各项功能"""
    base_url = "http://localhost:8082"
    
    print("🔧 测试新Web架构...")
    print("=" * 50)
    
    # 1. 测试主页
    print("1. 📄 测试主页...")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("   ✅ 主页加载成功")
        else:
            print(f"   ❌ 主页加载失败: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 主页连接失败: {e}")
    
    # 2. 测试静态资源
    print("2. 🎨 测试静态资源...")
    static_files = [
        "/static/css/main.css",
        "/static/js/main.js",
        "/static/js/auto_trade.js",
        "/static/js/backtest.js",
        "/static/js/stocks.js",
        "/static/js/monitoring.js"
    ]
    
    for file_path in static_files:
        try:
            response = requests.get(f"{base_url}{file_path}")
            if response.status_code == 200:
                print(f"   ✅ {file_path}")
            else:
                print(f"   ❌ {file_path} - {response.status_code}")
        except Exception as e:
            print(f"   ❌ {file_path} - {e}")
    
    # 3. 测试页面模板
    print("3. 📱 测试页面模板...")
    pages = [
        "/",
        "/backtest",
        "/auto_trade",
        "/stocks",
        "/monitoring"
    ]
    
    for page in pages:
        try:
            response = requests.get(f"{base_url}{page}")
            if response.status_code == 200:
                print(f"   ✅ {page}")
            else:
                print(f"   ❌ {page} - {response.status_code}")
        except Exception as e:
            print(f"   ❌ {page} - {e}")
    
    # 4. 测试API端点
    print("4. 📡 测试API端点...")
    api_endpoints = [
        ("/api/status", "GET"),
        ("/api/stocks", "GET"),
        ("/api/backtest", "GET")
    ]
    
    for endpoint, method in api_endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{base_url}{endpoint}")
            
            if response.status_code == 200:
                print(f"   ✅ {method} {endpoint}")
                # 如果是JSON响应，显示部分内容
                if 'application/json' in response.headers.get('content-type', ''):
                    data = response.json()
                    if isinstance(data, dict):
                        print(f"      📊 响应字段: {list(data.keys())}")
            else:
                print(f"   ❌ {method} {endpoint} - {response.status_code}")
        except Exception as e:
            print(f"   ❌ {method} {endpoint} - {e}")
    
    # 5. 测试自动交易API
    print("5. ⚡ 测试自动交易API...")
    try:
        # 测试启动自动交易
        response = requests.post(f"{base_url}/api/auto_trade/start", 
                               json={"mode": "paper", "stocks": "tech5", "strategy": "conservative"})
        if response.status_code == 200:
            print("   ✅ 自动交易启动API")
            result = response.json()
            print(f"      📊 响应: {result.get('message', 'Success')}")
        else:
            print(f"   ❌ 自动交易启动API - {response.status_code}")
        
        # 测试停止自动交易
        response = requests.post(f"{base_url}/api/auto_trade/stop")
        if response.status_code == 200:
            print("   ✅ 自动交易停止API")
        else:
            print(f"   ❌ 自动交易停止API - {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ 自动交易API测试失败: {e}")
    
    print("\n🎉 Web架构测试完成!")
    print("💡 如果所有测试都通过，说明前后端分离架构工作正常")

if __name__ == "__main__":
    test_web_architecture()