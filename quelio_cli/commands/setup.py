"""`setup` command: configure the API and store credentials."""

from __future__ import annotations

import getpass
import os
import sys


from ..api import BadgeApi
from ..config import Config, normalize_url
from ..constants import CONFIG_PATH, KEYRING_SERVICE, DEFAULT_API_URL


def _parse_work_days(user_input: str) -> list[int]:
    """Parse work days input. Examples: '1-5', '0,1,2,3,4', '1,2,3,4,5'
    Returns list of weekday numbers (0=Mon, 6=Sun)."""
    user_input = user_input.strip()
    if not user_input:
        return [0, 1, 2, 3, 4]  # Default: Mon-Fri

    # Handle range format like "1-5"
    if "-" in user_input:
        try:
            parts = user_input.split("-")
            if len(parts) == 2:
                start = int(parts[0].strip())
                end = int(parts[1].strip())
                # Convert from 1-based (Mon=1) to 0-based (Mon=0)
                return list(range(start - 1, end))
        except Exception:
            pass

    # Handle comma-separated format like "0,1,2,3,4" or "1,2,3,4,5"
    try:
        days = [int(d.strip()) for d in user_input.split(",")]
        # Auto-detect if user used 1-based (1-7) or 0-based (0-6)
        if all(1 <= d <= 7 for d in days):
            # Convert from 1-based to 0-based
            return [d - 1 for d in days]
        elif all(0 <= d <= 6 for d in days):
            return days
    except Exception:
        pass

    return [0, 1, 2, 3, 4]  # Default on parse error


def run() -> None:
    print("\n— Configuration Badge CLI —\n")
    existing = Config.load()
    default_url = existing.api_url if existing else DEFAULT_API_URL
    default_user = existing.username if existing else ""
    default_week = existing.weekly_hours if existing else 38
    default_work_days = existing.work_days if existing else [0, 1, 2, 3, 4]

    api_url_in = input(f"URL de l'API [{default_url}]: ") or default_url
    api_url = normalize_url(api_url_in)
    username = input(f"Nom d'utilisateur [{default_user}]: ").strip() or default_user
    try:
        weekly_in = input(f"Heures/semaine [{default_week}]: ").strip()
        weekly_hours = int(weekly_in) if weekly_in else int(default_week)
    except Exception:
        weekly_hours = int(default_week)

    # Work days configuration
    print("\nJours de travail (0=Lun, 1=Mar, 2=Mer, 3=Jeu, 4=Ven, 5=Sam, 6=Dim)")
    print("Formats acceptés: '1-5' (Lun-Ven) ou '1,2,3,4,5' ou '0,1,2,3,4'")
    default_days_str = ",".join(str(d + 1) for d in default_work_days)
    work_days_in = input(f"Jours de travail [{default_days_str}]: ").strip()
    work_days = _parse_work_days(work_days_in) if work_days_in else default_work_days

    password = getpass.getpass("Mot de passe: ")

    # Quick connectivity check before saving
    print("Test de connexion…", end=" ")
    api = BadgeApi(api_url, username, password)
    try:
        data = api.fetch()
        ok = bool(data.get("hours"))
    except Exception as e:
        print("❌")
        print(f"Échec: {e}")
        sys.exit(2)
    print("✅")

    # Save config and password in keychain if available
    conf = Config(api_url=normalize_url(api_url), username=username, weekly_hours=weekly_hours, work_days=work_days)
    conf.save()
    try:
        import keyring
        keyring.set_password(KEYRING_SERVICE, f"{username}@{api_url}", password)
        print("Identifiants enregistrés (mot de passe dans le trousseau macOS).")
    except Exception as e:
        print("Avertissement: impossible d'enregistrer le mot de passe dans le trousseau.")
        print(f"Détail: {e}")
        print("Vous pourrez fournir le mot de passe via l'env `BADGECLI_PASSWORD` ou à la demande.")
