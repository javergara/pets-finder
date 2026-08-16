"""Anti-drift entre `Swipe`/`HomeProfile` y el SQL que se ejecuta en producción.

Mismo hueco que cierra `test_migracion_pets.py`, ahora para las dos tablas de
AD-03: en prod corre `SKIP_DB_CREATE_ALL=1`, así que el esquema **no** sale de
los modelos, lo escribe a mano alguien en el SQL Editor de Supabase. Si el
modelo gana una columna, si el `unique` no se transcribe o si la PK cambia, dev y
prod divergen **en silencio** — los tests siguen verdes sobre SQLite y en
Postgres el invariante no existe.

`home_profiles` viaja en esta ventana y no en AD-04 (decisión del líder): el deck
consulta la tabla para calcular la afinidad, y si no existe en prod la ruta
responde 500. **AD-04 se queda sin migración propia.**

⚠️ Los dos `.sql` están **escritos, no ejecutados**, y su orden de despliegue es
después de `AD-01-pets.sql`: `swipes.pet_id` referencia `public.pets`.

⚠️ `Swipe` y `HomeProfile` se importan a nivel de módulo (ver la cabecera de
`test_pets.py`): un import perezoso deja la tabla fuera de `Base.metadata` en
otros tests.
"""

import re

import pytest
from soporte_migraciones import MIGRACIONES_DIR, columnas_del_sql, definiciones_de_columna
from sqlalchemy import UniqueConstraint

from reencuentro_api.models.home_profile import HomeProfile
from reencuentro_api.models.swipe import Swipe

SQL_SWIPES = MIGRACIONES_DIR / "AD-03-swipes.sql"
SQL_HOME_PROFILES = MIGRACIONES_DIR / "AD-03-home-profiles.sql"


@pytest.fixture(scope="module")
def sql_swipes() -> str:
    assert SQL_SWIPES.exists(), f"Falta la migración versionada {SQL_SWIPES}"
    return SQL_SWIPES.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def sql_home_profiles() -> str:
    assert SQL_HOME_PROFILES.exists(), f"Falta la migración versionada {SQL_HOME_PROFILES}"
    return SQL_HOME_PROFILES.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def sqls(sql_swipes, sql_home_profiles) -> dict[str, str]:
    """Las dos migraciones por nombre de tabla, para los casos parametrizados."""
    return {"swipes": sql_swipes, "home_profiles": sql_home_profiles}


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


@pytest.mark.parametrize(
    ("tabla", "modelo"),
    [("swipes", Swipe), ("home_profiles", HomeProfile)],
)
def test_columnas_del_sql_son_exactamente_las_del_modelo(sqls, tabla, modelo):
    """Si el modelo gana o pierde una columna, la migración tiene que enterarse."""
    del_sql = columnas_del_sql(sqls[tabla], tabla)
    del_modelo = {columna.name for columna in modelo.__table__.columns}

    faltan_en_sql = del_modelo - del_sql
    sobran_en_sql = del_sql - del_modelo
    assert not faltan_en_sql, f"El modelo tiene columnas que la migración no crea: {faltan_en_sql}"
    assert not sobran_en_sql, f"Columnas del .sql que el modelo no tiene: {sorted(sobran_en_sql)}"
    assert del_sql == del_modelo


@pytest.mark.parametrize(
    ("tabla", "modelo"),
    [("swipes", Swipe), ("home_profiles", HomeProfile)],
)
def test_que_columna_admite_nulos_coincide_con_el_modelo(sqls, tabla, modelo):
    """El `not null` es la mitad del contrato de una columna.

    Aquí se juega, en concreto, `presupuesto_mensual_cop`: es opcional a
    propósito (`services/afinidad.py` degrada a solo-experiencia cuando falta), y
    crearla `not null` en prod haría fallar todo guardado de perfil sin ese dato.
    Una PK es `not null` implícita, así que no se le exige la palabra.
    """
    definiciones = definiciones_de_columna(sqls[tabla], tabla)

    for columna in modelo.__table__.columns:
        definicion = definiciones[columna.name].lower()
        acepta_nulos = "not null" not in definicion and "primary key" not in definicion
        assert acepta_nulos == bool(columna.nullable), (
            f"{tabla}.{columna.name}: el .sql dice "
            f"{'nullable' if acepta_nulos else 'not null'} y el modelo lo contrario "
            f"({definiciones[columna.name]!r})"
        )


def test_el_presupuesto_mensual_queda_nullable_en_produccion(sql_home_profiles):
    """El caso concreto, con nombre propio para que un rojo se lea solo."""
    definicion = definiciones_de_columna(sql_home_profiles, "home_profiles")
    assert "not null" not in definicion["presupuesto_mensual_cop"].lower()


# --- Constraints: lo que más se olvida al transcribir a mano -------------------


