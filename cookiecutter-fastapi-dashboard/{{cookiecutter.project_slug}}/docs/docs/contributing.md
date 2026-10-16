# Contribuer

## Conventions git

Hooks installés à la génération du projet (`.git/hooks`) :

| Hook | Règle | Exemple |
|------|-------|---------|
| `commit-msg` | `[feat\|fix\|docs\|style\|refactor\|test\|chore]: message` | `[feat]: cadran ventes par catégorie` |
| `pre-push` | Tags au format `vX.Y.Z` | `v1.2.0` |

Les commits de merge et de revert générés par git sont acceptés tels quels.

## Avant d'ouvrir une merge request

```bash
make lint          # ruff
make test          # pytest
make docs-build    # documentation en mode strict
```

- Mettre à jour la section `[Unreleased]` de `CHANGELOG.md`.
- Mettre à jour la page de documentation concernée : une route, une variable
  d'environnement ou une table ajoutée doit y apparaître.

## Documentation

Les pages sont dans `docs/docs/`, la navigation dans `docs/mkdocs.yml`.

- Une nouvelle page doit être ajoutée à la `nav`.
- La [référence du code](reference/core.md) est générée depuis les docstrings : documenter les
  fonctions publiques au format Google (`Args:`, `Returns:`, `Raises:`).
- Le [changelog](changelog.md) est inclus depuis `CHANGELOG.md` : ne pas le recopier.
{% if cookiecutter.ci_tool == "GitHub" %}
## CI/CD

`.github/workflows/pipeline.yaml` :

| Déclencheur | Effet |
|-------------|-------|
| Push sur `develop` | Construction de la documentation, image `ghcr.io/{{ cookiecutter.github_owner }}/{{ cookiecutter.project_slug }}-dev` taguée avec le SHA |
| Lancement manuel | Choix de l'environnement (`develop`, `staging`, `production`) et du niveau de version ; image versionnée et release GitHub |

Secrets requis : `USERNAME`, `TOKEN`.
{% endif %}
