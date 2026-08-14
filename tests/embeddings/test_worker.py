"""Tests del worker de embeddings.

Corren en la suite normal: sin red, sin torch y sin descargar modelos — el
cálculo del vector se inyecta falso. Lo que se verifica aquí es la lógica del
worker (a quién procesa, qué escribe, qué respeta), no la calidad del modelo.
"""

from datetime import date

import pytest
from embeddings import cli
from embeddings.modelo import PIPELINE

from reencuentro_api.models import Report, User

VECTOR = [0.1] * 384


def _reporte(session, **extra) -> int:
    """Crea un reporte y devuelve su id.

    Devuelve el id y no el objeto a propósito: `cli.main()` cierra la sesión al
    terminar y cualquier instancia viva quedaría desprendida (DetachedInstance).
    """
    if session.get(User, 1) is None:
        session.add(User(id=1, nombre="Ana", email="ana@example.com", ciudad="Cali"))
    campos = dict(
        user_id=1,
        tipo="perdido",
        especie="perro",
        descripcion="Perro café",
        zona="Cali",
        lat=3.44,
        lng=-76.52,
        fecha_evento=date(2026, 8, 11),
        foto_url="https://bucket.supabase.co/x.jpg",
    )
    campos.update(extra)
    reporte = Report(**campos)
    session.add(reporte)
    session.commit()
    return reporte.id


