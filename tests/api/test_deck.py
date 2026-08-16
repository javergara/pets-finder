"""Deck de descubrimiento (AD-03 paso 7): `GET /api/pets/deck`.

Es el único test de extremo a extremo del acceptance A3 ("cada tarjeta muestra
score y al menos dos razones"): los servicios puros ya están cubiertos uno a uno
(`test_afinidad.py`, `test_descubrir.py`, `test_filtros.py`), pero solo aquí se
ve que el router los encadena en el orden correcto y con el perfil real.

⚠️ **La ruta se declara entre `/adopciones` y `/{pet_id}`.** Si quedara después
de la dinámica, FastAPI intentaría convertir "deck" en un `pet_id` y respondería
422 — un bug que parece "la ruta no existe".
`test_deck_no_se_parsea_como_pet_id_y_responde_200` es la garantía viva de ese
orden.

⚠️ `Pet`, `Swipe`, `HomeProfile`, `Organizacion` y `User` se importan a nivel de
módulo a propósito: el fixture `db_session` hace `create_all` con lo que esté
registrado en `Base.metadata` en ese instante, y un import perezoso produce un
`no such table` intermitente según el orden de colección de pytest.
"""

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import event

from reencuentro_api.models.home_profile import HomeProfile
from reencuentro_api.models.organizacion import Organizacion
from reencuentro_api.models.pet import Pet
from reencuentro_api.models.swipe import Swipe
from reencuentro_api.models.user import User


@pytest.fixture()
def adoptante(db_session):
    """Quien mira el deck. Sin `lat`/`lng`: es el caso mayoritario del repo."""
    user = User(nombre="Ana", email="ana@example.co", ciudad="Armenia")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture()
def otro_adoptante(db_session):
    user = User(nombre="Lucía", email="lucia@example.co", ciudad="Pereira")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture()
def publicador(db_session):
    """El rescatista dueño de las mascotas: NO es quien mira el deck."""
    user = User(nombre="Carlos", email="carlos@example.co", ciudad="Pereira")
    db_session.add(user)
    db_session.commit()
    return user


def _pet(publicador_id: int, **overrides) -> Pet:
    campos = {
        "user_id": publicador_id,
        "telefono_contacto": "3105558899",
        "nombre": "Canela",
        "especie": "perro",
        "sexo": "hembra",
        "edad_meses": 18,
        "tamano": "mediano",
        "energia": "media",
        "historia": "Rescatada en Armenia tras el sismo, busca hogar.",
        "zona": "Armenia",
    }
    campos.update(overrides)
    return Pet(**campos)


def _sembrar(db_session, publicador, *nombres_y_overrides) -> dict[str, Pet]:
    """Siembra el catálogo del test y devuelve las mascotas por nombre (con id)."""
    mascotas = {
        nombre: _pet(publicador.id, nombre=nombre, **overrides)
        for nombre, overrides in nombres_y_overrides
    }
    db_session.add_all(mascotas.values())
    db_session.commit()
    return mascotas


def _home(db_session, user_id: int, **overrides) -> HomeProfile:
    """Perfil de hogar sin reglas duras activas, salvo que el test las pida."""
    campos = {
        "user_id": user_id,
        "vivienda": "casa",
        "espacio_exterior": "patio",
        "personas_en_casa": 2,
        "tiene_ninos": False,
        "tiene_otros_perros": False,
        "tiene_otros_gatos": False,
        "horas_fuera_dia": 6,
        "experiencia_previa": "algo",
        "presupuesto_mensual_cop": 200_000,
        "preferencia_especies": ["perro"],
        "preferencia_tamanos": ["mediano"],
        "preferencia_energia": "media",
    }
    campos.update(overrides)
    home = HomeProfile(**campos)
    db_session.add(home)
    db_session.commit()
    return home


def _nombres(respuesta) -> list[str]:
    return [m["nombre"] for m in respuesta.json()]


