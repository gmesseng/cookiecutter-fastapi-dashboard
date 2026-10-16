# Changelog
Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),  
et ce projet suit [Semantic Versioning](https://semver.org/lang/fr/).

## [2.1.0] - 2026-10-16
### Ajouté
- Documentation MkDocs Material dans chaque projet généré (`docs/mkdocs.yml`, pages `docs/docs/`),
  sur le modèle du template Airflow : guides (installation, configuration, API, ajout d'un cadran,
  ETL, dépannage, contribution), référence du code via mkdocstrings, changelog inclus depuis
  `CHANGELOG.md`.
- `requirements-docs.txt`, cibles `make docs-install`, `make docs`, `make docs-build`, service
  `docs` (profil `docs`) dans `docker-compose.yml`, job de build strict dans la CI GitHub.
- Variable `docs_port` (défaut `9000`).

## [2.0.0] - 2026-10-16
### Modifié
- Le template Airflow devient `cookiecutter-fastapi-dashboard` : le projet généré est une API
  FastAPI de dashboard / KPI issue de `reading-classroom-dashboard-api`.
- Hook post-génération : le contrôle des messages de commit passe dans un hook `commit-msg`
  (l'ancien `pre-commit` vérifiait le message du commit précédent), `git init` est exécuté
  avant l'installation des hooks, et le format des tags devient `vX.Y.Z`.
- `ci_tool` est désormais effectif (`GitHub` / `None`).

### Ajouté
- Hook pré-génération de validation des réponses.
- Variables `env_prefix`, `api_port`, `redis_host_port`, `analytics_schema`, `include_etl`,
  `github_owner`, `init_git`.
- Création automatique du `.env` avec une `SECRET_KEY` aléatoire.

### Supprimé
- Configuration Airflow (DAGs, plugins, `airflow.cfg`), scripts `resources/`, MkDocs,
  `.gitlab-ci.yml` et script `install_compliance_hooks.sh`.
- Variables inutilisées `postgres_version`, `open_source_license`.

## [1.2.0] - 2025-02-03
### Ajouté
- Intégration de Celery pour la gestion des tâches asynchrones.
- Ajout de Flower pour la supervision de Celery.
- Ajout du support Redis pour le broker.

### Modifié
- Mise à jour du `Dockerfile` pour gérer `BUILD_ENVIRONMENT`.

### Corrigé
- Problème de variable d’environnement non chargée dans Docker.

## [1.1.0] - 2025-01-20
### Ajouté
- Mise en place de Airflow avec la configuration de base.
- Ajout de la configuration PostgreSQL et Redis dans `docker-compose.yml`.
