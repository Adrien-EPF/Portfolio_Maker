# CLAUDE.md

Règles de comportement pour ce dépôt. Le vocabulaire du domaine est dans `CONTEXT.md`, les pointeurs skills/issues dans `AGENTS.md` — ne pas dupliquer ici.

## Git
- Travailler directement sur `main` : pas de branches ni de pull requests pour ce dépôt.
- Quand un commit clôt une issue GitHub, la référencer dans le message (`closes #N`), comme dans l'historique existant.

## Tests
- Une tâche n'est terminée qu'après un `pytest` qui passe, même pour un petit changement.
- Toute nouvelle route ou tout nouveau comportement visible s'accompagne d'un test dans `tests/test_pages.py`.

## Dépendances
- Proposer et attendre la validation de l'utilisateur avant d'ajouter une entrée à `requirements.txt`.

## Base de données
- `portfolio.db` est un fichier de dev local, ignoré par git : pas de cérémonie de migration à respecter en modifiant les modèles SQLModel.

## Design handoffs
- Un dossier `design_handoff_*` est une spec à suivre à la lettre — couleurs, espacements, structure HTML — avant d'implémenter, pas une simple inspiration.