@contextmanager
def _contar_consultas(session):
    """Cuenta las sentencias SQL reales que salen por el engine del test.

    Misma red anti-N+1 que en `test_pets.py`: sin las dos queries batch con `IN`,
    cada mascota del deck añadiría un round-trip por su publicador.
    """
    sentencias: list[str] = []
    engine = session.get_bind()

    def _registrar(conn, cursor, statement, parameters, context, executemany):
        sentencias.append(statement)

    event.listen(engine, "before_cursor_execute", _registrar)
    try:
        yield sentencias
    finally:
        event.remove(engine, "before_cursor_execute", _registrar)


# --- Orden de rutas: la garantía viva ------------------------------------------


def test_deck_no_se_parsea_como_pet_id_y_responde_200(client, db_session):
    """Si `GET /deck` se declarara después de `GET /{pet_id}`, FastAPI trataría
    de convertir "deck" en int y esto sería un 422 (bug que parece "la ruta no
    existe"). Con la base vacía el deck es una lista vacía, no un error."""
    respuesta = client.get("/api/pets/deck")

    assert respuesta.status_code != 422
    assert respuesta.status_code == 200
    assert respuesta.json() == []


# --- Exclusión de lo ya visto (acceptance) -------------------------------------


def test_excluye_las_mascotas_ya_swipeadas_por_ese_adoptante(
    client, db_session, adoptante, publicador
):
    mascotas = _sembrar(db_session, publicador, ("Canela", {}), ("Rocky", {}), ("Mishi", {}))
    db_session.add(Swipe(user_id=adoptante.id, pet_id=mascotas["Rocky"].id, direccion="pass"))
    db_session.commit()

    nombres = _nombres(client.get(f"/api/pets/deck?adoptante_id={adoptante.id}"))

    assert sorted(nombres) == ["Canela", "Mishi"]
    assert "Rocky" not in nombres


def test_no_excluye_las_swipeadas_por_otro_adoptante(
    client, db_session, adoptante, otro_adoptante, publicador
):
    """El swipe es información de una persona, no del catálogo (ADR 0002)."""
    mascotas = _sembrar(db_session, publicador, ("Canela", {}), ("Rocky", {}))
    db_session.add(Swipe(user_id=otro_adoptante.id, pet_id=mascotas["Rocky"].id, direccion="like"))
    db_session.commit()

    nombres = _nombres(client.get(f"/api/pets/deck?adoptante_id={adoptante.id}"))

    assert sorted(nombres) == ["Canela", "Rocky"]


def test_excluye_las_que_no_estan_disponibles(client, db_session, adoptante, publicador):
    _sembrar(
        db_session,
        publicador,
        ("Canela", {}),
        ("En proceso", {"estado": "en_proceso"}),
        ("Adoptada", {"estado": "adoptado", "adoptado_en": datetime(2026, 8, 12, 10, 0)}),
    )

    nombres = _nombres(client.get(f"/api/pets/deck?adoptante_id={adoptante.id}"))

    assert nombres == ["Canela"]


# --- Con perfil y sin perfil (decisión 1 del líder) ----------------------------


def test_sin_perfil_de_hogar_responde_200_con_afinidad_null(
    client, db_session, adoptante, publicador
):
    """`adopta-v1` devolvía 404 si el adoptante no tenía cuestionario. Aquí eso
    rompería el onboarding entero y contradice el acceptance de AD-04: el deck
    responde 200 y la invitación a completar el perfil no bloquea."""
    _sembrar(db_session, publicador, ("Canela", {}), ("Rocky", {}))

    respuesta = client.get(f"/api/pets/deck?adoptante_id={adoptante.id}")

    assert respuesta.status_code == 200
    assert len(respuesta.json()) == 2
    assert all(m["afinidad"] is None for m in respuesta.json())


