import os
import time
from datetime import datetime, timedelta
from typing import List, Optional

import edgar

from gotothemoon.datacollector.schemas import DisclosureSchema
from gotothemoon.datacollector.utils.tickers import get_us_tickers


class EdgarCollector:
    """
    Collects public company disclosures from the U.S. Securities and Exchange
    Commission (SEC) EDGAR database.
    """

    def __init__(self, user_agent: Optional[str] = None):
        """
        Initializes the EdgarCollector.

        Args:
            user_agent (str, optional): A user agent string to identify your
                                        client to the SEC. It should be in the
                                        format "Sample Company Name AdminContact@example.com".
                                        If not provided, a default will be used.
        """
        self.user_agent = user_agent or "GoToTheMoon Project jules@example.com"
        edgar.set_identity(self.user_agent)
        print(f"EDGAR identity set to: '{self.user_agent}'")

    def fetch_disclosures(self, start_date: str, end_date: str) -> List[DisclosureSchema]:
        """
        Fetches all public disclosures for S&P 500 and NASDAQ-100 companies
        within a given date range.

        Args:
            start_date (str): The start date in 'YYYY-MM-DD' format.
            end_date (str): The end date in 'YYYY-MM-DD' format.

        Returns:
            List[DisclosureSchema]: A list of disclosure data objects.
        """
        all_disclosures: List[DisclosureSchema] = []
        tickers = get_us_tickers(self.user_agent)

        date_range = f"{start_date}:{end_date}"
        print(f"\nFetching EDGAR disclosures for {len(tickers)} tickers from {date_range}...")

        for i, ticker in enumerate(tickers):
            print(f"[{i+1}/{len(tickers)}] Fetching for {ticker}...")
            try:
                company = edgar.Company(ticker)
                filings = company.get_filings(filing_date=date_range)

                for filing in filings:
                    disclosure = DisclosureSchema(
                        id=filing.accession_no,
                        source='EDGAR',
                        country='US',
                        report_title=filing.form, # e.g. 10-K, 8-K
                        company_name=company.name,
                        company_symbol=ticker,
                        url_to_document=filing.url,
                        filing_type=filing.form,
                        published_at=filing.filing_date.isoformat(),
                    )
                    all_disclosures.append(disclosure)

                # SEC rate limit: 10 requests per second.
                time.sleep(0.1)

            except Exception as e:
                print(f"Could not fetch filings for {ticker}. Error: {e}")

        print(f"\nSuccessfully collected {len(all_disclosures)} disclosures.")
        return all_disclosures


if __name__ == '__main__':
    print("--- Running EDGAR Collector Example ---")

    collector = EdgarCollector(user_agent="Test Project test@example.com")

    # Fetch disclosures for the last 3 days as a test
    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=3)
    start_date_str = start_dt.strftime('%Y-%m-%d')
    end_date_str = end_dt.strftime('%Y-%m-%d')

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

    print("\n--- EDGAR Collector Example Finished ---")
