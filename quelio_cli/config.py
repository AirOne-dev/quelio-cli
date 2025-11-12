"""Configuration model and helpers."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Optional

from .constants import CONFIG_DIR, CONFIG_PATH, DEFAULT_API_URL


def normalize_url(u: str) -> str:
    """Normalize API URL by escaping spaces and ensuring a trailing slash."""
    u = u.strip().replace(" ", "%20")
    if not u.endswith("/"):
        u += "/"
    return u


@dataclass
class Config:
    api_url: str
    username: str
    weekly_hours: int = 38
    work_days: list[int] = None  # 0=lundi, 1=mardi, ..., 6=dimanche

    def __post_init__(self):
        # Default work days: Monday to Friday (0-4)
        if self.work_days is None:
            self.work_days = [0, 1, 2, 3, 4]

    @staticmethod
    def load() -> Optional["Config"]:
        """Load configuration from disk, return None if missing/invalid."""
        if not os.path.exists(CONFIG_PATH):
            return None
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Config(
                api_url=data.get("api_url", DEFAULT_API_URL),
                username=data["username"],
                weekly_hours=int(data.get("weekly_hours", 38)),
                work_days=data.get("work_days", [0, 1, 2, 3, 4]),
            )
        except Exception:
            return None

    def save(self) -> None:
        """Persist configuration to disk."""
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "api_url": self.api_url,
                    "username": self.username,
                    "weekly_hours": int(self.weekly_hours),
                    "work_days": self.work_days if self.work_days else [0, 1, 2, 3, 4],
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

