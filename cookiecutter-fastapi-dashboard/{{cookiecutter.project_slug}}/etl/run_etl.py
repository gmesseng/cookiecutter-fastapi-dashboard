"""
run_etl.py — ETL en rechargement complet, SOURCE (OLTP) -> DEST ({{ cookiecutter.analytics_schema }}).

Alimente les tables du data mart définies dans db/001_mart.sql (MART_TABLES ci-dessous).
Pour l'adapter : déclarer les tables source dans TABLES, les tables produites dans
MART_TABLES, les rapprochements dans CHECKS, et écrire la transformation dans le SQL.

Déroulé — tout le travail côté DEST tient dans UNE transaction (tout ou rien) :
  1. Extract   : photo cohérente de la source (REPEATABLE READ, READ ONLY). Chaque table est
                 streamée par COPY TO STDOUT -> pipe -> COPY FROM STDIN : aucune ligne ne
                 transite par des objets Python, la mémoire reste constante.
  2. Load      : tables temporaires DEST (ON COMMIT DROP), indexées puis analysées. Aucune
                 copie de l'OLTP ne persiste après le run.
  3. Transform : exécution de db/001_mart.sql (DDL idempotent + TRUNCATE/INSERT) avec
                 search_path = pg_temp : le SQL lit les tables temporaires sous leurs noms source.
  4. Contrôles : rapprochements bloquants (volumes, montants). Un écart -> ROLLBACK : la
                 version précédente des tables reste servie à l'API.
  5. Journal   : {{ cookiecutter.analytics_schema }}.etl_mart_runs, écrit sur une connexion séparée en autocommit,
                 pour qu'un échec reste visible malgré le rollback.

Usage :
    python etl/run_etl.py               # run complet
    python etl/run_etl.py --dry-run     # tout exécuter puis ROLLBACK (rien n'est publié)
    python etl/run_etl.py --sql chemin/vers/autre.sql

Codes de sortie : 0 = succès, 1 = échec (rollback effectué), 2 = un autre run est déjà en cours.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

import psycopg2
import psycopg2.extensions
import structlog
from dotenv import load_dotenv
from psycopg2 import sql
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

load_dotenv()

# Logs JSON en UTF-8 même sur une console Windows (cp1252).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(ensure_ascii=False),
    ],
    wrapper_class=structlog.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)
log = structlog.get_logger().bind(logger="etl_mart")

SOURCE_POSTGRES_URI = os.getenv("{{ cookiecutter.env_prefix }}SOURCE_POSTGRES_URI")
DEST_POSTGRES_URI = os.getenv("{{ cookiecutter.env_prefix }}DEST_POSTGRES_URI")
SOURCE_SCHEMA = os.getenv("{{ cookiecutter.env_prefix }}SOURCE_SCHEMA", "public")
TARGET_SCHEMA = os.getenv("{{ cookiecutter.env_prefix }}DEST_SCHEMA", "{{ cookiecutter.analytics_schema }}")            # schéma des tables créées par db/001_mart.sql
RUNS_TABLE = f"{TARGET_SCHEMA}.etl_mart_runs"
DEFAULT_SQL_PATH = Path(__file__).resolve().parents[1] / "db" / "001_mart.sql"

# Tables produites par le SQL du mart (comptées après la transformation, journalisées).
MART_TABLES: tuple[str, ...] = ("fact_example",)

COPY_BUFFER = 1 << 20                  # 1 Mo par lecture/écriture du pipe
ADVISORY_LOCK_KEY = 4_204_190_001      # empêche deux runs simultanés sur la même DEST


# ---------------------------------------------------------------------------
# Tables extraites : uniquement ce que lit db/001_mart.sql.
# `columns` = liste blanche (None = toutes), `exclude` = colonnes lourdes ou
# sensibles jamais copiées, `where` = filtre côté source, `indexes` = clés de
# jointure indexées sur la table temporaire avant la transformation.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TableSpec:
    name: str
    columns: tuple[str, ...] | None = None
    exclude: tuple[str, ...] = ()
    where: str | None = None
    indexes: tuple[tuple[str, ...], ...] = field(default_factory=tuple)


TABLES: tuple[TableSpec, ...] = (
    # Exemple — à remplacer par les tables source réellement lues par db/001_mart.sql.
    TableSpec("items", columns=("id", "category", "amount", "created_at"), indexes=(("id",),)),
)


# ---------------------------------------------------------------------------
# Connexions
# ---------------------------------------------------------------------------

def _plain_uri(uri: str) -> str:
    """Accepte aussi une URI SQLAlchemy (postgresql+asyncpg://) comme celles de l'API."""
    return re.sub(r"^postgresql\+\w+://", "postgresql://", uri)


@retry(
    retry=retry_if_exception_type(psycopg2.OperationalError),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(5),
    reraise=True,
)
def connect(uri: str, application_name: str):
    try:
        conn = psycopg2.connect(_plain_uri(uri), application_name=application_name)
    except UnicodeDecodeError as exc:   # message serveur en cp1252 (Windows francophone)
        message = exc.object.decode("cp1252", errors="replace").strip()
        sys.exit(f"[FATAL] Connexion PostgreSQL impossible : {message}")
    with conn.cursor() as cur:
        # Format texte de COPY identique des deux côtés, quel que soit le réglage des serveurs.
        cur.execute("SET client_encoding TO 'UTF8'; SET DateStyle TO 'ISO, YMD'; SET IntervalStyle TO 'postgres'")
    conn.commit()
    return conn


# ---------------------------------------------------------------------------
# Journal des runs (connexion autocommit séparée)
# ---------------------------------------------------------------------------

class RunJournal:
    def __init__(self, uri: str):
        self.conn = connect(uri, "etl_mart_journal")
        self.conn.autocommit = True
        self.run_id: int | None = None
        with self.conn.cursor() as cur:
            cur.execute(f"""
                CREATE SCHEMA IF NOT EXISTS {TARGET_SCHEMA};
                CREATE TABLE IF NOT EXISTS {RUNS_TABLE} (
                    run_id                  BIGSERIAL PRIMARY KEY,
                    started_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
                    finished_at             TIMESTAMPTZ,
                    status                  TEXT NOT NULL,          -- running | ok | dry_run | error | skipped
                    duration_ms             INTEGER,
                    rows_extracted          JSONB,
                    rows_loaded             JSONB,
                    checks                  JSONB,
                    error                   TEXT
                )
            """)

    def start(self) -> None:
        with self.conn.cursor() as cur:
            cur.execute(f"INSERT INTO {RUNS_TABLE} (status) VALUES ('running') RETURNING run_id")
            self.run_id = cur.fetchone()[0]

    def finish(self, status: str, duration_ms: int, extracted: dict, counts: dict, checks: list, error: str | None) -> None:
        if self.run_id is None:
            return
        with self.conn.cursor() as cur:
            cur.execute(
                f"""UPDATE {RUNS_TABLE}
                    SET finished_at = now(), status = %s, duration_ms = %s, rows_extracted = %s,
                        rows_loaded = %s, checks = %s, error = %s
                    WHERE run_id = %s""",
                (status, duration_ms, json.dumps(extracted), json.dumps(counts),
                 json.dumps(checks, default=str), error, self.run_id),
            )

    def close(self) -> None:
        self.conn.close()


# ---------------------------------------------------------------------------
# Extract + Load : COPY streamé source -> table temporaire DEST
# ---------------------------------------------------------------------------

def source_columns(src_conn, spec: TableSpec) -> list[tuple[str, str]]:
    """(nom, type DEST) des colonnes à copier ; les ENUM Prisma deviennent du TEXT."""
    with src_conn.cursor() as cur:
        cur.execute(
            """
            SELECT a.attname,
                   CASE WHEN t.typtype = 'e' THEN 'text' ELSE format_type(a.atttypid, a.atttypmod) END
            FROM pg_attribute a
            JOIN pg_class c     ON c.oid = a.attrelid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            JOIN pg_type t      ON t.oid = a.atttypid
            WHERE n.nspname = %s AND c.relname = %s AND a.attnum > 0 AND NOT a.attisdropped
            ORDER BY a.attnum
            """,
            (SOURCE_SCHEMA, spec.name),
        )
        cols = cur.fetchall()
    if not cols:
        raise RuntimeError(f"Table source introuvable : {SOURCE_SCHEMA}.{spec.name}")
    available = {name for name, _ in cols}
    if spec.columns:
        missing = set(spec.columns) - available
        if missing:
            raise RuntimeError(f"Colonnes absentes de {SOURCE_SCHEMA}.{spec.name} : {sorted(missing)}")
        cols = [c for c in cols if c[0] in spec.columns]
    return [c for c in cols if c[0] not in spec.exclude]


def stream_copy(src_conn, dst_conn, copy_out: str, copy_in: str) -> int:
    """
    COPY source TO STDOUT -> pipe OS -> COPY dest FROM STDIN, en parallèle (un thread
    producteur). Mémoire constante quel que soit le volume.
    """
    read_fd, write_fd = os.pipe()
    reader = os.fdopen(read_fd, "rb", buffering=COPY_BUFFER)
    writer = os.fdopen(write_fd, "wb", buffering=COPY_BUFFER)
    producer_error: list[BaseException] = []

    def produce() -> None:
        try:
            with src_conn.cursor() as cur:
                cur.copy_expert(copy_out, writer, size=COPY_BUFFER)
        except BaseException as exc:      # remonté au thread principal après join()
            producer_error.append(exc)
        finally:
            try:
                writer.close()            # EOF pour le consommateur
            except OSError:
                pass

    producer = threading.Thread(target=produce, name="copy-producer", daemon=True)
    producer.start()
    try:
        with dst_conn.cursor() as cur:
            cur.copy_expert(copy_in, reader, size=COPY_BUFFER)
            rows = cur.rowcount
    finally:
        reader.close()                    # débloque le producteur si le consommateur a échoué
        producer.join()
    if producer_error:
        # Un producteur interrompu ferme le pipe : le COPY destination a pu "réussir" sur des
        # données partielles. On lève quand même -> la transaction DEST est annulée.
        raise producer_error[0]
    return rows


def extract_load(src_conn, dst_conn) -> dict[str, int]:
    extracted: dict[str, int] = {}
    for spec in TABLES:
        t0 = time.perf_counter()
        cols = source_columns(src_conn, spec)
        ident = sql.Identifier(spec.name)
        col_idents = [sql.Identifier(name) for name, _ in cols]

        with dst_conn.cursor() as cur:
            cur.execute(sql.SQL("CREATE TEMP TABLE {} ({}) ON COMMIT DROP").format(
                ident,
                sql.SQL(", ").join(sql.SQL("{} {}").format(sql.Identifier(n), sql.SQL(t)) for n, t in cols),
            ))

        select = sql.SQL("SELECT {} FROM {}.{}").format(
            sql.SQL(", ").join(col_idents), sql.Identifier(SOURCE_SCHEMA), ident,
        )
        if spec.where:
            select = sql.SQL("{} WHERE {}").format(select, sql.SQL(spec.where))
        copy_out = sql.SQL("COPY ({}) TO STDOUT").format(select).as_string(src_conn)
        copy_in = sql.SQL("COPY pg_temp.{} ({}) FROM STDIN").format(ident, sql.SQL(", ").join(col_idents)).as_string(dst_conn)

        rows = stream_copy(src_conn, dst_conn, copy_out, copy_in)

        with dst_conn.cursor() as cur:
            for idx_cols in spec.indexes:
                cur.execute(sql.SQL("CREATE INDEX ON pg_temp.{} ({})").format(
                    ident, sql.SQL(", ").join(sql.Identifier(c) for c in idx_cols)))
            cur.execute(sql.SQL("ANALYZE pg_temp.{}").format(ident))   # autovacuum ignore les tables temporaires

        extracted[spec.name] = rows
        log.info("table_copiee", table=spec.name, lignes=rows, colonnes=len(cols),
                 duree_ms=round((time.perf_counter() - t0) * 1000))
    return extracted


# ---------------------------------------------------------------------------
# Transform : exécution du fichier SQL du mart
# ---------------------------------------------------------------------------

def load_transform_sql(path: Path) -> str:
    """Le fichier gère sa propre transaction (BEGIN/COMMIT) pour un usage manuel ; ici c'est
    le script qui la pilote, donc ces deux lignes sont retirées."""
    text = path.read_text(encoding="utf-8")
    return re.sub(r"^\s*(BEGIN|COMMIT)\s*;\s*$", "", text, flags=re.MULTILINE | re.IGNORECASE)


# ---------------------------------------------------------------------------
# Contrôles bloquants (exécutés dans la transaction, avant COMMIT)
# ---------------------------------------------------------------------------

CHECKS: tuple[tuple[str, str], ...] = (
    # (nom, requête renvoyant (valeur_mart, valeur_référence)) — un écart fait échouer le run.
    (
        "lignes_vs_source",
        f"""
        SELECT (SELECT COUNT(*) FROM {TARGET_SCHEMA}.fact_example),
               (SELECT COUNT(*) FROM pg_temp.items)
        """,
    ),
    (
        "montant_vs_source",
        f"""
        SELECT (SELECT COALESCE(SUM(amount), 0) FROM {TARGET_SCHEMA}.fact_example),
               (SELECT COALESCE(SUM(amount), 0) FROM pg_temp.items)
        """,
    ),
)


def run_checks(dst_conn) -> list[dict]:
    results = []
    with dst_conn.cursor() as cur:
        for name, query in CHECKS:
            cur.execute(query)
            mart_value, source_value = cur.fetchone()
            ok = mart_value == source_value
            results.append({"controle": name, "mart": mart_value, "reference": source_value, "ok": ok})
            log.info("controle", controle=name, mart=str(mart_value), reference=str(source_value), ok=ok)
    return results


class CheckFailed(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run(sql_path: Path, dry_run: bool, lock_timeout: str) -> int:
    if not SOURCE_POSTGRES_URI or not DEST_POSTGRES_URI:
        sys.exit("[FATAL] {{ cookiecutter.env_prefix }}SOURCE_POSTGRES_URI / {{ cookiecutter.env_prefix }}DEST_POSTGRES_URI manquant(s) — copier .env.example vers .env et le remplir.")
    transform_sql = load_transform_sql(sql_path)   # échoue tôt si le fichier est absent

    started = time.perf_counter()
    journal = RunJournal(DEST_POSTGRES_URI)
    src_conn = connect(SOURCE_POSTGRES_URI, "etl_mart_extract")
    dst_conn = connect(DEST_POSTGRES_URI, "etl_mart_load")
    extracted: dict[str, int] = {}
    counts: dict[str, int] = {}
    checks: list[dict] = []

    try:
        with dst_conn.cursor() as cur:
            cur.execute("SELECT pg_try_advisory_xact_lock(%s)", (ADVISORY_LOCK_KEY,))
            if not cur.fetchone()[0]:
                log.warning("run_deja_en_cours")
                dst_conn.rollback()
                return 2

        journal.start()
        log.info("etl_debut", run_id=journal.run_id, dry_run=dry_run, sql=str(sql_path), schema_source=SOURCE_SCHEMA)

        # Photo cohérente de toute la source : toutes les tables voient le même instant.
        src_conn.set_session(isolation_level=psycopg2.extensions.ISOLATION_LEVEL_REPEATABLE_READ, readonly=True)

        with dst_conn.cursor() as cur:
            # TRUNCATE prend un verrou exclusif : on échoue vite plutôt que d'attendre une lecture longue.
            cur.execute(sql.SQL("SET LOCAL lock_timeout = {}").format(sql.Literal(lock_timeout)))
            cur.execute("SET LOCAL search_path TO pg_temp")

        extracted = extract_load(src_conn, dst_conn)
        src_conn.rollback()                  # libère la photo source au plus tôt

        t0 = time.perf_counter()
        with dst_conn.cursor() as cur:
            cur.execute(transform_sql)
            for table in MART_TABLES:
                cur.execute(sql.SQL("SELECT COUNT(*) FROM {}.{}").format(
                    sql.Identifier(TARGET_SCHEMA), sql.Identifier(table)))
                counts[table] = cur.fetchone()[0]
        log.info("transformation_ok", duree_ms=round((time.perf_counter() - t0) * 1000), **counts)

        checks = run_checks(dst_conn)
        failed = [c["controle"] for c in checks if not c["ok"]]
        if failed:
            raise CheckFailed(f"Contrôles en échec : {', '.join(failed)}")

        if dry_run:
            dst_conn.rollback()
            status = "dry_run"
        else:
            dst_conn.commit()
            status = "ok"
        duration_ms = round((time.perf_counter() - started) * 1000)
        journal.finish(status, duration_ms, extracted, counts, checks, None)
        log.info("etl_fin", run_id=journal.run_id, statut=status, duree_ms=duration_ms, **counts)
        return 0

    except Exception as exc:
        dst_conn.rollback()                  # l'ancienne version des tables reste en place
        duration_ms = round((time.perf_counter() - started) * 1000)
        journal.finish("error", duration_ms, extracted, counts, checks, f"{type(exc).__name__}: {exc}")
        log.error("etl_echec", run_id=journal.run_id, erreur=f"{type(exc).__name__}: {exc}", duree_ms=duration_ms)
        return 1
    finally:
        for conn in (src_conn, dst_conn):
            try:
                conn.close()
            except Exception:
                pass
        journal.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Recharge les tables du data mart ({{ cookiecutter.analytics_schema }}).")
    parser.add_argument("--dry-run", action="store_true", help="Exécute tout puis annule (rien n'est publié).")
    parser.add_argument("--sql", type=Path, default=DEFAULT_SQL_PATH, help="Fichier SQL du mart (défaut : db/001_mart.sql).")
    parser.add_argument("--lock-timeout", default="15s", help="Attente max du verrou sur les tables cibles (défaut : 15s).")
    args = parser.parse_args()
    sys.exit(run(args.sql, args.dry_run, args.lock_timeout))
