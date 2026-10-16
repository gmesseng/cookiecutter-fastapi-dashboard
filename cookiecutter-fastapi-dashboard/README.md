# Cookiecutter FastAPI Dashboard

A Cookiecutter template for jumpstarting production-ready, read-only **FastAPI dashboard / KPI APIs**
served from an analytical PostgreSQL database, with a Redis cache.

Extracted from the `reading-classroom-dashboard-api` project: the infrastructure is kept as is,
the Ready Classroom business code is replaced by one example KPI that shows the full path
(schema → service → handler → route).

## Features

- [x] FastAPI app: JWT (HS256) on every route, permission check from the `perms` claim
- [x] Redis cache through a `@cached(prefix=...)` decorator (key = prefix + every argument)
- [x] Rate limiting (slowapi, 60 req/min per IP), request ID, JSON access logs (structlog), security headers
- [x] Machine-readable JSON errors, GET-only OpenAPI, ReDoc
- [x] `/healthz`, `/readyz`, `/health` probes (Redis + SOURCE and DEST databases)
- [x] Two async SQLAlchemy engines: SOURCE (OLTP) and DEST (analytics)
- [x] Optional ETL SOURCE → DEST: streamed COPY, single transaction, blocking checks, run journal
- [x] Docker image (uv), docker-compose for Redis, Makefile, smoke tests
- [x] MkDocs Material documentation in every project (`docs/`): guides + code reference (mkdocstrings), strict build in CI
- [x] Optional GitHub Actions pipeline: ghcr.io images per environment, versioned releases
- [x] Git hooks: commit message and tag conventions

## Technology and Tools

- Python, FastAPI, Pydantic Settings
- PostgreSQL (asyncpg / psycopg2), SQLAlchemy async
- Redis
- Docker, GitHub Actions
- MkDocs, Material for MkDocs, mkdocstrings

## Usage

Install Cookiecutter:

    $ pip install "cookiecutter>=2.6.0"

Generate a project (local path or repository URL):

    $ cookiecutter path/to/cookiecutter-fastapi-dashboard

Answer the prompts, for example:

    [1/18] project_name (Kaeyros BI analytics Project): Sales Dashboard API
    [2/18] project_slug (sales-dashboard-api):
    [3/18] description (API FastAPI de dashboard et KPI, ...):
    [4/18] company_name (Kaeyros Analytics):
    [5/18] author_name (Kaeyros Analytics):
    [6/18] email (contact@kaeyros-analytics.com):
    [7/18] version (1.0.0):
    [8/18] env_prefix (SDA_):
    [9/18] python_version (3.11):
    [10/18] api_port (8000):
    [11/18] redis_host_port (6380):
    [12/18] docs_port (9000):
    [13/18] analytics_schema (analytics):
    [14/18] include_etl (y):
    [15/18] Select ci_tool
      1 - GitHub
      2 - None
      Choose from [1/2] (1):
    [16/18] github_owner (kaeyros-analytics-org):
    [17/18] init_git (y):
    [18/18] debug (y):

Non-interactive generation:

    $ cookiecutter path/to/cookiecutter-fastapi-dashboard --no-input \
        project_name="Sales Dashboard API" env_prefix=SALES_ include_etl=n ci_tool=None

## Template variables

| Variable | Default | Used for |
|----------|---------|----------|
| `project_name` | `Kaeyros BI analytics Project` | API title, README, `.env` |
| `project_slug` | derived (kebab-case) | folder, compose project, Docker image names |
| `description` | — | OpenAPI description, README |
| `company_name` | `Kaeyros Analytics` | LICENSE, `COMPANY_NAME` setting |
| `author_name`, `email`, `version` | — | CHANGELOG, OpenAPI version |
| `env_prefix` | initials of `project_name` + `_` | prefix of every environment variable (`RC_` in the original project) |
| `python_version` | `3.11` | Docker base image |
| `api_port` | `8000` | uvicorn, Dockerfile, CORS defaults |
| `redis_host_port` | `6380` | docker-compose published port, `.env` |
| `docs_port` | `9000` | MkDocs server port (`make docs`, docker-compose `docs` profile) |
| `analytics_schema` | `analytics` | data mart schema (API + ETL) |
| `include_etl` | `y` | keeps `etl/` and `db/` |
| `ci_tool` | `GitHub` / `None` | keeps `.github/` |
| `github_owner` | `kaeyros-analytics-org` | ghcr.io registry owner |
| `init_git` | `y` | `git init` + hooks |

Derived, not prompted: `__project_snake` (slug with underscores) for the Redis key prefix,
logger name, container and volume names.

## Documentation

Every generated project ships a MkDocs Material site in `docs/` (same layout as the Airflow
template: `docs/mkdocs.yml` + pages in `docs/docs/`):

| Page | Content |
|------|---------|
| Présentation | architecture, features |
| Installation et lancement | setup, Redis, ETL, API, tests, Docker, docs |
| Configuration | every `<env_prefix>*` variable |
| Structure du projet | tree and layering rules |
| Utiliser l'API | JWT, permissions, routes, error codes, cache |
| Ajouter un cadran KPI | step-by-step + checklist |
| ETL et data mart | only when `include_etl=y` |
| Référence du code | generated from docstrings (mkdocstrings) |
| Dépannage, Contribuer, Changelog, À propos | changelog included from `CHANGELOG.md` |

Commands in the generated project: `make docs-install`, `make docs`, `make docs-build`
(strict), or `docker compose --profile docs up docs`. With `ci_tool=GitHub`, the pipeline
builds the docs in strict mode and uploads `docs/site` as an artifact.

## Hooks

- `hooks/pre_gen_project.py`: validates the slug, env prefix, ports, schema name and Python version,
  and rejects `"` / `\` in values injected into Python strings. Nothing is generated on error.
- `hooks/post_gen_project.py`:
  1. removes `.github/` (`ci_tool=None`) and `etl/` + `db/` + `docs/docs/etl.md` (`include_etl=n`);
  2. creates `.env` from `.env.example` with a random `SECRET_KEY`;
  3. if `init_git=y` and git is installed: `git init`, then installs
     `commit-msg` (`[feat|fix|docs|style|refactor|test|chore]: message`) and
     `pre-push` (tags `vX.Y.Z`, the format read by the CI versioning script).

## After generation

    $ cd sales-dashboard-api
    $ python -m venv .venv && source .venv/bin/activate
    $ pip install -r requirements.txt
    $ pytest                                   # smoke tests, no database needed
    # fill the PostgreSQL URIs in .env, then:
    $ docker compose up -d                     # Redis
    $ python etl/run_etl.py --dry-run          # if include_etl=y
    $ make dev                                 # http://localhost:8000/docs
    $ python generate_test_token.py            # JWT for Swagger "Authorize"
    $ make docs-install && make docs           # project documentation, http://localhost:9000

Then push to a new repository:

    $ git add .
    $ git commit -m "[feat]: first commit"
    $ git remote add origin https://github.com/<owner>/sales-dashboard-api.git
    $ git push -u origin develop
