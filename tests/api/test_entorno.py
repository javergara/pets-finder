"""Compatibilidad con las env vars de la integración Vercel×Supabase (Marketplace)."""

from reencuentro_api import media
from reencuentro_api.models.base import _database_url_desde_entorno


def test_database_url_explicita_gana_y_fuerza_psycopg3(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://x:y@host:6543/postgres")
    monkeypatch.setenv("POSTGRES_URL", "postgres://otro")

    assert _database_url_desde_entorno() == "postgresql+psycopg://x:y@host:6543/postgres"


def test_postgres_url_de_la_integracion_se_normaliza(monkeypatch):
    """La integración inyecta scheme legacy postgres:// y params que libpq
    rechaza (supa=..., pgbouncer=true) — deben limpiarse conservando sslmode,
    y el dialecto queda explícito en psycopg v3 (psycopg2 no tiene wheels para
    los runtimes nuevos: el build de Vercel fallaba compilándolo)."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv(
        "POSTGRES_URL",
        "postgres://u.abc:pass@aws-0.pooler.supabase.com:6543/postgres"
        "?sslmode=require&supa=base-pooler.x",
    )

    assert _database_url_desde_entorno() == (
        "postgresql+psycopg://u.abc:pass@aws-0.pooler.supabase.com:6543/postgres?sslmode=require"
    )


def test_sin_ninguna_env_var_cae_a_sqlite_local(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("POSTGRES_URL", raising=False)
    monkeypatch.delenv("POSTGRES_PRISMA_URL", raising=False)

    assert _database_url_desde_entorno().startswith("sqlite:///")


def test_service_role_key_de_la_integracion_activa_supabase(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://abc.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "clave-de-la-integracion")

    assert media.supabase_configurado()
    assert media._config_supabase() == (
        "https://abc.supabase.co",
        "clave-de-la-integracion",
        "fotos",
    )


def test_supabase_service_key_propia_tiene_prioridad(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://abc.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "clave-propia")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "clave-de-la-integracion")

    assert media._config_supabase() == ("https://abc.supabase.co", "clave-propia", "fotos")
