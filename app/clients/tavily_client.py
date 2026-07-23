import os
import requests
from dotenv import load_dotenv

load_dotenv()


class TavilyClient:
    """Thin client wrapper around the Tavily Search API."""

    BASE_URL = "https://api.tavily.com/search"

    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError("TAVILY_API_KEY not found in environment variables")

    def search(self, query: str, max_results: int = 3) -> list[dict]:
        """Run a single search query and return simplified results."""
        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": max_results,
        }

        response = requests.post(self.BASE_URL, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = []
        seen_urls = set()
        for item in data.get("results", []):
            title = (item.get("title") or "").strip()
            url = (item.get("url") or "").strip()
            snippet = (item.get("content") or "").strip()
            if not title or not url or not snippet or url in seen_urls:
                continue
            seen_urls.add(url)
            results.append({"title": title, "url": url, "snippet": snippet[:600]})
            if len(results) >= max_results:
                break
        return results
