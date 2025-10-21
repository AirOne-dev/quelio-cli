Quelio CLI
==========

Un petit outil en ligne de commande pour consulter vos badgeages de la semaine dans une interface TUI (terminal) et en mode texte.

<br />
<img width="405" height="727" alt="image" src="https://github.com/user-attachments/assets/fc6412ef-b448-4b59-a5e6-be62908edc16" />
<br /><br />

Pré-requis
- [AirOne-dev/quelio-api](https://github.com/AirOne-dev/quelio-api) configuré et installé sur un serveur web
- Python 3

Setup
- Rendre la commande executable: `chmod +x ./quelio`
- Configurer l'app : `./quelio setup`

Utilisation
- `./quelio setup` — Démarre l’assistant de configuration.
- `./quelio` — Ouvre le tableau de bord interactif (TUI).
- `./quelio status` — Affiche un résumé texte (sans TUI).
- `./quelio logout` — Nettoie les identifiants et la config.

Notes
- Le TUI se met à jour en temps réel pour les badgeages en cours (timeline, totaux, temps restant).
- Le “temps restant” est calculé selon vos heures/semaine définies lors du `setup`.
- Pour rendre la commande accessible partout, ajoutez le dossier courant à votre `PATH` ou créez un lien symbolique vers `quelio` dans un répertoire déjà présent dans votre `PATH`.
- Le script `./quelio` gère automatiquement:
    - La création d’un virtualenv local (`python3 -m venv .`) si absent.
    - L’installation des dépendances Python requises (`requests`, `textual`, `rich`, `keyring`) si manquantes.
    - Le lancement de l'app
