# À propos

| | |
|---|---|
| Projet | {{ cookiecutter.project_name }} |
| Version | {{ cookiecutter.version }} |
| Société | {{ cookiecutter.company_name }} |
| Contact | [{{ cookiecutter.email }}](mailto:{{ cookiecutter.email }}) |
{%- if cookiecutter.ci_tool == "GitHub" %}
| Dépôt | [{{ cookiecutter.github_owner }}/{{ cookiecutter.project_slug }}](https://github.com/{{ cookiecutter.github_owner }}/{{ cookiecutter.project_slug }}) |
{%- endif %}

Projet généré depuis le template `cookiecutter-fastapi-dashboard`.

## Stack

- [FastAPI](https://fastapi.tiangolo.com/), [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [SQLAlchemy](https://docs.sqlalchemy.org/) async + asyncpg, PostgreSQL
- [Redis](https://redis.io/)
- [structlog](https://www.structlog.org/), [slowapi](https://slowapi.readthedocs.io/)
- Documentation : [MkDocs](https://www.mkdocs.org/), [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/), [mkdocstrings](https://mkdocstrings.github.io/)

## Licence

© {{ cookiecutter.company_name }} — voir `LICENSE.txt`.
