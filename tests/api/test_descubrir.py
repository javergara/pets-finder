"""Orden del deck de descubrimiento (AD-03 paso 4).

Función pura sobre `PetOut`: sin DB, sin FastAPI. Los seis primeros casos vienen
de `origin/adopta-v1:tests/api/test_deck.py` y fijan que el port no cambió una
línea de lógica; el último es propio de este repo.

⚠️ `_ahora()` es una **función**, no la constante `AHORA` de módulo del original.
Un valor calculado una vez en la importación es una fecha-bomba latente (el mismo
patrón que hizo fallar `Reportes.test.tsx` al día siguiente, feature 35): lo que
se quiere fijar es un instante **relativo a la corrida**, no uno congelado.
"""

from datetime import datetime, timedelta, timezone

from reencuentro_api.schemas.pet import AfinidadOut, PetOut
from reencuentro_api.services.descubrir import es_dificil_de_ubicar, ordenar_deck


def _ahora() -> datetime:
    """El mismo instante naive-UTC contra el que compara `es_dificil_de_ubicar`.

    `publicado_en` es `timestamp without time zone` en los dos motores (el
    `create_all` de SQLite y `migrations/AD-01-pets.sql`), así que restarle un
    datetime *aware* lanza `TypeError`. Aquí se replica a propósito.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _pet(id_: int, score: int | None, **overrides) -> PetOut:
    """Mascota de salida mínima. `score=None` → `afinidad=None` (sin perfil)."""
    base = dict(
        id=id_,
        organizacion_id=1,
        user_id=None,
        report_id=None,
        nombre=f"Mascota{id_}",
        especie="perro",
        raza="Criolla",
        sexo="macho",
        edad_meses=24,
        tamano="mediano",
        energia="media",
        fotos=[],
        historia="Historia de prueba",
        tags=[],
        esterilizado=True,
        vacunas_al_dia=True,
        microchip=True,
        desparasitado=True,
        apto_ninos=True,
        apto_perros=True,
        apto_gatos=True,
        zona="Armenia",
        ciudad_texto=None,
        barrio=None,
        lat=None,
        lng=None,
        telefono_contacto="3001112233",
        estado="disponible",
        publicado_en=_ahora(),
        adoptado_en=None,
        publicador=None,
        afinidad=(
            None
            if score is None
            else AfinidadOut(score=score, explicacion="", razones=[], incompatible=False)
        ),
    )
    base.update(overrides)
    return PetOut(**base)


# --- Los seis de adopta-v1: la lógica no cambió ----------------------------


def test_senior_es_dificil_de_ubicar():
    pet = _pet(1, 50, edad_meses=90)
    assert es_dificil_de_ubicar(pet)


def test_necesita_experiencia_es_dificil_de_ubicar():
    pet = _pet(1, 50, tags=["necesita experiencia"])
    assert es_dificil_de_ubicar(pet)


def test_publicada_hace_mas_de_90_dias_es_dificil_de_ubicar():
    pet = _pet(1, 50, publicado_en=_ahora() - timedelta(days=120))
    assert es_dificil_de_ubicar(pet)


def test_mascota_comun_no_es_dificil_de_ubicar():
    pet = _pet(1, 50)
    assert not es_dificil_de_ubicar(pet)


def test_ordenar_deck_inserta_dificiles_cada_4_o_5_tarjetas():
    normales = [_pet(i, score=100 - i) for i in range(12)]
    dificiles = [_pet(100 + i, score=10 - i, edad_meses=90) for i in range(3)]

    deck = ordenar_deck(normales + dificiles)

    # No se pierde ni se duplica ninguna mascota
    assert sorted(p.id for p in deck) == sorted(p.id for p in normales + dificiles)

    posiciones_dificiles = [i + 1 for i, p in enumerate(deck) if es_dificil_de_ubicar(p)]
    # Cada mascota difícil aparece en una posición múltiplo de 4 o 5
    assert all(pos % 4 == 0 or pos % 5 == 0 for pos in posiciones_dificiles)
    # Las tres mascotas difíciles se insertaron (no quedaron todas al final sin tocar)
    assert len(posiciones_dificiles) == 3
    assert posiciones_dificiles[0] <= 5


def test_ordenar_deck_sin_dificiles_devuelve_orden_por_afinidad():
    pets = [_pet(1, score=50), _pet(2, score=90), _pet(3, score=70)]

    deck = ordenar_deck(pets)

    assert [p.id for p in deck] == [2, 3, 1]


# --- Propio de este repo: el camino por defecto de AD-03 -------------------


def test_ordenar_deck_con_afinidad_none_no_revienta():
    """Sin perfil de hogar TODAS las mascotas llegan con `afinidad=None`.

    Es el caso mayoritario en producción, no un borde: el deck responde 200 sin
    perfil (decisión 2 del líder) y la invitación a completarlo no bloquea. Con
    todos los scores empatados en 0 el orden por afinidad no decide nada, pero
    la inserción de difíciles tiene que seguir ocurriendo — si no, quien no tiene
    perfil jamás vería a las que más necesitan visibilidad.
    """
    normales = [_pet(i, score=None) for i in range(12)]
    dificiles = [_pet(100 + i, score=None, tags=["necesita experiencia"]) for i in range(3)]

    deck = ordenar_deck(normales + dificiles)

    assert all(p.afinidad is None for p in deck)
    assert sorted(p.id for p in deck) == sorted(p.id for p in normales + dificiles)

    posiciones_dificiles = [i + 1 for i, p in enumerate(deck) if es_dificil_de_ubicar(p)]
    assert len(posiciones_dificiles) == 3
    assert all(pos % 4 == 0 or pos % 5 == 0 for pos in posiciones_dificiles)
    assert posiciones_dificiles[0] <= 5
