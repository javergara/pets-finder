import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_DB_PATH = REPO_ROOT / "data" / "app.db"


def _con_driver_psycopg(url: str) -> str:
    """Fuerza el dialecto psycopg v3 en URLs de Postgres.

    El driver es `psycopg` (v3): psycopg2 no tiene wheels binarios para los
    runtimes nuevos de Python (el build de Vercel intentaba compilarlo desde
    fuente y fallaba por falta de pg_config). SQLAlchemy con `postgresql://`
    a secas asume psycopg2, así que se explicita `postgresql+psycopg://`.
    """
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


def _database_url_desde_entorno() -> str:
    """DATABASE_URL explícita, o la de la integración Vercel×Supabase, o SQLite local.

    La integración del Marketplace inyecta `POSTGRES_URL` (pooler) en vez de
    `DATABASE_URL`, con el scheme legacy `postgres://` y query params que libpq
    rechaza (`supa=...`, `pgbouncer=true`) — aquí se normaliza: dialecto
    psycopg v3 explícito y solo se conserva `sslmode`.
    """
    explicita = os.environ.get("DATABASE_URL")
    if explicita:
        return _con_driver_psycopg(explicita)

    cruda = os.environ.get("POSTGRES_URL") or os.environ.get("POSTGRES_PRISMA_URL")
    if not cruda:
        return f"sqlite:///{DEFAULT_DB_PATH}"

    base, _, query = cruda.partition("?")
    params = [p for p in query.split("&") if p.startswith("sslmode=")]
    return _con_driver_psycopg(base) + (f"?{'&'.join(params)}" if params else "")


DATABASE_URL = _database_url_desde_entorno()


class Base(DeclarativeBase):
    pass


def make_engine(database_url: str = DATABASE_URL):
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args)


engine = make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
