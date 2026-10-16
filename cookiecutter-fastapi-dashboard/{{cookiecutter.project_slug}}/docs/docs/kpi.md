# Ajouter un cadran KPI

Le cadran d'exemple `GET /api/v1/dashboards/kpis/exemple` montre le chemin complet.
Pour un nouveau cadran, suivre les mêmes étapes, dans cet ordre.

## 1. Modèle de réponse

`app/schemas/responses.py` :

```python
class VentesParCategorie(BaseModel):
    categorie: str = Field(..., description="Catégorie de produit")
    montant: float = Field(..., description="Somme de `amount` sur la période")


class VentesParCategorieResponse(BaseModel):
    data: list[VentesParCategorie]
```

## 2. Service

`app/services/dashboard_service.py` : le SQL, les filtres via `build_where`, et le cache
via `@cached`. Le `prefix` doit être unique pour chaque cadran.

```python
@cached(prefix="ventes_par_categorie")
async def ventes_par_categorie(query: Dict[str, Any]) -> VentesParCategorieResponse:
    where_clauses, params = build_where(query, date_column="f.created_at")
    sql = f"""
        SELECT f.category AS categorie, COALESCE(SUM(f.amount), 0) AS montant
        FROM {settings.T_FACT_EXAMPLE} f
        WHERE {" AND ".join(where_clauses)}
        GROUP BY f.category
        ORDER BY montant DESC
    """
    rows = await fetch_all(sql, params)
    return VentesParCategorieResponse(data=[VentesParCategorie(**r) for r in rows])
```

!!! warning "Paramètres SQL"
    Seuls les noms de tables (issus de `settings`) sont insérés dans la chaîne SQL.
    Les valeurs venant de la requête passent **toujours** par des paramètres liés
    (`:date_start`), jamais par une f-string.

## 3. Handler

`app/api/v1/endpoints/dashboards.py` : pas de décorateur, pas de logique.

```python
async def get_ventes_par_categorie(
    filters: DashboardFilters = Depends(parse_filters),
    _u: dict = Depends(require_permission(Perm.DASHBOARD_READ)),
) -> responses.VentesParCategorieResponse:
    """Montant des ventes par catégorie sur la période."""
    return await dashboard_service.ventes_par_categorie(filters.to_params())
```

## 4. Route

`app/api/v1/router.py` :

```python
router.add_api_route(
    "/dashboards/kpis/ventes-par-categorie",
    dashboards.get_ventes_par_categorie,
    methods=["GET"],
    tags=[ApiTag.DASHBOARDS],
    response_model=responses.VentesParCategorieResponse,
    summary="Cadran KPI — ventes par catégorie",
)
```

## 5. Nouvelle table (si besoin)

1. Constante dans `app/core/constants.py` (ex. `TABLE_FACT_VENTES = "fact_ventes"`).
2. Champ et propriété dans `app/core/config.py` (`TABLE_FACT_VENTES`, `T_FACT_VENTES`).
3. Variable dans `.env.example`.
{%- if cookiecutter.include_etl == "y" %}
4. Alimentation dans `db/001_mart.sql`, puis `TABLES`, `MART_TABLES` et `CHECKS` dans
   `etl/run_etl.py` (voir [ETL et data mart](etl.md)).
{%- endif %}

## 6. Nouvelle permission (si besoin)

Ajouter la valeur à la classe `Perm` de `app/core/constants.py`, la passer à
`require_permission(...)` et la documenter dans [Utiliser l'API](api.md#permissions).

## Checklist

- [ ] Modèle de réponse avec une `description` sur chaque champ
- [ ] Service décoré par `@cached` avec un `prefix` unique
- [ ] Valeurs SQL passées en paramètres liés
- [ ] Handler protégé par `require_permission`
- [ ] Route déclarée dans `router.py` avec `response_model` et `summary`
- [ ] Test ajouté dans `tests/`
- [ ] Route ajoutée au tableau de [Utiliser l'API](api.md#routes)
- [ ] Entrée dans `CHANGELOG.md`, section `[Unreleased]`
