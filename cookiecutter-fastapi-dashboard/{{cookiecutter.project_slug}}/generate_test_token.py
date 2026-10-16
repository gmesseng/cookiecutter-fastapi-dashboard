"""
Génère un token JWT de test pour tester les endpoints sur Swagger.

Usage :
    python generate_test_token.py

Ensuite sur http://localhost:{{ cookiecutter.api_port }}/docs :
    1. Cliquer sur le bouton "Authorize" 🔒
    2. Coller : Bearer <le token affiché>
    3. Cliquer Authorize → tous les endpoints sont débloqués
"""
import sys
from datetime import timedelta

# Réencode stdout en UTF-8 — évite un crash sur console Windows (cp1252) à
# cause des emojis ci-dessous.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Charge automatiquement le .env
from app.core.config import settings
from app.core.security import create_access_token

token = create_access_token(
    subject="test-user",
    expires_delta=timedelta(days=1),
    extra_claims={"email": "test-user@{{ cookiecutter.project_slug }}.test", "roles": ["SUPER_ADMIN"], "perms": ["*"]},
)

print("\n" + "="*60)
print("✅ TOKEN DE TEST GÉNÉRÉ")
print("="*60)
print(f"\nSECRET_KEY utilisée : {settings.SECRET_KEY[:10]}...")
print("\nTon token :\n")
print(f"Bearer {token}")
print("\n" + "="*60)
print("👉 Copie la ligne 'Bearer ...' complète dans Swagger > Authorize")
print("="*60 + "\n")
