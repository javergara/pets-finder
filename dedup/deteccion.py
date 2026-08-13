"""Núcleo de detección de duplicados: funciones puras sobre dicts de la API.

El teléfono identifica a la PERSONA, no al caso — una familia pierde varias
mascotas y un rescatista encuentra muchas. Por eso es llave de candidatos,
nunca veredicto: tipo+especie acotan y el nombre discrimina (dos nombres
distintos con el mismo teléfono son dos mascotas del mismo dueño). Nada de
aquí decide borrar: la detección produce hallazgos para revisión humana.
"""

import re
import unicodedata
from typing import Any

Reporte = dict[str, Any]


def normalizar_texto(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFD", texto)
    sin_tildes = "".join(c for c in sin_tildes if unicodedata.category(c) != "Mn")
    return sin_tildes.strip().lower()


def clave_telefono(telefono: str | None) -> str | None:
    """Últimos 10 dígitos: '573001234567' y '3001234567' son el mismo número."""
    if not telefono:
        return None
    digitos = re.sub(r"\D", "", telefono)
    return digitos[-10:] if len(digitos) >= 10 else (digitos or None)


def _nombre(reporte: Reporte) -> str | None:
    nombre = reporte.get("nombre_mascota")
    return normalizar_texto(nombre) if nombre else None


def posibles_duplicados(nuevo: Reporte, existentes: list[Reporte]) -> list[dict[str, Any]]:
    """Hallazgos de un reporte candidato contra un corpus (chequeo de publish).

    Niveles: 'casi seguro' (tel+tipo+especie+nombre) y 'posible' (sin nombre
    para distinguir). Nombres distintos con el mismo teléfono → no es duplicado.
    """
    tel = clave_telefono(nuevo.get("telefono_contacto"))
    if tel is None:
        return []
    hallazgos: list[dict[str, Any]] = []
    nombre_nuevo = _nombre(nuevo)
    for existente in existentes:
        if clave_telefono(existente.get("telefono_contacto")) != tel:
            continue
        if existente.get("tipo") != nuevo.get("tipo"):
            continue
        if existente.get("especie") != nuevo.get("especie"):
            continue
        nombre_existente = _nombre(existente)
        if nombre_nuevo and nombre_existente:
            if nombre_nuevo != nombre_existente:
                continue  # mismo dueño, otra mascota (caso Iru y Nala)
            nivel, razon = "casi seguro", "mismo teléfono, tipo, especie y nombre"
        else:
            nivel, razon = "posible", "mismo teléfono, tipo y especie; sin nombre para distinguir"
        hallazgos.append({"id": existente.get("id"), "nivel": nivel, "razon": razon})
    return hallazgos


def clusters_duplicados(reportes: list[Reporte]) -> list[dict[str, Any]]:
    """Agrupa un corpus completo en clusters de posibles duplicados del MISMO caso.

    Cluster = mismo teléfono + tipo + especie, partido por nombre: los reportes
    con el mismo nombre forman un cluster 'casi seguro'; los sin nombre se
    agrupan aparte como 'posible' (pueden ser cualquiera de las mascotas de esa
    persona). Solo se emiten clusters con 2+ reportes.
    """
    por_caso: dict[tuple, list[Reporte]] = {}
    for r in reportes:
        tel = clave_telefono(r.get("telefono_contacto"))
        if tel is None:
            continue
        llave = (tel, r.get("tipo"), r.get("especie"), _nombre(r))
        por_caso.setdefault(llave, []).append(r)

    clusters = []
    for (tel, tipo, especie, nombre), grupo in sorted(por_caso.items()):
        if len(grupo) < 2:
            continue
        clusters.append(
            {
                "telefono": tel,
                "tipo": tipo,
                "especie": especie,
                "nombre": nombre,
                "nivel": "casi seguro" if nombre else "posible",
                "reportes": sorted(grupo, key=_orden_canonico),
            }
        )
    return clusters


def _orden_canonico(reporte: Reporte) -> tuple:
    """El canónico de un cluster: primero el manual (lo escribió la familia,
    con su pin y su foto), y a igual fuente el más antiguo."""
    return (0 if reporte.get("fuente") == "manual" else 1, reporte.get("id") or 0)


def aporta_informacion(canonico: Reporte, sobrante: Reporte) -> list[str]:
    """Qué tiene el sobrante que el canónico no — borrar sería perderlo.

    Borrar un duplicado no es gratis: la copia crawleada suele traer la
    descripción del post (señas que la familia no escribió), y puede tener
    foto o características que al canónico le faltan. La fusión real es una
    feature de producto (enlazar, no borrar); mientras no exista, cualquier
    aporte degrada el sobrante a revisión humana."""
    razones = [
        campo
        for campo in ("foto_url", "raza", "color", "tamano", "barrio")
        if sobrante.get(campo) and not canonico.get(campo)
    ]
    if len(sobrante.get("descripcion") or "") > 1.5 * len(canonico.get("descripcion") or ""):
        razones.append("descripción más completa")
    return razones


def plan_curacion(clusters: list[dict[str, Any]], user_id_crawler: int | None) -> list[dict]:
    """Sugerencia conservadora por cluster: conservar el canónico; un sobrante
    solo es auto-curable si es copia crawl del usuario del crawler (lo único
    que sus herramientas de autor pueden eliminar), el nivel es 'casi seguro'
    Y no aporta información que el canónico no tenga. Los duplicados manuales
    requieren a su autor o una feature de moderación de la app."""
    plan = []
    for c in clusters:
        canonico, *sobrantes = c["reportes"]
        acciones = []
        for s in sobrantes:
            es_crawl_propio = s.get("fuente") == "crawl" and s.get("user_id") == user_id_crawler
            aporte = aporta_informacion(canonico, s)
            if es_crawl_propio and c["nivel"] == "casi seguro" and not aporte:
                accion = "eliminable (copia crawl propia)"
            elif aporte:
                accion = f"revisión humana (aporta: {', '.join(aporte)})"
            else:
                accion = "revisión humana"
            acciones.append({"id": s["id"], "accion": accion})
        plan.append({**c, "canonico": canonico["id"], "sobrantes": acciones})
    return plan
