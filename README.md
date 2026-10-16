# Cookiecutter FastAPI Dashboard

A [Cookiecutter](https://cookiecutter.readthedocs.io/) template that generates a production-ready,
read-only **FastAPI dashboard / KPI API** on top of an analytical PostgreSQL database, with a Redis cache.

It was created so that every developer at Kaeyros Analytics can **start a new project in minutes**
instead of rebuilding the same foundations each time. It is extracted from the
`reading-classroom-dashboard-api` project: the infrastructure is kept as is, and the business code is
replaced by one example KPI that shows the full path (schema → service → handler → route).

## Set up a new project (step by step)

### 1. Prerequisites

| Tool | Needed for |
|------|-----------|
| Python 3.11 (or the version you choose) | Cookiecutter and the API |
| git | Cloning the template, hooks, versioning |
| PostgreSQL 14+ | A SOURCE (OLTP) database and a DEST (analytics) database |
| Docker + Docker Compose | Redis (and, optionally, the documentation server) |

### 2. Install Cookiecutter

```bash
pip install "cookiecutter>=2.6.0"
```

### 3. Generate the project

From a local copy of this template:

```bash
cookiecutter path/to/cookiecutter-fastapi-dashboard
```

or straight from the repository:

```bash
cookiecutter <repository-url>
```

Cookiecutter asks one question per variable and shows the default in parentheses; press **Enter** to accept it.
Example:

```text
project_name (Kaeyros BI analytics Project): Sales Dashboard API
project_slug (sales-dashboard-api):
description (API FastAPI de dashboard et KPI, en lecture seule sur une base analytique):
company_name (Kaeyros Analytics):
author_name (Kaeyros Analytics):
email (contact@kaeyros-analytics.com):
version (1.0.0):
env_prefix (SDA_):
python_version (3.11):
api_port (8000):
redis_host_port (6380):
docs_port (9000):
analytics_schema (analytics):
include_etl (y):
Select ci_tool:
  1 - GitHub
  2 - None
  Choose from 1, 2 (1):
github_owner (kaeyros-analytics-org):
init_git (y):
debug (y):
```

Generate without any prompt (handy in scripts):

```bash
cookiecutter path/to/cookiecutter-fastapi-dashboard --no-input \
    project_name="Sales Dashboard API" env_prefix=SALES_ include_etl=n ci_tool=None
```

> The answers are validated **before** anything is created (slug, env prefix, ports, schema name,
> Python version). If one is invalid, the generation stops with an explicit message and no folder is written.


## License

See `LICENSE.txt` in the generated project.
