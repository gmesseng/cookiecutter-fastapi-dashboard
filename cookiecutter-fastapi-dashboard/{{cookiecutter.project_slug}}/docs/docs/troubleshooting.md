# Dépannage

## L'API ne démarre pas

??? failure "`ValidationError` … `SECRET_KEY contient un placeholder insecure`"
    `{{ cookiecutter.env_prefix }}SECRET_KEY` vaut une valeur d'exemple. En générer une :

    ```bash
    python -c "import secrets; print(secrets.token_urlsafe(48))"
    ```

??? failure "`ValidationError` … `Field required`"
    Une variable obligatoire manque (`SECRET_KEY`, `SOURCE_POSTGRES_URI`, `DEST_POSTGRES_URI`).
    Vérifier que le `.env` est dans le dossier d'où l'API est lancée et que les noms portent
    bien le préfixe `{{ cookiecutter.env_prefix }}` (sensible à la casse).

??? failure "`ConnectionError` vers Redis au démarrage"
    L'API se connecte à Redis dès le démarrage. Lancer `docker compose up -d`, puis vérifier
    que `{{ cookiecutter.env_prefix }}REDIS_PORT` correspond au port publié
    (`{{ cookiecutter.env_prefix }}REDIS_HOST_PORT`, `{{ cookiecutter.redis_host_port }}` par défaut).

## Les appels échouent

??? failure "`401 auth/invalid-token`"
    Le token n'a pas été signé avec la même `{{ cookiecutter.env_prefix }}SECRET_KEY`, ou il lui manque
    `exp` / `iat`. Dans Swagger, coller la ligne complète `Bearer …` affichée par
    `python generate_test_token.py`.

??? failure "`403 auth/missing-scope`"
    La claim `perms` du token ne contient ni la permission de la route ni `"*"`.

??? failure "`400` … `date_start … doit être inférieure ou égale à date_end`"
    Inverser les bornes de la période.

??? failure "`500 internal/error`"
    Chercher le `request_id` de la réponse dans les logs JSON de l'API : l'exception complète
    y figure. Cause fréquente : table absente du schéma `{{ cookiecutter.analytics_schema }}`
    {%- if cookiecutter.include_etl == "y" %} (ETL jamais lancé){% endif %}.

??? failure "`429 Too Many Requests`"
    Limite de 60 requêtes par minute et par IP atteinte (`app/core/rate_limit.py`).

## Les données ne bougent pas

??? question "Les chiffres ne changent pas après un rechargement"
    Le cadran est servi depuis Redis jusqu'à expiration (`{{ cookiecutter.env_prefix }}REDIS_TTL`,
    300 s par défaut). Pour forcer le recalcul :

    ```bash
    redis-cli -p {{ cookiecutter.redis_host_port }} --scan --pattern '{{ cookiecutter.__project_snake }}:*' | xargs redis-cli -p {{ cookiecutter.redis_host_port }} del
    ```
{% if cookiecutter.include_etl == "y" %}
??? question "L'ETL termine en erreur"
    Consulter la dernière ligne de `{{ cookiecutter.analytics_schema }}.etl_mart_runs` (colonnes `error`
    et `checks`). Le rollback garantit que l'API sert toujours la version précédente.
{% endif %}
## `/health` renvoie 305

Au moins un service est down ; la réponse indique lequel dans `error` :

```json
{
  "status": 305,
  "services": {
    "app": {"status": "up"},
    "cache": {"type": "redis", "status": "up"},
    "source_db": {"type": "postgresql", "status": "down", "error": "…"},
    "destination_db": {"type": "postgresql", "status": "up"}
  },
  "error": {"source_db": "…"}
}
```

## La documentation ne se construit pas

`make docs-build` utilise le mode strict : un lien cassé ou une page absente de la `nav`
de `docs/mkdocs.yml` fait échouer la construction. Le message indique le fichier en cause.
