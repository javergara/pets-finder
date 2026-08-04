import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .models.base import Base, engine
from .routers import chat, matches, pets, shelters, sponsorships, swipes, users

REPO_ROOT = Path(__file__).resolve().parents[3]
IMAGES_DIR = REPO_ROOT / "data" / "seed" / "images"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Adopta API", lifespan=lifespan)

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


# sponsorships.router va antes que pets.router: define /api/pets/necesitan-apoyo,
# que si se registrara después quedaría eclipsado por /api/pets/{pet_id} (pets.py)
# tratando "necesitan-apoyo" como un pet_id inválido (422 en vez de 200).
app.include_router(sponsorships.router)
app.include_router(pets.router)
app.include_router(swipes.router)
app.include_router(matches.router)
app.include_router(users.router)
app.include_router(shelters.router)
app.include_router(chat.router)

if IMAGES_DIR.exists():
    app.mount("/media", StaticFiles(directory=str(IMAGES_DIR)), name="media")
