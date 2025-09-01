import requests
from typing import List
from dataclasses import asdict

from .models import HeroStatsUpload


class BackendClient:
    """Client for interacting with the OW2Stats backend API."""

    def __init__(self, backend_url: str):
        if not backend_url:
            raise ValueError("backend_url must be provided.")
        self.backend_url = backend_url.rstrip("/")
        self.batch_upload_url = f"{self.backend_url}/api/heroes/batch"

    def upload_stats(self, stats: List[HeroStatsUpload]):
        """Uploads a list of hero statistics to the backend."""
        if not stats:
            print("No stats to upload.")
            return

        try:
            # Convert list of dataclasses to a list of dictionaries
            payload = [asdict(stat) for stat in stats]
            response = requests.post(self.batch_upload_url, json=payload, timeout=15)
            response.raise_for_status()
            print(f"Successfully uploaded {len(stats)} hero stats.")
        except requests.RequestException as e:
            print(f"An error occurred while uploading stats to the backend: {e}")
