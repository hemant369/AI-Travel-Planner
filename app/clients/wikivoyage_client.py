"""Free, no-key client for the Wikivoyage MediaWiki API."""

from urllib.parse import quote
import requests


class WikivoyageClient:
    """Fetch concise destination overviews from Wikivoyage."""

    API_URL = "https://en.wikivoyage.org/w/api.php"
    HEADERS = {"User-Agent": "WayfinderTravelPlanner/1.0 (https://github.com)"}

    def __init__(self) -> None:
        self._session = requests.Session()
        self._session.headers.update(self.HEADERS)

    def get_overview(self, destination: str) -> list[dict]:
        """Return a 1-item list with title, url, and intro snippet if found."""
        params = {
            "action": "query",
            "prop": "extracts",
            "exintro": 1,
            "explaintext": 1,
            "redirects": 1,
            "titles": destination,
            "format": "json",
        }
        response = self._session.get(self.API_URL, params=params, timeout=10)
        response.raise_for_status()
        pages = (response.json().get("query") or {}).get("pages") or {}
        for page in pages.values():
            if "missing" in page:
                continue
            title = (page.get("title") or destination).strip()
            extract = " ".join((page.get("extract") or "").split())
            if not extract:
                continue
            url = f"https://en.wikivoyage.org/wiki/{quote(title.replace(' ', '_'))}"
            return [{"title": f"{title} — Wikivoyage", "url": url, "snippet": extract[:1200]}]
        return []
