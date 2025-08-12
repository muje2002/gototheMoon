import os
import time
from datetime import datetime, timedelta
from typing import List, Optional

import pandas as pd
from pykrx import stock
import OpenDartReader

from gotothemoon.datacollector.schemas import DisclosureSchema


class DartCollector:
    """
    Collects public company disclosures from the DART (Data Analysis, Retrieval and
    Transfer System) of South Korea's Financial Supervisory Service (FSS).
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initializes the DartCollector.

        Args:
            api_key (str, optional): The DART API key. If not provided, it will
                                     be read from the DART_API_KEY environment
                                     variable.
        """
        self.api_key = api_key or os.getenv("DART_API_KEY")
        if not self.api_key:
            raise ValueError("DART API key is required. Please provide it or set the DART_API_KEY environment variable.")
        self.dart = OpenDartReader(self.api_key)

    def _get_target_tickers(self) -> List[str]:
        """
        Gets a list of all tickers for KOSPI and KOSDAQ listed companies.

        Returns:
            List[str]: A list of stock tickers.
        """
        print("Fetching all KOSPI and KOSDAQ tickers...")
        kospi_tickers = stock.get_market_ticker_list(market="KOSPI")
        kosdaq_tickers = stock.get_market_ticker_list(market="KOSDAQ")
        all_tickers = list(set(kospi_tickers + kosdaq_tickers))
        print(f"Found {len(all_tickers)} unique tickers.")
        return all_tickers

    def fetch_disclosures(self, start_date: str, end_date: str) -> List[DisclosureSchema]:
        """
        Fetches all public disclosures for KOSPI and KOSDAQ companies within a
        given date range.

        Args:
            start_date (str): The start date in 'YYYYMMDD' format.
            end_date (str): The end date in 'YYYYMMDD' format.

        Returns:
            List[DisclosureSchema]: A list of disclosure data objects.
        """
        all_disclosures: List[DisclosureSchema] = []

        # DART API can search for all companies at once.
        # The API is more efficient when querying by date range for all companies
        # rather than iterating through each company.
        print(f"Fetching all disclosures from {start_date} to {end_date}...")
        try:
            # kind='A' is for regular disclosures (정기공시)
            df = self.dart.list(start=start_date, end=end_date, kind='A', final=True)
            if df is None or df.empty:
                print("No disclosures found for the given period.")
                return []

            for _, row in df.iterrows():
                disclosure = DisclosureSchema(
                    id=row.get('rcept_no', ''),
                    source='DART',
                    country='KR',
                    report_title=row.get('report_nm', ''),
                    company_name=row.get('corp_name', ''),
                    company_symbol=row.get('stock_code', ''),
                    url_to_document=row.get('rcept_url', ''),
                    filing_type=row.get('report_nm', ''), # Using report_nm as filing_type
                    published_at=pd.to_datetime(row.get('rcept_dt', '')).isoformat(),
                )
                all_disclosures.append(disclosure)

        except Exception as e:
            print(f"An error occurred while fetching disclosures: {e}")

        print(f"Successfully collected {len(all_disclosures)} disclosures.")
        return all_disclosures


if __name__ == '__main__':
    print("--- Running DART Collector Example ---")

    # IMPORTANT: To run this example, you must have your DART API key set as an
    # environment variable.
    # On Linux/macOS: export DART_API_KEY='your_api_key_here'
    # On Windows: set DART_API_KEY='your_api_key_here'

    if not os.getenv("DART_API_KEY"):
        print("\nERROR: DART_API_KEY environment variable not set.")
        print("Please set it to your API key to run this example.")
    else:
        print(f"Using DART API key found in environment.")
        collector = DartCollector()

        # Fetch disclosures for the last 3 days as a test
        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=3)
        start_date_str = start_dt.strftime('%Y%m%d')
        end_date_str = end_dt.strftime('%Y%m%d')

        print(f"\nFetching disclosures from {start_date_str} to {end_date_str}...")
        disclosures = collector.fetch_disclosures(start_date=start_date_str, end_date=end_date_str)

        if disclosures:
            print(f"\nSuccessfully fetched {len(disclosures)} disclosures.")
            print("--- First 3 Disclosures ---")
            for i, disclosure in enumerate(disclosures[:3]):
                print(f"[{i+1}] {disclosure.company_name} ({disclosure.company_symbol}) - {disclosure.report_title}")
                print(f"  - Published: {disclosure.published_at}")
                print(f"  - URL: {disclosure.url_to_document}")
        else:
            print("\nNo disclosures found in the last 3 days.")

    print("\n--- DART Collector Example Finished ---")
