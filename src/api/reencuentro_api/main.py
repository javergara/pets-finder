import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .media import MEDIA_DIR
from .models.base import Base, engine
from .routers import reports, uploads, users


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
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

# En serverless (Vercel, ADR 0007) el filesystem es de solo lectura: si no se
# puede crear/encontrar el directorio, simplemente no se monta /media — en
# producción todas las fotos son URLs absolutas de Supabase (ADR 0006).
try:
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
except OSError:
    pass
if MEDIA_DIR.is_dir():
    app.mount("/media", StaticFiles(directory=str(MEDIA_DIR)), name="media")
