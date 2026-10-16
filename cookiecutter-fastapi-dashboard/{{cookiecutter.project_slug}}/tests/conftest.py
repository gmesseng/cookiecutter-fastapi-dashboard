"""
Configuration minimale pour importer l'application sans .env ni services externes :
les engines SQLAlchemy et le client Redis ne se connectent qu'à la première requête.
"""
import os

os.environ.setdefault("{{ cookiecutter.env_prefix }}SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("{{ cookiecutter.env_prefix }}SOURCE_POSTGRES_URI", "postgresql://test:test@localhost:5432/test_source")
os.environ.setdefault("{{ cookiecutter.env_prefix }}DEST_POSTGRES_URI", "postgresql://test:test@localhost:5432/test_dest")
