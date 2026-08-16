"""Etiqueta y reglas de transición de una solicitud de adopción (AD-05).

Funciones puras: sin I/O, sin DB, sin FastAPI. **Cero imports fuera de
`datetime`** — es lo que permite recorrer la matriz entera de estados y acciones
sin levantar la app ni una base de datos, y lo que hace que el router pueda
quedarse delgado (ver `docs/conventions.md` §1).

Portado casi literal de `services/solicitudes.py` de la era Adopta
(`adopta-v1`), con tres cambios:

- La cuarta acción, **`aprobar`**, que allá no existía: el refugio solo podía
  agendar, pedir información o descartar. Es la que lleva la mascota hasta la
  franja de celebración de `/adoptar`.
- **`ORDEN_ACCIONES`**, porque `acciones_disponibles` viaja al frontend y el
  orden de los botones no puede depender del orden de iteración de un dict.
- Donde el original decía "refugio", aquí se dice **publicador**: una mascota
  cuelga de una organización de la red de apoyo **o** de un rescatista
  individual (ver `models/pet.py`), y los dos gestionan igual sus solicitudes.

⚠️ **Los estados persistidos son exactamente los de `ESTADOS_SOLICITUD`.**
`aprobar` y `descartar` son nombres de acción HTTP
(`POST /api/solicitudes/{id}/aprobar`), **nunca** valores de `Match.estado`:
llevan a `adoptado` y `cerrado` respectivamente (ADR 0002, nota de vigencia de
2026-08-15). Inventar un estado `"aprobado"` no rompería nada visible — la rama
de `solicitado` es el `else` de `calcular_etiqueta_solicitud`, así que ese
estado mostraría *"Sin responder · N días"* sobre una adopción ya cerrada. Lo
prohíbe `test_ningun_estado_persistido_cae_al_branch_de_solicitado`.

`calcular_etiqueta_solicitud(estado, creado_en, ahora=None)` mapea las 5 ramas de
`Match.estado` a un texto:

- `visita_agendada` -> "Visita agendada"
- `en_revision` -> "En revisión" (sin importar cuántos días lleve)
- `solicitado`, con menos de 2 días desde `creado_en` -> "Cuestionario nuevo"
- `solicitado`, con 2 días o más -> "Sin responder · N días" (N entero)
- `adoptado` -> "Adopción cerrada"
- `cerrado` -> "Solicitud cerrada"

Ninguna transición ocurre aquí ni en el router al calcular la etiqueta (ADR
0002): esto solo lee el estado para decidir qué texto mostrar.
`validar_transicion` decide si el llamador **puede** mutar; persistir es
responsabilidad del router.
"""

from datetime import datetime, timezone

#: Los cinco estados que de verdad se guardan en `matches.estado`.
ESTADOS_SOLICITUD: tuple[str, ...] = (
    "solicitado",
    "en_revision",
    "visita_agendada",
    "adoptado",
    "cerrado",
)

#: Motivo con el que se cierran las demás solicitudes cuando una se aprueba
#: (paso 3). Vive aquí, y no incrustado en el router, porque es copy de producto
#: —lo lee quien no se quedó con la mascota— y porque su test compara contra la
#: misma constante en vez de contra una cadena repetida.
MOTIVO_ADOPTADA_POR_OTRA = "La mascota fue adoptada por otra familia"


def calcular_etiqueta_solicitud(
    estado: str, creado_en: datetime, ahora: datetime | None = None
) -> str:
    if ahora is None:
        ahora = datetime.now(timezone.utc)

    if estado == "visita_agendada":
        return "Visita agendada"
    if estado == "adoptado":
        return "Adopción cerrada"
    if estado == "cerrado":
        return "Solicitud cerrada"
    if estado == "en_revision":
        return "En revisión"

    # "solicitado": depende de cuántos días lleva sin respuesta.
    # `creado_en` vuelve naive de la DB aunque se haya guardado con
    # `datetime.now(timezone.utc)`, y no solo en SQLite: la columna es
    # `timestamp without time zone` también en Postgres (ver
    # `migrations/AD-05-matches.sql`). Se normaliza antes de restar para evitar
    # `TypeError: can't subtract offset-naive and offset-aware datetimes`.
    if creado_en.tzinfo is None:
        creado_en = creado_en.replace(tzinfo=timezone.utc)

    dias = (ahora - creado_en).days
    if dias < 2:
        return "Cuestionario nuevo"
    return f"Sin responder · {dias} días"


class TransicionInvalidaError(Exception):
    """El publicador intentó una acción sobre una solicitud en un estado que no la permite."""


