# Backtrader Trading System

A professional quantitative trading system built with Python and the Backtrader framework, designed for both backtesting and live trading.

## 🎯 Quick Start

```bash
# Install dependencies (already done)
pip install -r requirements.txt

# Run example backtest
python examples/simple_strategy.py
```

**Results**: AAPL 17.32% return | SPY 12.94% return

## ✨ Features

### 📈 Trading Strategies
- **SMA Crossover**: Moving average crossover signals (10/30, 5/20 periods)
- **RSI Strategy**: RSI overbought/oversold conditions (14-period)  
- **Bollinger Bands**: Mean reversion at band extremes
- **Mean Reversion**: Z-score based statistical arbitrage
- **Base Strategy**: Foundation for custom strategy development

### 📊 Data Feeds
- **Yahoo Finance**: Real-time and historical data via yfinance
- **CSV Files**: Custom data import with flexible column mapping
- **Live Feeds**: Real-time streaming data (WebSocket support)

### 🏦 Broker Integration
- **Paper Trading**: Realistic simulation with commission/slippage
- **Alpaca**: Commission-free stock trading (placeholder)
- **Interactive Brokers**: Professional trading platform (placeholder)

### 🛡️ Risk Management
- **Position Sizing**: Fixed, percentage, Kelly Criterion, volatility-adjusted
- **Stop Losses**: Fixed, trailing, percentage-based, ATR-based
- **Portfolio Risk**: Drawdown limits, daily loss limits, position limits

### 📊 Analytics & Reporting
- **Performance Metrics**: Sharpe ratio, total return, max drawdown
- **Trade Analysis**: Win rate, profit/loss, trade statistics
- **Real-time Monitoring**: Portfolio value, position tracking

## 🚀 Usage Examples

### Basic Backtest
```python
import backtrader as bt
from src.strategies.sma_crossover import SMACrossoverStrategy
from src.data.yahoo_feed import YahooDataFeed
from src.brokers.paper_broker import PaperBroker

# Create engine
cerebro = bt.Cerebro()

# Add strategy
cerebro.addstrategy(SMACrossoverStrategy, fast_period=10, slow_period=30)

# Add data
data = YahooDataFeed.create_data_feed('AAPL', period='1y')
cerebro.adddata(data)

# Set up broker
broker = PaperBroker.create_realistic_broker(cash=10000)
broker.setup_broker(cerebro)

# Run backtest
results = cerebro.run()
```

### Custom Strategy
```python
from src.strategies.base_strategy import BaseStrategy

class MyStrategy(BaseStrategy):
    def buy_signal(self):
        return self.data.close[0] > self.data.close[-1] * 1.02
    
    def sell_signal(self):
        return self.data.close[0] < self.data.close[-1] * 0.98
```

### Risk Management
```python
from src.risk.risk_manager import RiskManager
from src.risk.position_sizer import PercentSizer

# Portfolio risk management  
risk_manager = RiskManager(
    max_portfolio_risk=0.02,  # 2% max risk per trade
    max_daily_loss=0.05,      # 5% max daily loss
    max_drawdown=0.10         # 10% max drawdown
)

# Position sizing
sizer = PercentSizer(percent=0.1)  # 10% of portfolio per trade
```

## 🏗️ Project Structure

```
backtrader_trading/
├── src/
│   ├── strategies/          # Trading strategies
│   │   ├── base_strategy.py      # Foundation strategy class
│   │   ├── sma_crossover.py      # Moving average crossover
│   │   ├── rsi_strategy.py       # RSI-based trading
│   │   ├── bollinger_bands.py    # Bollinger Bands strategy
│   │   └── mean_reversion.py     # Mean reversion strategy
│   ├── data/               # Data feed implementations
│   │   ├── yahoo_feed.py         # Yahoo Finance data
│   │   ├── csv_feed.py           # CSV file data
│   │   └── live_feed.py          # Real-time data feeds
│   ├── brokers/            # Broker integrations
│   │   ├── paper_broker.py       # Paper trading
│   │   ├── alpaca_broker.py      # Alpaca integration
│   │   └── interactive_brokers.py # IB integration
│   ├── risk/               # Risk management
│   │   ├── position_sizer.py     # Position sizing algorithms
│   │   ├── risk_manager.py       # Portfolio risk controls
│   │   └── stop_loss.py          # Stop loss management
│   ├── analyzers/          # Performance analyzers
│   ├── indicators/         # Custom indicators
│   ├── utils/              # Utility functions
│   └── web/                # Web dashboard (FastAPI)
├── examples/
│   └── simple_strategy.py       # Example backtest
├── tests/                  # Unit tests
├── config/                 # Configuration files
├── data/                   # Historical data
├── logs/                   # Log files
└── notebooks/              # Jupyter notebooks
```

## 🔧 Configuration

### Environment Variables
```bash
# .env file
YAHOO_API_KEY=your_key_here
ALPACA_API_KEY=your_alpaca_key
ALPACA_SECRET_KEY=your_alpaca_secret
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://user:pass@localhost/trading
```

### Strategy Parameters
```python
# Modify strategy parameters
strategy_params = {
    'fast_period': 10,
    'slow_period': 30,
    'stake_percentage': 0.95,
    'stop_loss': 0.02,
    'take_profit': 0.05
}
```

## 📋 Requirements

- Python 3.8+
- Backtrader 1.9.78+
- yfinance for data
- pandas, numpy for data manipulation
- FastAPI for web interface
- Redis for caching
- PostgreSQL for data storage

## 🚀 VS Code Integration

### Available Tasks
- **Run Backtest Example**: Execute the example strategy
- **Run Tests**: Execute unit tests
- **Format Code**: Format with Black and isort

### Extensions Installed
- Python
- Pylint
- Black Formatter
- isort

## 📊 Performance Results

### Example Backtest Results (2023)
| Strategy | Symbol | Return | Trades | Win Rate | Max Drawdown |
|----------|---------|--------|--------|----------|--------------|
| SMA Cross | AAPL   | 17.32% | 4      | 50.0%    | 11.61%       |
| SMA Cross | SPY    | 12.94% | 6      | 50.0%    | 8.38%        |

## 🛠️ Development

### Running Tests
```bash
python -m pytest tests/
```

### Adding New Strategy
1. Inherit from `BaseStrategy`
2. Implement `buy_signal()` and `sell_signal()` methods
3. Add to `src/strategies/__init__.py`

### Adding New Data Feed
1. Inherit from `bt.feeds.DataBase` or `bt.feeds.PandasData`
2. Implement data fetching logic
3. Add to `src/data/__init__.py`

## 📝 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new features
4. Submit pull request

## 📞 Support

For questions and support, please open an issue on GitHub.

---

**⚠️ Disclaimer**: This software is for educational purposes only. Past performance does not guarantee future results. Trading involves risk of financial loss.

## Documentation

- [Getting Started Guide](docs/getting-started.md)
- [Strategy Development](docs/strategies.md)
- [Data Feeds Setup](docs/data-feeds.md)
- [Risk Management](docs/risk-management.md)
- [API Reference](docs/api-reference.md)

## Requirements

- Python 3.9+
- Backtrader
- PostgreSQL (optional)
- Redis (optional)

## License

MIT License