"""Anti-drift entre el modelo `Pet` y el SQL que se ejecuta en producción.

En prod corre `SKIP_DB_CREATE_ALL=1`: el esquema **no** se crea solo a partir de
los modelos, lo escribe a mano `migrations/AD-01-pets.sql` en el SQL Editor de
Supabase. Esa mano es el punto débil: si el modelo gana una columna o el
`CheckConstraint` no se transcribe, dev y prod divergen **en silencio** — los
tests siguen verdes sobre SQLite (donde `create_all` sí aplica el CHECK) y en
Postgres el invariante sencillamente no existe.

Este archivo cierra ese hueco: compara el `.sql` versionado contra
`Pet.__table__` y exige que digan lo mismo.

El parser de `create table` vive en `soporte_migraciones.py`, compartido con el
anti-drift de AD-03 (`test_migracion_swipes.py`). Los casos de abajo no cambiaron
al extraerlo: que sigan verdes es la prueba de que la extracción no alteró nada.

⚠️ `Pet` se importa a nivel de módulo (ver la cabecera de `test_pets.py`): un
import perezoso deja la tabla fuera de `Base.metadata` en otros tests.
"""

import re

import pytest
from soporte_migraciones import (
    MIGRACIONES_DIR,
    _normalizar_expresion,
    check_del_modelo,
    columnas_del_sql,
    expresion_del_check,
)

from reencuentro_api.models.pet import Pet

SQL_PETS = MIGRACIONES_DIR / "AD-01-pets.sql"


@pytest.fixture(scope="module")
def sql_pets() -> str:
    assert SQL_PETS.exists(), f"Falta la migración versionada {SQL_PETS}"
    return SQL_PETS.read_text(encoding="utf-8")


def test_columnas_del_sql_son_exactamente_las_del_modelo(sql_pets):
    """Si el modelo gana o pierde una columna, la migración tiene que enterarse."""
    del_sql = columnas_del_sql(sql_pets, "pets")
    del_modelo = {columna.name for columna in Pet.__table__.columns}

    faltan_en_sql = del_modelo - del_sql
    sobran_en_sql = del_sql - del_modelo
    assert not faltan_en_sql, f"El modelo tiene columnas que la migración no crea: {faltan_en_sql}"
    assert not sobran_en_sql, f"Columnas del .sql que el modelo no tiene: {sorted(sobran_en_sql)}"
    assert del_sql == del_modelo


def test_el_check_del_publicador_viaja_a_produccion(sql_pets):
    """El invariante "organización XOR rescatista" no llega solo con el deploy."""
    assert "ck_pets_publicador_exclusivo" in sql_pets
    en_sql = _normalizar_expresion(expresion_del_check(sql_pets, "ck_pets_publicador_exclusivo"))
    en_modelo = _normalizar_expresion(check_del_modelo(Pet, "ck_pets_publicador_exclusivo"))
    assert en_sql == en_modelo, f"El CHECK difiere: .sql={en_sql!r} modelo={en_modelo!r}"


def test_la_tabla_nueva_activa_row_level_security(sql_pets):
    """Toda tabla de prod lleva RLS, como el resto (el backend entra por service key)."""
    assert re.search(
        r"alter\s+table\s+(?:public\.)?pets\s+enable\s+row\s+level\s+security",
        sql_pets,
        re.IGNORECASE,
    ), "Falta el 'enable row level security' sobre pets"


@pytest.mark.parametrize("prohibido", ["drop ", "truncate", "drop column"])
def test_la_migracion_es_aditiva(sql_pets, prohibido):
    """Se ejecuta contra una DB con datos reales: nada puede destruir nada."""
    assert prohibido not in sql_pets.lower(), f"La migración contiene '{prohibido}'"