def test_con_perfil_cada_tarjeta_trae_score_y_al_menos_dos_razones(
    client, db_session, adoptante, publicador
):
    """Acceptance A3, de extremo a extremo: score + ≥2 razones legibles."""
    _sembrar(db_session, publicador, ("Canela", {}), ("Rocky", {"energia": "alta"}))
    _home(db_session, adoptante.id)

    cuerpo = client.get(f"/api/pets/deck?adoptante_id={adoptante.id}").json()

    assert len(cuerpo) == 2
    for mascota in cuerpo:
        afinidad = mascota["afinidad"]
        assert afinidad is not None
        assert isinstance(afinidad["score"], int)
        assert 0 <= afinidad["score"] <= 100
        assert afinidad["incompatible"] is False
        assert afinidad["explicacion"]
        assert len(afinidad["razones"]) >= 2
        assert all(isinstance(razon, str) and razon for razon in afinidad["razones"])


def test_excluye_las_incompatibles_con_el_perfil(client, db_session, adoptante, publicador):
    _sembrar(
        db_session,
        publicador,
        ("Canela", {}),
        ("Bonita", {"apto_ninos": False}),
        ("Michi", {"especie": "gato", "apto_gatos": False}),
    )
    _home(db_session, adoptante.id, tiene_ninos=True, tiene_otros_gatos=True)

    nombres = _nombres(client.get(f"/api/pets/deck?adoptante_id={adoptante.id}"))

    assert nombres == ["Canela"]


def test_incluir_incompatibles_true_las_devuelve_marcadas(
    client, db_session, adoptante, publicador
):
    _sembrar(db_session, publicador, ("Canela", {}), ("Bonita", {"apto_ninos": False}))
    _home(db_session, adoptante.id, tiene_ninos=True)

    cuerpo = client.get(
        f"/api/pets/deck?adoptante_id={adoptante.id}&incluir_incompatibles=true"
    ).json()

    por_nombre = {m["nombre"]: m for m in cuerpo}
    assert sorted(por_nombre) == ["Bonita", "Canela"]
    assert por_nombre["Bonita"]["afinidad"]["incompatible"] is True
    assert por_nombre["Bonita"]["afinidad"]["score"] == 0
    assert por_nombre["Bonita"]["afinidad"]["razones"]
    assert por_nombre["Canela"]["afinidad"]["incompatible"] is False


# --- Filtros (los mismos chips que el catálogo) --------------------------------


def test_respeta_el_filtro_de_especie(client, db_session, adoptante, publicador):
    _sembrar(
        db_session,
        publicador,
        ("Canela", {}),
        ("Michi", {"especie": "gato"}),
        ("Kiwi", {"especie": "otro"}),
    )

    url = f"/api/pets/deck?adoptante_id={adoptante.id}"
    assert sorted(_nombres(client.get(f"{url}&especie=perro&especie=gato"))) == ["Canela", "Michi"]
    assert _nombres(client.get(f"{url}&especie=otro")) == ["Kiwi"]


def test_respeta_el_filtro_de_edad_categoria(client, db_session, adoptante, publicador):
    _sembrar(
        db_session,
        publicador,
        ("Cachorra", {"edad_meses": 5}),
        ("Joven", {"edad_meses": 20}),
        ("Adulta", {"edad_meses": 50}),
        ("Senior", {"edad_meses": 100}),
    )

    url = f"/api/pets/deck?adoptante_id={adoptante.id}"
    assert _nombres(client.get(f"{url}&edad_categoria=cachorro")) == ["Cachorra"]
    assert sorted(_nombres(client.get(f"{url}&edad_categoria=adulto&edad_categoria=senior"))) == [
        "Adulta",
        "Senior",
    ]


def test_respeta_el_filtro_de_zona(client, db_session, adoptante, publicador):
    _sembrar(
        db_session,
        publicador,
        ("Canela", {}),
        ("Rocky", {"zona": "Pereira"}),
        ("Michi", {"zona": "Cali"}),
    )

    url = f"/api/pets/deck?adoptante_id={adoptante.id}"
    assert _nombres(client.get(f"{url}&zona=Armenia")) == ["Canela"]
    assert sorted(_nombres(client.get(f"{url}&zona=Pereira&zona=Cali"))) == ["Michi", "Rocky"]


