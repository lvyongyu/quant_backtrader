"""
Example trading strategy implementation.

This module demonstrates how to create and run a simple
trading strategy using the Backtrader framework.
"""

import sys
import os
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    import backtrader as bt
    from src.strategies.sma_crossover import SMACrossoverStrategy
    from src.data.yahoo_feed import YahooDataFeed
    from src.brokers.paper_broker import PaperBroker
except ImportError as e:
    print(f"Import error: {e}")
    print("Please install required dependencies with: pip install -r requirements.txt")
    sys.exit(1)


def run_backtest(
    symbol: str = 'AAPL',
    cash: float = 10000.0,
    fast_period: int = 10,
    slow_period: int = 30,
    start_date: str = '2023-01-01',
    end_date: str = '2024-01-01'
):
    """
    Run a simple SMA crossover backtest.
    
    Args:
        symbol: Stock symbol to trade
        cash: Starting cash amount
        fast_period: Fast SMA period
        slow_period: Slow SMA period
        start_date: Start date for backtest (YYYY-MM-DD)
        end_date: End date for backtest (YYYY-MM-DD)
    """
    print(f"Running backtest for {symbol}")
    print(f"Strategy: SMA Crossover ({fast_period}/{slow_period})")
    print(f"Period: {start_date} to {end_date}")
    print(f"Starting cash: ${cash:,.2f}")
    print("-" * 50)
    
    # Create Cerebro engine
    cerebro = bt.Cerebro()
    
    # Add strategy
    cerebro.addstrategy(
        SMACrossoverStrategy,
        fast_period=fast_period,
        slow_period=slow_period,
        debug=True
    )
    
    # Create data feed
    try:
        data_feed = YahooDataFeed.create_data_feed(
            symbol=symbol,
            start=start_date,
            end=end_date,
            interval='1d'
        )
        cerebro.adddata(data_feed)
    except Exception as e:
        print(f"Error creating data feed: {e}")
        return
    
    # Set up broker
    paper_broker = PaperBroker.create_realistic_broker(cash=cash)
    paper_broker.setup_broker(cerebro)
    
    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    
    # Print starting conditions
    starting_value = cerebro.broker.getvalue()
    print(f'Starting Portfolio Value: ${starting_value:,.2f}')
    
    # Run backtest
    try:
        results = cerebro.run()
        strategy = results[0]
        
        # Print final results
        final_value = cerebro.broker.getvalue()
        total_return = ((final_value - starting_value) / starting_value) * 100
        
        print("-" * 50)
        print(f'Final Portfolio Value: ${final_value:,.2f}')
        print(f'Total Return: {total_return:.2f}%')
        
        # Print analyzer results
        if hasattr(strategy.analyzers, 'sharpe'):
            sharpe = strategy.analyzers.sharpe.get_analysis()
            print(f'Sharpe Ratio: {sharpe.get("sharperatio", "N/A")}')
        
        if hasattr(strategy.analyzers, 'drawdown'):
            drawdown = strategy.analyzers.drawdown.get_analysis()
            print(f'Max Drawdown: {drawdown.get("max", {}).get("drawdown", "N/A"):.2f}%')
        
        if hasattr(strategy.analyzers, 'trades'):
            trades = strategy.analyzers.trades.get_analysis()
            total_trades = trades.get('total', {}).get('total', 0)
            won_trades = trades.get('won', {}).get('total', 0)
            lost_trades = trades.get('lost', {}).get('total', 0)
            win_rate = (won_trades / total_trades * 100) if total_trades > 0 else 0
            
            print(f'Total Trades: {total_trades}')
            print(f'Winning Trades: {won_trades}')
            print(f'Losing Trades: {lost_trades}')
            print(f'Win Rate: {win_rate:.1f}%')
        
        print("-" * 50)
        
    except Exception as e:
        print(f"Error running backtest: {e}")
        return


def main():
    """Main function to run example backtests."""
    print("Backtrader Trading System - Example Strategy")
    print("=" * 60)
    
    # Example 1: AAPL with default settings
    run_backtest(
        symbol='AAPL',
        cash=10000.0,
        fast_period=10,
        slow_period=30,
        start_date='2023-01-01',
        end_date='2024-01-01'
    )
    
    print("\n" + "=" * 60)
    
    # Example 2: SPY with different settings
    run_backtest(
        symbol='SPY',
        cash=10000.0,
        fast_period=5,
        slow_period=20,
        start_date='2023-01-01',
        end_date='2024-01-01'
    )


if __name__ == '__main__':
    main()