import os
import time
import hashlib
from typing import List, Optional

import finnhub

from gotothemoon.datacollector.schemas import ResearchSchema
from gotothemoon.datacollector.utils.tickers import get_us_tickers, get_kr_tickers

class ResearchCollector:
    """
    Collects analyst recommendations and research data from Finnhub.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initializes the ResearchCollector.

        Args:
            api_key (str, optional): The Finnhub API key. If not provided, it
                                     will be read from the FINNHUB_API_KEY
                                     environment variable.
        """
        self.api_key = api_key or os.getenv("FINNHUB_API_KEY")
        if not self.api_key:
            raise ValueError("Finnhub API key is required. Please provide it or set the FINNHUB_API_KEY environment variable.")
        self.client = finnhub.Client(api_key=self.api_key)

    def fetch_research(self) -> List[ResearchSchema]:
        """
        Fetches analyst recommendation trends for all target US and KR companies.

        Returns:
            List[ResearchSchema]: A list of research data objects.
        """
        all_research: List[ResearchSchema] = []
        us_tickers = get_us_tickers()
        kr_tickers = get_kr_tickers()
        all_tickers = us_tickers + kr_tickers

        print(f"\nFetching analyst recommendations for {len(all_tickers)} tickers from Finnhub...")

        for i, ticker in enumerate(all_tickers):
            print(f"[{i+1}/{len(all_tickers)}] Fetching for {ticker}...")
            try:
                # Finnhub API call for recommendation trends
                recommendations = self.client.recommendation_trends(ticker)

                if not recommendations:
                    print(f"  - No recommendation data found for {ticker}.")
                    continue

                for rec in recommendations:
                    # Create a summary rating string
                    rating_summary = f"Buy: {rec.get('buy', 0)}, Hold: {rec.get('hold', 0)}, Sell: {rec.get('sell', 0)}, StrongBuy: {rec.get('strongBuy', 0)}, StrongSell: {rec.get('strongSell', 0)}"

                    # Create a unique ID for this record
                    record_id = hashlib.sha256(f"{ticker}{rec.get('period', '')}".encode()).hexdigest()

                    country = "US" if ticker in us_tickers else "KR"

                    schema = ResearchSchema(
                        id=record_id,
                        source="Finnhub",
                        country=country,
                        report_title="Analyst Recommendation Trend",
                        firm_name="Aggregated by Finnhub",
                        company_symbol=rec.get('symbol', ticker),
                        rating=rating_summary,
                        published_at=rec.get('period', ''),
                    )
                    all_research.append(schema)

                # Respect Finnhub's rate limit (60 calls/minute on free plan)
                time.sleep(1.1)

            except Exception as e:
                # Finnhub API often raises a generic Exception with a string message
                if "API limit reached" in str(e):
                    print("Finnhub API limit reached. Stopping for now.")
                    break
                print(f"Could not fetch recommendations for {ticker}. Error: {e}")

        print(f"\nSuccessfully collected {len(all_research)} research records.")
        return all_research


if __name__ == '__main__':
    print("--- Running Research Collector Example ---")

    if not os.getenv("FINNHUB_API_KEY"):
        print("\nERROR: FINNHUB_API_KEY environment variable not set.")
        print("Please set it to your API key to run this example.")
    else:
        print(f"Using Finnhub API key found in environment.")
        collector = ResearchCollector()

        # Fetch research for a small subset for testing
        # The main method gets all tickers, so we just run it
        research_data = collector.fetch_research()

        if research_data:
            print(f"\nSuccessfully fetched {len(research_data)} research records.")
            print("--- First 3 Records ---")
            for i, item in enumerate(research_data[:3]):
                print(f"[{i+1}] {item.company_symbol} ({item.published_at})")
                print(f"  - Rating: {item.rating}")
        else:
            print("\nNo research data found in the example run.")

    print("\n--- Research Collector Example Finished ---")
