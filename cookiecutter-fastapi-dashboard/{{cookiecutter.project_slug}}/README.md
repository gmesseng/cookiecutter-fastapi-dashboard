# {{ cookiecutter.project_name }}

{{ cookiecutter.description }}.

API backend (FastAPI) en lecture seule qui alimente des écrans **dashboard / KPI**.
L'API ne lit **jamais** la base transactionnelle (OLTP) directement : {% if cookiecutter.include_etl == "y" %}un ETL
recopie les données source dans une base analytique et les transforme en tables
dénormalisées ; {% endif %}l'API ne sert que les tables du schéma `{{ cookiecutter.analytics_schema }}`, avec un cache Redis.

```
┌──────────────────────┐   etl/run_etl.py         ┌──────────────────────────────┐     ┌──────────────┐
│ Base SOURCE (OLTP)   │ ───────────────────────► │ Base DEST (analytique)       │ ──► │ API FastAPI  │
│ schéma public        │  COPY + db/001_mart.sql  │ {{ "%-28s"|format(cookiecutter.analytics_schema ~ ".fact_example") }} │     │ + cache Redis│
└──────────────────────┘                          └──────────────────────────────┘     └──────────────┘
```

---

## Sommaire

1. [Prérequis](#prérequis)
2. [Installation](#installation)
3. [Structure du projet](#structure-du-projet)
4. [Ajouter un cadran KPI](#ajouter-un-cadran-kpi)
5. [Variables d'environnement](#variables-denvironnement)
6. [Documentation](#documentation)
7. [Conventions git](#conventions-git)

---

## Prérequis

- Python {{ cookiecutter.python_version }}
- PostgreSQL 14 ou plus récent (bases SOURCE et DEST)
- Docker et Docker Compose, pour Redis

---

## Installation

```bash
# 1. Environnement Python
python -m venv .venv
source .venv/bin/activate          # Windows : .venv\Scripts\activate
pip install -r requirements.txt

# 2. Configuration : .env est créé à la génération (SECRET_KEY aléatoire).
#    Sinon : cp .env.example .env, puis renseigner les URI PostgreSQL.

# 3. Redis
docker compose up -d
{% if cookiecutter.include_etl == "y" %}
# 4. Alimenter le data mart (SOURCE -> DEST)
python etl/run_etl.py --dry-run    # tout exécuter puis ROLLBACK
python etl/run_etl.py
{% endif %}
# Lancer l'API
make dev                           # http://localhost:{{ cookiecutter.api_port }}/docs

# Token JWT de test pour Swagger (bouton Authorize)
python generate_test_token.py
```

Endpoints techniques :

| Route | Rôle |
|-------|------|
| `GET /healthz` | Liveness probe (process vivant) |
| `GET /readyz` | Readiness probe (Redis + bases SOURCE et DEST joignables) |
| `GET /health` | Statut détaillé de chaque service externe |
| `GET /docs`, `GET /redoc` | Documentation OpenAPI (routes GET uniquement) |

---

## Structure du projet

```
app/
├── main.py                  # bootstrap : middlewares, CORS, rate limit, erreurs, probes
├── api/
│   ├── deps.py              # require_permission (claim JWT "perms")
│   ├── params.py            # paramètres de requête partagés (pagination)
│   └── v1/
│       ├── router.py        # déclaration centralisée de toutes les routes
│       └── endpoints/       # handlers, sans logique ni SQL
├── core/                    # config, constantes, sécurité, cache, rate limit, logs, erreurs, santé
├── db/session.py            # sessions async SOURCE et DEST
├── schemas/                 # filtres (dépendances FastAPI) et modèles de réponse
└── services/                # logique métier et SQL (cache Redis via @cached)
{%- if cookiecutter.include_etl == "y" %}
db/001_mart.sql              # schéma et transformation du data mart
etl/run_etl.py               # ETL SOURCE -> DEST (COPY streamé, transaction unique, contrôles)
{%- endif %}
docs/                        # documentation MkDocs (mkdocs.yml + pages docs/docs/)
tests/                       # tests de fumée (sans PostgreSQL ni Redis)
```

---

## Ajouter un cadran KPI

Le cadran d'exemple `GET /api/v1/dashboards/kpis/exemple` montre le chemin complet :

1. **Modèle de réponse** dans `app/schemas/responses.py`.
2. **Service** dans `app/services/` : SQL sur `settings.T_...`, filtres via `build_where`, décoré par `@cached(prefix="...")`.
3. **Handler** dans `app/api/v1/endpoints/` : dépendances `parse_filters` et `require_permission(...)`, délègue au service.
4. **Route** déclarée dans `app/api/v1/router.py` (`router.add_api_route`).
5. Nouvelles tables : constante dans `app/core/constants.py`, champ et propriété dans `app/core/config.py`{% if cookiecutter.include_etl == "y" %}, alimentation dans `db/001_mart.sql` + `TABLES` / `MART_TABLES` / `CHECKS` de `etl/run_etl.py`{% endif %}.

---

## Variables d'environnement

Toutes les variables sont préfixées par `{{ cookiecutter.env_prefix }}`. Voir [.env.example](.env.example).

| Variable | Description |
|----------|-------------|
| `{{ cookiecutter.env_prefix }}SOURCE_POSTGRES_URI` | URI de la base SOURCE (OLTP) |
| `{{ cookiecutter.env_prefix }}DEST_POSTGRES_URI` | URI de la base DEST (analytique) |
{%- if cookiecutter.include_etl == "y" %}
| `{{ cookiecutter.env_prefix }}SOURCE_SCHEMA` | Schéma des tables source, `public` par défaut (lu par l'ETL) |
| `{{ cookiecutter.env_prefix }}DEST_SCHEMA` | Schéma du mart, `{{ cookiecutter.analytics_schema }}` par défaut (lu par l'ETL) |
{%- endif %}
| `{{ cookiecutter.env_prefix }}ANALYTICS_SCHEMA`, `{{ cookiecutter.env_prefix }}TABLE_FACT_EXAMPLE` | Schéma et noms des tables lues par l'API |
| `{{ cookiecutter.env_prefix }}SECRET_KEY` | Clé de signature JWT. L'API refuse de démarrer si c'est une valeur d'exemple |
| `{{ cookiecutter.env_prefix }}ACCESS_TOKEN_EXPIRE_MINUTES` | Durée de validité des tokens |
| `{{ cookiecutter.env_prefix }}REDIS_HOST`, `{{ cookiecutter.env_prefix }}REDIS_PORT`, `{{ cookiecutter.env_prefix }}REDIS_DB`, `{{ cookiecutter.env_prefix }}REDIS_TTL`, `{{ cookiecutter.env_prefix }}REDIS_KEY_PREFIX` | Connexion Redis et durée du cache |
| `{{ cookiecutter.env_prefix }}REDIS_HOST_PORT` | Port hôte publié par docker-compose pour Redis |
| `{{ cookiecutter.env_prefix }}DOCS_PORT` | Port hôte publié par docker-compose pour la documentation |
| `{{ cookiecutter.env_prefix }}BACKEND_CORS_ORIGINS` | Origines CORS autorisées (liste JSON ou valeurs séparées par des virgules) |

---

## Documentation

La documentation complète du projet (installation, configuration, API, ajout d'un cadran,
{%- if cookiecutter.include_etl == "y" %} ETL,{% endif %} dépannage, référence du code) est dans [docs/](docs/), au format
[MkDocs Material](https://squidfunk.github.io/mkdocs-material/).

```bash
make docs-install                          # dépendances (requirements-docs.txt)
make docs                                  # http://localhost:{{ cookiecutter.docs_port }}
make docs-build                            # site statique dans docs/site/ (mode strict)
docker compose --profile docs up docs      # même serveur, via Docker
```

Toute nouvelle route, variable d'environnement ou table doit être documentée dans `docs/docs/`.

---

## Conventions git

Hooks installés à la génération (`.git/hooks`) :

- **commit-msg** : `[feat|fix|docs|style|refactor|test|chore]: message`
- **pre-push** : tags au format `vX.Y.Z`{% if cookiecutter.ci_tool == "GitHub" %} (format lu par `.github/scripts/get-version.sh`)

CI/CD GitHub Actions (`.github/workflows/pipeline.yaml`) : build et push de l'image sur
`ghcr.io/{{ cookiecutter.github_owner }}/{{ cookiecutter.project_slug }}-{dev,stg,prod}`, release GitHub sur déclenchement manuel.
Secrets requis : `USERNAME`, `TOKEN`.{% endif %}

Raccourcis du Makefile : `make install`, `make up`, `make down`, `make dev`, `make run`, `make test`, `make lint`, `make token`, `make docs`, `make docs-build`{% if cookiecutter.include_etl == "y" %}, `make etl`, `make etl-dry-run`{% endif %}.

---

## Licence

Voir [LICENSE.txt](LICENSE.txt) — © {{ cookiecutter.company_name }}.
