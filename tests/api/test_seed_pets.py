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

# Catálogos de las tres columnas del perfil de hogar que todavía no tienen un
# `Literal` propio: los declara `schemas/user.py` en AD-04. Hasta entonces la
# fuente de verdad es `services/afinidad.py` (AD-03 paso 3), que **indexa**
# diccionarios con estos valores: una clave fuera de catálogo no da un 422, da
# un `KeyError` a mitad del cálculo del deck.
VIVIENDAS = ("apartamento", "casa")
ESPACIOS_EXTERIORES = ("ninguno", "patio", "jardin")
EXPERIENCIAS_PREVIAS = ("ninguna", "algo", "mucha")


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


# --- Perfil de hogar del seed (AD-03 paso 2) ---------------------------------


def test_el_seed_siembra_exactamente_un_perfil_de_hogar():
    """Uno solo, y el de la usuaria demo: sin él, el score con sus razones
    (acceptance A3 de AD-03) no se puede ver en el recorrido manual ni probar de
    extremo a extremo. Más de uno no aporta nada al recorrido y sí ruido."""
    assert isinstance(seed.HOME_PROFILE, dict)
    assert seed.HOME_PROFILE["user_idx"] == 0  # Ana Martínez, el DEMO_USER_ID = 1


def test_el_perfil_de_hogar_apunta_a_un_usuario_que_existe():
    assert 0 <= seed.HOME_PROFILE["user_idx"] < len(seed.USERS)


def test_los_valores_del_perfil_de_hogar_estan_en_los_catalogos():
    """Mismo criterio que las mascotas: el modelo guarda `String`, así que un
    valor fuera de catálogo se sembraría igual y reventaría más tarde."""
    perfil = seed.HOME_PROFILE
    assert perfil["vivienda"] in VIVIENDAS
    assert perfil["espacio_exterior"] in ESPACIOS_EXTERIORES
    assert perfil["experiencia_previa"] in EXPERIENCIAS_PREVIAS
    assert perfil["preferencia_energia"] in get_args(EnergiaPet)
    for especie in perfil["preferencia_especies"]:
        assert especie in get_args(EspeciePet), especie
    for tamano in perfil["preferencia_tamanos"]:
        assert tamano in get_args(TamanoPet), tamano


def test_el_perfil_de_hogar_es_coherente_con_las_mascotas_sembradas():
    """El deck tiene que mostrar **variedad** de scores, no todo 100 ni todo
    incompatible: para eso las preferencias dejan fuera a algunas mascotas del
    catálogo sin dejar fuera a todas, y la regla dura de niños excluye a alguna
    (`apto_ninos=False`) pero no a la mayoría."""
    perfil = seed.HOME_PROFILE

    en_preferencia = [p for p in seed.PETS if p["tamano"] in perfil["preferencia_tamanos"]]
    assert 0 < len(en_preferencia) < len(seed.PETS)

    if perfil["tiene_ninos"]:
        sin_ninos = [p for p in seed.PETS if p.get("apto_ninos") is False]
        assert len(sin_ninos) == 1, "una sola incompatible: con más, el deck se queda vacío"


def test_el_perfil_de_hogar_declara_un_presupuesto_pero_la_columna_es_opcional():
    """El dato es opcional (decisión de producto: pedir COP en plena emergencia
    añade fricción), pero el seed sí lo da para que el recorrido manual ejercite
    la rama completa de `_score_experiencia_presupuesto`, no la degradada."""
    assert seed.HOME_PROFILE["presupuesto_mensual_cop"] > 0


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
