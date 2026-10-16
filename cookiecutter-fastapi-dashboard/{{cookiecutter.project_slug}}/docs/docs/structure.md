# Structure du projet

```text
{{ cookiecutter.project_slug }}/
├── app/
│   ├── main.py                  # bootstrap : middlewares, CORS, rate limit, erreurs, probes
│   ├── api/
│   │   ├── deps.py              # require_permission (claim JWT "perms")
│   │   ├── params.py            # paramètres de requête partagés (pagination)
│   │   └── v1/
│   │       ├── router.py        # déclaration centralisée de toutes les routes
│   │       └── endpoints/       # handlers, sans logique ni SQL
│   ├── core/                    # config, constantes, sécurité, cache, rate limit, logs, erreurs, santé
│   ├── db/session.py            # sessions async SOURCE et DEST
│   ├── schemas/                 # filtres (dépendances FastAPI) et modèles de réponse
│   └── services/                # logique métier et SQL (cache Redis via @cached)
{%- if cookiecutter.include_etl == "y" %}
├── db/001_mart.sql              # schéma et transformation du data mart
├── etl/run_etl.py               # ETL SOURCE -> DEST
{%- endif %}
├── docs/
│   ├── mkdocs.yml               # configuration de cette documentation
│   └── docs/                    # pages Markdown
├── tests/                       # tests de fumée (sans PostgreSQL ni Redis)
├── generate_test_token.py       # JWT de test pour Swagger
├── docker-compose.yml           # Redis (+ serveur de docs, profil "docs")
├── Dockerfile                   # image de l'API
├── Makefile                     # raccourcis
├── requirements.txt             # dépendances de l'API
└── requirements-docs.txt        # dépendances de la documentation
```

## Découpage en couches

Une requête traverse les couches dans un seul sens :

```mermaid
flowchart LR
    R["router.py<br/>route + response_model"] --> H["endpoints/<br/>handler"]
    H --> D["deps.py · schemas/filters.py<br/>JWT, permissions, filtres"]
    H --> S["services/<br/>SQL + @cached"]
    S --> F["services/fetch_data.py"]
    F --> DB[("Base DEST")]
```

| Couche | Rôle | Interdit |
|--------|------|----------|
| `api/v1/router.py` | Enregistre chaque route : chemin, handler, tag, `response_model` | Logique |
| `api/v1/endpoints/` | Déclare les dépendances (filtres, permission) et appelle le service | SQL, calcul |
| `services/` | Écrit le SQL, calcule, met en cache | Accès à la requête HTTP |
| `services/fetch_data.py` | Exécute le SQL et renvoie des `dict` | Logique métier |
| `core/` | Briques techniques transverses | Code métier |

## Points d'entrée

- `app/main.py` : objet `app` lancé par uvicorn (`uvicorn app.main:app`).
{%- if cookiecutter.include_etl == "y" %}
- `etl/run_etl.py` : script autonome, lancé par un planificateur (cron, Airflow…).
{%- endif %}
- `generate_test_token.py` : outil de développement.