def test_respeta_los_filtros_de_convivencia(client, db_session, adoptante, publicador):
    _sembrar(
        db_session,
        publicador,
        ("Canela", {}),
        ("SinNinos", {"apto_ninos": False}),
        ("SinPerros", {"apto_perros": False}),
        ("SinGatos", {"apto_gatos": False}),
    )

    url = f"/api/pets/deck?adoptante_id={adoptante.id}"
    assert _nombres(client.get(f"{url}&apto_ninos=true&apto_perros=true&apto_gatos=true")) == [
        "Canela"
    ]
    assert _nombres(client.get(f"{url}&apto_ninos=false")) == ["SinNinos"]
    assert _nombres(client.get(f"{url}&apto_gatos=false")) == ["SinGatos"]


def test_sin_coordenadas_del_adoptante_la_distancia_no_excluye_a_nadie(
    client, db_session, adoptante, publicador
):
    """El `User` puede no tener `lat`/`lng` (la mayoría no los tiene): la
    degradación elegante de `services/filtros.py` no excluye a nadie en vez de
    devolver un deck vacío."""
    assert adoptante.lat is None and adoptante.lng is None
    _sembrar(
        db_session,
        publicador,
        ("Canela", {"lat": 4.535, "lng": -75.68}),
        ("Rocky", {"lat": 3.45, "lng": -76.53}),
        ("Sin pin", {}),
    )

    cuerpo = client.get(f"/api/pets/deck?adoptante_id={adoptante.id}&distancia_km=1").json()

    assert sorted(m["nombre"] for m in cuerpo) == ["Canela", "Rocky", "Sin pin"]
    assert all(m["distancia_km"] is None for m in cuerpo)


# --- Sin cuenta y adoptante inexistente (decisión 2 del líder) -----------------


def test_sin_adoptante_id_responde_200_sin_excluir_ni_calcular_afinidad(
    client, db_session, adoptante, publicador
):
    """`adoptante_id` es opcional: exigirlo forzaría al frontend a mandar el id
    de una persona real cuando no hay cuenta (`getActiveUserId()` cae al
    `DEMO_USER_ID = 1`), que es el bug de autoría del fix `cc4de85`."""
    mascotas = _sembrar(db_session, publicador, ("Canela", {}), ("Rocky", {}))
    db_session.add(Swipe(user_id=adoptante.id, pet_id=mascotas["Rocky"].id, direccion="pass"))
    _home(db_session, adoptante.id)

    respuesta = client.get("/api/pets/deck")

    assert respuesta.status_code == 200
    assert sorted(_nombres(respuesta)) == ["Canela", "Rocky"]
    assert all(m["afinidad"] is None for m in respuesta.json())


def test_adoptante_inexistente_devuelve_404(client, db_session, publicador):
    _sembrar(db_session, publicador, ("Canela", {}))

    respuesta = client.get("/api/pets/deck?adoptante_id=9999")

    assert respuesta.status_code == 404
    assert "9999" in respuesta.json()["detail"]


# --- Tamaño del deck y orden ---------------------------------------------------


def test_limit_recorta_el_deck(client, db_session, adoptante, publicador):
    _sembrar(db_session, publicador, *((f"Mascota {n}", {}) for n in range(9)))

    url = f"/api/pets/deck?adoptante_id={adoptante.id}"
    assert len(client.get(f"{url}&limit=4").json()) == 4
    assert len(client.get(url).json()) == 9
    assert client.get(f"{url}&limit=0").status_code == 422
    assert client.get(f"{url}&limit=51").status_code == 422


