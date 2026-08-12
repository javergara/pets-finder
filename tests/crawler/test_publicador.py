"""El corazón del crawler: PostExtraido → ReportIn validados de la API."""

from datetime import date

import pytest
from crawler.publicador import a_json, convertir, desde_json
from crawler.schema import PostExtraido
from pydantic import ValidationError


def _post(**overrides):
    datos = {
        "es_publicacion": True,
        "plataforma": "instagram",
        "autor_handle": "rescate.cali",
        "telefono": None,
        "ciudad_texto": "Cali",
        "barrio": "Ciudad Jardín",
        "fecha_evento": "2026-08-11",
        "mascotas": [
            {
                "tipo": "encontrado",
                "especie": "perro",
                "raza": "Criollo / mestizo",
                "color": "Negro",
                "tamano": "pequeño",
                "situacion": "conmigo",
                "descripcion": "Perrita negra pequeña con pañoleta de colores.",
            },
            {
                "tipo": "encontrado",
                "especie": "perro",
                "color": "Miel / dorado",
                "situacion": None,
                "descripcion": "Perro dorado mediano, asustado, cerca del parque.",
            },
        ],
        "confianza": 0.85,
    }
    datos.update(overrides)
    return PostExtraido.model_validate(datos)


def test_un_reporte_por_mascota_compartiendo_post():
    payloads = convertir(_post(), user_id=7, url_post="https://instagram.com/p/ABC/")

    assert len(payloads) == 2
    for indice, payload in enumerate(payloads):
        meta = payload.crawl_metadata
        assert payload.fuente == "crawl"
        assert meta.url_post == "https://instagram.com/p/ABC/"
        assert meta.autor_handle == "rescate.cali"
        assert meta.indice_mascota == indice
        assert meta.total_mascotas == 2
        # Comparten zona (Cali resuelta con centro) y fecha del post.
        assert payload.zona == "Cali"
        assert payload.fecha_evento == date(2026, 8, 11)
        assert (payload.lat, payload.lng) == (3.452, -76.532)


def test_extraccion_sin_contacto_falla_local_con_el_mensaje_del_backend():
    """El contrato es el ReportIn real: una extracción no publicable truena en
    convertir, con el copy del backend — nunca como 422 remoto a mitad de corrida."""
    post = _post(autor_handle=None, telefono=None)
    with pytest.raises(ValidationError, match="camino de contacto"):
        convertir(post, user_id=7)


def test_roundtrip_json_del_registro_de_dedup():
    """a_json → JSONL → desde_json devuelve payloads equivalentes y re-validados."""
    payloads = convertir(_post(), user_id=7, url_post="https://instagram.com/p/ABC/")
    recuperados = desde_json(a_json(payloads))
    assert recuperados == payloads


def test_encontrado_sin_situacion_cae_en_vista_y_sin_nombre():
    payloads = convertir(_post(), user_id=7)
    assert payloads[0].situacion == "conmigo"  # la que el post sí dice
    assert payloads[1].situacion == "vista"  # fallback honesto
    assert payloads[1].nombre_mascota is None


def test_perdido_conserva_nombre_y_no_lleva_situacion():
    post = _post(
        mascotas=[
            {
                "tipo": "perdido",
                "especie": "gato",
                "nombre_mascota": "Otto",
                # Ruido típico del LLM: situacion en un perdido — se descarta.
                "situacion": "vista",
                "descripcion": "Gato blanco con negro, collar del Capitán América.",
            }
        ]
    )
    payloads = convertir(post, user_id=7)
    assert payloads[0].nombre_mascota == "Otto"
    assert payloads[0].situacion is None


def test_clave_post_genera_idempotency_id_por_mascota():
    payloads = convertir(
        _post(),
        user_id=7,
        url_post="https://instagram.com/p/ABC/",
        clave_post="https://instagram.com/p/ABC/",
    )
    assert payloads[0].idempotency_id == "https://instagram.com/p/ABC/#0"
    assert payloads[1].idempotency_id == "https://instagram.com/p/ABC/#1"


