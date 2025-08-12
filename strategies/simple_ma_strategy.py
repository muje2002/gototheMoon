import pandas as pd
import numpy as np

class SimpleMAStrategy:
    """
    A simple moving average (SMA) crossover trading strategy.
    - A 'BUY' signal is generated when the short-term SMA crosses above the long-term SMA.
    - A 'SELL' signal is generated when the short-term SMA crosses below the long-term SMA.
    - Otherwise, the signal is 'HOLD'.
    """
    def __init__(self, short_window: int = 20, long_window: int = 50):
        """
        Initializes the SimpleMAStrategy.

        Args:
            short_window (int): The lookback period for the short-term moving average.
            long_window (int): The lookback period for the long-term moving average.
        """
        if short_window >= long_window:
            raise ValueError("short_window must be less than long_window")
        self.short_window = short_window
        self.long_window = long_window

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generates trading signals for the given historical data.

        Args:
            data (pd.DataFrame): A DataFrame containing at least a 'Close' price column.

        Returns:
            pd.Series: A Series of trading signals ('BUY', 'SELL', 'HOLD') indexed by date.
        """
        if len(data) < self.long_window:
            return pd.Series('HOLD', index=data.index, name='signal')

        signals = pd.DataFrame(index=data.index)

        # Calculate moving averages
        signals['short_mavg'] = data['Close'].rolling(window=self.short_window, min_periods=self.short_window).mean()
        signals['long_mavg'] = data['Close'].rolling(window=self.long_window, min_periods=self.long_window).mean()

        # Create a 'position' column: 1 if short > long, -1 if short < long
        signals['position'] = np.sign(signals['short_mavg'] - signals['long_mavg'])

        # The signal is the change from bearish (-1) to bullish (1) -> BUY (diff=2)
        # or from bullish (1) to bearish (-1) -> SELL (diff=-2)
        signals['signal_val'] = signals['position'].diff()

        signals['signal'] = 'HOLD'
        signals.loc[signals['signal_val'] == 2.0, 'signal'] = 'BUY'
        signals.loc[signals['signal_val'] == -2.0, 'signal'] = 'SELL'

        return signals['signal']
