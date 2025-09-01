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
        self.batch_upload_url = f"{self.backend_url}/api/v1/heroes/batch"

    def upload_stats(self, stats: List[HeroStatsUpload]):
        """Uploads a list of hero statistics to the backend."""
        if not stats:
            print("No stats to upload")
            return

        payload = [asdict(stat) for stat in stats]

        try:
            # Convert list of dataclasses to a list of dictionaries
            response = requests.post(self.batch_upload_url, json=payload, timeout=15)
            response.raise_for_status()
            print(
                f"Successfully uploaded {len(stats)} hero stats, count={len(stats)}, url={self.batch_upload_url}"
            )
        except requests.RequestException as e:
            print(
                f"An error occurred while uploading stats to the backend, err={e}, url={self.batch_upload_url}, stat={stats[0]}"
            )
