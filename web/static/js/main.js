/**
 * 🚀 量化交易系统 - 通用JavaScript库
 * 提供API调用、UI交互等通用功能
 */

class TradingAPI {
    constructor(baseURL = '') {
        this.baseURL = baseURL;
    }

    /**
     * 通用API请求方法
     */
    async request(url, options = {}) {
        try {
            const response = await fetch(this.baseURL + url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API请求失败:', error);
            throw error;
        }
    }

    /**
     * GET请求
     */
    async get(url) {
        return this.request(url, { method: 'GET' });
    }

    /**
     * POST请求
     */
    async post(url, data) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // ===================
    // 具体API方法
    // ===================

    /**
     * 获取系统状态
     */
    async getSystemStatus() {
        return this.get('/api/status');
    }

    /**
     * 获取股票数据
     */
    async getStocksData() {
        return this.get('/api/stocks');
    }

    /**
     * 运行回测
     */
    async runBacktest(params) {
        return this.post('/api/backtest', params);
    }

    /**
     * 启动自动交易
     */
    async startAutoTrade() {
        return this.get('/api/auto_trade/start');
    }

    /**
     * 停止自动交易
     */
    async stopAutoTrade() {
        return this.get('/api/auto_trade/stop');
    }

    /**
     * 更新交易配置
     */
    async updateTradeConfig(config) {
        return this.post('/api/auto_trade/config', config);
    }
}

// 全局API实例
const api = new TradingAPI();

/**
 * UI工具类
 */
class UIUtils {
    /**
     * 显示加载状态
     */
    static showLoading(element, text = '加载中...') {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        if (element) {
            element.innerHTML = `<div class="loading"></div> ${text}`;
        }
    }

    /**
     * 显示错误信息
     */
    static showError(element, message) {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        if (element) {
            element.innerHTML = `<div class="alert danger">❌ ${message}</div>`;
        }
    }

    /**
     * 显示成功信息
     */
    static showSuccess(element, message) {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        if (element) {
            element.innerHTML = `<div class="alert success">✅ ${message}</div>`;
        }
    }

    /**
     * 格式化数字
     */
    static formatNumber(num, decimals = 2) {
        return new Intl.NumberFormat('zh-CN', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(num);
    }

    /**
     * 格式化货币
     */
    static formatCurrency(amount) {
        return new Intl.NumberFormat('zh-CN', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    }

    /**
     * 格式化百分比
     */
    static formatPercentage(value) {
        return (value * 100).toFixed(2) + '%';
    }

    /**
     * 切换标签页
     */
    static switchTab(tabName) {
        // 隐藏所有标签内容
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        
        // 移除所有标签的active状态
        document.querySelectorAll('.tab').forEach(tab => {
            tab.classList.remove('active');
        });
        
        // 显示选中的标签内容
        const targetContent = document.getElementById(tabName);
        if (targetContent) {
            targetContent.classList.add('active');
        }
        
        // 设置当前标签为active
        event.target.classList.add('active');
    }

    /**
     * 自动滚动到底部
     */
    static scrollToBottom(element) {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        if (element) {
            element.scrollTop = element.scrollHeight;
        }
    }

    /**
     * 复制到剪贴板
     */
    static async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.showNotification('已复制到剪贴板', 'success');
        } catch (err) {
            console.error('复制失败:', err);
            this.showNotification('复制失败', 'error');
        }
    }

