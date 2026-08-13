"""Detección de duplicados: llave por teléfono (persona), discriminación por nombre."""

from dedup.deteccion import (
    aporta_informacion,
    clave_telefono,
    clusters_duplicados,
    fusiones_por_canonico,
    marcar_conflictos_hermanos,
    plan_curacion,
    posibles_duplicados,
    relleno_determinista,
)


def _rep(id=1, telefono="3001234567", tipo="perdido", especie="gato", nombre=None, **extra):
    return {
        "id": id,
        "telefono_contacto": telefono,
        "tipo": tipo,
        "especie": especie,
        "nombre_mascota": nombre,
        "fuente": extra.pop("fuente", "manual"),
        "user_id": extra.pop("user_id", 1),
        **extra,
    }


def test_mismo_nombre_es_casi_seguro_y_normaliza_telefono_y_nombre():
    """'Whiskey' publicado en dos páginas: mismo caso aunque el número traiga
    el 57 y el nombre venga en mayúsculas."""
    dups = posibles_duplicados(
        _rep(nombre="WHISKEY", telefono="+57 300 123 4567"),
        [_rep(id=24, nombre="whiskey")],
    )
    assert dups == [
        {"id": 24, "nivel": "casi seguro", "razon": "mismo teléfono, tipo, especie y nombre"}
    ]


def test_nombres_distintos_no_es_duplicado():
    """Caso Iru y Nala: misma persona, misma especie, dos mascotas reales."""
    assert posibles_duplicados(_rep(nombre="Iru"), [_rep(nombre="Nala")]) == []


def test_sin_nombre_para_distinguir_es_posible():
    dups = posibles_duplicados(
        _rep(tipo="encontrado", nombre=None),
        [_rep(id=30, tipo="encontrado", nombre=None)],
    )
    assert dups[0]["nivel"] == "posible"


def test_tipo_o_especie_distintos_no_son_candidatos():
    assert posibles_duplicados(_rep(), [_rep(tipo="encontrado")]) == []
    assert posibles_duplicados(_rep(), [_rep(especie="perro")]) == []


def test_sin_telefono_no_hay_chequeo():
    assert clave_telefono(None) is None
    assert posibles_duplicados(_rep(telefono=None), [_rep(telefono=None)]) == []


def test_clusters_agrupa_por_caso_y_exige_dos_o_mas():
    reportes = [
        _rep(id=26, nombre="Mila"),
        _rep(id=61, nombre="mila"),  # duplicado manual-manual
        _rep(id=194, nombre="Mila", fuente="crawl", user_id=49),
        _rep(id=99, nombre="Rocky"),  # solo, no forma cluster
        _rep(id=44, nombre="Luna", telefono="3009999999"),  # otro teléfono
    ]
    clusters = clusters_duplicados(reportes)
    assert len(clusters) == 1
    assert clusters[0]["nombre"] == "mila"
    assert [r["id"] for r in clusters[0]["reportes"]] == [26, 61, 194]
    assert clusters[0]["nivel"] == "casi seguro"


def test_canonico_es_el_primero_creado_sin_importar_origen():
    """Regla del operador: cronología sobre procedencia — un crawl creado
    antes que el manual es el canónico."""
    reportes = [
        _rep(id=200, nombre="Mila", fuente="crawl", user_id=49, creado_en="2026-08-11T08:00:00"),
        _rep(id=26, nombre="Mila", creado_en="2026-08-12T10:00:00"),
    ]
    clusters = clusters_duplicados(reportes)
    assert [r["id"] for r in clusters[0]["reportes"]] == [200, 26]


def test_aporta_informacion_detecta_perdidas():
    canonico = _rep(id=1, descripcion="Mancha en la cara. Collar naranja", foto_url="a.jpg")
    sobrante = _rep(
        id=2,
        color="Bicolor (manchas)",
        descripcion="Gato blanco con manchas negras: mancha sobre el ojo izquierdo y frente.",
        foto_url="b.jpg",
    )
    assert aporta_informacion(canonico, sobrante) == ["color", "descripción más completa"]
    # Sin aporte (todo lo del sobrante ya está en el canónico) → lista vacía.
    assert aporta_informacion(sobrante, canonico) == []


def test_sobrante_que_aporta_nunca_es_eliminable():
    """El caso real de prod: la copia crawl describe mejor a la mascota."""
    reportes = [
        _rep(id=24, nombre="Whiskey", descripcion="Mancha en la cara.", foto_url="a.jpg"),
        _rep(
            id=136,
            nombre="Whiskey",
            fuente="crawl",
            user_id=49,
            foto_url="b.jpg",
            descripcion="Gato blanco, mancha negra sobre el ojo izquierdo y la frente.",
        ),
    ]
    plan = plan_curacion(clusters_duplicados(reportes), user_id_crawler=49)
    assert plan[0]["sobrantes"][0]["accion"] == "revisión humana (aporta: descripción más completa)"


def test_plan_canonico_y_solo_cura_copias_crawl_propias():
    desc = "Descripción equivalente en todos."
    reportes = [
        _rep(id=194, nombre="Mila", fuente="crawl", user_id=49, descripcion=desc),
        _rep(id=26, nombre="Mila", descripcion=desc),  # más antiguo (id menor) → canónico
        _rep(id=61, nombre="Mila", descripcion=desc),  # manual duplicado → revisión, nunca auto
    ]
    plan = plan_curacion(clusters_duplicados(reportes), user_id_crawler=49)
    assert plan[0]["canonico"] == 26
    acciones = {s["id"]: s["accion"] for s in plan[0]["sobrantes"]}
    assert acciones[194] == "eliminable (copia crawl propia)"
    assert acciones[61] == "revisión humana"


