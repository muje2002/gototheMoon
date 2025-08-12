from typing import List
import requests
from bs4 import BeautifulSoup
from pykrx import stock

def _scrape_wiki_tickers(url: str, table_index: int, symbol_col: int, user_agent: str) -> List[str]:
    """Helper to scrape tickers from a Wikipedia table."""
    try:
        resp = requests.get(url, headers={'User-Agent': user_agent})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        table = soup.find_all('table', {'class': 'wikitable'})[table_index]
        tickers = []
        for row in table.find_all('tr')[1:]:
            ticker = row.find_all('td')[symbol_col].text.strip()
            tickers.append(ticker)
        return tickers
    except Exception as e:
        print(f"Could not scrape tickers from {url}. Error: {e}")
        return []

def get_us_tickers(user_agent: str = "GoToTheMoon Project/1.0") -> List[str]:
    """
    Gets a combined list of S&P 500 and NASDAQ-100 tickers.
    """
    print("Fetching S&P 500 tickers...")
    sp500 = _scrape_wiki_tickers(
        'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies', 0, 0, user_agent
    )
    print("Fetching NASDAQ-100 tickers...")
    nasdaq100 = _scrape_wiki_tickers(
        'https://en.wikipedia.org/wiki/Nasdaq-100', 4, 1, user_agent
    )

    all_tickers = sorted(list(set(sp500 + nasdaq100)))
    print(f"Found {len(all_tickers)} unique US tickers.")
    # Replace dots with dashes for tickers like 'BRK.B' -> 'BRK-B' for some APIs
    all_tickers = [ticker.replace('.', '-') for ticker in all_tickers]
    return all_tickers

def get_kr_tickers() -> List[str]:
    """
    Gets a list of all tickers for KOSPI and KOSDAQ listed companies.
    """
    print("Fetching all KOSPI and KOSDAQ tickers...")
    kospi_tickers = stock.get_market_ticker_list(market="KOSPI")
    kosdaq_tickers = stock.get_market_ticker_list(market="KOSDAQ")
    all_tickers = sorted(list(set(kospi_tickers + kosdaq_tickers)))
    print(f"Found {len(all_tickers)} unique KR tickers.")
    return all_tickers
