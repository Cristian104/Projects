import aiohttp
import feedparser
from urllib.parse import quote
from loguru import logger
from app.core.config import settings

class NewsAggregator:
    def __init__(self):
        # Google News RSS Search URL (Global English)
        self.base_url = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"

    async def fetch_latest(self, ticker):
        """
        Fetches targeted news using the Company Name map.
        """
        # 1. Translate Ticker -> Human Search Query
        # If not in map, default to just "Ticker stock news"
        query_term = settings.COMPANY_MAP.get(ticker, f"{ticker} stock news")
        encoded_query = quote(query_term)
        
        url = self.base_url.format(query=encoded_query)
        logger.info(f"⚡ Fetching news for: '{query_term}'...")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status != 200:
                        logger.warning(f"⚠️ Google News error {response.status} for {ticker}")
                        return []

                    xml_data = await response.text()
                    feed = feedparser.parse(xml_data)

                    headlines = []
                    # Grab top 5 freshest articles
                    for entry in feed.entries[:5]:
                        headlines.append({
                            "title": entry.title,
                            "link": entry.link,
                            "source": entry.source.title if hasattr(entry, 'source') else "Google News",
                            "published": entry.published if hasattr(entry, 'published') else "Unknown"
                        })
                    
                    if not headlines:
                        logger.warning(f"⚠️ No articles found for {ticker}. using fallback.")
                        return []

                    return headlines[:2]

        except Exception as e:
            logger.error(f"❌ News Aggregator Failed: {e}")
            return []
