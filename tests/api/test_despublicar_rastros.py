"""`DELETE /api/pets/{id}` cuando la mascota ya dejó rastros (AD-09).

Vive aparte de `tests/api/test_pets_publicar.py` —donde está el resto del
`DELETE` de AD-02— por una sola razón: **estos tests necesitan una base de datos
que fuerce las claves foráneas, y la del `conftest` no lo hace**.

⚠️ **SQLite no comprueba las FK salvo que se le pida** (`PRAGMA foreign_keys`
llega en `OFF` en cada conexión nueva). Postgres sí, siempre. Como las tres FK
hacia `public.pets` están declaradas **sin `ON DELETE`** (`swipes.pet_id`,
`matches.pet_id`, `favorites.pet_id` — ver `migrations/AD-03-swipes.sql`,
`AD-05-matches.sql` y `AD-07-favorites.sql`), borrar una mascota con un solo
swipe encima revienta en producción con `IntegrityError` → 500 con traza, y la
suite entera lo ve verde. Ese hueco es el que cierra este archivo.

Por eso el `db_session_fk` de abajo **no** reemplaza al `db_session` global: se
usa solo aquí. Encenderle las FK a los 738 tests existentes rompería casos que
borran a propósito filas con hijos apuntándolas (p. ej.
`test_despublicar_mascota_de_organizacion_eliminada_devuelve_403`, que elimina
una organización con una mascota colgando para comprobar el 403), y ese no es el
trabajo de esta corrección.

`test_el_fixture_fuerza_las_fk_y_el_global_no` es el candado del propio fixture:
si alguien le quita el listener, estos tests volverían a pasar con el código
roto y ahí sí serían decorativos.
"""

from datetime import datetime

import pytest
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from reencuentro_api.models.base import Base
from reencuentro_api.models.favorite import Favorite
from reencuentro_api.models.match import Match
from reencuentro_api.models.organizacion import Organizacion
from reencuentro_api.models.pet import Pet
from reencuentro_api.models.report import Report
from reencuentro_api.models.swipe import Swipe
from reencuentro_api.models.user import User
from reencuentro_api.routers import pets as pets_router

# El copy exacto del 409, escrito a mano y no importado del router: si se importara
# la constante, renombrar el mensaje dejaría el test verde con otro texto en la
# cara del usuario (mismo criterio que `MENSAJE_REPORTE_CON_MASCOTA` en
# `test_pets_publicar.py`).
MENSAJE_UNA_SOLICITUD = (
    "Esta mascota tiene 1 solicitud de adopción abierta: "
    "ciérrala antes de despublicar a la mascota"
)
MENSAJE_DOS_SOLICITUDES = (
    "Esta mascota tiene 2 solicitudes de adopción abiertas: "
    "ciérralas antes de despublicar a la mascota"
)

#: Los tres estados desde los que una solicitud todavía puede moverse. Se escriben
#: a mano (no se derivan de `ESTADOS_SOLICITUD` menos `ESTADOS_TERMINALES`) para
#: que este archivo no herede el mismo error si alguien mueve la frontera.
ESTADOS_VIVOS = ("solicitado", "en_revision", "visita_agendada")


# --- Infraestructura: una base que sí comprueba las FK --------------------------


