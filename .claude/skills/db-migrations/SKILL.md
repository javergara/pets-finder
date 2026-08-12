---
name: db-migrations
description: Crea o actualiza el esquema SQLite de forma segura cuando cambian los modelos SQLAlchemy. Usar antes de tocar cualquier archivo en src/api/reencuentro_api/models/.
---

# db-migrations

## Cuándo usar
Al añadir/modificar una entidad del modelo de datos (`User`, `Report`).

## Cómo (alcance MVP — sin Alembic)

Por decisión documentada en `docs/architecture.md` §6, el MVP usa `SQLAlchemy.metadata.create_all` en vez de migraciones formales, porque los datos son 100% semilla desechable y reproducible (`scripts/seed.py`), no datos reales que haya que preservar entre cambios de esquema.

1. Cambia el modelo en `src/api/reencuentro_api/models/`.
2. Borra `data/app.db` (está gitignored, no hay pérdida real) y vuelve a correr `python3 scripts/seed.py` — esto recrea el esquema completo desde los modelos actuales.
3. Corre los tests de persistencia en `tests/api/` para confirmar que el nuevo esquema funciona con las queries existentes.
4. Documenta el cambio de modelo en `changes.md` (qué campo/tabla cambió y por qué).

## Cuándo esto deja de ser suficiente

Si el proyecto pasa a tener datos reales persistentes (más allá del seed) — típicamente al desplegar en producción con reportes reales (feature `11-despliegue` y siguientes) — este enfoque ya no alcanza y hay que introducir Alembic (o el equivalente). Eso se decide con un ADR nuevo, no se anticipa aquí.
