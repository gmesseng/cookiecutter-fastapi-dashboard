.PHONY: run dev install lint test up down token docs docs-build docs-install{% if cookiecutter.include_etl == "y" %} etl etl-dry-run{% endif %}

run:
	uvicorn app.main:app --host 0.0.0.0 --port {{ cookiecutter.api_port }}

dev:
	uvicorn app.main:app --reload --port {{ cookiecutter.api_port }}

up:
	docker compose up -d

down:
	docker compose down
{% if cookiecutter.include_etl == "y" %}
etl:
	python etl/run_etl.py

etl-dry-run:
	python etl/run_etl.py --dry-run
{% endif %}
token:
	python generate_test_token.py

install:
	pip install -r requirements.txt

lint:
	ruff check app/ && ruff format --check app/

test:
	pytest

docs-install:
	pip install -r requirements-docs.txt

docs:
	mkdocs serve -f docs/mkdocs.yml --dev-addr 0.0.0.0:{{ cookiecutter.docs_port }}

docs-build:
	mkdocs build --strict -f docs/mkdocs.yml
