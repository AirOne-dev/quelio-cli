"""HTTP client for the Kelio badge API."""

from __future__ import annotations

from typing import Dict

import requests

from .config import normalize_url
from .constants import DEFAULT_COOKIES


class ApiError(RuntimeError):
    """Raised when the API call fails or returns an invalid response."""


class BadgeApi:
    """Simple API wrapper around a single POST endpoint."""

    def __init__(self, api_url: str, username: str, password: str) -> None:
        self.api_url = normalize_url(api_url)
        self.username = username
        self.password = password

    def fetch(self) -> Dict:
        """POST credentials and return parsed JSON data."""
        try:
            resp = requests.post(
                self.api_url,
                files={
                    "username": (None, self.username),
                    "password": (None, self.password),
                },
                cookies=DEFAULT_COOKIES,
                timeout=20,
            )
        except requests.RequestException as e:  # pragma: no cover
            raise ApiError(f"Erreur réseau: {e}")
        if resp.status_code != 200:
            raise ApiError(f"HTTP {resp.status_code}: {resp.text[:200]}")
        try:
            data = resp.json()
        except Exception:
            raise ApiError("Réponse invalide (JSON)")
        if not isinstance(data, dict) or "hours" not in data:
            raise ApiError("Réponse inattendue de l'API")
        return data

