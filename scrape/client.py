import requests
from typing import List, Dict

class BackendClient:
    """Client for interacting with the OW2Stats backend API."""

    def __init__(self, backend_url: str):
        if not backend_url:
            raise ValueError("backend_url must be provided.")
        self.backend_url = backend_url.rstrip('/')
        self.batch_upload_url = f"{self.backend_url}/api/heroes/batch"

    def upload_stats(self, stats: List[Dict]):
        """Uploads a list of hero statistics to the backend."""
        if not stats:
            print("No stats to upload.")
            return

        try:
            # The backend expects a list of hero stats objects in JSON format
            response = requests.post(self.batch_upload_url, json=stats, timeout=15)
            response.raise_for_status()  # This will raise an HTTPError for bad responses (4xx or 5xx)
            print(f"Successfully uploaded {len(stats)} hero stats.")
        except requests.RequestException as e:
            print(f"An error occurred while uploading stats to the backend: {e}")

