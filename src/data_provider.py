import pandas as pd
from typing import List, Dict

class DataProvider:
    """
    Provides historical stock data.
    In a real application, this would fetch data from a database or a financial data API.
    For this example, it will read data from a local CSV file.
    """
    def __init__(self, data_path: str):
        """
        Initializes the DataProvider.

        Args:
            data_path (str): The path to the CSV file containing the stock data.
        """
        self.data_path = data_path
        self.dataframe = self._load_data()

    def _load_data(self) -> pd.DataFrame:
        """
        Loads data from the CSV file and prepares it.
        """
        try:
            df = pd.read_csv(self.data_path)
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
            return df
        except FileNotFoundError:
            # Return an empty DataFrame if the file doesn't exist yet
            # In a real scenario, you might want to raise an error or log a warning
            print(f"Warning: Data file not found at {self.data_path}. Returning empty DataFrame.")
            return pd.DataFrame()

    def get_data(self, tickers: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """
        Retrieves historical data for the given tickers and date range.

        Args:
            tickers (List[str]): A list of stock tickers.
            start_date (str): The start date of the period (YYYY-MM-DD).
            end_date (str): The end date of the period (YYYY-MM-DD).

        Returns:
            Dict[str, pd.DataFrame]: A dictionary where keys are tickers and values are
                                     DataFrames with the historical data for that ticker.
        """
        data = {}
        # Ensure the main dataframe is not empty
        if self.dataframe.empty:
            return data

        for ticker in tickers:
            # Assuming columns are named like 'AAPL_Open', 'AAPL_High', etc.
            ticker_cols = [col for col in self.dataframe.columns if col.startswith(ticker)]
            if not ticker_cols:
                continue

            ticker_df = self.dataframe[ticker_cols].copy()
            # Rename columns to remove ticker prefix (e.g., 'AAPL_Open' -> 'Open')
            ticker_df.columns = [col.split('_')[1] for col in ticker_cols]

            # Filter by date
            mask = (ticker_df.index >= start_date) & (ticker_df.index <= end_date)
            data[ticker] = ticker_df.loc[mask]

        return data
