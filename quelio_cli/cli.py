"""CLI entrypoint and command dispatcher."""

from __future__ import annotations

import sys
from typing import List


def main(argv: List[str] | None = None) -> None:
    if argv is None:
        argv = sys.argv
    if len(argv) <= 1:
        from .commands import dashboard
        dashboard.run()
        return
    cmd = argv[1].lower()
    if cmd == "setup":
        from .commands import setup
        setup.run()
    elif cmd == "logout":
        from .commands import logout
        logout.run()
    elif cmd == "status":
        from .commands import status
        status.run()
    elif cmd in ("dashboard", "ui", "tui"):
        from .commands import dashboard
        dashboard.run()
    else:
        print(
            "Commandes disponibles :\n"
            "  setup       – configurer et tester la connexion\n"
            "  logout      – supprimer les identifiants\n"
            "  status      – résumé non-interactif\n"
            "  dashboard   – interface interactive (par défaut)\n"
        )
