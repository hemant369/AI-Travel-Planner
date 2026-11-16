import os
import threading
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
        self._local = threading.local()

    def _get_session(self) -> requests.Session:
        session = getattr(self._local, "session", None)
        if session is None:
            session = requests.Session()
            self._local.session = session
        return session

    def search(self, query: str, max_results: int = 3, snippet_chars: int = 600) -> list[dict]:
        """Run a single search query and return simplified results."""
        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": max_results,
            "exclude_domains": [
                "youtube.com",
                "facebook.com",
                "instagram.com",
                "tiktok.com",
                "pinterest.com",
            ],
        }

        try:
            response = self._get_session().post(self.BASE_URL, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else "unknown"
            raise RuntimeError(f"Tavily returned HTTP {status}") from e
        except requests.RequestException as e:
            raise RuntimeError("Failed to connect to Tavily Search API") from e

        results = []
        seen_urls = set()
        for item in data.get("results", []):
            title = (item.get("title") or "").strip()
            url = (item.get("url") or "").strip()
            snippet = (item.get("content") or "").strip()
            if not title or not url or not snippet or url in seen_urls:
                continue
            seen_urls.add(url)
            results.append({"title": title, "url": url, "snippet": snippet[:snippet_chars]})
            if len(results) >= max_results:
                break
        return results
