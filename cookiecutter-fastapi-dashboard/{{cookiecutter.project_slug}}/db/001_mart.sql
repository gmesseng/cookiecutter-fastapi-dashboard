-- ============================================================================
-- {{ cookiecutter.project_name }} — Data Mart
--
--   {{ cookiecutter.analytics_schema }}.fact_example -> table d'exemple lue par l'API (app/services/dashboard_service.py)
--
-- Chargement : rechargement complet (TRUNCATE + INSERT dans une transaction), piloté
-- par etl/run_etl.py. Les tables source sont lues via search_path = pg_temp : ce sont
-- les copies temporaires déclarées dans TABLES (etl/run_etl.py), sous leur nom source.
--
-- Pour un usage manuel (psql), les lignes BEGIN/COMMIT encadrent le script ; l'ETL
-- les retire et gère lui-même la transaction.
-- ============================================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS {{ cookiecutter.analytics_schema }};

-- ============================================================================
-- 1. SCHÉMA
-- ============================================================================

CREATE TABLE IF NOT EXISTS {{ cookiecutter.analytics_schema }}.fact_example (
    id          TEXT PRIMARY KEY,
    category    TEXT,
    amount      NUMERIC(14, 2) NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ    NOT NULL
);

CREATE INDEX IF NOT EXISTS fact_example_created_at_idx
    ON {{ cookiecutter.analytics_schema }}.fact_example (created_at);

-- ============================================================================
-- 2. CHARGEMENT
-- ============================================================================

TRUNCATE {{ cookiecutter.analytics_schema }}.fact_example;

INSERT INTO {{ cookiecutter.analytics_schema }}.fact_example (id, category, amount, created_at)
SELECT i.id::text, i.category, COALESCE(i.amount, 0), i.created_at
FROM items i;

COMMIT;
