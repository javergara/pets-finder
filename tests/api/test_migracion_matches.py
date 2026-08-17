"""Anti-drift entre el modelo `Match` y el SQL que se ejecuta en producción.

Mismo hueco que cierran `test_migracion_pets.py` y `test_migracion_swipes.py`: en
prod corre `SKIP_DB_CREATE_ALL=1`, así que el esquema **no** sale de los modelos,
lo escribe a mano alguien en el SQL Editor de Supabase. Si el modelo gana una
columna, si el `unique` no se transcribe o si un `not null` se cuela donde el
modelo admite nulos, dev y prod divergen **en silencio** — los tests siguen
verdes sobre SQLite y en Postgres el invariante no existe (o de más, que aquí es
peor: un `not null` sobrando en `mensaje` haría fallar cada swipe-derecha sin
mensaje).

⚠️ `AD-05-matches.sql` está **escrito, no ejecutado**, y su orden de despliegue
es **después** de `AD-03-swipes.sql` y `AD-03-home-profiles.sql`, que también
siguen sin ejecutar: el swipe-derecha crea la fila de `matches` en el mismo
request que la de `swipes`.

⚠️ `Match` se importa a nivel de módulo (ver la cabecera de `test_pets.py`): un
import perezoso deja la tabla fuera de `Base.metadata` en otros tests.
"""

import re

import pytest
from soporte_migraciones import MIGRACIONES_DIR, columnas_del_sql, definiciones_de_columna
from sqlalchemy import UniqueConstraint

from reencuentro_api.models.match import Match

SQL_MATCHES = MIGRACIONES_DIR / "AD-05-matches.sql"


@pytest.fixture(scope="module")
def sql_matches() -> str:
    assert SQL_MATCHES.exists(), f"Falta la migración versionada {SQL_MATCHES}"
    return SQL_MATCHES.read_text(encoding="utf-8")


def _columnas_del_unique(sql: str, nombre: str) -> list[str]:
    """Las columnas del `constraint <nombre> unique (a, b)` tal como están."""
    encontrado = re.search(rf"constraint\s+{nombre}\s+unique\s*\(([^)]*)\)", sql, re.IGNORECASE)
    assert encontrado, f"El .sql no declara el constraint {nombre}"
    return [columna.strip().strip('"') for columna in encontrado.group(1).split(",")]


def _unique_del_modelo(modelo, nombre: str) -> list[str]:
    for constraint in modelo.__table__.constraints:
        if isinstance(constraint, UniqueConstraint) and constraint.name == nombre:
            return [columna.name for columna in constraint.columns]
    raise AssertionError(f"El modelo {modelo.__name__} no declara el constraint {nombre}")


# --- Columnas: el modelo y el .sql dicen lo mismo ------------------------------


def test_columnas_del_sql_son_exactamente_las_del_modelo(sql_matches):
    """Si el modelo gana o pierde una columna, la migración tiene que enterarse.

    Aquí atrapa además el accidente inverso del portado: un `shelter_id`
    transcrito desde el `matches` de `adopta-v1` sobraría en el .sql (y en prod
    sería `not null` contra una tabla `shelters` que no existe).
    """
    del_sql = columnas_del_sql(sql_matches, "matches")
    del_modelo = {columna.name for columna in Match.__table__.columns}

    faltan_en_sql = del_modelo - del_sql
    sobran_en_sql = del_sql - del_modelo
    assert not faltan_en_sql, f"El modelo tiene columnas que la migración no crea: {faltan_en_sql}"
    assert not sobran_en_sql, f"Columnas del .sql que el modelo no tiene: {sorted(sobran_en_sql)}"
    assert del_sql == del_modelo


def test_que_columna_admite_nulos_coincide_con_el_modelo(sql_matches):
    """El `not null` es la mitad del contrato de una columna.

    Aquí se juegan cuatro: `mensaje` y `telefono_contacto` (el adoptante puede
    swipear sin escribir nada), `motivo_descarte` (solo existe si se descartó) y
    `actualizado_en` (nulo hasta que el publicador actúa). Crear cualquiera de
    ellas `not null` en prod rompería el swipe-derecha entero. Una PK es `not
    null` implícita, así que no se le exige la palabra.
    """
    definiciones = definiciones_de_columna(sql_matches, "matches")

    for columna in Match.__table__.columns:
        definicion = definiciones[columna.name].lower()
        acepta_nulos = "not null" not in definicion and "primary key" not in definicion
        assert acepta_nulos == bool(columna.nullable), (
            f"matches.{columna.name}: el .sql dice "
            f"{'nullable' if acepta_nulos else 'not null'} y el modelo lo contrario "
            f"({definiciones[columna.name]!r})"
        )


# --- Constraints e índices: lo que más se olvida al transcribir a mano ---------


