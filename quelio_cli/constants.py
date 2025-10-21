"""Global constants and defaults for Quelio CLI."""

from __future__ import annotations

import os


# Configuration paths
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".badgecli")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
KEYRING_SERVICE = "badgecli"

# API defaults
DEFAULT_API_URL = (
    "https://www.example.com/quel%20io/api/"
)
DEFAULT_COOKIES = {}

# Weekday labels (French) for user-facing output
WEEKDAY_FR = [
    "lundi",
    "mardi",
    "mercredi",
    "jeudi",
    "vendredi",
    "samedi",
    "dimanche",
]

PAUSE_PAID_MINUTES = 7
