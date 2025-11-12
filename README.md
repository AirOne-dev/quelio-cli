Quelio CLI
==========

Un petit outil en ligne de commande pour consulter vos badgeages de la semaine dans une interface TUI (terminal) et en mode texte.

Pré-requis
- Python 3

Setup
- Rendre la commande executable: `chmod +x ./quelio`
- Configurer l'app : `./quelio setup`

Utilisation
- `./quelio setup` — Démarre l'assistant de configuration.
- `./quelio` — Ouvre le tableau de bord interactif (TUI).
- `./quelio status` — Affiche un résumé texte (sans TUI).
- `./quelio logout` — Nettoie les identifiants et la config.

Configuration
Lors du `setup`, vous pouvez configurer:
- **URL de l'API** — L'URL du serveur de badgeage.
- **Nom d'utilisateur** — Votre identifiant.
- **Heures/semaine** — Votre objectif hebdomadaire (ex: 38h).
- **Jours de travail** — Les jours où vous travaillez (par défaut: Lun-Ven).
  - Formats acceptés:
    - `1-5` (Lundi à Vendredi)
    - `1,2,3,4,5` (notation 1-7: 1=Lun, 7=Dim)
    - `0,1,2,3,4` (notation 0-6: 0=Lun, 6=Dim)
  - Exemples:
    - Lun-Ven: `1-5`
    - Lun-Sam: `1-6`
    - Mar-Ven: `2,3,4,5`

Notes
- Le TUI se met à jour en temps réel pour les badgeages en cours (timeline, totaux, temps restant).
- Le "temps restant" est calculé selon vos heures/semaine et jours de travail définis lors du `setup`.
- Les jours sans pointage sont automatiquement déduits du temps restant (seuls les jours de travail configurés sont pris en compte).
- Pour rendre la commande accessible partout, ajoutez le dossier courant à votre `PATH` ou créez un lien symbolique vers `quelio` dans un répertoire déjà présent dans votre `PATH`.
- Le script `./quelio` gère automatiquement:
    - La création d'un virtualenv local (`python3 -m venv .`) si absent.
    - L'installation des dépendances Python requises (`requests`, `textual`, `rich`, `keyring`) si manquantes.
    - Le lancement de l'app
