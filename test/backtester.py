import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class Backtester:
    """
    A class to run a backtest for a given trading strategy.
    """
    def __init__(self, data_provider, strategy, tickers, start_date, end_date, initial_capital=100000.0):
        """
        Initializes the Backtester.

        Args:
            data_provider: An instance of a data provider class.
            strategy: An instance of a trading strategy class.
            tickers (List[str]): A list of stock tickers to trade.
            start_date (str): The start date of the backtest (YYYY-MM-DD).
            end_date (str): The end date of the backtest (YYYY-MM-DD).
            initial_capital (float): The starting capital for the backtest.
        """
        self.data_provider = data_provider
        self.strategy = strategy
        self.tickers = tickers
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital

        self.cash = initial_capital
        self.portfolio = {ticker: {'shares': 0, 'value': 0.0} for ticker in self.tickers}
        self.trade_log = []
        self.portfolio_history = []

    def run(self):
        """
        Runs the backtest simulation.
        """
        # Fetch all necessary data at once
        all_data = self.data_provider.get_data(self.tickers, self.start_date, self.end_date)
        if not all_data:
            print("No data available for the given tickers and date range. Aborting backtest.")
            return None

        # --- Pre-calculate all signals for efficiency ---
        all_signals = {}
        for ticker in self.tickers:
            if ticker in all_data and not all_data[ticker].empty:
                all_signals[ticker] = self.strategy.generate_signals(all_data[ticker])

        # --- Use a unified date index from the actual data ---
        unified_dates = sorted(list(set.union(*(set(df.index) for df in all_data.values()))))
        sim_dates = [d for d in unified_dates if pd.to_datetime(self.start_date) <= d <= pd.to_datetime(self.end_date)]

        # --- Main simulation loop ---
        for date in sim_dates:
            current_date_str = date.strftime('%Y-%m-%d')
            portfolio_value = self.cash

            for ticker in self.tickers:
                # Update portfolio value with current price
                if ticker in all_data and date in all_data[ticker].index:
                    current_price = all_data[ticker].loc[date]['Close']
                    portfolio_value += self.portfolio[ticker]['shares'] * current_price
                    self.portfolio[ticker]['value'] = self.portfolio[ticker]['shares'] * current_price

                    # Look up pre-calculated signal
                    signal = all_signals[ticker].get(date, 'HOLD')

                    # Execute trades
                    if signal == 'BUY' and self.cash > current_price:
                        investment_amount = self.cash * 0.1
                        shares_to_buy = int(investment_amount / current_price)
                        if shares_to_buy > 0:
                            cost = shares_to_buy * current_price
                            self.cash -= cost
                            self.portfolio[ticker]['shares'] += shares_to_buy
                            self.trade_log.append(f"{current_date_str}: BOUGHT {shares_to_buy} {ticker} @ {current_price:.2f}")

                    elif signal == 'SELL' and self.portfolio[ticker]['shares'] > 0:
                        shares_to_sell = self.portfolio[ticker]['shares']
                        revenue = shares_to_sell * current_price
                        self.cash += revenue
                        self.portfolio[ticker]['shares'] = 0
                        self.trade_log.append(f"{current_date_str}: SOLD {shares_to_sell} {ticker} @ {current_price:.2f}")

            self.portfolio_history.append({'date': date, 'value': portfolio_value})

        return self._calculate_performance_metrics()

    def _calculate_performance_metrics(self):
        """
        Calculates performance metrics after the backtest is complete.
        """
        if not self.portfolio_history:
            return {"error": "No trades were made and no portfolio history was recorded."}

        report = {}
        portfolio_df = pd.DataFrame(self.portfolio_history).set_index('date')

        # 1. Total Return
        final_value = portfolio_df['value'].iloc[-1]
        report['Total Return (%)'] = ((final_value - self.initial_capital) / self.initial_capital) * 100

        # 2. Annualized Return
        num_days = (portfolio_df.index[-1] - portfolio_df.index[0]).days
        num_years = num_days / 365.25
        report['Annualized Return (%)'] = ((1 + report['Total Return (%)'] / 100)**(1/num_years) - 1) * 100 if num_years > 0 else 0

        # 3. Maximum Drawdown (MDD)
        portfolio_df['peak'] = portfolio_df['value'].cummax()
        portfolio_df['drawdown'] = (portfolio_df['value'] - portfolio_df['peak']) / portfolio_df['peak']
        report['Max Drawdown (%)'] = portfolio_df['drawdown'].min() * 100

        # 4. Sharpe Ratio (assuming risk-free rate is 0)
        portfolio_df['daily_return'] = portfolio_df['value'].pct_change()
        if portfolio_df['daily_return'].std() > 0:
            sharpe_ratio = (portfolio_df['daily_return'].mean() / portfolio_df['daily_return'].std()) * np.sqrt(252) # 252 trading days
        else:
            sharpe_ratio = 0.0
        report['Sharpe Ratio'] = sharpe_ratio

        # 5. Other stats
        report['Start Date'] = self.start_date
        report['End Date'] = self.end_date
        report['Initial Capital'] = self.initial_capital
        report['Final Portfolio Value'] = final_value
        report['Total Trades'] = len(self.trade_log)

        return {
            "performance_summary": report,
            "portfolio_history": portfolio_df,
            "trade_log": self.trade_log
        }