@pytest.fixture()
def worker(monkeypatch, db_session):
    """Enchufa el CLI a la DB en memoria y a un embebedor falso."""
    monkeypatch.setattr(cli, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(cli, "leer_foto", lambda url: b"bytes-de-foto")
    monkeypatch.setattr(cli, "vector_de_foto", lambda contenido: list(VECTOR))
    return cli


def test_solo_procesa_los_que_les_falta_el_vector(worker, db_session):
    sin_vector = _reporte(db_session)
    al_dia = _reporte(db_session, embedding=list(VECTOR), embedding_modelo=PIPELINE)
    viejo = _reporte(db_session, embedding=list(VECTOR), embedding_modelo="pipeline-viejo/v0")
    sin_foto = _reporte(db_session, foto_url=None)

    ids = [r.id for r in worker.pendientes(db_session, rehacer=False, reporte_id=None)]

    assert sin_vector in ids
    assert viejo in ids, "un vector de otro pipeline no es comparable: hay que rehacerlo"
    assert al_dia not in ids
    assert sin_foto not in ids, "sin foto no hay nada que embeber"


def test_rehacer_incluye_los_que_ya_estan_al_dia(worker, db_session):
    al_dia = _reporte(db_session, embedding=list(VECTOR), embedding_modelo=PIPELINE)

    ids = [r.id for r in worker.pendientes(db_session, rehacer=True, reporte_id=None)]

    assert al_dia in ids


def test_dry_run_no_escribe_nada(worker, db_session):
    reporte_id = _reporte(db_session)

    assert worker.main([]) == 0

    guardado = db_session.get(Report, reporte_id)
    assert guardado.embedding is None
    assert guardado.embedding_modelo is None


def test_escribir_guarda_vector_y_pipeline(worker, db_session):
    reporte_id = _reporte(db_session)

    assert worker.main(["--escribir"]) == 0

    guardado = db_session.get(Report, reporte_id)
    assert guardado.embedding == VECTOR
    assert guardado.embedding_modelo == PIPELINE


def test_foto_sin_animal_deja_el_reporte_intacto(monkeypatch, worker, db_session):
    """Degradación elegante: sin vector, el reporte sigue existiendo igual."""
    monkeypatch.setattr(cli, "vector_de_foto", lambda contenido: None)
    reporte_id = _reporte(db_session)

    assert worker.main(["--escribir"]) == 0

    guardado = db_session.get(Report, reporte_id)
    assert guardado.embedding is None
    assert guardado.embedding_modelo is None
    assert guardado.descripcion == "Perro café"


def test_una_foto_ilegible_no_frena_a_las_demas(monkeypatch, worker, db_session):
    """La primera falla al descargar; la segunda debe procesarse igual."""
    roto_id = _reporte(db_session, foto_url="https://bucket.supabase.co/roto.jpg")
    bueno_id = _reporte(db_session, foto_url="https://bucket.supabase.co/bueno.jpg")
    monkeypatch.setattr(cli, "leer_foto", lambda url: None if "roto" in url else b"bytes-de-foto")

    assert worker.main(["--escribir"]) == 0

    assert db_session.get(Report, roto_id).embedding is None
    assert db_session.get(Report, bueno_id).embedding == VECTOR, "una foto rota no frena la corrida"


def test_reporte_puntual(worker, db_session):
    primero_id = _reporte(db_session)
    segundo_id = _reporte(db_session)

    assert worker.main(["--escribir", "--reporte", str(segundo_id)]) == 0

    assert db_session.get(Report, segundo_id).embedding == VECTOR
    assert db_session.get(Report, primero_id).embedding is None


def test_limite_corta_la_corrida(worker, db_session):
    """--limite existe para la primera pasada cautelosa contra producción."""
    primero_id = _reporte(db_session)
    segundo_id = _reporte(db_session)

    assert worker.main(["--escribir", "--limite", "1"]) == 0

    assert db_session.get(Report, primero_id).embedding == VECTOR
    assert db_session.get(Report, segundo_id).embedding is None


def test_leer_foto_local_y_ausente(tmp_path, monkeypatch):
    """La foto local se lee del disco; la que no existe devuelve None sin lanzar."""
    monkeypatch.setattr(cli, "MEDIA_DIR", tmp_path)
    (tmp_path / "uploads").mkdir()
    (tmp_path / "uploads" / "foto.jpg").write_bytes(b"contenido")

    assert cli.leer_foto("/media/uploads/foto.jpg") == b"contenido"
    assert cli.leer_foto("/media/uploads/no-existe.jpg") is None
    assert cli.leer_foto("ruta-rara") is None


# --- Guardas de seguridad de `leer_foto` ---
#
# `foto_url` la fija quien crea el reporte y cualquiera puede crear uno (no hay
# auth real, ADR 0005 §4). Este worker corre en la máquina del dueño o en CI.


def test_no_descarga_urls_fuera_del_bucket_propio(monkeypatch):
    """Sin esto el worker es un SSRF contra la red interna de quien lo corre."""
    monkeypatch.setattr(cli, "prefijo_publico", lambda: "https://abc.supabase.co/x/public/fotos/")

    def _no_debe_llamarse(*args, **kwargs):
        raise AssertionError("no debió salir ninguna petición de red")

    monkeypatch.setattr(cli.requests, "get", _no_debe_llamarse)

    assert cli.leer_foto("http://169.254.169.254/latest/meta-data/") is None
    assert cli.leer_foto("http://localhost:8000/admin") is None
    assert cli.leer_foto("https://otro-host.com/foto.jpg") is None


def test_sin_supabase_configurado_no_descarga_nada(monkeypatch):
    monkeypatch.setattr(cli, "prefijo_publico", lambda: None)
    monkeypatch.setattr(
        cli.requests, "get", lambda *a, **k: (_ for _ in ()).throw(AssertionError("no"))
    )

    assert cli.leer_foto("https://abc.supabase.co/x/public/fotos/f.jpg") is None


def test_no_lee_archivos_fuera_de_media(tmp_path, monkeypatch):
    """`Path` deja que un componente absoluto descarte la base y que '..' escale."""
    media = tmp_path / "media"
    (media / "uploads").mkdir(parents=True)
    (media / "uploads" / "ok.jpg").write_bytes(b"foto")
    secreto = tmp_path / "secreto.txt"
    secreto.write_text("credenciales")
    monkeypatch.setattr(cli, "MEDIA_DIR", media)

    assert cli.leer_foto("/media/uploads/ok.jpg") == b"foto"
    assert cli.leer_foto("/media/uploads/../../secreto.txt") is None, "traversal con .."
    assert cli.leer_foto(f"/media/{secreto}") is None, "ruta absoluta que descarta la base"
