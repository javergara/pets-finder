"""Páginas HTML para bots de redes (feature 21, ADR 0009): og tags por reporte y,
desde AD-08, por mascota en adopción.

⚠️ `Pet` se importa a nivel de módulo a propósito (mismo motivo que en
`test_pets.py`): el fixture `db_session` hace `create_all` con lo que esté
registrado en `Base.metadata` en ese instante, y un import perezoso produce un
`no such table: pets` intermitente según el orden de colección de pytest.
"""

from datetime import date

import pytest

from reencuentro_api.models.pet import Pet
from reencuentro_api.models.report import Report
from reencuentro_api.models.user import User


@pytest.fixture()
def reporte(db_session):
    user = User(nombre="Ana", email="ana@example.co", ciudad="Armenia")
    db_session.add(user)
    db_session.commit()
    r = Report(
        user_id=user.id,
        tipo="perdido",
        especie="perro",
        nombre_mascota="Rocky",
        descripcion='Criollo color miel con collar rojo & pañoleta "verde".',
        foto_url="/media/uploads/abc.jpg",
        zona="Armenia",
        lat=4.54,
        lng=-75.68,
        fecha_evento=date(2026, 8, 10),
        telefono_contacto="3001234567",
    )
    db_session.add(r)
    db_session.commit()
    return r


def test_pagina_de_reporte_lleva_los_og_tags(client, reporte):
    respuesta = client.get(f"/reporte/{reporte.id}")

    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"].startswith("text/html")
    html = respuesta.text
    assert '<meta property="og:title" content="Rocky — Se perdió en Armenia">' in html
    assert 'og:site_name" content="Pet Finder Col"' in html
    # La foto relativa se vuelve absoluta con el dominio del sitio.
    assert (
        '<meta property="og:image" content="https://petfinder-col.com/media/uploads/abc.jpg">'
        in html
    )
    assert (
        '<meta property="og:url" content="https://petfinder-col.com/reporte/'
        f'{reporte.id}">' in html
    )
    # La descripción con caracteres especiales queda escapada, no rompe el HTML.
    assert "&amp;" in html and "&quot;verde&quot;" in html


def test_pagina_sin_foto_omite_og_image(client, db_session, reporte):
    reporte.foto_url = None
    db_session.commit()

    html = client.get(f"/reporte/{reporte.id}").text

    assert "og:image" not in html
    assert 'og:title" content="Rocky' in html


def test_pagina_con_foto_absoluta_la_usa_tal_cual(client, db_session, reporte):
    reporte.foto_url = "https://cdn.example.com/foto.jpg"
    db_session.commit()

    html = client.get(f"/reporte/{reporte.id}").text

    assert '<meta property="og:image" content="https://cdn.example.com/foto.jpg">' in html


def test_pagina_con_foto_del_bucket_la_sirve_via_fotos_del_dominio(client, db_session, reporte):
    """Feature 49: la og:image del bucket propio sale por {sitio}/fotos/{nombre}
    (el proxy con caché de vercel.json), no por la URL directa de Supabase — el
    rastreador de WhatsApp descarga la imagen en CADA compartida y era egress
    del bucket. Una URL absoluta ajena (test anterior) sigue pasando intacta."""
    reporte.foto_url = "https://abc123.supabase.co/storage/v1/object/public/fotos/abc123.jpg"
    db_session.commit()

    html = client.get(f"/reporte/{reporte.id}").text

    assert (
        '<meta property="og:image" content="https://petfinder-col.com/fotos/abc123.jpg">' in html
    )


def test_pagina_de_reporte_inexistente_devuelve_404(client, db_session):
    assert client.get("/reporte/999").status_code == 404


# ── Mascotas en adopción (AD-08 paso 2) ──────────────────────────────────────
# Misma página, otro contenido. Lo que estos casos protegen, por orden de
# gravedad: (1) que el og:title no mienta sobre el estado de la mascota, (2) que
# el texto de usuario vaya escapado —es HTML que servimos a terceros—, y (3) que
# la foto se absolutice, porque una relativa no la resuelve ningún rastreador.


@pytest.fixture()
def mascota(db_session):
    user = User(nombre="Ana", email="ana-pets@example.co", ciudad="Armenia")
    db_session.add(user)
    db_session.commit()
    pet = Pet(
        user_id=user.id,
        nombre="Canela",
        especie="perro",
        raza="Cocker mestiza",
        sexo="hembra",
        edad_meses=18,
        tamano="mediano",
        energia="media",
        fotos=["/media/uploads/canela.jpg"],
        historia='Rescatada tras el sismo con collar rojo & pañoleta "verde".',
        zona="Armenia",
        telefono_contacto="3001234567",
    )
    db_session.add(pet)
    db_session.commit()
    return pet