def test_el_unique_de_la_solicitud_viaja_a_produccion_con_su_nombre(sql_matches):
    """Sin `uq_match_user_pet`, dos requests simultáneos del mismo swipe-derecha
    meten dos solicitudes por la misma mascota y el publicador ve duplicados que
    no puede unir. El nombre importa: es el que dice el modelo y el que buscará la
    verificación post-migración en `pg_constraint`."""
    assert "uq_match_user_pet" in sql_matches
    en_sql = _columnas_del_unique(sql_matches, "uq_match_user_pet")
    en_modelo = _unique_del_modelo(Match, "uq_match_user_pet")
    assert en_sql == en_modelo, f"El UNIQUE difiere: .sql={en_sql} modelo={en_modelo}"


def test_las_claves_foraneas_del_modelo_viajan_a_produccion(sql_matches):
    """SQLite no fuerza las FK y Postgres sí: si una no se transcribe, el error
    aparece recién en prod (o no aparece nunca y quedan filas huérfanas)."""
    definiciones = definiciones_de_columna(sql_matches, "matches")
    esperadas = {"user_id": "public.users", "pet_id": "public.pets"}

    for columna, destino in esperadas.items():
        definicion = definiciones[columna].lower()
        assert (
            f"references {destino}" in definicion
        ), f"matches.{columna} debería referenciar {destino}: {definicion!r}"


def test_los_indices_del_modelo_viajan_a_produccion(sql_matches):
    """`index=True` en el modelo crea `ix_matches_<columna>` con `create_all`; en
    prod hay que escribirlo. Son los dos accesos del módulo: las solicitudes de un
    adoptante (`/adoptar/mis-solicitudes`) y las de una mascota — esta última es
    la que usa el join a `pets` del panel del publicador y el cierre masivo al
    aprobar, que sin índice recorre la tabla entera."""
    indexadas = [columna.name for columna in Match.__table__.columns if columna.index]
    assert sorted(indexadas) == ["pet_id", "user_id"]

    for columna in indexadas:
        assert re.search(
            rf"create\s+index\s+(?:if\s+not\s+exists\s+)?ix_matches_{columna}\s+"
            rf"on\s+(?:public\.)?matches\s*\(\s*{columna}\s*\)",
            sql_matches,
            re.IGNORECASE,
        ), f"Falta el índice ix_matches_{columna}"


# --- Convenciones del repo para todo .sql de producción ------------------------


def test_la_tabla_nueva_activa_row_level_security(sql_matches):
    """Toda tabla de prod lleva RLS, como el resto (el backend entra por service
    key). En `matches` pesa más que en otras: guarda el teléfono del adoptante y
    el motivo por el que no se quedó con la mascota."""
    assert re.search(
        r"alter\s+table\s+(?:public\.)?matches\s+enable\s+row\s+level\s+security",
        sql_matches,
        re.IGNORECASE,
    ), "Falta el 'enable row level security' sobre matches"


@pytest.mark.parametrize("prohibido", ["drop ", "truncate", "drop column"])
def test_la_migracion_es_aditiva(sql_matches, prohibido):
    """Se ejecuta contra una DB con datos reales: nada puede destruir nada."""
    assert prohibido not in sql_matches.lower(), f"La migración contiene '{prohibido}'"


def test_los_tipos_son_los_que_emite_create_all(sql_matches):
    """Mismo criterio que `AD-01-pets.sql` y `AD-03-swipes.sql`: el SQL escrito a
    mano tiene que producir el esquema que `create_all` genera en local, o dev y
    prod difieren en algo que ningún test vería. `identity`/`jsonb`/`timestamptz`
    son las tres tentaciones "más modernas" que rompen esa igualdad.

    `timestamp without time zone` no es un descuido: es lo que obliga a
    `calcular_etiqueta_solicitud` a normalizar el `creado_en` naive **también en
    Postgres**, y hay un test que lo cubre.

    Y **sin `DEFAULT` de DB**: los defaults los pone Python (modelo y schemas);
    duplicarlos aquí crearía dos fuentes de verdad que se separan con el tiempo —
    empezando por `estado`, que el modelo fija en `"solicitado"`.
    """
    for nombre, definicion in definiciones_de_columna(sql_matches, "matches").items():
        minuscula = definicion.lower()
        assert "identity" not in minuscula, f"matches.{nombre} usa identity, no serial"
        assert "jsonb" not in minuscula, f"matches.{nombre} usa jsonb; create_all emite json"
        assert "timestamptz" not in minuscula and "with time zone" not in minuscula, (
            f"matches.{nombre} lleva zona horaria; create_all emite "
            "'timestamp without time zone'"
        )
        assert "default" not in minuscula, f"matches.{nombre} declara un DEFAULT de DB"


def test_la_cabecera_avisa_de_que_no_esta_ejecutada_y_de_su_orden(sql_matches):
    """La migración se aplica a mano, con autorización explícita del dueño y
    ANTES del merge a `main`. El orden no es un detalle: `matches.pet_id`
    referencia `public.pets` y esta tabla viaja después de las dos de AD-03, que
    tampoco se han ejecutado todavía."""
    cabecera = sql_matches.lower()
    assert "escrito, no ejecutado" in cabecera
    assert "ad-03-swipes.sql" in cabecera
    assert "ad-03-home-profiles.sql" in cabecera
