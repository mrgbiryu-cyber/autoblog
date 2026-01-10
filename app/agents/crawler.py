# app/agents/crawler.py

import asyncio
import random

class CrawlerAgent:
    def __init__(self):
        pass

    async def fetch_latest_news(self, keyword: str) -> dict:
        print(f"     [Crawler] Searching web for '{keyword}'...")
        await asyncio.sleep(1)
        fake_news_db = [
            f"2026 Latest Trends in {keyword}: Market is booming significantly.",
            f"Experts say {keyword} will be the key technology of the year.",
            f"New regulations regarding {keyword} have been announced today."
        ]
        selected_news = random.choice(fake_news_db)
        return {
            "content": selected_news,
            "source": "https://news.google.com/search?q=" + keyword
        }

