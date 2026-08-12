import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .models.base import Base, engine
from .routers import users

REPO_ROOT = Path(__file__).resolve().parents[3]
MEDIA_DIR = REPO_ROOT / "data" / "media"


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

MEDIA_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(MEDIA_DIR)), name="media")
