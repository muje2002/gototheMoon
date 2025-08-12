import hashlib
import time
from datetime import datetime
from typing import List, Dict, Tuple, Set

from gnews import GNews
from newspaper import Article, Config

from gotothemoon.datacollector.schemas import NewsSchema


class NewsCollector:
    """
    Collects news articles from various sources using GNews for discovery and
    Newspaper3k for full-text extraction.
    """

    def __init__(self):
        """Initializes the NewsCollector."""
        self.user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
        self.article_config = Config()
        self.article_config.browser_user_agent = self.user_agent
        self.article_config.request_timeout = 10

    def _get_full_text(self, url: str) -> str:
        """
        Retrieves the full text of an article from its URL.

        Args:
            url (str): The URL of the article.

        Returns:
            str: The full text of the article, or an empty string if it fails.
        """
        try:
            article = Article(url, config=self.article_config)
            article.download()
            article.parse()
            return article.text
        except Exception as e:
            print(f"  - Failed to download or parse article at {url}. Error: {e}")
            return ""

    def _calculate_hash(self, text: str) -> str:
        """Calculates a SHA256 hash for a given text."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def fetch_news(self,
                     country_code: str,
                     start_date: datetime,
                     end_date: datetime,
                     news_sources: List[str],
                     max_articles_per_day: int) -> List[NewsSchema]:
        """
        Fetches news articles for a given country and list of sources.

        Args:
            country_code (str): The country code (e.g., 'US', 'KR').
            start_date (datetime): The start date for fetching news.
            end_date (datetime): The end date for fetching news.
            news_sources (List[str]): A list of news source domains.
            max_articles_per_day (int): The maximum number of articles to fetch per day.

        Returns:
            List[NewsSchema]: A list of unique news data objects.
        """
        print(f"--- Starting News Collection for {country_code} ---")
        gnews = GNews(country=country_code, start_date=start_date, end_date=end_date)

        all_articles: List[NewsSchema] = []
        processed_hashes: Dict[str, NewsSchema] = {}

        for source_domain in news_sources:
            print(f"\nFetching news from: {source_domain}")
            query = f"site:{source_domain}"

            try:
                articles = gnews.get_news(query)
                print(f"  - Found {len(articles)} articles from GNews.")

                # Limit articles to respect the daily limit
                articles_to_process = articles[:max_articles_per_day]

                for i, article_data in enumerate(articles_to_process):
                    print(f"  - Processing article {i+1}/{len(articles_to_process)}: {article_data['title']}")

                    full_text = self._get_full_text(article_data['url'])
                    if not full_text:
                        continue # Skip if we can't get the content

                    # Use a combination of title and the first 500 chars of text for robust hashing
                    content_to_hash = article_data['title'] + full_text[:500]
                    content_hash = self._calculate_hash(content_to_hash)

                    if content_hash in processed_hashes:
                        print("  - Duplicate found. Incrementing count.")
                        processed_hashes[content_hash].duplicate_count += 1
                    else:
                        # New article, create a schema object
                        schema = NewsSchema(
                            id=content_hash,
                            source=article_data.get('publisher', {}).get('title', source_domain),
                            country=country_code,
                            headline=article_data['title'],
                            url=article_data['url'],
                            content=full_text,
                            published_at=article_data['published date'],
                            duplicate_count=1
                        )
                        processed_hashes[content_hash] = schema
                        all_articles.append(schema)

            except Exception as e:
                print(f"An error occurred while fetching from {source_domain}: {e}")

        print(f"\n--- Finished News Collection for {country_code}. Found {len(all_articles)} unique articles. ---")
        return all_articles

if __name__ == '__main__':
    collector = NewsCollector()

    # --- Example for US News ---
    us_sources = ["nytimes.com", "wsj.com"] # A small subset for testing
    us_start_date = datetime.now() - timedelta(days=1)
    us_end_date = datetime.now()

    us_news = collector.fetch_news(
        country_code='US',
        start_date=us_start_date,
        end_date=us_end_date,
        news_sources=us_sources,
        max_articles_per_day=5 # Limit for example
    )

    if us_news:
        print("\n--- First 3 US News Articles ---")
        for i, news_item in enumerate(us_news[:3]):
            print(f"[{i+1}] {news_item.headline} (Duplicates: {news_item.duplicate_count})")
            print(f"  - Source: {news_item.source}")
            print(f"  - Published: {news_item.published_at}")
    else:
        print("\nNo US news found in the example run.")