def test_plan_sin_usuario_crawler_todo_es_revision():
    reportes = [_rep(id=1, nombre="Mila"), _rep(id=2, nombre="Mila", fuente="crawl", user_id=49)]
    plan = plan_curacion(clusters_duplicados(reportes), user_id_crawler=None)
    assert all(s["accion"].startswith("revisión") for s in plan[0]["sobrantes"])


def test_cluster_posible_nunca_es_eliminable():
    """Sin nombre no hay certeza: aunque sean copias crawl propias, a revisión."""
    reportes = [
        _rep(id=1, tipo="encontrado", nombre=None, fuente="crawl", user_id=49),
        _rep(id=2, tipo="encontrado", nombre=None, fuente="crawl", user_id=49),
    ]
    plan = plan_curacion(clusters_duplicados(reportes), user_id_crawler=49)
    assert plan[0]["nivel"] == "posible"
    assert all(s["accion"].startswith("revisión") for s in plan[0]["sobrantes"])


def test_relleno_determinista_solo_llena_vacios():
    canonico = _rep(id=24, nombre="Whiskey", tipo="perdido")
    sobrantes = [
        _rep(id=136, color="Bicolor (manchas)", nombre="Whiskey"),
        _rep(id=140, color="Negro", tamano="mediano"),  # color llega tarde: gana el primero
    ]
    cambios = relleno_determinista(canonico, sobrantes)
    assert cambios == {"color": "Bicolor (manchas)", "tamano": "mediano"}


def test_relleno_no_pone_nombre_en_encontrados():
    canonico = _rep(id=30, tipo="encontrado", nombre=None)
    cambios = relleno_determinista(canonico, [_rep(id=31, nombre="Rex")])
    assert "nombre_mascota" not in cambios


def _sobrante_juzgado(id, conf=0.95, conflicto=False):
    juez = {"mismo_caso": True, "confianza": conf}
    if conflicto:
        juez["conflicto_hermanos"] = True
    return {"id": id, "accion": "revisión humana", "juez": juez}


def test_fusiones_por_canonico_agrupa_todos_los_sobrantes():
    """Varios sobrantes del mismo canónico → UN grupo (un solo PUT), no N."""
    por_id = {
        37: _rep(id=37, user_id=7, tipo="encontrado"),
        83: _rep(id=83, fuente="crawl", user_id=49, tipo="encontrado"),
        84: _rep(id=84, fuente="crawl", user_id=49, tipo="encontrado"),
    }
    plan = [{"canonico": 37, "sobrantes": [_sobrante_juzgado(83), _sobrante_juzgado(84)]}]
    grupos = fusiones_por_canonico(plan, por_id, user_id_crawler=49, incluir_manuales=True)
    assert len(grupos) == 1
    assert [s["id"] for s in grupos[0]["sobrantes"]] == [83, 84]
    assert grupos[0]["user_id_editor"] == 7  # edita como el autor del canónico


def test_fusiones_respeta_banderas_confianza_y_conflictos():
    por_id = {
        10: _rep(id=10, fuente="crawl", user_id=49, tipo="encontrado"),
        11: _rep(id=11, fuente="crawl", user_id=49, tipo="encontrado"),
        26: _rep(id=26),  # manual
    }
    # Par crawl propio: entra sin bandera.
    plan = [{"canonico": 10, "sobrantes": [_sobrante_juzgado(11)]}]
    assert len(fusiones_por_canonico(plan, por_id, user_id_crawler=49)) == 1
    # Canónico manual sin bandera: fuera.
    plan = [{"canonico": 26, "sobrantes": [_sobrante_juzgado(11)]}]
    assert fusiones_por_canonico(plan, por_id, user_id_crawler=49) == []
    # Confianza baja o conflicto de hermanos: fuera aunque haya bandera.
    plan = [{"canonico": 26, "sobrantes": [_sobrante_juzgado(11, conf=0.5)]}]
    assert fusiones_por_canonico(plan, por_id, 49, incluir_manuales=True) == []
    plan = [{"canonico": 26, "sobrantes": [_sobrante_juzgado(11, conflicto=True)]}]
    assert fusiones_por_canonico(plan, por_id, 49, incluir_manuales=True) == []


def test_hermanos_del_mismo_post_no_pueden_ser_ambos_el_mismo_caso():
    por_id = {
        37: _rep(id=37, user_id=7, tipo="encontrado"),
        83: _rep(
            id=83,
            fuente="crawl",
            user_id=49,
            tipo="encontrado",
            idempotency_id="drive:post-A#0",
        ),
        84: _rep(
            id=84,
            fuente="crawl",
            user_id=49,
            tipo="encontrado",
            idempotency_id="drive:post-B#1",
        ),
        85: _rep(
            id=85,
            fuente="crawl",
            user_id=49,
            tipo="encontrado",
            idempotency_id="drive:post-B#2",
        ),
    }
    plan = [
        {
            "canonico": 37,
            "sobrantes": [
                _sobrante_juzgado(83, 0.99),
                _sobrante_juzgado(84, 0.90),
                _sobrante_juzgado(85, 0.82),
            ],
        }
    ]

    marcar_conflictos_hermanos(plan, por_id)

    # 84 y 85 son hermanos (mismo post B) reclamando el mismo canónico → conflicto ambos.
    marcas = {s["id"]: s["juez"].get("conflicto_hermanos") for s in plan[0]["sobrantes"]}
    assert marcas == {83: None, 84: True, 85: True}
    # La fusión solo procede para el veredicto sin conflicto (#83).
    grupos = fusiones_por_canonico(plan, por_id, user_id_crawler=49, incluir_manuales=True)
    assert [s["id"] for s in grupos[0]["sobrantes"]] == [83]
