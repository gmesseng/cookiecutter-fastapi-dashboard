"""Valide les réponses avant toute génération (le projet n'est pas créé en cas d'erreur)."""
import re
import sys

ERRORS = []

project_slug = "{{ cookiecutter.project_slug }}"
env_prefix = "{{ cookiecutter.env_prefix }}"
api_port = "{{ cookiecutter.api_port }}"
redis_host_port = "{{ cookiecutter.redis_host_port }}"
docs_port = "{{ cookiecutter.docs_port }}"
analytics_schema = "{{ cookiecutter.analytics_schema }}"
python_version = "{{ cookiecutter.python_version }}"

if not re.fullmatch(r"[a-z][a-z0-9]*(-[a-z0-9]+)*", project_slug):
    ERRORS.append(f"project_slug '{project_slug}' : minuscules, chiffres et tirets uniquement (ex. mon-dashboard-api).")

if not re.fullmatch(r"[A-Z][A-Z0-9]*_", env_prefix):
    ERRORS.append(f"env_prefix '{env_prefix}' : majuscules ASCII terminées par '_' (ex. RC_).")

for name, value in (("api_port", api_port), ("redis_host_port", redis_host_port), ("docs_port", docs_port)):
    if not value.isdigit() or not 0 < int(value) < 65536:
        ERRORS.append(f"{name} '{value}' : port invalide.")

if not re.fullmatch(r"[a-z_][a-z0-9_]*", analytics_schema):
    ERRORS.append(f"analytics_schema '{analytics_schema}' : identifiant SQL en minuscules attendu.")

if not re.fullmatch(r"3\.\d+", python_version):
    ERRORS.append(f"python_version '{python_version}' : format attendu 3.X (ex. 3.11).")

# Ces valeurs sont injectées dans des chaînes Python/YAML entre guillemets doubles.
for name, value in (
    ("project_name", r"""{{ cookiecutter.project_name|replace('"', '\\"') }} """),
    ("company_name", r"""{{ cookiecutter.company_name|replace('"', '\\"') }} """),
    ("description", r"""{{ cookiecutter.description|replace('"', '\\"') }} """),
):
    if '"' in value or "\\" in value:
        ERRORS.append(f"{name} ne doit contenir ni guillemet double ni antislash.")

if ERRORS:
    print("ERREUR : paramètres invalides :")
    for err in ERRORS:
        print(f"  - {err}")
    sys.exit(1)