def test_las_dificiles_de_ubicar_quedan_intercaladas_sin_perfil(
    client, db_session, adoptante, publicador
):
    """`ordenar_deck` se llama SIEMPRE, también sin perfil de hogar.

    `adopta-v1` solo ordenaba cuando había `HomeProfile`; sin eso, las mascotas
    difíciles de ubicar no se intercalan para quien no completó el cuestionario
    —que es la mayoría de la gente— y quedan enterradas al final del deck.
    """
    _sembrar(
        db_session,
        publicador,
        *((f"Normal {n}", {}) for n in range(12)),
        *(
            (f"Difícil {n}", {"edad_meses": 100, "publicado_en": datetime(2026, 8, 10, 9, 0)})
            for n in range(3)
        ),
    )

    cuerpo = client.get(f"/api/pets/deck?adoptante_id={adoptante.id}").json()

    assert len(cuerpo) == 15
    assert all(m["afinidad"] is None for m in cuerpo)
    posiciones = [i + 1 for i, m in enumerate(cuerpo) if m["nombre"].startswith("Difícil")]
    assert len(posiciones) == 3
    assert all(pos % 4 == 0 or pos % 5 == 0 for pos in posiciones)
    assert posiciones[0] <= 5


def test_una_publicada_hace_mas_de_90_dias_tambien_se_intercala(
    client, db_session, adoptante, publicador
):
    """La tercera vía de "difícil de ubicar" depende de la fecha real, así que se
    siembra relativa a la corrida (nunca un literal: sería una fecha-bomba)."""
    hace_120_dias = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=120)
    _sembrar(
        db_session,
        publicador,
        *((f"Normal {n}", {}) for n in range(6)),
        ("Olvidada", {"publicado_en": hace_120_dias}),
    )

    cuerpo = client.get(f"/api/pets/deck?adoptante_id={adoptante.id}").json()

    posicion = [m["nombre"] for m in cuerpo].index("Olvidada") + 1
    assert posicion % 4 == 0 or posicion % 5 == 0
    assert posicion <= 5


# --- Orden base determinista (la diferencia SQLite ↔ Postgres) -----------------


def test_el_deck_sale_ordenado_por_publicado_en_descendente(
    client, db_session, adoptante, publicador
):
    """La query lleva `ORDER BY publicado_en DESC, id DESC`, el mismo criterio del
    catálogo (`listar_mascotas`).

    ⚠️ Sin ese `ORDER BY` este test **también** queda rojo en SQLite, pero por
    casualidad: la base devuelve las filas en orden de `rowid` (el de inserción),
    que aquí es justo el inverso del esperado. En Postgres el orden de base es
    arbitrario y no habría nada que aseverar. Por eso la siembra va del más
    antiguo al más nuevo: es la única forma de que el motor de los tests note la
    ausencia del orden que sí importa en producción.
    """
    ahora = datetime.now(timezone.utc).replace(tzinfo=None)
    _sembrar(
        db_session,
        publicador,
        ("Canela", {"publicado_en": ahora - timedelta(days=3)}),
        ("Rocky", {"publicado_en": ahora - timedelta(days=2)}),
        ("Luna", {"publicado_en": ahora - timedelta(days=1)}),
    )

    respuesta = client.get(f"/api/pets/deck?adoptante_id={adoptante.id}")

    assert _nombres(respuesta) == ["Luna", "Rocky", "Canela"]


def test_dos_llamadas_seguidas_devuelven_el_mismo_orden_sin_perfil(client, db_session, publicador):
    """Sin perfil de hogar **todas** las mascotas empatan (`ordenar_deck` las
    puntúa a 0 y `sorted` es estable), así que el orden que ve el usuario es el
    que sale de la base. Sin `ORDER BY` eso lo decide Postgres a su antojo y dos
    requests seguidos pueden barajar el deck: quien recarga vería otra carta
    encima sin haber hecho nada.

    Las fechas van relativas a la corrida y nunca literales: un `publicado_en`
    fijo se vuelve "difícil de ubicar" a los 90 días y `ordenar_deck` empezaría a
    intercalar, cambiando el orden esperado (la fecha-bomba de la feature 35).
    """
    momento = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1)
    _sembrar(
        db_session,
        publicador,
        *((f"Mascota {n}", {"publicado_en": momento}) for n in range(6)),
    )

    primera = _nombres(client.get("/api/pets/deck"))
    segunda = _nombres(client.get("/api/pets/deck"))

    assert primera == segunda
    # Empatadas en `publicado_en`, desempata el id descendente: la última
    # publicada primero, igual que en el catálogo.
    assert primera == [f"Mascota {n}" for n in reversed(range(6))]


