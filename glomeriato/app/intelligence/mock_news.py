class MockNewsAggregator:
    async def fetch_latest(self, ticker):
        """Mock news feed to test DeepSeek sentiment and decision logic."""
        return [
            {
                "title": f"BREAKING: {ticker} reports 500% earnings growth and new AI partnership", 
                "source": "Lab News",
                "published": "Just now"
            },
            {
                "title": f"Institutional investors moving heavily into {ticker} after breakthrough", 
                "source": "Mock Finance",
                "published": "1 minute ago"
            }
        ]
