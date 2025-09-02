import logging
import requests
from typing import List
from dataclasses import asdict

from .models import HeroStatsUpload


class BackendClient:
    """Client for interacting with the OW2Stats backend API."""

    def __init__(
        self,
        logger: logging.Logger,
        backend_url: str,
    ):
        if not backend_url:
            raise ValueError("backend_url must be provided.")
        self.backend_url = backend_url.rstrip("/")
        self.batch_upload_url = f"{self.backend_url}/api/v1/heroes/batch"
        self.logger = logger

    def upload_stats(self, stats: List[HeroStatsUpload]):
        """Uploads a list of hero statistics to the backend."""
        if not stats:
            self.logger.debug("No stats to upload")
            return

        # Convert list of dataclasses to a list of dictionaries
        payload = [asdict(stat) for stat in stats]

        try:
            response = requests.post(self.batch_upload_url, json=payload, timeout=15)
            response.raise_for_status()
            self.logger.debug(
                f"Successfully uploaded hero stats, count={len(stats)}, url={self.batch_upload_url}"
            )
        except requests.RequestException as e:
            self.logger.warn(
                f"An error occurred while uploading stats to the backend, err={e}, url={self.batch_upload_url}, stat={stats[0]}"
            )