# --- Anti-N+1 ------------------------------------------------------------------


def _sembrar_con_publicadores_distintos(db_session, desde: int, cantidad: int) -> None:
    """Dos mascotas por iteración, cada una con un publicador propio.

    Que cada fila cuelgue de una organización y de un rescatista **distintos** es
    lo que hace real el test: si todas compartieran publicador, el `IN` de una
    sola fila escondería el N+1.
    """
    for n in range(desde, desde + cantidad):
        rescatista = User(nombre=f"Rescatista {n}", email=f"r{n}@example.co", ciudad="Armenia")
        db_session.add(rescatista)
        db_session.flush()
        fundacion = Organizacion(
            user_id=rescatista.id,
            tipo="fundacion",
            nombre=f"Fundación {n}",
            descripcion="Rescate tras el sismo.",
            zona="Armenia",
            direccion="Cra 14 #10-25",
            lat=4.535,
            lng=-75.68,
            telefono_contacto="3001112233",
        )
        db_session.add(fundacion)
        db_session.flush()
        # `user_id=None` (el positional) + `organizacion_id`: el CHECK
        # `ck_pets_publicador_exclusivo` exige exactamente uno de los dos.
        db_session.add(_pet(None, organizacion_id=fundacion.id, nombre=f"Fundada {n}"))
        db_session.add(_pet(rescatista.id, nombre=f"Rescatada {n}"))
    db_session.commit()


def test_el_deck_no_hace_una_consulta_por_publicador(client, db_session, adoptante):
    """Anti-N+1: el número de consultas NO crece con el tamaño del deck.

    Son siempre 5 — el adoptante, su perfil de hogar, las mascotas y **una** query
    con `IN` por cada tabla de publicador — aunque cada mascota tenga un
    publicador distinto.

    ⚠️ **Lo que hace real a este test es que cada fila tenga un publicador
    propio**, no el `expunge_all()`. Medido por mutación (2026-08-15, AD-03 paso
    7): con `session.get` por fila el conteo se va a 7 y 23 —rojo— pero si todas
    las mascotas cuelgan del mismo publicador vuelve a 5 y **pasa igual**, porque
    dentro de un mismo request el identity map responde el segundo `get` de la
    misma fila sin tocar la base.

    `expunge_all()` se conserva porque es la receta de `memory/memory.md`
    (el fixture `db_session` comparte una sola sesión con el `TestClient`, y en
    producción cada request abre la suya), pero aquí **no** es lo que sostiene la
    aserción: el `commit()` de la siembra ya expira todo el identity map, así que
    el test queda rojo con la implementación ingenua se llame o no. Deja de ser
    inocuo el día que alguien mida sin un `commit()` de por medio.
    """
    # El **id**, no la instancia: `expunge_all()` la deja detached y leerle un
    # atributo después lanzaría `DetachedInstanceError` (patrón de
    # `test_home_profile_modelo.py`).
    adoptante_id = adoptante.id
    _home(db_session, adoptante_id)
    _sembrar_con_publicadores_distintos(db_session, desde=0, cantidad=2)

    db_session.expunge_all()
    with _contar_consultas(db_session) as deck_corto:
        cuerpo_corto = client.get(f"/api/pets/deck?adoptante_id={adoptante_id}").json()

    _sembrar_con_publicadores_distintos(db_session, desde=2, cantidad=6)

    db_session.expunge_all()
    with _contar_consultas(db_session) as deck_largo:
        cuerpo_largo = client.get(f"/api/pets/deck?adoptante_id={adoptante_id}&limit=50").json()

    assert len(cuerpo_corto) == 4
    assert len(cuerpo_largo) == 16
    assert all(m["publicador"] is not None for m in cuerpo_largo)
    assert len(deck_corto) == 5
    assert len(deck_largo) == 5


