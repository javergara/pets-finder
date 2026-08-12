import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_DB_PATH = REPO_ROOT / "data" / "app.db"


def _database_url_desde_entorno() -> str:
    """DATABASE_URL explícita, o la de la integración Vercel×Supabase, o SQLite local.

    La integración del Marketplace inyecta `POSTGRES_URL` (pooler) en vez de
    `DATABASE_URL`, con el scheme legacy `postgres://` (SQLAlchemy 2 solo acepta
    `postgresql://`) y query params que libpq/psycopg2 rechazan (`supa=...`,
    `pgbouncer=true`) — aquí se normaliza: scheme corregido y solo se conserva
    `sslmode`.
    """
    explicita = os.environ.get("DATABASE_URL")
    if explicita:
        return explicita

    cruda = os.environ.get("POSTGRES_URL") or os.environ.get("POSTGRES_PRISMA_URL")
    if not cruda:
        return f"sqlite:///{DEFAULT_DB_PATH}"

    base, _, query = cruda.partition("?")
    if base.startswith("postgres://"):
        base = "postgresql://" + base[len("postgres://") :]
    params = [p for p in query.split("&") if p.startswith("sslmode=")]
    return base + (f"?{'&'.join(params)}" if params else "")


DATABASE_URL = _database_url_desde_entorno()


class Base(DeclarativeBase):
    pass


def make_engine(database_url: str = DATABASE_URL):
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args)


engine = make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
