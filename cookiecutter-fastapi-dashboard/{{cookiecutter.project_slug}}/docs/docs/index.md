# {{ cookiecutter.project_name }}

{{ cookiecutter.description }}.

API backend **FastAPI en lecture seule** qui alimente des écrans **dashboard / KPI**.
L'API ne lit jamais la base transactionnelle (OLTP) pour calculer ses cadrans :
{%- if cookiecutter.include_etl == "y" %} un ETL recopie les données source dans une base analytique et
les transforme en tables dénormalisées ;{% endif %} l'API sert les tables du schéma
`{{ cookiecutter.analytics_schema }}` de la base analytique, avec un cache Redis devant chaque cadran.

## Architecture

```mermaid
flowchart LR
    SRC[("Base SOURCE<br/>OLTP — schéma public")]
    DEST[("Base DEST<br/>analytique — schéma {{ cookiecutter.analytics_schema }}")]
    API["API FastAPI"]
    REDIS[("Redis<br/>cache des cadrans")]
    FRONT["Front dashboard"]
{%- if cookiecutter.include_etl == "y" %}
    SRC -- "etl/run_etl.py<br/>COPY + db/001_mart.sql" --> DEST
{%- endif %}
    DEST --> API
    API <--> REDIS
    FRONT -- "JWT Bearer" --> API
```

!!! info "Pourquoi deux bases ?"
    Les requêtes d'agrégation des dashboards sont lourdes. Les exécuter sur la base
    transactionnelle ralentirait l'application métier. La base analytique contient des
    tables déjà préparées pour la lecture ; l'API n'a plus qu'à filtrer et agréger.

## Fonctionnalités

- **JWT HS256** obligatoire sur toutes les routes métier, permissions lues dans la claim `perms`.
- **Cache Redis** transparent via le décorateur `@cached(prefix=...)`.
- **Rate limiting** : 60 requêtes / minute / IP (slowapi).
- **Observabilité** : `X-Request-ID` propagé, access log JSON (structlog).
- **Sécurité HTTP** : HSTS, `nosniff`, `X-Frame-Options: DENY`, CORS limité à `GET`.
- **Erreurs JSON normalisées** : `{"code", "message", "request_id"}`.
- **Probes** `/healthz`, `/readyz` et `/health` (Redis + bases SOURCE et DEST).
{%- if cookiecutter.include_etl == "y" %}
- **ETL** SOURCE → DEST : COPY streamé, transaction unique, contrôles bloquants, journal des runs.
{%- endif %}

## Par où commencer

| Je veux… | Page |
|----------|------|
| Installer et lancer le projet | [Installation et lancement](setup.md) |
| Connaître les variables d'environnement | [Configuration](configuration.md) |
| Appeler l'API depuis un front | [Utiliser l'API](api.md) |
| Ajouter un nouvel indicateur | [Ajouter un cadran KPI](kpi.md) |
{%- if cookiecutter.include_etl == "y" %}
| Alimenter ou modifier le data mart | [ETL et data mart](etl.md) |
{%- endif %}
| Comprendre une erreur | [Dépannage](troubleshooting.md) |
