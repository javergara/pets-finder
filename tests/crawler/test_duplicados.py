"""Dedup v0 por teléfono: llave de candidatos, nunca veredicto (ADR 0010).

El teléfono identifica a la persona, no al caso — el diseño lo asume: los
hallazgos se reportan para revisión humana y solo el nombre discrimina entre
las mascotas de una misma persona.
"""

from crawler.publicador import convertir, posibles_duplicados
from crawler.schema import PostExtraido


def _payload(nombre=None, telefono="3001234567", tipo="perdido", especie="gato"):
    mascota = {
        "tipo": tipo,
        "especie": especie,
        "descripcion": "Señas de prueba de la mascota.",
    }
    if tipo == "perdido":
        mascota["nombre_mascota"] = nombre
    else:
        mascota["situacion"] = "conmigo"
    post = PostExtraido.model_validate(
        {
            "es_publicacion": True,
            "plataforma": "instagram",
            "autor_handle": "cuenta.prueba",
            "telefono": telefono,
            "ciudad_texto": "Cali",
            "mascotas": [mascota],
            "confianza": 0.9,
        }
    )
    return convertir(post, user_id=7)[0]


def _existente(id=1, telefono="3001234567", tipo="perdido", especie="gato", nombre=None):
    return {
        "id": id,
        "telefono_contacto": telefono,
        "tipo": tipo,
        "especie": especie,
        "nombre_mascota": nombre,
    }


def test_mismo_nombre_es_casi_seguro_y_normaliza_telefono_y_nombre():
    """'Whiskey' publicado en dos páginas: mismo caso aunque el número traiga
    el 57 y el nombre venga en mayúsculas."""
    dups = posibles_duplicados(
        _payload(nombre="WHISKEY", telefono="+57 300 123 4567"),
        [_existente(id=24, nombre="whiskey", telefono="3001234567")],
    )
    assert dups == [
        {"id": 24, "nivel": "casi seguro", "razon": "mismo teléfono, tipo, especie y nombre"}
    ]


def test_nombres_distintos_no_es_duplicado():
    """Caso Iru y Nala: misma persona, misma especie, dos mascotas reales."""
    dups = posibles_duplicados(
        _payload(nombre="Iru"),
        [_existente(nombre="Nala")],
    )
    assert dups == []


def test_sin_nombre_para_distinguir_es_posible():
    """Un rescatista publica varios encontrados sin nombre: ambiguo → revisar."""
    dups = posibles_duplicados(
        _payload(tipo="encontrado"),
        [_existente(id=30, tipo="encontrado", nombre=None)],
    )
    assert dups[0]["nivel"] == "posible"
    assert dups[0]["id"] == 30


def test_tipo_o_especie_distintos_no_son_candidatos():
    assert posibles_duplicados(_payload(), [_existente(tipo="encontrado")]) == []
    assert posibles_duplicados(_payload(), [_existente(especie="perro")]) == []


def test_sin_telefono_no_hay_chequeo():
    payload = _payload(telefono=None)
    assert payload.telefono_contacto is None
    assert posibles_duplicados(payload, [_existente(telefono=None)]) == []
