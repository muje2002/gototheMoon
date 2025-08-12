import sys
import os
import pandas as pd

# Add the project root to the Python path to allow for module imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.backtest import Backtester
from src.data_provider import DataProvider
from strategies.simple_ma_strategy import SimpleMAStrategy

def main():
    """
    Main function to configure and run the backtest.
    """
    # --- Configuration ---
    tickers = ['GME', 'AMC']
    start_date = '2023-01-03'
    end_date = '2023-02-28'
    initial_capital = 100000.0
    data_path = 'data/sample_us_stocks.csv' # Path relative to the project root

    # --- Initialization ---
    # 1. Initialize the Data Provider
    data_provider = DataProvider(data_path=data_path)

    # 2. Initialize the Trading Strategy
    # Using a more sensitive 2-day/5-day window to ensure crossovers in sample data
    strategy = SimpleMAStrategy(short_window=2, long_window=5)

    # 3. Initialize the Backtester
    backtester = Backtester(
        data_provider=data_provider,
        strategy=strategy,
        tickers=tickers,
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_capital
    )

    # --- Run Backtest ---
    results = backtester.run()

    # --- Display Results ---
    if results:
        print("--- Backtest Results ---")

        # Print Performance Summary
        summary = results['performance_summary']
        print("\n--- Performance Summary ---")
        for key, value in summary.items():
            if isinstance(value, float):
                print(f"{key}: {value:.2f}")
            else:
                print(f"{key}: {value}")

        # Print Portfolio History
        history = results['portfolio_history']
        print("\n--- Portfolio History (first 5 rows) ---")
        print(history.head())

        # Print Trade Log
        trade_log = results['trade_log']
        print("\n--- Trade Log ---")
        if trade_log:
            for trade in trade_log:
                print(trade)
        else:
            print("No trades were executed.")

        print("\n--- Backtest Complete ---")
    else:
        print("Backtest did not produce any results.")

if __name__ == "__main__":
    main()
