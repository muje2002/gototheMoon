import json
import os
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict

from gotothemoon.datacollector.schemas import BaseSchema
from gotothemoon.datacollector.sources.kr_dart import DartCollector
from gotothemoon.datacollector.sources.us_edgar import EdgarCollector
from gotothemoon.datacollector.sources.news_collector import NewsCollector
from gotothemoon.datacollector.sources.research_collector import ResearchCollector

# --- Approved News Sources ---
KR_NEWS_SOURCES = [
    "news.naver.com", "news.daum.net", "chosun.com", "joongang.co.kr",
    "donga.com", "hani.co.kr", "mk.co.kr", "hankyung.com", "yonhapnews.co.kr", "ytn.co.kr"
]

US_NEWS_SOURCES = [
    "nytimes.com", "wsj.com", "washingtonpost.com", "cnn.com", "foxnews.com",
    "msnbc.com", "abcnews.go.com", "cbsnews.com", "nbcnews.com", "apnews.com",
    "reuters.com", "bloomberg.com", "cnbc.com", "usatoday.com", "npr.org",
    "latimes.com", "chicagotribune.com", "forbes.com", "businessinsider.com", "marketwatch.com"
]


def save_data(data: List[BaseSchema], base_data_path: Path):
    """
    Saves a list of data schemas to JSON files, organized by year, month,
    day, and category.
    """
    if not data:
        return

    # Group data by date, country, and category for file organization
    grouped_data: Dict[str, Dict[str, List]] = defaultdict(list)

    for item in data:
        try:
            # Handle multiple date formats to get a datetime object
            if not item.published_at: continue

            dt_obj = None
            if "Z" in item.published_at:
                dt_obj = datetime.fromisoformat(item.published_at.replace("Z", "+00:00"))
            elif "GMT" in item.published_at:
                 dt_obj = datetime.strptime(item.published_at, '%a, %d %b %Y %H:%M:%S %Z')
            else: # Assume YYYY-MM-DD
                dt_obj = datetime.fromisoformat(item.published_at)

            # Define path and group key
            year, month, day = str(dt_obj.year), f"{dt_obj.month:02d}", f"{dt_obj.day:02d}"
            group_key = (year, month, day, item.country, item.category)
            grouped_data[group_key].append(asdict(item))

        except Exception as e:
            print(f"Could not process item {item.id} with date '{item.published_at}'. Skipping. Error: {e}")
            continue

    # Write each group to a separate file
    for (year, month, day, country, category), records in grouped_data.items():
        storage_path = base_data_path / year / month / day
        storage_path.mkdir(parents=True, exist_ok=True)

        # Each file will contain records for one category for one day
        file_path = storage_path / f"{country}-{category}.json"

        print(f"Saving {len(records)} records to {file_path}")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=4)


def run_disclosure_collectors(start_date: str, end_date: str) -> List[BaseSchema]:
    """Runs all implemented disclosure collectors."""
    all_data: List[BaseSchema] = []
    # --- Run KR DART Collector ---
    print("\n" + "="*50)
    print("--- Running KR DART Collector ---")
    if os.getenv("DART_API_KEY"):
        try:
            collector = DartCollector()
            start_dart = start_date.replace('-', '')
            end_dart = end_date.replace('-', '')
            all_data.extend(collector.fetch_disclosures(start_dart, end_dart))
        except Exception as e:
            print(f"Failed to run DART collector: {e}")
    else:
        print("Skipping DART collector: DART_API_KEY not set.")
    print("="*50 + "\n")

    # --- Run US EDGAR Collector ---
    print("\n" + "="*50)
    print("--- Running US EDGAR Collector ---")
    try:
        collector = EdgarCollector()
        all_data.extend(collector.fetch_disclosures(start_date, end_date))
    except Exception as e:
        print(f"Failed to run EDGAR collector: {e}")
    print("="*50 + "\n")
    return all_data


def run_news_collectors(start_date: datetime, end_date: datetime) -> List[BaseSchema]:
    """Runs all implemented news collectors."""
    all_data: List[BaseSchema] = []
    collector = NewsCollector()

    # --- Run US News Collector ---
    all_data.extend(collector.fetch_news(
        country_code='US',
        start_date=start_date,
        end_date=end_date,
        news_sources=US_NEWS_SOURCES,
        max_articles_per_day=10 # Limit to 10 per source for this run
    ))

    # --- Run KR News Collector ---
    all_data.extend(collector.fetch_news(
        country_code='KR',
        start_date=start_date,
        end_date=end_date,
        news_sources=KR_NEWS_SOURCES,
        max_articles_per_day=10 # Limit to 10 per source for this run
    ))
    return all_data

def run_research_collector() -> List[BaseSchema]:
    """Runs the research data collector."""
    all_data: List[BaseSchema] = []
    print("\n" + "="*50)
    print("--- Running Research Collector ---")
    if os.getenv("FINNHUB_API_KEY"):
        try:
            collector = ResearchCollector()
            all_data.extend(collector.fetch_research())
        except Exception as e:
            print(f"Failed to run Research collector: {e}")
    else:
        print("Skipping Research collector: FINNHUB_API_KEY not set.")
    print("="*50 + "\n")
    return all_data


if __name__ == '__main__':
    DAYS_TO_FETCH = 2 # Keep it short for testing

    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=DAYS_TO_FETCH)
    start_date_str = start_dt.strftime('%Y-%m-%d')
    end_date_str = end_dt.strftime('%Y-%m-%d')

    print(f"--- Starting Data Collection Runner ---")
    print(f"Fetching data from {start_date_str} to {end_date_str}")

    # Set the base path to a top-level 'data' directory
    base_data_path = Path(__file__).parent.parent.parent / 'data'
    all_collected_data = []

    # Run Disclosure Collectors
    disclosure_data = run_disclosure_collectors(start_date=start_date_str, end_date=end_date_str)
    all_collected_data.extend(disclosure_data)

    # Run News Collectors
    news_data = run_news_collectors(start_date=start_dt, end_date=end_dt)
    all_collected_data.extend(news_data)

    # Run Research Collector
    research_data = run_research_collector()
    all_collected_data.extend(research_data)

    # --- Save all collected data ---
    if all_collected_data:
        print(f"\nTotal items collected across all sources: {len(all_collected_data)}. Saving data...")
        save_data(all_collected_data, base_data_path)
    else:
        print("\nNo data collected.")

    print("\n--- Data Collection Runner Finished ---")
