"""
Pools de connexions PostgreSQL async via SQLAlchemy + asyncpg.

Deux bases distinctes (cf. app/core/config.py) :
  get_session()        -> base DEST/analytique — la grande majorité des lectures API.
  get_source_session()  -> base SOURCE/OLTP — comptes/rôles, événements bruts,
                           factures, QR codes, audit_logs, bulk_messages : tout
                           ce que l'ETL n'a pas dupliqué dans "analytics".
"""
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_async_engine(
    settings.DEST_POSTGRES_ASYNC_URI,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=False,
)

source_engine = create_async_engine(
    settings.SOURCE_POSTGRES_ASYNC_URI,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=False,
)

_AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

_SourceAsyncSessionLocal = sessionmaker(
    source_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@asynccontextmanager
async def get_session():
    """
    Usage :
        async with get_session() as session:
            result = await session.execute(text("SELECT 1"))
    """
    async with _AsyncSessionLocal() as session:
        yield session


@asynccontextmanager
async def get_source_session():
    async with _SourceAsyncSessionLocal() as session:
        yield session


async def close_engine() -> None:
    await engine.dispose()
    await source_engine.dispose()