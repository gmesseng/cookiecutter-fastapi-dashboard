# Installation et lancement

## Prérequis

- Python {{ cookiecutter.python_version }}
- PostgreSQL 14 ou plus récent : une base SOURCE (OLTP) et une base DEST (analytique)
- Docker et Docker Compose, pour Redis (et, en option, le serveur de documentation)

## Installation

```bash
python -m venv .venv
source .venv/bin/activate          # Windows : .venv\Scripts\activate
pip install -r requirements.txt
```

Le fichier `.env` est créé à la génération du projet, avec une `{{ cookiecutter.env_prefix }}SECRET_KEY`
aléatoire. S'il manque :

```bash
cp .env.example .env
```

Renseigner ensuite au minimum les deux URI PostgreSQL
(voir [Configuration](configuration.md)) :

```dotenv
{{ cookiecutter.env_prefix }}SOURCE_POSTGRES_URI=postgresql://user:password@host:5432/source_db
{{ cookiecutter.env_prefix }}DEST_POSTGRES_URI=postgresql://user:password@host:5432/analytics_db
```

## Démarrer Redis

```bash
docker compose up -d               # ou : make up
```

Redis est publié sur le port hôte `{{ cookiecutter.redis_host_port }}`
(variable `{{ cookiecutter.env_prefix }}REDIS_HOST_PORT`).
{% if cookiecutter.include_etl == "y" %}
## Alimenter le data mart

```bash
python etl/run_etl.py --dry-run    # tout exécuter puis ROLLBACK : rien n'est publié
python etl/run_etl.py              # run réel
```

Détails : [ETL et data mart](etl.md).
{% endif %}
## Lancer l'API

```bash
make dev                           # rechargement automatique
make run                           # sans rechargement
```

| URL | Contenu |
|-----|---------|
| `http://localhost:{{ cookiecutter.api_port }}/docs` | Swagger UI |
| `http://localhost:{{ cookiecutter.api_port }}/redoc` | ReDoc |
| `http://localhost:{{ cookiecutter.api_port }}/health` | État des services externes |

Pour tester les routes dans Swagger, générer un token et le coller dans **Authorize** :

```bash
python generate_test_token.py      # ou : make token
```

## Lancer les tests

```bash
make test
```

Les tests de fumée n'ont besoin ni de PostgreSQL ni de Redis.

## Lancer avec Docker

```bash
docker build -t {{ cookiecutter.project_slug }} .
docker run --env-file .env -p {{ cookiecutter.api_port }}:{{ cookiecutter.api_port }} {{ cookiecutter.project_slug }}
```

!!! warning
    Le `.env` n'est jamais copié dans l'image (voir `.dockerignore`) : les variables sont
    injectées au lancement du conteneur. Depuis un conteneur, `localhost` désigne le conteneur
    lui-même : adapter `{{ cookiecutter.env_prefix }}REDIS_HOST` et les URI PostgreSQL.

## Consulter cette documentation

=== "En local"

    ```bash
    make docs-install                  # mkdocs, thème Material, mkdocstrings
    make docs                          # http://localhost:{{ cookiecutter.docs_port }}
    make docs-build                    # site statique dans docs/site/ (mode strict)
    ```

=== "Avec Docker"

    ```bash
    docker compose --profile docs up docs    # http://localhost:{{ cookiecutter.docs_port }}
    ```
