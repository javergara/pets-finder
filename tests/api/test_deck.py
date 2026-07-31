from datetime import datetime, timedelta, timezone

from adopta_api.schemas.pet import AfinidadOut, PetOut
from adopta_api.services.deck import es_dificil_de_ubicar, ordenar_deck

AHORA = datetime.now(timezone.utc).replace(tzinfo=None)


def _pet(id_: int, score: int, **overrides) -> PetOut:
    base = dict(
        id=id_,
        shelter_id=1,
        nombre=f"Mascota{id_}",
        especie="perro",
        raza="Criolla",
        sexo="macho",
        edad_meses=24,
        tamano="mediano",
        energia="media",
        fotos=[],
        historia="",
        tags=[],
        esterilizado=True,
        vacunas_al_dia=True,
        microchip=True,
        desparasitado=True,
        apto_ninos=True,
        apto_perros=True,
        apto_gatos=True,
        estado="disponible",
        publicado_en=AHORA,
        shelter=None,
        afinidad=AfinidadOut(score=score, explicacion="", incompatible=False),
    )
    base.update(overrides)
    return PetOut(**base)


def test_senior_es_dificil_de_ubicar():
    pet = _pet(1, 50, edad_meses=90)
    assert es_dificil_de_ubicar(pet)


def test_necesita_experiencia_es_dificil_de_ubicar():
    pet = _pet(1, 50, tags=["necesita experiencia"])
    assert es_dificil_de_ubicar(pet)


def test_publicada_hace_mas_de_90_dias_es_dificil_de_ubicar():
    pet = _pet(1, 50, publicado_en=AHORA - timedelta(days=120))
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
