"""`logout` command: delete stored credentials and config."""

from __future__ import annotations

import os


from ..config import Config
from ..constants import CONFIG_PATH, KEYRING_SERVICE


def run() -> None:
    conf = Config.load()
    if conf:
        try:
            import keyring
            keyring.delete_password(KEYRING_SERVICE, f"{conf.username}@{conf.api_url}")
        except Exception:
            pass
        try:
            os.remove(CONFIG_PATH)
        except FileNotFoundError:
            pass
        print("Déconnecté et configuration supprimée.")
    else:
        print("Aucune configuration trouvée.")
