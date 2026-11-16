import os

import requests
from dotenv import load_dotenv

load_dotenv()


class SerperClient:
    MAPS_URL = "https://google.serper.dev/maps"
    SEARCH_URL = "https://google.serper.dev/search"

    def __init__(self):
        self.api_key = os.getenv("SERPER_API_KEY")

        if not self.api_key:
            raise ValueError("SERPER_API_KEY is missing.")

        self._session = requests.Session()

    def _post(self, url: str, payload: dict) -> dict:
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }
        try:
            response = self._session.post(
                url,
                headers=headers,
                json=payload,
                timeout=15,
            )
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            raise RuntimeError(f"Serper returned an HTTP error: {e}") from e
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to connect to Serper: {e}") from e

    def search_hotels(
        self,
        destination: str,
        check_in: str,
        check_out: str,
        travelers: int,
        total_budget_inr: int,
    ) -> dict:
        return self._post(self.MAPS_URL, {"q": f"hotels in {destination}"})

    def search_hotel_price_for_place(
        self,
        hotel_name: str,
        destination: str,
        check_in: str,
        check_out: str,
    ) -> dict:
        """Fetch indicative nightly rate snippets for a specific hotel via Google Web Search."""
        clean_name = hotel_name.split("|")[0].split(" - ")[0].strip()
        return self._post(
            self.SEARCH_URL,
            {
                "q": f"{clean_name} {destination} price per night INR {check_in}",
                "gl": "in",
                "hl": "en",
                "num": 5,
            },
        )
