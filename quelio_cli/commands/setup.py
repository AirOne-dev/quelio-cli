"""`setup` command: configure the API and store credentials."""

from __future__ import annotations

import getpass
import os
import sys


from ..api import BadgeApi
from ..config import Config, normalize_url
from ..constants import CONFIG_PATH, KEYRING_SERVICE, DEFAULT_API_URL


def run() -> None:
    print("\n— Configuration Badge CLI —\n")
    existing = Config.load()
    default_url = existing.api_url if existing else DEFAULT_API_URL
    default_user = existing.username if existing else ""
    default_week = existing.weekly_hours if existing else 38

    api_url_in = input(f"URL de l'API [{default_url}]: ") or default_url
    api_url = normalize_url(api_url_in)
    username = input(f"Nom d'utilisateur [{default_user}]: ").strip() or default_user
    try:
        weekly_in = input(f"Heures/semaine [{default_week}]: ").strip()
        weekly_hours = int(weekly_in) if weekly_in else int(default_week)
    except Exception:
        weekly_hours = int(default_week)
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
    conf = Config(api_url=normalize_url(api_url), username=username, weekly_hours=weekly_hours)
    conf.save()
    try:
        import keyring
        keyring.set_password(KEYRING_SERVICE, f"{username}@{api_url}", password)
        print("Identifiants enregistrés (mot de passe dans le trousseau macOS).")
    except Exception as e:
        print("Avertissement: impossible d'enregistrer le mot de passe dans le trousseau.")
        print(f"Détail: {e}")
        print("Vous pourrez fournir le mot de passe via l'env `BADGECLI_PASSWORD` ou à la demande.")