def test_el_unique_del_swipe_viaja_a_produccion_con_su_nombre(sql_swipes):
    """Sin `uq_swipe_user_pet` un doble-tap del gesto mete dos filas y, en AD-05,
    dos solicitudes a la misma organización. El nombre importa: es el que dice el
    modelo y el que buscará la verificación post-migración en `pg_constraint`."""
    assert "uq_swipe_user_pet" in sql_swipes
    en_sql = _columnas_del_unique(sql_swipes, "uq_swipe_user_pet")
    en_modelo = _unique_del_modelo(Swipe, "uq_swipe_user_pet")
    assert en_sql == en_modelo, f"El UNIQUE difiere: .sql={en_sql} modelo={en_modelo}"


def test_home_profiles_tiene_user_id_como_primary_key(sql_home_profiles):
    """La PK es `user_id` y no hay `id` propio: un perfil por persona, y la fila
    existiendo *es* la señal de "cuestionario completo" (el upsert de AD-04 se
    apoya en eso). Con una PK distinta, prod aceptaría dos perfiles del mismo
    usuario y el deck elegiría uno al azar."""
    definiciones = definiciones_de_columna(sql_home_profiles, "home_profiles")
    assert "primary key" in definiciones["user_id"].lower()
    assert [columna.name for columna in HomeProfile.__table__.primary_key.columns] == ["user_id"]


def test_las_claves_foraneas_del_modelo_viajan_a_produccion(sqls):
    """SQLite no fuerza las FK y Postgres sí: si una no se transcribe, el error
    aparece recién en prod (o no aparece nunca y quedan filas huérfanas)."""
    esperadas = {
        ("swipes", "user_id"): "public.users",
        ("swipes", "pet_id"): "public.pets",
        ("home_profiles", "user_id"): "public.users",
    }
    for (tabla, columna), destino in esperadas.items():
        definicion = definiciones_de_columna(sqls[tabla], tabla)[columna].lower()
        assert (
            f"references {destino}" in definicion
        ), f"{tabla}.{columna} debería referenciar {destino}: {definicion!r}"


def test_los_indices_del_modelo_viajan_a_produccion(sql_swipes):
    """`index=True` en el modelo crea `ix_swipes_<columna>` con `create_all`; en
    prod hay que escribirlo. Son los dos accesos del módulo: excluir del deck lo
    ya visto (por adoptante) y contar el interés de una mascota (por mascota)."""
    for columna in Swipe.__table__.columns:
        if not columna.index:
            continue
        assert re.search(
            rf"create\s+index\s+(?:if\s+not\s+exists\s+)?ix_swipes_{columna.name}\s+"
            rf"on\s+(?:public\.)?swipes\s*\(\s*{columna.name}\s*\)",
            sql_swipes,
            re.IGNORECASE,
        ), f"Falta el índice ix_swipes_{columna.name}"


# --- Convenciones del repo para todo .sql de producción ------------------------


@pytest.mark.parametrize("tabla", ["swipes", "home_profiles"])
def test_la_tabla_nueva_activa_row_level_security(sqls, tabla):
    """Toda tabla de prod lleva RLS, como el resto (el backend entra por service key)."""
    assert re.search(
        rf"alter\s+table\s+(?:public\.)?{tabla}\s+enable\s+row\s+level\s+security",
        sqls[tabla],
        re.IGNORECASE,
    ), f"Falta el 'enable row level security' sobre {tabla}"


@pytest.mark.parametrize("tabla", ["swipes", "home_profiles"])
@pytest.mark.parametrize("prohibido", ["drop ", "truncate", "drop column"])
def test_la_migracion_es_aditiva(sqls, tabla, prohibido):
    """Se ejecuta contra una DB con datos reales: nada puede destruir nada."""
    assert prohibido not in sqls[tabla].lower(), f"La migración de {tabla} contiene '{prohibido}'"


@pytest.mark.parametrize("tabla", ["swipes", "home_profiles"])
def test_los_tipos_son_los_que_emite_create_all(sqls, tabla):
    """Mismo criterio que `AD-01-pets.sql`: el SQL escrito a mano tiene que
    producir el esquema que `create_all` genera en local, o dev y prod difieren
    en algo que ningún test vería. `identity`/`jsonb`/`timestamptz` son las tres
    tentaciones "más modernas" que rompen esa igualdad.

    Y **sin `DEFAULT` de DB**: los defaults los pone Python (modelo y schemas);
    duplicarlos aquí crearía dos fuentes de verdad que se separan con el tiempo.
    """
    for nombre, definicion in definiciones_de_columna(sqls[tabla], tabla).items():
        minuscula = definicion.lower()
        assert "identity" not in minuscula, f"{tabla}.{nombre} usa identity, no serial"
        assert "jsonb" not in minuscula, f"{tabla}.{nombre} usa jsonb; create_all emite json"
        assert "timestamptz" not in minuscula and "with time zone" not in minuscula, (
            f"{tabla}.{nombre} lleva zona horaria; create_all emite "
            "'timestamp without time zone'"
        )
        assert "default" not in minuscula, f"{tabla}.{nombre} declara un DEFAULT de DB"
