"""Radar de reencuentros (feature 43)."""

from datetime import date

import pytest

from reencuentro_api.models.report import Report
from reencuentro_api.models.user import User
from reencuentro_api.services import notificaciones
from reencuentro_api.services.radar import MAX_POR_REPORTE, parejas_a_avisar


def _reporte(**overrides) -> Report:
    datos = dict(
        user_id=1,
        tipo="perdido",
        especie="perro",
        descripcion="d",
        zona="Cali",
        lat=3.4500,
        lng=-76.5300,
        fecha_evento=date(2026, 8, 10),
        telefono_contacto="300",
        estado="activo",
    )
    datos.update(overrides)
    return Report(**datos)


# --- Función pura ---


def test_solo_parejas_nuevas_con_tope_y_umbral():
    perdido = _reporte(id=1)
    candidatos = [
        _reporte(id=10, tipo="encontrado", situacion="conmigo", lat=3.4510, lng=-76.5310),
        _reporte(id=11, tipo="encontrado", situacion="conmigo", lat=3.4520, lng=-76.5320),
        _reporte(id=12, tipo="encontrado", situacion="conmigo", lat=3.4530, lng=-76.5330),
        _reporte(id=13, tipo="encontrado", situacion="conmigo", lat=3.4540, lng=-76.5340),
        # Fuera de umbral: mismo punto pero 60 días de diferencia (puntaje 30).
        _reporte(id=14, tipo="encontrado", situacion="conmigo", fecha_evento=date(2026, 10, 9)),
    ]

    parejas = parejas_a_avisar([perdido], candidatos, ya_avisadas=set())

    ids = [c.id for _, c, _, _ in parejas]
    assert len(ids) == MAX_POR_REPORTE  # tope de 3, ordenados por cercanía
    assert ids == [10, 11, 12]
    assert 14 not in ids

    # La pareja ya avisada no se repite y entra la siguiente en el orden.
    repeticion = parejas_a_avisar([perdido], candidatos, ya_avisadas={(1, 10)})
    assert [c.id for _, c, _, _ in repeticion] == [11, 12, 13]


def test_las_razones_acompanan_cada_pareja():
    perdido = _reporte(id=1, color="Negro")
    candidato = _reporte(
        id=10, tipo="encontrado", situacion="conmigo", color="Negro", lat=3.4510, lng=-76.5310
    )

    parejas = parejas_a_avisar([perdido], [candidato], set())

    _, _, _, razones = parejas[0]
    assert "mismo perro" in razones and "mismo color" in razones


# --- Endpoint ---


@pytest.fixture()
def sembrado(db_session):
    ana = User(nombre="Ana", email="ana@example.co", ciudad="Cali")
    db_session.add(ana)
    db_session.flush()
    perdido = _reporte(user_id=ana.id, nombre_mascota="Rocky")
    encontrado = _reporte(
        user_id=ana.id, tipo="encontrado", situacion="conmigo", lat=3.4510, lng=-76.5310
    )
    db_session.add_all([perdido, encontrado])
    db_session.commit()
    return perdido, encontrado


def test_sin_cron_secret_esta_apagado(client, monkeypatch):
    monkeypatch.delenv("CRON_SECRET", raising=False)

    assert client.get("/api/radar").status_code == 503


def test_token_invalido_es_401(client, monkeypatch):
    monkeypatch.setenv("CRON_SECRET", "s3creto")

    assert client.get("/api/radar").status_code == 401
    assert client.get("/api/radar", headers={"Authorization": "Bearer otro"}).status_code == 401


def test_corrida_avisa_al_autor_y_suscritos_y_no_repite(client, db_session, sembrado, monkeypatch):
    perdido, encontrado = sembrado
    monkeypatch.setenv("CRON_SECRET", "s3creto")
    enviados = []
    monkeypatch.setattr(
        notificaciones,
        "_enviar_email",
        lambda destino, asunto, html: (enviados.append((destino, asunto, html)), True)[1],
    )
    client.post(f"/api/reports/{perdido.id}/suscripciones", json={"email": "vecina@example.co"})
    # El autor también está suscrito: su correo no debe repetirse.
    client.post(f"/api/reports/{perdido.id}/suscripciones", json={"email": "ana@example.co"})

    r = client.get("/api/radar", headers={"Authorization": "Bearer s3creto"})

    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["parejas_nuevas"] == 1
    assert cuerpo["correos_enviados"] == 2  # ana + vecina, deduplicadas
    destinos = sorted(d for d, _, _ in enviados)
    assert destinos == ["ana@example.co", "vecina@example.co"]
    asunto, html = enviados[0][1], enviados[0][2]
    assert "Rocky" in asunto
    assert f"/reporte/{encontrado.id}" in html

    # Segunda corrida: nada nuevo que avisar.
    r2 = client.get("/api/radar", headers={"Authorization": "Bearer s3creto"})
    assert r2.json()["parejas_nuevas"] == 0
    assert len(enviados) == 2


def test_fallo_del_proveedor_no_rompe_la_corrida(client, db_session, sembrado, monkeypatch):
    monkeypatch.setenv("CRON_SECRET", "s3creto")

    def explota(*args):
        raise RuntimeError("proveedor caído")

    monkeypatch.setattr(notificaciones, "_enviar_email", explota)

    r = client.get("/api/radar", headers={"Authorization": "Bearer s3creto"})

    assert r.status_code == 200
    assert r.json()["parejas_nuevas"] == 1
