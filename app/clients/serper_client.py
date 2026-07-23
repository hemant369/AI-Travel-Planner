import os

import requests
from dotenv import load_dotenv

load_dotenv()


class SerperClient:
    BASE_URL = "https://google.serper.dev/maps"

    def __init__(self):
        self.api_key = os.getenv("SERPER_API_KEY")

        if not self.api_key:
            raise ValueError("SERPER_API_KEY is missing.")

    def search_hotels(self, destination: str, check_in: str, check_out: str,
                      travelers: int, total_budget_inr: int) -> dict:
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }

        payload = {
            "q": (f"Hotels in {destination} from {check_in} to {check_out} for "
                  f"{travelers} travelers within total trip budget INR {total_budget_inr}")
        }

        try:
            response = requests.post(
                self.BASE_URL,
                headers=headers,
                json=payload,
                timeout=15,
            )

            response.raise_for_status()

            return response.json()

        except requests.HTTPError as e:
            raise RuntimeError(
                f"Serper returned an HTTP error: {e}"
            ) from e

        except requests.RequestException as e:
            raise RuntimeError(
                f"Failed to connect to Serper: {e}"
            ) from e