def test_pagina_de_mascota_lleva_los_og_tags(client, mascota):
    respuesta = client.get(f"/adoptar/mascota/{mascota.id}")

    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"].startswith("text/html")
    html = respuesta.text
    assert '<meta property="og:title" content="Canela — En adopción en Armenia">' in html
    assert 'og:site_name" content="Pet Finder Col"' in html
    assert 'og:description" content="Rescatada tras el sismo' in html
    assert (
        '<meta property="og:url" content="https://petfinder-col.com/adoptar/mascota/'
        f'{mascota.id}">' in html
    )


def test_pagina_de_mascota_absolutiza_la_primera_foto(client, mascota):
    html = client.get(f"/adoptar/mascota/{mascota.id}").text

    assert (
        '<meta property="og:image" content="https://petfinder-col.com/media/uploads/canela.jpg">'
        in html
    )


def test_pagina_de_mascota_con_foto_absoluta_la_usa_tal_cual(client, db_session, mascota):
    """Las fotos de producción viven en Supabase Storage y llegan absolutas; las
    del seed y las locales llegan relativas. La misma regla que en el reporte."""
    mascota.fotos = ["https://cdn.example.com/canela.jpg"]
    db_session.commit()

    html = client.get(f"/adoptar/mascota/{mascota.id}").text

    assert '<meta property="og:image" content="https://cdn.example.com/canela.jpg">' in html


def test_pagina_de_mascota_con_foto_del_bucket_usa_el_proxy_fotos(client, db_session, mascota):
    """La misma regla de la feature 49 que en el reporte: `_absoluta` es común."""
    mascota.fotos = ["https://abc123.supabase.co/storage/v1/object/public/fotos/canela.jpg"]
    db_session.commit()

    html = client.get(f"/adoptar/mascota/{mascota.id}").text

    assert (
        '<meta property="og:image" content="https://petfinder-col.com/fotos/canela.jpg">' in html
    )


def test_pagina_de_mascota_sin_fotos_omite_og_image(client, db_session, mascota):
    """Una mascota puede publicarse sin fotos: `og:image` vacío pinta un hueco
    roto en WhatsApp, así que la etiqueta directamente no va."""
    mascota.fotos = []
    db_session.commit()

    html = client.get(f"/adoptar/mascota/{mascota.id}").text

    assert "og:image" not in html
    assert 'og:title" content="Canela' in html


def test_pagina_de_mascota_en_zona_otro_usa_la_ciudad_escrita(client, db_session, mascota):
    mascota.zona = "Otro"
    mascota.ciudad_texto = "Calarcá"
    db_session.commit()

    html = client.get(f"/adoptar/mascota/{mascota.id}").text

    assert 'og:title" content="Canela — En adopción en Calarcá"' in html


def test_pagina_de_mascota_sin_nombre_usa_el_titulo_compuesto(client, db_session, mascota):
    mascota.nombre = "  "
    db_session.commit()

    html = client.get(f"/adoptar/mascota/{mascota.id}").text

    assert 'og:title" content="Perro mediano cocker mestiza — En adopción en Armenia"' in html


def test_el_og_title_no_miente_sobre_el_estado(client, db_session, mascota):
    """Compartir una mascota ya adoptada diciendo "En adopción" manda gente a
    escribir por una mascota que ya tiene hogar. `en_proceso` sí se comparte como
    "En adopción" a propósito: es un matiz interno del publicador."""
    for estado, esperado in (
        ("disponible", "En adopción"),
        ("en_proceso", "En adopción"),
        ("adoptado", "Ya tiene hogar"),
    ):
        mascota.estado = estado
        db_session.commit()

        html = client.get(f"/adoptar/mascota/{mascota.id}").text

        assert f'og:title" content="Canela — {esperado} en Armenia"' in html


def test_el_texto_de_usuario_va_escapado(client, db_session, mascota):
    """El nombre y la historia los escribe quien publica: sin escapar, un `"`
    cierra el atributo y un `<` abre una etiqueta en el HTML que servimos."""
    mascota.nombre = 'Canela & "la <flaca>"'
    mascota.historia = 'Vivía en la calle & la cuidó "doña <Ana>".'
    db_session.commit()

    html = client.get(f"/adoptar/mascota/{mascota.id}").text

    assert 'og:title" content="Canela &amp; &quot;la &lt;flaca&gt;&quot; — En adopción' in html
    assert "og:description" in html and "&amp; la cuidó &quot;doña &lt;Ana&gt;&quot;" in html
    # Lo que nunca puede pasar: el texto crudo llegando al HTML.
    assert "<flaca>" not in html and "<Ana>" not in html


def test_pagina_de_mascota_inexistente_devuelve_404(client, db_session):
    """El 404 se asevera por el mensaje, no solo por el status: una ruta que ni
    siquiera existe también responde 404, así que sin esto el caso estaría verde
    con el endpoint sin escribir."""
    respuesta = client.get("/adoptar/mascota/999")

    assert respuesta.status_code == 404
    assert respuesta.json()["detail"] == "La mascota 999 no existe"
