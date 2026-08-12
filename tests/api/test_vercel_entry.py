"""El entry de Vercel (api/index.py, raíz del repo) debe exponer la app completa."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from api.index import app  # noqa: E402


def test_el_entry_de_vercel_expone_la_app_fastapi_completa(db_session):
    from fastapi.testclient import TestClient

    from reencuentro_api.services.db import get_session

    def _override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = _override_get_session
    try:
        with TestClient(app) as client:
            assert client.get("/health").json() == {"status": "ok"}

            respuesta = client.get("/api/reports")
            assert respuesta.status_code == 200
            assert isinstance(respuesta.json(), list)
    finally:
        app.dependency_overrides.clear()


def test_el_entry_es_la_misma_app_del_paquete():
    """api/index.py no debe crear una app paralela: es la instancia real."""
    from reencuentro_api.main import app as app_del_paquete

    assert app is app_del_paquete
