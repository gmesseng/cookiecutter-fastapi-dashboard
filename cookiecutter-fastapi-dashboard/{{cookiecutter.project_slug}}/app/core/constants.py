"""
Constantes applicatives — toutes les valeurs qui seraient sinon écrites en dur
dans les endpoints et services de l'API.

Recensement (une section par famille) :
   1. Application (valeurs par défaut de app/core/config.py)
   2. Pagination et limites de requête
   3. Permissions et tags OpenAPI
   4. Messages d'erreur

Les noms de tables/colonnes SQL restent dans les services : ce sont des
identifiants de schéma, pas des valeurs métier. Les noms de tables analytics
configurables restent dans app/core/config.py (variables d'environnement {{ cookiecutter.env_prefix }}*).
"""

# ═══════════════════════════════════════════════════════════════════════════
# 1. APPLICATION — valeurs par défaut, surchargeables via .env
# ═══════════════════════════════════════════════════════════════════════════

PROJECT_NAME = "{{ cookiecutter.project_name }}"
API_V1_STR = "/api/v1"
COMPANY_NAME = "{{ cookiecutter.company_name }}"

# ── JWT ──────────────────────────────────────────────────────────────
ACCESS_TOKEN_EXPIRATION_TIME = 30

# ── PostgreSQL / Data Mart ──────────────────────────────────────────
ANALYTICS_SCHEMA = "{{ cookiecutter.analytics_schema }}"
TABLE_FACT_EXAMPLE = "fact_example"

# ── Redis ────────────────────────────────────────────────────────────
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_TTL = 300
REDIS_KEY_PREFIX = "{{ cookiecutter.__project_snake }}:"

# ── CORS ─────────────────────────────────────────────────────────────
BACKEND_CORS_ORIGINS = (
    '["http://localhost:3000","http://localhost:{{ cookiecutter.api_port }}"]'
)


# ═══════════════════════════════════════════════════════════════════════════
# 2. PAGINATION ET LIMITES
# ═══════════════════════════════════════════════════════════════════════════

DEFAULT_PAGE = 1
MIN_PAGE = 1
DEFAULT_PAGE_SIZE = 50
MIN_PAGE_SIZE = 1
MAX_PAGE_SIZE = 200


# ═══════════════════════════════════════════════════════════════════════════
# 3. PERMISSIONS ET TAGS OPENAPI
# ═══════════════════════════════════════════════════════════════════════════

class Perm:
    """Permissions portées par la claim JWT "perms" (cf. app/api/deps.require_permission)."""
    WILDCARD = "*"
    DASHBOARD_READ = "dashboard:read"


MISSING_PERMISSION_MESSAGE = "Permission manquante : {permission}."


class ApiTag:
    """Tags OpenAPI (sections de la documentation Swagger)."""
    DASHBOARDS = "Dashboards"


# ═══════════════════════════════════════════════════════════════════════════
# 4. MESSAGES D'ERREUR
# ═══════════════════════════════════════════════════════════════════════════

class ErrorMessage:
    INVALID_DATE_RANGE = "date_start ({date_start}) doit être inférieure ou égale à date_end ({date_end})."
