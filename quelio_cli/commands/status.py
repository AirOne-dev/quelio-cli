"""`status` command: non-interactive weekly recap in plain text."""

from __future__ import annotations

import getpass
import os
import sys
from typing import Dict, List

from ..api import BadgeApi
from ..config import Config
from ..constants import KEYRING_SERVICE
from ..utils_time import format_week_summary, minutes_to_hhmm


def _resolve_password(username: str, api_url: str) -> str:
    """Resolve password from keychain, env vars, or prompt interactively."""
    import keyring
    key = f"{username}@{api_url}"
    pwd = None
    try:
        pwd = keyring.get_password(KEYRING_SERVICE, key)
    except Exception:
        pwd = None
    if not pwd:
        pwd = os.environ.get("BADGECLI_PASSWORD") or os.environ.get("BADGECLI_PWD")
    if not pwd:
        print("Mot de passe introuvable (keychain/env). Saisissez-le (non stocké):", file=sys.stderr)
        pwd = getpass.getpass("Mot de passe: ")
    return pwd


def run() -> None:
    conf = Config.load()
    if not conf:
        print("Pas encore configuré. Lancez: quelio setup")
        sys.exit(1)

    pwd = _resolve_password(conf.username, conf.api_url)

    api = BadgeApi(conf.api_url, conf.username, pwd)
    try:
        data = api.fetch()
    except Exception as e:
        print(f"Erreur de chargement: {e}")
        sys.exit(2)
    hours: Dict[str, List[str]] = data.get("hours", {})
    total_eff = data.get("total_effective") or "?"
    total_paid = data.get("total_paid") or "?"

    print("\nMa semaine")
    print(f"  Total effectif : {total_eff}")
    print(f"  Total payé     : {total_paid}")
    print()
    for d, wd, minutes_ in format_week_summary(hours):
        print(f"- {wd} {d} : {minutes_to_hhmm(minutes_)}")
    print()
