"""Datos de adopción del seed local (AD-01 paso 7): organizaciones y mascotas.

Valida las **constantes** de `scripts/seed.py`, no la DB: son datos puros, y si
se desalinean del modelo el seed revienta con un `IntegrityError` en el primer
`bash init.sh` de quien clone el repo (o, peor, siembra una mascota inservible
para el catálogo). Aquí se fija lo que features posteriores dan por hecho: el
XOR de publicador, la senior y la de "necesita experiencia" que alimentan el
deck de AD-03, y la adoptada de la franja de AD-05.

⚠️ `scripts/seed.py` se importa como módulo (nunca se ejecuta `main()`): correr
el seed hace `drop_all` y jamás debe pasar dentro de la suite.
"""

import sys
from pathlib import Path
from typing import get_args

import pytest
import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import seed  # noqa: E402

from reencuentro_api.schemas.organizacion import TipoOrganizacion  # noqa: E402
from reencuentro_api.schemas.pet import (  # noqa: E402
    EnergiaPet,
    EspeciePet,
    EstadoPet,
    SexoPet,
    TamanoPet,
)

EDAD_MESES_SENIOR = 84  # el umbral que usa el deck de AD-03


def _mascotas_de_organizacion() -> list[dict]:
    return [datos for datos in seed.PETS if datos.get("organizacion_idx") is not None]


def _mascotas_de_rescatista() -> list[dict]:
    return [datos for datos in seed.PETS if datos.get("user_idx") is not None]


# --- Publicador exclusivo: el invariante del CHECK, ya en los datos -----------


def test_cada_mascota_del_seed_cuelga_de_un_solo_publicador():
    """Ni las dos claves ni ninguna: `ck_pets_publicador_exclusivo` rechazaría
    la fila y el seed moriría a mitad de camino."""
    for datos in seed.PETS:
        tiene_organizacion = datos.get("organizacion_idx") is not None
        tiene_rescatista = datos.get("user_idx") is not None
        assert tiene_organizacion != tiene_rescatista, datos["nombre"]


def test_el_seed_reparte_las_mascotas_entre_organizaciones_y_rescatistas():
    """El catálogo tiene que mostrar los dos tipos de publicador (AD-01 A2/A3)."""
    assert len(_mascotas_de_organizacion()) == 4
    assert len(_mascotas_de_rescatista()) == 4
    assert len(seed.PETS) == 8


def test_los_publicadores_del_seed_apuntan_a_filas_que_existen():
    for datos in seed.PETS:
        if datos.get("organizacion_idx") is not None:
            assert 0 <= datos["organizacion_idx"] < len(seed.ORGANIZACIONES), datos["nombre"]
        else:
            assert 0 <= datos["user_idx"] < len(seed.USERS), datos["nombre"]

    for datos in seed.ORGANIZACIONES:
        assert 0 <= datos["user_idx"] < len(seed.USERS), datos["nombre"]


def test_las_mascotas_de_rescatista_traen_telefono_de_contacto():
    """`User` no tiene teléfono: sin esta columna la mascota es incontactable
    (misma regla que el `model_validator` de `PetIn`)."""
    for datos in _mascotas_de_rescatista():
        assert (datos.get("telefono_contacto") or "").strip(), datos["nombre"]


# --- Cobertura que consumen las features siguientes ---------------------------


def test_el_seed_incluye_al_menos_una_mascota_senior():
    seniors = [datos for datos in seed.PETS if datos["edad_meses"] > EDAD_MESES_SENIOR]
    assert seniors, "el deck de AD-03 intercala seniors: el seed necesita al menos una"


def test_el_seed_incluye_una_mascota_que_necesita_experiencia():
    con_tag = [datos for datos in seed.PETS if "necesita experiencia" in datos.get("tags", [])]
    assert con_tag, "`es_dificil_de_ubicar` de AD-03 se apoya en este tag"


def test_el_seed_incluye_una_mascota_adoptada_con_su_fecha():
    """La franja de celebración de AD-05 lee `GET /api/pets/adopciones`, que
    ordena por `adoptado_en`: una adoptada sin fecha no aparecería."""
    adoptadas = [datos for datos in seed.PETS if datos.get("estado") == "adoptado"]
    assert len(adoptadas) == 1
    assert adoptadas[0].get("adoptado_en") is not None

    for datos in seed.PETS:
        if datos.get("estado") != "adoptado":
            assert datos.get("adoptado_en") is None, datos["nombre"]


