import os

import requests
from dotenv import load_dotenv

load_dotenv()


class MapsClient:
    """
    Client for interacting with the Google Routes API.
    """

    BASE_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"

    DRIVE = "DRIVE"
    TWO_WHEELER = "TWO_WHEELER"

    def __init__(self) -> None:
        self.api_key = os.getenv("GOOGLE_MAPS_API_KEY")

        if not self.api_key:
            raise ValueError("GOOGLE_MAPS_API_KEY is not configured.")

    def compute_route(
        self,
        source: str,
        destination: str,
        travel_mode: str = DRIVE,
    ) -> dict:
        """
        Compute a route between two locations.

        Args:
            source: Starting location (city or address).
            destination: Destination location (city or address).
            travel_mode: Travel mode supported by the Google Routes API.
                Supported values include:
                - DRIVE
                - TWO_WHEELER

        Returns:
            Raw JSON response from the Google Routes API.

        Raises:
            RuntimeError:
                If the request fails or the API returns an error.
        """

        body = {
            "origin": {
                "address": source,
            },
            "destination": {
                "address": destination,
            },
            "travelMode": travel_mode,
        }

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": (
                "routes.distanceMeters,"
                "routes.duration,"
                "routes.polyline.encodedPolyline"
            ),
        }

        try:
            response = requests.post(
                self.BASE_URL,
                headers=headers,
                json=body,
                timeout=15,
            )

            response.raise_for_status()

            return response.json()

        except requests.HTTPError as e:
            error_message = response.text if response is not None else str(e)
            raise RuntimeError(
                f"Google Routes API returned an error: {error_message}"
            ) from e

        except requests.RequestException as e:
            raise RuntimeError(
                f"Failed to connect to Google Routes API: {e}"
            ) from e