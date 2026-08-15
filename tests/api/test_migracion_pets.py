"""Anti-drift entre el modelo `Pet` y el SQL que se ejecuta en producción.

En prod corre `SKIP_DB_CREATE_ALL=1`: el esquema **no** se crea solo a partir de
los modelos, lo escribe a mano `migrations/AD-01-pets.sql` en el SQL Editor de
Supabase. Esa mano es el punto débil: si el modelo gana una columna o el
`CheckConstraint` no se transcribe, dev y prod divergen **en silencio** — los
tests siguen verdes sobre SQLite (donde `create_all` sí aplica el CHECK) y en
Postgres el invariante sencillamente no existe.

Este archivo cierra ese hueco: compara el `.sql` versionado contra
`Pet.__table__` y exige que digan lo mismo.

⚠️ `Pet` se importa a nivel de módulo (ver la cabecera de `test_pets.py`): un
import perezoso deja la tabla fuera de `Base.metadata` en otros tests.
"""

import re
from pathlib import Path

import pytest
from sqlalchemy import CheckConstraint

from reencuentro_api.models.pet import Pet

MIGRACIONES_DIR = Path(__file__).resolve().parents[2] / "migrations"
SQL_PETS = MIGRACIONES_DIR / "AD-01-pets.sql"

PALABRAS_DE_CONSTRAINT = ("constraint", "check", "primary", "unique", "foreign", "exclude")


def _cuerpo_del_create_table(sql: str, tabla: str) -> str:
    """Devuelve lo que va entre los paréntesis del `create table ... <tabla> (…)`.

    Cuenta paréntesis en vez de usar una regex greedy porque el cuerpo contiene
    paréntesis propios (el `check ((a is null) <> (b is null))`).
    """
    inicio = re.search(
        rf"create\s+table\s+(?:if\s+not\s+exists\s+)?(?:public\.)?{tabla}\s*\(",
        sql,
        re.IGNORECASE,
    )
    assert inicio, f"El .sql no declara un 'create table' de {tabla}"
    profundidad = 0
    for pos in range(inicio.end() - 1, len(sql)):
        if sql[pos] == "(":
            profundidad += 1
        elif sql[pos] == ")":
            profundidad -= 1
            if profundidad == 0:
                return sql[inicio.end() : pos]
    raise AssertionError(f"El 'create table' de {tabla} no cierra su paréntesis")


def _partes_de_nivel_cero(cuerpo: str) -> list[str]:
    """Parte el cuerpo por las comas que no están dentro de un paréntesis."""
    partes, actual, profundidad = [], "", 0
    for caracter in cuerpo:
        if caracter == "(":
            profundidad += 1
        elif caracter == ")":
            profundidad -= 1
        if caracter == "," and profundidad == 0:
            partes.append(actual)
            actual = ""
        else:
            actual += caracter
    partes.append(actual)
    return [parte.strip() for parte in partes if parte.strip()]


def columnas_del_sql(sql: str, tabla: str) -> set[str]:
    """Nombres de columna declarados en el `create table` (sin las constraints)."""
    columnas = set()
    for parte in _partes_de_nivel_cero(_cuerpo_del_create_table(sql, tabla)):
        primera = parte.split()[0]
        if primera.lower() in PALABRAS_DE_CONSTRAINT:
            continue
        columnas.add(primera.strip('"'))
    return columnas


def _normalizar_expresion(expresion: str) -> str:
    """Minúsculas, espacios colapsados y sin espacios pegados a los paréntesis.

    Comparar carácter a carácter sería frágil: el modelo escribe
    `(organizacion_id IS NULL) <> (user_id IS NULL)` y el SQL lo envuelve en un
    paréntesis más y en minúsculas. Lo que importa es que sea la misma condición.
    """
    limpio = re.sub(r"\s+", " ", expresion.strip().lower())
    limpio = re.sub(r"\s*([()])\s*", r"\1", limpio)
    while limpio.startswith("(") and limpio.endswith(")"):
        interior = limpio[1:-1]
        if _partes_de_nivel_cero(interior) and interior.count("(") == interior.count(")"):
            limpio = interior
        else:
            break
    return limpio


def expresion_del_check(sql: str, nombre: str) -> str:
    """La condición del `constraint <nombre> check (…)` tal como está en el .sql."""
    inicio = re.search(rf"constraint\s+{nombre}\s+check\s*\(", sql, re.IGNORECASE)
    assert inicio, f"El .sql no declara el constraint {nombre}"
    profundidad = 0
    for pos in range(inicio.end() - 1, len(sql)):
        if sql[pos] == "(":
            profundidad += 1
        elif sql[pos] == ")":
            profundidad -= 1
            if profundidad == 0:
                return sql[inicio.end() : pos]
    raise AssertionError(f"El check {nombre} no cierra su paréntesis")


def check_del_modelo(modelo, nombre: str) -> str:
    for constraint in modelo.__table__.constraints:
        if isinstance(constraint, CheckConstraint) and constraint.name == nombre:
            return str(constraint.sqltext)
    raise AssertionError(f"El modelo {modelo.__name__} no declara el constraint {nombre}")


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