# --- De extremo a extremo con el endpoint del perfil (AD-04, acceptance 2) -----
#
# Todo lo de arriba siembra el `HomeProfile` a mano con `_home`, así que ningún
# test prueba que **el endpoint nuevo** sea el que alimenta al deck; y
# `test_afinidad.py` es función pura, sin HTTP. Estos dos casos cierran ese
# hueco: lo único que cambia entre las dos consultas al deck es el `PUT`.


def _payload_hogar(user_id: int, **overrides) -> dict:
    datos = {
        "user_id": user_id,
        "vivienda": "casa",
        "espacio_exterior": "patio",
        "personas_en_casa": 2,
        "tiene_ninos": False,
        "tiene_otros_perros": False,
        "tiene_otros_gatos": False,
        "horas_fuera_dia": 6,
        "experiencia_previa": "algo",
        "presupuesto_mensual_cop": None,
        "preferencia_especies": [],
        "preferencia_tamanos": [],
        "preferencia_energia": "media",
    }
    datos.update(overrides)
    return datos


def test_el_deck_cambia_de_afinidad_al_guardar_el_perfil(client, db_session, adoptante, publicador):
    """Acceptance 2: contestar el cuestionario puntúa y reordena el deck.

    Las dos mascotas se siembran con energías distintas (`media` y `alta`) y el
    hogar declara 10 horas fuera al día: eso es lo que las separa de verdad. Con
    dos mascotas iguales, "ahora hay afinidad" pasaría igual con un score
    constante, que no demostraría nada.
    """
    _sembrar(
        db_session, publicador, ("Canela", {"energia": "media"}), ("Rocky", {"energia": "alta"})
    )

    antes = client.get(f"/api/pets/deck?adoptante_id={adoptante.id}").json()
    assert len(antes) == 2
    assert all(m["afinidad"] is None for m in antes)

    guardado = client.put(
        f"/api/users/{adoptante.id}/home-profile",
        json=_payload_hogar(adoptante.id, horas_fuera_dia=10),
    )
    assert guardado.status_code == 200

    despues = client.get(f"/api/pets/deck?adoptante_id={adoptante.id}").json()

    assert len(despues) == 2
    assert all(m["afinidad"] is not None for m in despues)
    scores = {m["nombre"]: m["afinidad"]["score"] for m in despues}
    assert scores["Canela"] != scores["Rocky"]
    # Con 10 horas fuera de casa la de mucha energía encaja peor: el perfil no
    # rellena un número cualquiera, ordena.
    assert scores["Rocky"] < scores["Canela"]


def test_las_razones_del_deck_citan_las_respuestas_guardadas(
    client, db_session, adoptante, publicador
):
    """Acceptance 2: las razones son las del hogar que acaba de responder.

    `tiene_ninos=True` no excluye a Canela (es apta con niños; la regla dura solo
    muerde al revés), así que la convivencia sí puede aparecer citada.
    """
    _sembrar(db_session, publicador, ("Canela", {"energia": "media", "apto_ninos": True}))

    client.put(
        f"/api/users/{adoptante.id}/home-profile",
        json=_payload_hogar(
            adoptante.id, horas_fuera_dia=9, vivienda="apartamento", tiene_ninos=True
        ),
    )

    cuerpo = client.get(f"/api/pets/deck?adoptante_id={adoptante.id}").json()

    texto = " | ".join(cuerpo[0]["afinidad"]["razones"])
    assert "9 horas fuera al día" in texto
    assert "apartamento" in texto
    assert "niños" in texto
