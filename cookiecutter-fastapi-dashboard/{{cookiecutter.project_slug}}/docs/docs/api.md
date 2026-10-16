# Utiliser l'API

## Authentification

Toutes les routes métier (`/api/v1/...`) exigent un JWT signé en **HS256** avec
`{{ cookiecutter.env_prefix }}SECRET_KEY`, envoyé dans l'en-tête :

```http
Authorization: Bearer <token>
```

Claims lues par l'API :

| Claim | Obligatoire | Rôle |
|-------|-------------|------|
| `exp` | oui | Expiration |
| `iat` | oui | Date d'émission |
| `perms` | non | Liste de permissions, ex. `["dashboard:read"]` ; `"*"` les accorde toutes |

L'API **vérifie** les tokens mais n'expose pas de route de login : ils sont émis par le
service d'authentification, qui partage la même clé. `create_access_token`
(`app/core/security.py`) est disponible si l'API doit en émettre elle-même.

## Permissions

| Permission | Routes |
|------------|--------|
| `dashboard:read` | `/api/v1/dashboards/*` |

Une permission manquante renvoie `403` avec le code `auth/missing-scope`.

## Routes

### Métier

| Méthode | Route | Permission | Description |
|---------|-------|------------|-------------|
| GET | `/api/v1/dashboards/kpis/exemple` | `dashboard:read` | Cadran d'exemple : nombre de lignes et montant total |

Filtres communs aux cadrans :

| Paramètre | Format | Défaut |
|-----------|--------|--------|
| `date_start` | `YYYY-MM-DD` | aucune borne basse |
| `date_end` | `YYYY-MM-DD` | aujourd'hui |

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:{{ cookiecutter.api_port }}/api/v1/dashboards/kpis/exemple?date_start=2025-01-01&date_end=2025-12-31"
```

```json
{
  "data": {
    "valeur": 1250,
    "montant_total": 48210.5
  }
}
```

Le schéma complet de chaque route est publié par l'API elle-même : Swagger sur `/docs`,
ReDoc sur `/redoc`, JSON sur `/api/v1/openapi.json`. Seules les routes `GET` y figurent.

### Techniques (sans JWT)

| Route | Rôle | Réponse |
|-------|------|---------|
| `GET /healthz` | Liveness probe | `200 {"status": "alive"}` tant que le process tourne |
| `GET /readyz` | Readiness probe | `{"status": "ready"}` ou `{"status": "not_ready", "issues": [...]}` |
| `GET /health` | État détaillé de Redis, SOURCE et DEST | `200` si tout est up, `305` dès qu'un service est down |

## Format des erreurs

Toutes les erreurs ont la même forme :

```json
{
  "code": "auth/expired-token",
  "message": "Token expiré.",
  "request_id": "5b0f6c1e-…"
}
```

| Code | HTTP | Cause |
|------|------|-------|
| `auth/invalid-token` | 401 | Token mal formé, sans `exp`/`iat`, ou signé avec une autre clé |
| `auth/expired-token` | 401 | Token expiré |
| `auth/missing-scope` | 403 | Permission absente de la claim `perms` |
| `validation/error` | 422 | Paramètre invalide (ex. date mal formée) |
| `http/error` | 400, 403, 404… | Erreur HTTP générique (ex. `date_start` > `date_end`, en-tête `Authorization` absent) |
| `internal/error` | 500 | Erreur inattendue ; le détail est dans les logs, retrouvable par `request_id` |

## En-têtes utiles

| En-tête | Sens | Rôle |
|---------|------|------|
| `X-Request-ID` | requête et réponse | Identifiant de corrélation ; généré s'il est absent |
| `X-RateLimit-Limit`, `X-RateLimit-Remaining` | réponse | État du rate limiting (60 req/min/IP) |

## Cache

Chaque cadran est mis en cache dans Redis pendant `{{ cookiecutter.env_prefix }}REDIS_TTL` secondes
(300 par défaut). La clé contient tous les paramètres : deux périodes différentes ne
partagent pas d'entrée. Après un rechargement des données, les nouvelles valeurs
apparaissent au plus tard à l'expiration du cache.