def test_sin_clave_post_no_hay_idempotency_id():
    payloads = convertir(_post(), user_id=7)
    assert payloads[0].idempotency_id is None


def test_telefono_del_llm_se_sanea_a_digitos():
    payloads = convertir(_post(telefono="300 123 4567"), user_id=7)
    assert payloads[0].telefono_contacto == "3001234567"


def test_telefono_multiple_o_invalido_no_pasa_crudo():
    """'300 123 4567 / 310 987 6543' debe quedar en el primer número — nunca
    los 28 chars crudos (revienta el String(20)) ni los 20 dígitos pegados."""
    payloads = convertir(_post(telefono="300 123 4567 / 310 987 6543"), user_id=7)
    assert payloads[0].telefono_contacto == "3001234567"

    payloads = convertir(_post(telefono="llamar al refugio"), user_id=7)
    assert payloads[0].telefono_contacto is None


def test_facebook_lleva_grupo_en_su_variante():
    post = _post(plataforma="facebook", grupo="Mascotas Perdidas Cali")
    payloads = convertir(post, user_id=7)
    assert payloads[0].crawl_metadata.grupo == "Mascotas Perdidas Cali"


def test_whatsapp_mapea_grupo_a_nombre_grupo():
    post = _post(plataforma="whatsapp", grupo="Mascotas Eje Cafetero")
    payloads = convertir(post, user_id=7)
    meta = payloads[0].crawl_metadata
    assert meta.nombre_grupo == "Mascotas Eje Cafetero"
    assert not hasattr(meta, "grupo")


def test_grupo_no_viaja_fuera_de_facebook():
    """La API forbid-ea campos de otra variante: el publicador no debe mandarlos."""
    post = _post(grupo="ruido del LLM en un post de Instagram")
    payloads = convertir(post, user_id=7)
    assert not hasattr(payloads[0].crawl_metadata, "grupo")


def test_ciudad_fuera_de_zonas_va_como_otro():
    payloads = convertir(_post(ciudad_texto="Bucaramanga"), user_id=7)
    assert payloads[0].zona == "Otro"
    assert payloads[0].ciudad_texto == "Bucaramanga"


def test_ciudad_fallback_cuando_el_post_no_la_dice():
    """Caso real de pantallazos: el post no menciona ciudad, quien lo recolectó sí."""
    payloads = convertir(_post(ciudad_texto=None), user_id=7, ciudad_fallback="Cali")
    assert payloads[0].zona == "Cali"

    # La ciudad del post manda sobre el fallback.
    payloads = convertir(_post(ciudad_texto="Armenia"), user_id=7, ciudad_fallback="Cali")
    assert payloads[0].zona == "Armenia"


def test_sin_ciudad_cae_en_colombia():
    payloads = convertir(_post(ciudad_texto=None), user_id=7)
    assert payloads[0].zona == "Otro"
    assert payloads[0].ciudad_texto == "Colombia"


def test_sin_fecha_usa_fallback():
    payloads = convertir(_post(fecha_evento=None), user_id=7, fecha_fallback=date(2026, 8, 12))
    assert payloads[0].fecha_evento == date(2026, 8, 12)


def test_zona_insensible_a_tildes_y_mayusculas():
    payloads = convertir(_post(ciudad_texto="bogota"), user_id=7)
    assert payloads[0].zona == "Bogotá"


def test_medellin_es_zona_propia_desde_la_feature_26():
    """Las zonas vienen de services/ciudades.py (fuente única): una zona nueva
    del proyecto queda disponible para el crawler sin tocar nada aquí."""
    payloads = convertir(_post(ciudad_texto="medellin"), user_id=7)
    assert payloads[0].zona == "Medellín"
    assert (payloads[0].lat, payloads[0].lng) == (6.244, -75.581)
