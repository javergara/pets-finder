"""Herramientas compartidas por los tests anti-drift de `migrations/*.sql`.

No es un test (por eso no se llama `test_*.py` y pytest no lo colecta): es el
parser mínimo de `create table` que necesitan `test_migracion_pets.py` y
`test_migracion_swipes.py` para comparar el SQL versionado contra los modelos.

Vive aparte porque el segundo anti-drift habría copiado los mismos 60 renglones
de parser, y dos parsers que se separan con el tiempo son peor que ninguno. Los
tests de `pets` no cambiaron ni una línea al extraerlo — que siguieran verdes es
la única prueba de que la extracción no alteró nada.
"""

import re
from pathlib import Path

from sqlalchemy import CheckConstraint

MIGRACIONES_DIR = Path(__file__).resolve().parents[2] / "migrations"

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


def definiciones_de_columna(sql: str, tabla: str) -> dict[str, str]:
    """Cada columna del `create table` con su definición entera, ya normalizada
    a una sola línea (`{"presupuesto_mensual_cop": "presupuesto_mensual_cop integer"}`).

    Las constraints de tabla (las que empiezan por `constraint`, `unique`, …) no
    son columnas y quedan fuera.
    """
    definiciones: dict[str, str] = {}
    for parte in _partes_de_nivel_cero(_cuerpo_del_create_table(sql, tabla)):
        primera = parte.split()[0]
        if primera.lower() in PALABRAS_DE_CONSTRAINT:
            continue
        definiciones[primera.strip('"')] = " ".join(parte.split())
    return definiciones


def columnas_del_sql(sql: str, tabla: str) -> set[str]:
    """Nombres de columna declarados en el `create table` (sin las constraints)."""
    return set(definiciones_de_columna(sql, tabla))


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
