"""Anti-drift entre el modelo `Favorite` y el SQL que se ejecuta en producción.

Mismo hueco que cierran `test_migracion_pets.py`, `test_migracion_swipes.py` y
`test_migracion_matches.py`: en prod corre `SKIP_DB_CREATE_ALL=1`, así que el
esquema **no** sale de los modelos, lo escribe a mano alguien en el SQL Editor de
Supabase. Si el modelo gana una columna, si el `unique` no se transcribe o si un
`not null` se cuela donde el modelo admite nulos, dev y prod divergen **en
silencio**: los tests siguen verdes sobre SQLite y en Postgres el invariante no
existe (o existe de más).

En `favorites` lo que más pesa es el `unique`: es la ÚNICA garantía real de la
idempotencia del POST. Sin él en Postgres, dos toques al corazón guardan dos
filas y la rejilla de favoritas muestra la misma mascota repetida.

⚠️ `AD-07-favorites.sql` está **escrito, no ejecutado**, y es el **cuarto** de la
cola: `AD-03-swipes.sql` → `AD-03-home-profiles.sql` → `AD-05-matches.sql` → este.

⚠️ `Favorite` se importa a nivel de módulo (ver la cabecera de `test_pets.py`):
un import perezoso deja la tabla fuera de `Base.metadata` en otros tests.
"""

import re

import pytest
from soporte_migraciones import MIGRACIONES_DIR, columnas_del_sql, definiciones_de_columna
from sqlalchemy import UniqueConstraint

from reencuentro_api.models.favorite import Favorite

SQL_FAVORITES = MIGRACIONES_DIR / "AD-07-favorites.sql"


@pytest.fixture(scope="module")
def sql_favorites() -> str:
    assert SQL_FAVORITES.exists(), f"Falta la migración versionada {SQL_FAVORITES}"
    return SQL_FAVORITES.read_text(encoding="utf-8")


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


def test_columnas_del_sql_son_exactamente_las_del_modelo(sql_favorites):
    """Si el modelo gana o pierde una columna, la migración tiene que enterarse.

    La tabla es minúscula (cuatro columnas) justamente porque un favorito no
    tiene estado: la existencia de la fila es la señal. Cualquier columna de más
    en el .sql —un `estado`, un `notas` traído de otra tabla— sería `not null`
    contra un INSERT de la API que jamás la manda.
    """
    del_sql = columnas_del_sql(sql_favorites, "favorites")
    del_modelo = {columna.name for columna in Favorite.__table__.columns}

    faltan_en_sql = del_modelo - del_sql
    sobran_en_sql = del_sql - del_modelo
    assert not faltan_en_sql, f"El modelo tiene columnas que la migración no crea: {faltan_en_sql}"
    assert not sobran_en_sql, f"Columnas del .sql que el modelo no tiene: {sorted(sobran_en_sql)}"
    assert del_sql == del_modelo


def test_que_columna_admite_nulos_coincide_con_el_modelo(sql_favorites):
    """El `not null` es la mitad del contrato de una columna. Aquí las cuatro son
    obligatorias en el modelo, así que lo que atrapa este test es el descuido
    inverso: una columna creada nullable en prod dejaría entrar favoritos sin
    mascota o sin fecha por cualquier escritura que no venga de la API. Una PK es
    `not null` implícita, así que no se le exige la palabra."""
    definiciones = definiciones_de_columna(sql_favorites, "favorites")

    for columna in Favorite.__table__.columns:
        definicion = definiciones[columna.name].lower()
        acepta_nulos = "not null" not in definicion and "primary key" not in definicion
        assert acepta_nulos == bool(columna.nullable), (
            f"favorites.{columna.name}: el .sql dice "
            f"{'nullable' if acepta_nulos else 'not null'} y el modelo lo contrario "
            f"({definiciones[columna.name]!r})"
        )


# --- Constraints e índices: lo que más se olvida al transcribir a mano ---------


def test_el_unique_del_favorito_viaja_a_produccion_con_su_nombre(sql_favorites):
    """Sin `uq_favorite_user_pet` en Postgres, la idempotencia del POST se queda
    apoyada solo en el select previo del router —que es exactamente lo que hacía
    `adopta-v1`— y dos requests simultáneos del mismo corazón meten dos filas. El
    nombre importa: es el que dice el modelo y el que buscará la verificación
    post-migración en `pg_constraint`."""
    assert "uq_favorite_user_pet" in sql_favorites
    en_sql = _columnas_del_unique(sql_favorites, "uq_favorite_user_pet")
    en_modelo = _unique_del_modelo(Favorite, "uq_favorite_user_pet")
    assert en_sql == en_modelo, f"El UNIQUE difiere: .sql={en_sql} modelo={en_modelo}"


