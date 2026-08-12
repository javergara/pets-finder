"""El lifespan de arranque (feature 19): create_all por defecto, omitible en prod.

`SKIP_DB_CREATE_ALL=1` existe para recortar el arranque en frío del serverless:
el esquema de producción ya existe y no cambia solo, así que los round-trips de
verificación de create_all son puro costo en cada cold start.
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

from reencuentro_api.main import app


def test_arranque_ejecuta_create_all_por_defecto(monkeypatch):
    monkeypatch.delenv("SKIP_DB_CREATE_ALL", raising=False)

    with patch("reencuentro_api.main.Base.metadata.create_all") as create_all:
        with TestClient(app):
            pass

    create_all.assert_called_once()


def test_skip_db_create_all_omite_create_all_y_la_app_sirve(monkeypatch):
    monkeypatch.setenv("SKIP_DB_CREATE_ALL", "1")

    with patch("reencuentro_api.main.Base.metadata.create_all") as create_all:
        with TestClient(app) as client:
            assert client.get("/health").json() == {"status": "ok"}

    create_all.assert_not_called()
