#!/usr/bin/env python3
"""
自选股Web功能测试脚本
测试添加、删除自选股的Web API功能
"""

import requests
import json
import time

def test_watchlist_api():
    """测试自选股API功能"""
    base_url = "http://localhost:8084"
    
    print("📋 测试自选股Web API功能...")
    print("=" * 50)
    
    # 1. 测试获取自选股列表
    print("1. 📄 测试获取自选股列表...")
    try:
        response = requests.get(f"{base_url}/api/watchlist", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 获取成功: {data.get('data', [])}")
            print(f"   📊 总数: {data.get('total', 0)}")
        else:
            print(f"   ❌ 获取失败: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 获取失败: {e}")
    
    # 2. 测试添加股票到自选股
    print("\n2. ➕ 测试添加股票到自选股...")
    test_symbols = ['META', 'NFLX', 'AMD']
    
    for symbol in test_symbols:
        try:
            response = requests.post(f"{base_url}/api/watchlist/add", 
                                   json={"symbol": symbol}, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"   ✅ 添加 {symbol} 成功")
                else:
                    print(f"   ℹ️ 添加 {symbol}: {data.get('error', '未知错误')}")
            else:
                print(f"   ❌ 添加 {symbol} 失败: {response.status_code}")
        except Exception as e:
            print(f"   ❌ 添加 {symbol} 失败: {e}")
        
        time.sleep(0.5)  # 避免请求过快
    
    # 3. 再次获取自选股列表，验证添加结果
    print("\n3. 🔄 验证添加结果...")
    try:
        response = requests.get(f"{base_url}/api/watchlist", timeout=5)
        if response.status_code == 200:
            data = response.json()
            watchlist = data.get('data', [])
            print(f"   ✅ 当前自选股: {watchlist}")
            print(f"   📊 总数: {len(watchlist)}")
        else:
            print(f"   ❌ 获取失败: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 获取失败: {e}")
    
    # 4. 测试移除股票
    print("\n4. ➖ 测试移除股票...")
    remove_symbols = ['META', 'AMD']
    
    for symbol in remove_symbols:
        try:
            response = requests.post(f"{base_url}/api/watchlist/remove", 
                                   json={"symbol": symbol}, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"   ✅ 移除 {symbol} 成功")
                else:
                    print(f"   ℹ️ 移除 {symbol}: {data.get('error', '未知错误')}")
            else:
                print(f"   ❌ 移除 {symbol} 失败: {response.status_code}")
        except Exception as e:
            print(f"   ❌ 移除 {symbol} 失败: {e}")
        
        time.sleep(0.5)
    
    # 5. 最终验证
    print("\n5. 🎯 最终验证...")
    try:
        response = requests.get(f"{base_url}/api/watchlist", timeout=5)
        if response.status_code == 200:
            data = response.json()
            watchlist = data.get('data', [])
            print(f"   ✅ 最终自选股: {watchlist}")
            print(f"   📊 最终总数: {len(watchlist)}")
            
            # 检查是否还有NFLX但没有META和AMD
            has_nflx = 'NFLX' in watchlist
            no_meta = 'META' not in watchlist
            no_amd = 'AMD' not in watchlist
            
            if has_nflx and no_meta and no_amd:
                print("   🎉 测试结果符合预期！")
            else:
                print("   ⚠️ 测试结果需要检查")
        else:
            print(f"   ❌ 获取失败: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 获取失败: {e}")
    
    print("\n💡 测试完成！请在Web界面中验证功能是否正常工作。")
    print(f"🌐 打开浏览器访问: {base_url}")

if __name__ == "__main__":
    test_watchlist_api()