def test_las_claves_foraneas_del_modelo_viajan_a_produccion(sql_favorites):
    """SQLite no fuerza las FK y Postgres sí: si una no se transcribe, el error
    aparece recién en prod (o no aparece nunca y quedan filas huérfanas — un
    favorito a una mascota borrada rompería la rejilla de favoritas)."""
    definiciones = definiciones_de_columna(sql_favorites, "favorites")
    esperadas = {"user_id": "public.users", "pet_id": "public.pets"}

    for columna, destino in esperadas.items():
        definicion = definiciones[columna].lower()
        assert (
            f"references {destino}" in definicion
        ), f"favorites.{columna} debería referenciar {destino}: {definicion!r}"


def test_los_indices_del_modelo_viajan_a_produccion(sql_favorites):
    """`index=True` en el modelo crea `ix_favorites_<columna>` con `create_all`;
    en prod hay que escribirlo. Son los dos accesos del módulo: las favoritas de
    una persona (`/adoptar/mis-favoritas`) y, sobre todo, el `select` por
    `user_id` que el paso 3 hace en catálogo, ficha y deck — sin índice, cada
    listado recorre la tabla entera contra el pooler."""
    indexadas = [columna.name for columna in Favorite.__table__.columns if columna.index]
    assert sorted(indexadas) == ["pet_id", "user_id"]

    for columna in indexadas:
        assert re.search(
            rf"create\s+index\s+(?:if\s+not\s+exists\s+)?ix_favorites_{columna}\s+"
            rf"on\s+(?:public\.)?favorites\s*\(\s*{columna}\s*\)",
            sql_favorites,
            re.IGNORECASE,
        ), f"Falta el índice ix_favorites_{columna}"


# --- Convenciones del repo para todo .sql de producción ------------------------


def test_la_tabla_nueva_activa_row_level_security(sql_favorites):
    """Toda tabla de prod lleva RLS, como el resto (el backend entra por service
    key). Aquí protege un historial de navegación con nombre y apellido: qué
    mascotas mira cada persona, ligadas a su `users.id`."""
    assert re.search(
        r"alter\s+table\s+(?:public\.)?favorites\s+enable\s+row\s+level\s+security",
        sql_favorites,
        re.IGNORECASE,
    ), "Falta el 'enable row level security' sobre favorites"


@pytest.mark.parametrize("prohibido", ["drop ", "truncate", "drop column"])
def test_la_migracion_es_aditiva(sql_favorites, prohibido):
    """Se ejecuta contra una DB con datos reales: nada puede destruir nada."""
    assert prohibido not in sql_favorites.lower(), f"La migración contiene '{prohibido}'"


def test_los_tipos_son_los_que_emite_create_all(sql_favorites):
    """Mismo criterio que las tres migraciones anteriores: el SQL escrito a mano
    tiene que producir el esquema que `create_all` genera en local, o dev y prod
    difieren en algo que ningún test vería. `identity`/`jsonb`/`timestamptz` son
    las tres tentaciones "más modernas" que rompen esa igualdad.

    Y **sin `DEFAULT` de DB**: el `creado_en` lo pone Python
    (`default=lambda: datetime.now(timezone.utc)` en el modelo); un `default
    now()` aquí crearía dos fuentes de verdad para la misma fecha.
    """
    for nombre, definicion in definiciones_de_columna(sql_favorites, "favorites").items():
        minuscula = definicion.lower()
        assert "identity" not in minuscula, f"favorites.{nombre} usa identity, no serial"
        assert "jsonb" not in minuscula, f"favorites.{nombre} usa jsonb; create_all emite json"
        assert "timestamptz" not in minuscula and "with time zone" not in minuscula, (
            f"favorites.{nombre} lleva zona horaria; create_all emite "
            "'timestamp without time zone'"
        )
        assert "default" not in minuscula, f"favorites.{nombre} declara un DEFAULT de DB"


def test_la_cabecera_avisa_de_que_no_esta_ejecutada_y_de_su_orden(sql_favorites):
    """La migración se aplica a mano, con autorización explícita del dueño y
    ANTES del merge a `main`. El orden no es un detalle: `favorites.pet_id`
    referencia `public.pets` (ya en prod desde AD-01) y esta tabla es la **cuarta**
    de una cola de la que no se ha ejecutado ninguna."""
    cabecera = sql_favorites.lower()
    assert "escrito, no ejecutado" in cabecera
    assert "ad-03-swipes.sql" in cabecera
    assert "ad-03-home-profiles.sql" in cabecera
    assert "ad-05-matches.sql" in cabecera