@pytest.fixture()
def db_session_fk():
    """Clon de `db_session` (conftest) con `PRAGMA foreign_keys=ON`.

    El listener va sobre el evento `connect` del engine y no como un
    `session.execute("PRAGMA ...")`: SQLite **ignora ese pragma dentro de una
    transacción**, y una sesión de SQLAlchemy abre transacción antes de la
    primera sentencia. Puesto en `connect`, se aplica a la conexión cruda antes de
    que exista ninguna transacción — y con `StaticPool` esa conexión es la única
    que va a existir en todo el test.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _activar_fk(conexion_dbapi, _record):  # pragma: no cover - lo ejerce cada test
        cursor = conexion_dbapi.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = session_local()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client_fk(db_session_fk):
    """El `client` del conftest, pero hablando con la base de FK forzadas."""
    from fastapi.testclient import TestClient

    from reencuentro_api.main import app
    from reencuentro_api.services.db import get_session

    def _override_get_session():
        yield db_session_fk

    app.dependency_overrides[get_session] = _override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def fotos_borradas(monkeypatch):
    """Lista-espía sobre `borrar_foto` (mismo patrón que `test_pets_publicar.py`).

    `borrar_foto` nunca lanza, así que sin espiarla un 409 o un 204 salen igual de
    limpios aunque el endpoint se haya llevado del bucket fotos que no eran suyas.
    """
    llamadas: list[str] = []
    monkeypatch.setattr(pets_router, "borrar_foto", llamadas.append)
    return llamadas


# --- Datos ---------------------------------------------------------------------


@pytest.fixture()
def usuario(db_session_fk):
    user = User(nombre="Ana", email="ana@example.co", ciudad="Armenia")
    db_session_fk.add(user)
    db_session_fk.commit()
    return user


@pytest.fixture()
def adoptante(db_session_fk):
    user = User(nombre="Carlos", email="carlos@example.co", ciudad="Pereira")
    db_session_fk.add(user)
    db_session_fk.commit()
    return user


@pytest.fixture()
def otra_adoptante(db_session_fk):
    user = User(nombre="Lucía", email="lucia@example.co", ciudad="Manizales")
    db_session_fk.add(user)
    db_session_fk.commit()
    return user


@pytest.fixture()
def organizacion(db_session_fk, usuario):
    org = Organizacion(
        user_id=usuario.id,
        tipo="fundacion",
        nombre="Fundación Huellitas del Quindío",
        descripcion="Rescatamos mascotas afectadas por el sismo.",
        zona="Armenia",
        direccion="Cra 14 #10-25",
        lat=4.535,
        lng=-75.68,
        telefono_contacto="3001112233",
    )
    db_session_fk.add(org)
    db_session_fk.commit()
    return org


@pytest.fixture()
def mascota(db_session_fk, organizacion):
    pet = Pet(
        nombre="Canela",
        especie="perro",
        sexo="hembra",
        edad_meses=18,
        tamano="mediano",
        energia="media",
        historia="Rescatada en Armenia tras el sismo, busca hogar.",
        zona="Armenia",
        publicado_en=datetime(2026, 8, 14, 9, 0),
        organizacion_id=organizacion.id,
        fotos=["/media/uploads/canela-1.jpg"],
    )
    db_session_fk.add(pet)
    db_session_fk.commit()
    return pet


def _swipe(session, user_id: int, pet_id: int, direccion: str = "like") -> Swipe:
    fila = Swipe(user_id=user_id, pet_id=pet_id, direccion=direccion)
    session.add(fila)
    session.commit()
    return fila


def _favorito(session, user_id: int, pet_id: int) -> Favorite:
    fila = Favorite(user_id=user_id, pet_id=pet_id)
    session.add(fila)
    session.commit()
    return fila


def _solicitud(session, user_id: int, pet_id: int, estado: str) -> Match:
    fila = Match(user_id=user_id, pet_id=pet_id, estado=estado, mensaje="Me encantaría adoptarla")
    session.add(fila)
    session.commit()
    return fila


def _contar(session, modelo, pet_id: int) -> int:
    return session.scalar(select(func.count()).select_from(modelo).where(modelo.pet_id == pet_id))


# --- El candado del fixture ----------------------------------------------------


def test_el_fixture_fuerza_las_fk_y_el_global_no(db_session_fk, db_session, usuario):
    """La prueba de que estos tests valen algo.

    Un swipe apuntando a una mascota inexistente: en la base con `PRAGMA
    foreign_keys=ON` revienta, en la del conftest entra tan tranquilo. Si alguien
    quita el listener de `db_session_fk`, este test cae y avisa **antes** de que
    los demás vuelvan a ser decorativos.
    """
    with pytest.raises(IntegrityError):
        _swipe(db_session_fk, usuario.id, pet_id=9999)
    db_session_fk.rollback()

    global_usuario = User(nombre="Ana", email="ana@example.co", ciudad="Armenia")
    db_session.add(global_usuario)
    db_session.commit()
    _swipe(db_session, global_usuario.id, pet_id=9999)  # sin FK forzadas: no lanza
    assert _contar(db_session, Swipe, 9999) == 1


# --- 204: los rastros privados se van con la mascota ---------------------------


def test_despublicar_con_swipes_y_favoritos_devuelve_204_y_los_borra(
    client_fk, db_session_fk, mascota, usuario, adoptante, otra_adoptante
):
    """El bug que llegaba a producción como 500.

    Con las FK forzadas —o sea, como se comporta Postgres— un `session.delete(pet)`
    a secas revienta con `IntegrityError` en cuanto exista **un solo** swipe o
    favorito. Un swipe y un favorito son rastros privados sin valor propio: se
    borran con ella.
    """
    _swipe(db_session_fk, adoptante.id, mascota.id)
    _swipe(db_session_fk, otra_adoptante.id, mascota.id, direccion="pass")
    _favorito(db_session_fk, adoptante.id, mascota.id)
    _favorito(db_session_fk, otra_adoptante.id, mascota.id)

    respuesta = client_fk.delete(f"/api/pets/{mascota.id}?user_id={usuario.id}")

    assert respuesta.status_code == 204

    db_session_fk.expire_all()
    assert db_session_fk.get(Pet, mascota.id) is None
    assert _contar(db_session_fk, Swipe, mascota.id) == 0
    assert _contar(db_session_fk, Favorite, mascota.id) == 0


def test_despublicar_no_toca_los_rastros_de_otras_mascotas(
    client_fk, db_session_fk, mascota, organizacion, usuario, adoptante
):
    """El borrado en cascada filtra por `pet_id`, no arrasa la tabla."""
    vecina = Pet(
        nombre="Nube",
        especie="gato",
        sexo="macho",
        edad_meses=6,
        tamano="pequeno",
        energia="alta",
        historia="Rescatado en el mismo barrio, busca hogar.",
        zona="Armenia",
        publicado_en=datetime(2026, 8, 14, 10, 0),
        organizacion_id=organizacion.id,
    )
    db_session_fk.add(vecina)
    db_session_fk.commit()
    _swipe(db_session_fk, adoptante.id, mascota.id)
    _swipe(db_session_fk, adoptante.id, vecina.id)
    _favorito(db_session_fk, adoptante.id, vecina.id)

    assert client_fk.delete(f"/api/pets/{mascota.id}?user_id={usuario.id}").status_code == 204

    db_session_fk.expire_all()
    assert db_session_fk.get(Pet, vecina.id) is not None
    assert _contar(db_session_fk, Swipe, vecina.id) == 1
    assert _contar(db_session_fk, Favorite, vecina.id) == 1


def test_despublicar_sin_ningun_rastro_sigue_devolviendo_204(
    client_fk, db_session_fk, mascota, usuario, fotos_borradas
):
    """El caso que ya existía en `test_pets_publicar.py`, repetido aquí con las FK
    encendidas: la corrección no puede haberlo estropeado, ni haber dejado de
    borrar las fotos propias."""
    respuesta = client_fk.delete(f"/api/pets/{mascota.id}?user_id={usuario.id}")

    assert respuesta.status_code == 204
    assert fotos_borradas == ["/media/uploads/canela-1.jpg"]

    db_session_fk.expire_all()
    assert db_session_fk.get(Pet, mascota.id) is None


def test_despublicar_una_mascota_venida_de_un_reporte_limpia_rastros_pero_no_fotos(
    client_fk, db_session_fk, usuario, adoptante, fotos_borradas
):
    """La regla de AD-02 sigue en pie con el borrado en cascada encima.

    Si la mascota nació de un reporte, sus fotos **son las del reporte**, que sigue
    vivo: borrarlas dejaría imágenes rotas en la app. Como `borrar_foto` no lanza,
    el 204 saldría igual de verde; solo la espía lo delata.
    """
    reporte = Report(
        user_id=usuario.id,
        tipo="encontrado",
        especie="perro",
        descripcion="Perra encontrada cerca del Parque Sucre, la tengo conmigo.",
        foto_url="/media/uploads/reporte-principal.jpg",
        zona="Armenia",
        lat=4.535,
        lng=-75.68,
        situacion="conmigo",
        fecha_evento=datetime(2026, 8, 11).date(),
        telefono_contacto="3001112233",
    )
    db_session_fk.add(reporte)
    db_session_fk.commit()
    pet = Pet(
        nombre="Canela",
        especie="perro",
        sexo="hembra",
        edad_meses=18,
        tamano="mediano",
        energia="media",
        historia="Rescatada en Armenia tras el sismo, busca hogar.",
        zona="Armenia",
        publicado_en=datetime(2026, 8, 14, 9, 0),
        user_id=usuario.id,
        telefono_contacto="3001112233",
        report_id=reporte.id,
        fotos=[reporte.foto_url],
    )
    db_session_fk.add(pet)
    db_session_fk.commit()
    _swipe(db_session_fk, adoptante.id, pet.id)
    _favorito(db_session_fk, adoptante.id, pet.id)

    respuesta = client_fk.delete(f"/api/pets/{pet.id}?user_id={usuario.id}")

    assert respuesta.status_code == 204
    assert fotos_borradas == []

    db_session_fk.expire_all()
    assert db_session_fk.get(Pet, pet.id) is None
    assert _contar(db_session_fk, Swipe, pet.id) == 0
    assert _contar(db_session_fk, Favorite, pet.id) == 0
    assert db_session_fk.get(Report, reporte.id) is not None


@pytest.mark.parametrize("estado", ("adoptado", "cerrado"))
def test_despublicar_con_solo_solicitudes_terminales_devuelve_204(
    client_fk, db_session_fk, mascota, usuario, adoptante, estado
):
    """Una solicitud terminal (`adoptado`/`cerrado`) ya no es una conversación
    abierta: nadie espera respuesta, así que no bloquea y se va con la mascota."""
    _solicitud(db_session_fk, adoptante.id, mascota.id, estado=estado)

    respuesta = client_fk.delete(f"/api/pets/{mascota.id}?user_id={usuario.id}")

    assert respuesta.status_code == 204

    db_session_fk.expire_all()
    assert db_session_fk.get(Pet, mascota.id) is None
    assert _contar(db_session_fk, Match, mascota.id) == 0


# --- 409: una solicitud viva es una conversación con otra persona --------------


@pytest.mark.parametrize("estado", ESTADOS_VIVOS)
def test_despublicar_con_una_solicitud_viva_devuelve_409_y_no_borra_nada(
    client_fk, db_session_fk, mascota, usuario, adoptante, otra_adoptante, estado, fotos_borradas
):
    """Los tres estados no terminales bloquean, y el 409 va **antes** de tocar el
    bucket: al revés, el usuario perdería las fotos y encima la mascota seguiría
    publicada (misma trampa que ya cerró `eliminar_reporte`)."""
    _swipe(db_session_fk, otra_adoptante.id, mascota.id)
    _favorito(db_session_fk, otra_adoptante.id, mascota.id)
    solicitud = _solicitud(db_session_fk, adoptante.id, mascota.id, estado=estado)

    respuesta = client_fk.delete(f"/api/pets/{mascota.id}?user_id={usuario.id}")

    assert respuesta.status_code == 409
    assert respuesta.json()["detail"] == MENSAJE_UNA_SOLICITUD
    assert fotos_borradas == []

    # Nada se fue: ni la mascota, ni los rastros privados, ni la solicitud.
    db_session_fk.expire_all()
    assert db_session_fk.get(Pet, mascota.id) is not None
    assert _contar(db_session_fk, Swipe, mascota.id) == 1
    assert _contar(db_session_fk, Favorite, mascota.id) == 1
    assert db_session_fk.get(Match, solicitud.id) is not None
    assert client_fk.get(f"/api/pets/{mascota.id}").status_code == 200


def test_el_409_cuenta_solo_las_vivas_y_lo_dice_en_plural(
    client_fk, db_session_fk, mascota, usuario, adoptante, otra_adoptante
):
    """Dos vivas y una terminal: el mensaje dice **2**, no 3.

    Contar las cerradas asustaría con un número que no se corresponde con ninguna
    conversación pendiente, y quien intente cerrarlas no encontraría la tercera.
    """
    tercera = User(nombre="Miguel", email="miguel@example.co", ciudad="Armenia")
    db_session_fk.add(tercera)
    db_session_fk.commit()
    _solicitud(db_session_fk, adoptante.id, mascota.id, estado="solicitado")
    _solicitud(db_session_fk, otra_adoptante.id, mascota.id, estado="visita_agendada")
    _solicitud(db_session_fk, tercera.id, mascota.id, estado="cerrado")

    respuesta = client_fk.delete(f"/api/pets/{mascota.id}?user_id={usuario.id}")

    assert respuesta.status_code == 409
    assert respuesta.json()["detail"] == MENSAJE_DOS_SOLICITUDES

    db_session_fk.expire_all()
    assert _contar(db_session_fk, Match, mascota.id) == 3


def test_tras_cerrar_la_solicitud_la_mascota_si_se_despublica(
    client_fk, db_session_fk, mascota, usuario, adoptante
):
    """El 409 tiene salida, y es la que el propio mensaje indica: cerrar la
    solicitud. Sin este test, el mensaje podría estar mandando a un callejón."""
    solicitud = _solicitud(db_session_fk, adoptante.id, mascota.id, estado="solicitado")
    assert client_fk.delete(f"/api/pets/{mascota.id}?user_id={usuario.id}").status_code == 409

    cerrada = client_fk.post(
        f"/api/solicitudes/{solicitud.id}/descartar",
        json={"user_id": usuario.id, "motivo": "La mascota ya no está disponible"},
    )
    assert cerrada.status_code == 200

    respuesta = client_fk.delete(f"/api/pets/{mascota.id}?user_id={usuario.id}")

    assert respuesta.status_code == 204

    db_session_fk.expire_all()
    assert db_session_fk.get(Pet, mascota.id) is None
    assert _contar(db_session_fk, Match, mascota.id) == 0


def test_el_403_de_una_mascota_ajena_manda_sobre_el_409(
    client_fk, db_session_fk, mascota, adoptante
):
    """Quien no publicó la mascota no tiene por qué enterarse de cuántas
    solicitudes tiene: la autoría se resuelve primero."""
    _solicitud(db_session_fk, adoptante.id, mascota.id, estado="solicitado")

    respuesta = client_fk.delete(f"/api/pets/{mascota.id}?user_id={adoptante.id}")

    assert respuesta.status_code == 403
    assert respuesta.json()["detail"] == "Solo quien publicó la mascota puede despublicarla"