def test_el_seed_mezcla_especies_tamanos_energias_y_zonas():
    """Sin variedad los filtros del catálogo no se pueden probar a mano."""
    assert {"perro", "gato"} <= {datos["especie"] for datos in seed.PETS}
    assert {"pequeño", "mediano", "grande"} == {datos["tamano"] for datos in seed.PETS}
    assert {"baja", "media", "alta"} == {datos["energia"] for datos in seed.PETS}
    assert len({datos["zona"] for datos in seed.PETS}) >= 3


def test_los_valores_del_seed_estan_en_el_catalogo_de_la_api():
    """Los `Literal` de los schemas son la fuente de verdad: un valor fuera de
    catálogo se sembraría igual (el modelo guarda `String`) y luego reventaría
    al serializar el catálogo."""
    for datos in seed.PETS:
        assert datos["especie"] in get_args(EspeciePet), datos["nombre"]
        assert datos["sexo"] in get_args(SexoPet), datos["nombre"]
        assert datos["tamano"] in get_args(TamanoPet), datos["nombre"]
        assert datos["energia"] in get_args(EnergiaPet), datos["nombre"]
        assert datos.get("estado", "disponible") in get_args(EstadoPet), datos["nombre"]

    for datos in seed.ORGANIZACIONES:
        assert datos["tipo"] in get_args(TipoOrganizacion), datos["nombre"]


# --- Pines dentro de su zona (misma validación que los reportes) --------------


def test_los_pines_de_organizaciones_y_mascotas_caen_dentro_de_su_zona():
    for datos in seed.ORGANIZACIONES:
        seed._validar_pin(datos["nombre"], datos["zona"], datos["lat"], datos["lng"])
    for datos in seed.PETS:
        seed._validar_pin(datos["nombre"], datos["zona"], datos.get("lat"), datos.get("lng"))


def test_un_pin_fuera_de_su_zona_aborta_el_seed():
    with pytest.raises(SystemExit):
        seed._validar_pin("Mascota de prueba", "Armenia", 4.65, -74.06)


def test_una_zona_desconocida_aborta_el_seed():
    with pytest.raises(SystemExit):
        seed._validar_pin("Mascota de prueba", "Barranquilla", 10.96, -74.79)


# --- Fotos: el prefijo se parametriza sin romper las de los reportes ----------


def test_la_foto_de_un_reporte_conserva_el_nombre_report_id(monkeypatch):
    """Regresión del paso 7: parametrizar el prefijo no puede renombrar las
    fotos existentes en `data/media/seed/` (quedarían huérfanas y el listado
    mostraría 404)."""

    class _Respuesta:
        content = b"jpeg falso"

        def raise_for_status(self):
            return None

    monkeypatch.setattr(seed.requests, "get", lambda *a, **k: _Respuesta())

    nombre, contenido, content_type = seed._obtener_foto(7, "Rocky", "perro")

    assert nombre == "report_7.jpg"
    assert contenido == b"jpeg falso"
    assert content_type == "image/jpeg"


def test_la_foto_de_una_mascota_usa_el_prefijo_pet(monkeypatch):
    class _Respuesta:
        content = b"jpeg falso"

        def raise_for_status(self):
            return None

    monkeypatch.setattr(seed.requests, "get", lambda *a, **k: _Respuesta())

    nombre, _contenido, _content_type = seed._obtener_foto(3, "Nala", "perro", prefijo="pet")

    assert nombre == "pet_3.jpg"


@pytest.mark.parametrize(
    ("prefijo", "esperado"),
    [("report", "report_5.svg"), ("pet", "pet_5.svg")],
)
def test_sin_red_la_foto_cae_en_el_placeholder_svg(monkeypatch, prefijo, esperado):
    """El seed nunca falla por falta de red (skill `seed-data`): el mismo
    fallback vale para reportes y para mascotas."""

    def _sin_red(*_args, **_kwargs):
        raise requests.RequestException("sin red")

    monkeypatch.setattr(seed.requests, "get", _sin_red)

    nombre, contenido, content_type = seed._obtener_foto(5, "Nala", "perro", prefijo=prefijo)

    assert nombre == esperado
    assert content_type == "image/svg+xml"
    assert b"Nala" in contenido
