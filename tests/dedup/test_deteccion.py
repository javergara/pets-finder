"""Detección de duplicados: llave por teléfono (persona), discriminación por nombre."""

from dedup.deteccion import (
    aporta_informacion,
    clave_telefono,
    clusters_duplicados,
    plan_curacion,
    posibles_duplicados,
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


def test_plan_canonico_prefiere_manual_y_solo_cura_copias_crawl_propias():
    desc = "Descripción equivalente en todos."
    reportes = [
        _rep(id=194, nombre="Mila", fuente="crawl", user_id=49, descripcion=desc),
        _rep(id=26, nombre="Mila", descripcion=desc),  # manual → canónico
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
    assert all(s["accion"] == "revisión humana" for s in plan[0]["sobrantes"])


def test_cluster_posible_nunca_es_eliminable():
    """Sin nombre no hay certeza: aunque sean copias crawl propias, a revisión."""
    reportes = [
        _rep(id=1, tipo="encontrado", nombre=None, fuente="crawl", user_id=49),
        _rep(id=2, tipo="encontrado", nombre=None, fuente="crawl", user_id=49),
    ]
    plan = plan_curacion(clusters_duplicados(reportes), user_id_crawler=49)
    assert plan[0]["nivel"] == "posible"
    assert all(s["accion"] == "revisión humana" for s in plan[0]["sobrantes"])


def test_pares_fusionables_exige_juez_confiado_y_par_crawl_propio():
    from dedup.deteccion import pares_fusionables

    por_id = {
        10: _rep(id=10, fuente="crawl", user_id=49, tipo="encontrado"),
        11: _rep(id=11, fuente="crawl", user_id=49, tipo="encontrado"),
        26: _rep(id=26),  # manual
    }
    fusion = {"descripcion": "Señas combinadas.", "nombre_mascota": "Rex"}
    plan = [
        {  # par crawl-crawl con juez confiado → fusionable (y sin nombre: es encontrado)
            "canonico": 10,
            "sobrantes": [
                {
                    "id": 11,
                    "accion": "revisión humana",
                    "juez": {"mismo_caso": True, "confianza": 0.9, "fusion": fusion},
                }
            ],
        },
        {  # canónico manual → nunca se aplica, queda como sugerencia
            "canonico": 26,
            "sobrantes": [
                {
                    "id": 11,
                    "accion": "revisión humana",
                    "juez": {"mismo_caso": True, "confianza": 0.95, "fusion": fusion},
                }
            ],
        },
        {  # confianza baja → fuera
            "canonico": 10,
            "sobrantes": [
                {
                    "id": 11,
                    "accion": "revisión humana",
                    "juez": {"mismo_caso": True, "confianza": 0.5, "fusion": fusion},
                }
            ],
        },
    ]
    pares = pares_fusionables(plan, por_id, user_id_crawler=49)
    assert len(pares) == 1
    assert pares[0]["canonico"] == 10
    assert "nombre_mascota" not in pares[0]["fusion"]  # encontrado no lleva nombre
    assert pares[0]["fusion"]["descripcion"] == "Señas combinadas."