    /**
     * 显示通知
     */
    static showNotification(message, type = 'info', duration = 3000) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        // 添加样式
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 600;
            z-index: 10000;
            animation: slideInRight 0.3s ease;
        `;
        
        // 根据类型设置背景色
        const colors = {
            success: '#00b894',
            error: '#e74c3c',
            warning: '#fdcb6e',
            info: '#17a2b8'
        };
        notification.style.backgroundColor = colors[type] || colors.info;
        
        document.body.appendChild(notification);
        
        // 自动移除
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, duration);
    }
}

/**
 * 数据工具类
 */
class DataUtils {
    /**
     * 生成随机股票数据（用于演示）
     */
    static generateMockStockData(symbol) {
        const basePrice = Math.random() * 500 + 100;
        const change = (Math.random() - 0.5) * 20;
        const changePercent = (change / basePrice) * 100;
        
        return {
            symbol,
            price: basePrice.toFixed(2),
            change: (change >= 0 ? '+' : '') + change.toFixed(2),
            changePercent: (changePercent >= 0 ? '+' : '') + changePercent.toFixed(2) + '%',
            volume: Math.floor(Math.random() * 50000000) + 1000000,
            marketCap: (Math.random() * 2000 + 100).toFixed(0) + 'B'
        };
    }

    /**
     * 生成模拟回测结果
     */
    static generateMockBacktestResult(params) {
        const returnRate = Math.random() * 0.8 - 0.2; // -20% 到 +60%
        const finalValue = Math.floor(params.capital * (1 + returnRate));
        const annualizedReturn = returnRate / (params.period === '6m' ? 0.5 : 
                                             params.period === '1y' ? 1 : 
                                             params.period === '2y' ? 2 : 3);
        
        return {
            symbol: params.symbol,
            strategy: params.strategy,
            period: params.period,
            initialCapital: params.capital,
            finalValue,
            totalReturn: returnRate,
            annualizedReturn,
            maxDrawdown: -(Math.random() * 15 + 5) / 100,
            sharpeRatio: Math.random() * 1.5 + 0.5,
            winRate: Math.random() * 30 + 50,
            totalTrades: Math.floor(Math.random() * 30) + 10,
            timestamp: new Date().toLocaleString()
        };
    }

    /**
     * 验证表单数据
     */
    static validateForm(formData, rules) {
        const errors = [];
        
        for (const [field, rule] of Object.entries(rules)) {
            const value = formData[field];
            
            if (rule.required && (!value || value.toString().trim() === '')) {
                errors.push(`${rule.label || field} 是必填项`);
                continue;
            }
            
            if (rule.type === 'number' && value !== undefined) {
                const num = parseFloat(value);
                if (isNaN(num)) {
                    errors.push(`${rule.label || field} 必须是数字`);
                    continue;
                }
                
                if (rule.min !== undefined && num < rule.min) {
                    errors.push(`${rule.label || field} 不能小于 ${rule.min}`);
                }
                
                if (rule.max !== undefined && num > rule.max) {
                    errors.push(`${rule.label || field} 不能大于 ${rule.max}`);
                }
            }
        }
        
        return errors;
    }
}

/**
 * 图表工具类（简化版）
 */
class ChartUtils {
    /**
     * 创建简单的ASCII图表
     */
    static createASCIIChart(data, width = 50) {
        const max = Math.max(...data);
        const min = Math.min(...data);
        const range = max - min;
        
        return data.map(value => {
            const normalized = (value - min) / range;
            const barLength = Math.round(normalized * width);
            return '█'.repeat(barLength) + '░'.repeat(width - barLength);
        }).join('\n');
    }
}

// 页面加载完成后的初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 量化交易系统前端已加载');
    
    // 添加全局错误处理
    window.addEventListener('error', function(event) {
        console.error('页面错误:', event.error);
        UIUtils.showNotification('页面发生错误，请刷新重试', 'error');
    });
    
    // 添加全局点击事件处理
    document.addEventListener('click', function(event) {
        // 处理标签页切换
        if (event.target.classList.contains('tab')) {
            const tabName = event.target.getAttribute('data-tab');
            if (tabName) {
                UIUtils.switchTab(tabName);
            }
        }
    });
});

// 导出到全局作用域
window.TradingAPI = TradingAPI;
window.UIUtils = UIUtils;
window.DataUtils = DataUtils;
window.ChartUtils = ChartUtils;
window.api = api;