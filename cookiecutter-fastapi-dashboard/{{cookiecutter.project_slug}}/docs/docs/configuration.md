# Configuration

La configuration est centralisée dans `app/core/config.py` (pydantic-settings).
Les valeurs sont lues dans les variables d'environnement, puis dans le fichier `.env`.
Toutes les variables sont préfixées par **`{{ cookiecutter.env_prefix }}`**.

!!! danger "Démarrage refusé"
    L'API refuse de démarrer si `{{ cookiecutter.env_prefix }}SECRET_KEY` vaut une valeur d'exemple
    (`change_me`, `secret`, `generate_a_secure_key_here_never_commit_the_real_one`…) ou si une URI
    PostgreSQL est vide. Il n'existe aucune valeur de repli non sécurisée.

## Bases de données

| Variable | Défaut | Description |
|----------|--------|-------------|
| `{{ cookiecutter.env_prefix }}SOURCE_POSTGRES_URI` | — (obligatoire) | URI de la base SOURCE (OLTP) |
| `{{ cookiecutter.env_prefix }}DEST_POSTGRES_URI` | — (obligatoire) | URI de la base DEST (analytique), lue par l'API |
| `{{ cookiecutter.env_prefix }}ANALYTICS_SCHEMA` | `{{ cookiecutter.analytics_schema }}` | Schéma des tables lues par l'API |
| `{{ cookiecutter.env_prefix }}TABLE_FACT_EXAMPLE` | `fact_example` | Table du cadran d'exemple |
{%- if cookiecutter.include_etl == "y" %}
| `{{ cookiecutter.env_prefix }}SOURCE_SCHEMA` | `public` | Schéma des tables source (lu par l'ETL) |
| `{{ cookiecutter.env_prefix }}DEST_SCHEMA` | `{{ cookiecutter.analytics_schema }}` | Schéma du mart (écrit par l'ETL) |
{%- endif %}

Les URI s'écrivent au format `postgresql://…` ; l'API les convertit elle-même en
`postgresql+asyncpg://…` pour SQLAlchemy async.

## Sécurité

| Variable | Défaut | Description |
|----------|--------|-------------|
| `{{ cookiecutter.env_prefix }}SECRET_KEY` | — (obligatoire) | Clé de signature des JWT (HS256), partagée avec le service qui émet les tokens |
| `{{ cookiecutter.env_prefix }}ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Durée de validité des tokens émis par `create_access_token` |
| `{{ cookiecutter.env_prefix }}BACKEND_CORS_ORIGINS` | `localhost:3000`, `localhost:{{ cookiecutter.api_port }}` | Origines CORS autorisées : liste JSON ou valeurs séparées par des virgules |

## Redis

| Variable | Défaut | Description |
|----------|--------|-------------|
| `{{ cookiecutter.env_prefix }}REDIS_HOST` | `localhost` | Hôte Redis |
| `{{ cookiecutter.env_prefix }}REDIS_PORT` | `6379` (`{{ cookiecutter.redis_host_port }}` dans `.env.example`) | Port Redis |
| `{{ cookiecutter.env_prefix }}REDIS_DB` | `0` | Numéro de base Redis |
| `{{ cookiecutter.env_prefix }}REDIS_TTL` | `300` | Durée de vie du cache, en secondes |
| `{{ cookiecutter.env_prefix }}REDIS_KEY_PREFIX` | `{{ cookiecutter.__project_snake }}:` | Préfixe de toutes les clés de cache |

## Application

| Variable | Défaut | Description |
|----------|--------|-------------|
| `{{ cookiecutter.env_prefix }}PROJECT_NAME` | `{{ cookiecutter.project_name }}` | Titre de l'API (OpenAPI) |
| `{{ cookiecutter.env_prefix }}API_V1_STR` | `/api/v1` | Préfixe des routes métier |
| `{{ cookiecutter.env_prefix }}COMPANY_NAME` | `{{ cookiecutter.company_name }}` | Nom de la société |

## Docker Compose

Lues par `docker-compose.yml` uniquement, pas par l'API.

| Variable | Défaut | Description |
|----------|--------|-------------|
| `{{ cookiecutter.env_prefix }}REDIS_HOST_PORT` | `{{ cookiecutter.redis_host_port }}` | Port hôte publié pour Redis |
| `{{ cookiecutter.env_prefix }}DOCS_PORT` | `{{ cookiecutter.docs_port }}` | Port hôte publié pour cette documentation |

## Ajouter une variable

1. Valeur par défaut dans `app/core/constants.py` (section 1).
2. Champ typé dans la classe `Settings` de `app/core/config.py`.
3. Ligne commentée dans `.env.example`, et ligne dans le tableau de cette page.