#: Copy de producto de cada acción y de cada estado, para el mensaje del 409.
#:
#: ⚠️ **Ese mensaje lo lee una persona**: viaja como `detail` del 409 y la
#: pantalla lo pinta tal cual en su aviso (`docs/conventions.md` §3). Hasta AD-06
#: decía *"No se puede 'pedir-informacion' una solicitud en estado 'adoptado'"* —
#: el slug de la ruta y el nombre de la columna, delante de quien solo pulsó un
#: botón. Los identificadores son de quien programa; el estado ya tiene copy en
#: `ETIQUETA_ESTADO_SOLICITUD` del frontend y estos son su equivalente aquí.
#:
#: Los dos diccionarios cubren `ORDEN_ACCIONES` y `ESTADOS_SOLICITUD` completos,
#: con un candado en `tests/api/test_solicitudes_service.py`: sin él, un estado
#: nuevo sin frase convertiría el 409 explicado en un 500 con traza.
ACCION_LEGIBLE: dict[str, str] = {
    "agendar-visita": "agendar una visita",
    "pedir-informacion": "pedir más información",
    "aprobar": "confirmar la adopción",
    "descartar": "cerrar esta solicitud",
}

ESTADO_LEGIBLE: dict[str, str] = {
    "solicitado": "todavía está esperando respuesta",
    "en_revision": "ya está en revisión",
    "visita_agendada": "ya tiene una visita agendada",
    "adoptado": "ya terminó con la adopción confirmada",
    "cerrado": "ya está cerrada",
}

#: Qué decir cuando el estado no está en el catálogo. No debería ocurrir nunca
#: —los cinco estados salen de un `Literal` y el candado los cubre—, pero un
#: `KeyError` aquí sería un 500 con traza en la cara de quien pulsó el botón, y
#: el caso de negocio (la acción no aplica) es cierto igual.
ESTADO_LEGIBLE_DESCONOCIDO = "ya no admite esta acción"


TRANSICIONES_VALIDAS: dict[str, set[str]] = {
    "agendar-visita": {"solicitado", "en_revision"},
    "pedir-informacion": {"solicitado"},
    "aprobar": {"solicitado", "en_revision", "visita_agendada"},
    "descartar": {"solicitado", "en_revision", "visita_agendada"},
}

#: El orden en que se ofrecen las acciones, de menos a más definitivo. Existe
#: aparte de `TRANSICIONES_VALIDAS` porque esa estructura es un dict y el orden
#: de los botones en pantalla no puede depender del orden de iteración de un
#: dict: un reordenamiento inocente del literal movería "Descartar" al primer
#: lugar. `test_orden_acciones_cubre_toda_la_matriz` exige que las dos digan
#: siempre las mismas acciones.
ORDEN_ACCIONES: tuple[str, ...] = (
    "agendar-visita",
    "pedir-informacion",
    "aprobar",
    "descartar",
)


def validar_transicion(estado_actual: str, accion: str) -> None:
    """Lanza `TransicionInvalidaError` si `accion` no es aplicable desde `estado_actual`.

    Los estados terminales (`adoptado`, `cerrado`) nunca aparecen en ninguno de
    los sets de `TRANSICIONES_VALIDAS`, así que cualquier acción sobre una
    solicitud en esos estados siempre lanza — no hace falta un caso especial.
    """
    if estado_actual not in TRANSICIONES_VALIDAS[accion]:
        estado = ESTADO_LEGIBLE.get(estado_actual, ESTADO_LEGIBLE_DESCONOCIDO)
        raise TransicionInvalidaError(
            f"Ya no puedes {ACCION_LEGIBLE[accion]}: esta solicitud {estado}. "
            "Actualiza la página para verla como está ahora."
        )


def acciones_disponibles(estado: str, es_publicador: bool) -> list[str]:
    """Las acciones que quien consulta puede ejecutar ahora mismo, ya ordenadas.

    Lo calcula el backend a propósito: en `adopta-v1` la pantalla de detalle
    reimplementaba la matriz de transiciones a mano, y dos fuentes de verdad que
    se separan dejan la UI mintiendo — botones que se pintan y responden 409.

    Para el adoptante es **siempre `[]`**: el match no es mutuo (ADR 0002) y
    quien publicó es el único que decide. Sin este corte, el detalle le pintaría
    al adoptante un botón "Aprobar" sobre su propia solicitud.
    """
    if not es_publicador:
        return []
    return [accion for accion in ORDEN_ACCIONES if estado in TRANSICIONES_VALIDAS[accion]]
