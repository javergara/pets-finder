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
    """El canónico de un cluster es el PRIMERO en ser creado, sin importar su
    origen (decisión del operador): el registro más antiguo es el caso
    original — conserva su id, sus links compartidos y sus avistamientos; los
    posteriores son re-reportes que se fusionan hacia él."""
    return (reporte.get("creado_en") or "", reporte.get("id") or 0)


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


def relleno_determinista(canonico: Reporte, sobrantes: list[Reporte]) -> dict[str, Any]:
    """Campos de catálogo que al canónico le faltan, tomados del primer
    sobrante que los traiga — valores que ya existían en reportes, nunca del
    LLM. Lo que el canónico ya tiene no se toca."""
    cambios: dict[str, Any] = {}
    for campo in ("raza", "color", "tamano", "barrio", "nombre_mascota"):
        if canonico.get(campo):
            continue
        for sobrante in sobrantes:
            if sobrante.get(campo):
                cambios[campo] = sobrante[campo]
                break
    if canonico.get("tipo") == "encontrado":
        cambios.pop("nombre_mascota", None)
    return cambios


def clave_post_de(reporte: Reporte) -> str | None:
    """El post de origen de un reporte crawleado: idempotency `<clave>#<i>`."""
    idem = reporte.get("idempotency_id") or ""
    return idem.rsplit("#", 1)[0] if "#" in idem else None


def marcar_conflictos_hermanos(plan: list[dict[str, Any]], por_id: dict[int, Reporte]) -> None:
    """Consistencia que el juzgado par-por-par no ve: dos HERMANOS del mismo
    post son animales distintos por construcción — no pueden ser ambos 'mismo
    caso' que un canónico. Si un grupo de hermanos reclama dos o más veces al
    mismo canónico, el juez se confundió con ese post (típico: foto grupal
    compartida): TODO el grupo se marca en conflicto y vuelve a revisión
    humana; la fusión queda solo para veredictos sin conflicto."""
    for c in plan:
        reclamos_por_post: dict[str, list[dict]] = {}
        for s in c["sobrantes"]:
            veredicto = s.get("juez") or {}
            if not veredicto.get("mismo_caso"):
                continue
            clave = clave_post_de(por_id.get(s["id"], {}))
            if clave:
                reclamos_por_post.setdefault(clave, []).append(s)
        for hermanos in reclamos_por_post.values():
            if len(hermanos) > 1:
                for s in hermanos:
                    s["juez"]["conflicto_hermanos"] = True


def fusiones_por_canonico(
    plan: list[dict[str, Any]],
    por_id: dict[int, Reporte],
    user_id_crawler: int | None,
    umbral: float = 0.8,
    incluir_manuales: bool = False,
) -> list[dict[str, Any]]:
    """Grupos de fusión a nivel de CLUSTER: un canónico absorbe TODOS sus
    sobrantes confirmados de una vez.

    Par por par la fusión se pisa a sí misma (cada PUT recalculado contra el
    canónico original borra el append anterior) y apila N bloques repetidos —
    por eso aquí: un grupo por canónico, una síntesis, un solo PUT.

    Gates por sobrante: juez 'mismo caso' con confianza >= umbral y sin
    conflicto de hermanos. El canónico es el primero en ser creado, sin
    importar el origen. Cualquier reporte ajeno involucrado exige
    incluir_manuales=True (se edita/borra vía el user_id de su autor: modelo
    de confianza del MVP — correr con el ok del dueño de la plataforma)."""

    def _crawl_propio(reporte: Reporte) -> bool:
        return reporte.get("fuente") == "crawl" and reporte.get("user_id") == user_id_crawler

    grupos = []
    for c in plan:
        canonico = por_id.get(c["canonico"])
        if not canonico:
            continue
        elegidos = []
        for s in c["sobrantes"]:
            veredicto = s.get("juez") or {}
            if not veredicto.get("mismo_caso") or veredicto.get("conflicto_hermanos"):
                continue
            if float(veredicto.get("confianza", 0.0)) < umbral:
                continue
            sobrante = por_id.get(s["id"])
            if not sobrante:
                continue
            if not incluir_manuales and not (_crawl_propio(canonico) and _crawl_propio(sobrante)):
                continue
            elegidos.append(sobrante)
        if elegidos:
            grupos.append(
                {
                    "canonico": canonico,
                    "sobrantes": elegidos,
                    "propio": _crawl_propio(canonico),
                    "user_id_editor": canonico.get("user_id"),
                }
            )
    return grupos
