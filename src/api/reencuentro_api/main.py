import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

from .media import MEDIA_DIR
from .models.base import Base, engine
from .routers import (
    avisos_ayuda,
    organizaciones,
    paginas,
    radar,
    reports,
    suscripciones,
    uploads,
    users,
)

logger = logging.getLogger("reencuentro")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Diagnóstico visible en los logs de la función (Vercel): qué DB resolvió el
    # entorno. Si aparece "sqlite" en producción, faltan las env vars de Supabase.
    logger.warning("Arranque — dialecto de DB: %s", engine.dialect.name)
    # SKIP_DB_CREATE_ALL=1 (producción, feature 19): el esquema de prod ya existe
    # y no cambia solo — saltarse los round-trips de verificación de create_all
    # recorta el arranque en frío del serverless. Sin la variable (dev/tests),
    # create_all sigue creando el esquema como siempre.
    if os.environ.get("SKIP_DB_CREATE_ALL", "").strip() == "1":
        logger.warning("SKIP_DB_CREATE_ALL=1 — se omite create_all en el arranque")
        yield
        return
    # Arranque resiliente: si create_all falla (p. ej. SQLite sobre el filesystem
    # de solo lectura de serverless porque faltan las env vars), la app igual
    # sirve /health y cada endpoint de datos falla por request con error claro —
    # nunca un FUNCTION_INVOCATION_FAILED mudo en el boot.
    try:
        Base.metadata.create_all(bind=engine)
    except (SQLAlchemyError, OSError):
        logger.exception("create_all falló en el arranque; la app sirve igual")
    yield


app = FastAPI(title="Reencuentro API", lifespan=lifespan)

cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# Regla de orden heredada de la versión anterior de esta API: cualquier ruta literal
# (p. ej. /api/reports/reunidos) debe registrarse ANTES que su ruta dinámica
# (/api/reports/{report_id}), o queda eclipsada y responde 422.
app.include_router(users.router)
app.include_router(reports.router)
app.include_router(uploads.router)
app.include_router(organizaciones.router)
app.include_router(avisos_ayuda.router)
app.include_router(suscripciones.router)
app.include_router(radar.router)
app.include_router(paginas.router)

# En serverless (Vercel, ADR 0007) el filesystem es de solo lectura: si no se
# puede crear/encontrar el directorio, simplemente no se monta /media — en
# producción todas las fotos son URLs absolutas de Supabase (ADR 0006).
try:
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
except OSError:
    pass
if MEDIA_DIR.is_dir():
    app.mount("/media", StaticFiles(directory=str(MEDIA_DIR)), name="media")
