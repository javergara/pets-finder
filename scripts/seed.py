#!/usr/bin/env python3
"""Seed determinista de Reencuentro: borra y recrea data/app.db con datos de ejemplo.

Provisional de la feature 01-pivot-fundaciones: solo usuarios. Los reportes de
mascotas perdidas/encontradas (con fotos y coordenadas por zona) llegan con la
feature 02-reportes-backend.

Correrlo dos veces produce exactamente el mismo resultado (drop_all + create_all,
sin aleatoriedad sin semilla).
"""

import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src" / "api"))

from reencuentro_api.models import Base, SessionLocal, User, engine  # noqa: E402

RANDOM_SEED = 42

# El primer usuario insertado (id=1) es el usuario demo del frontend
# (src/web/src/lib/constants.ts::DEMO_USER_ID — deben mantenerse en sync).
USERS = [
    {"nombre": "Ana Martínez", "email": "ana@example.com", "ciudad": "Armenia", "barrio": "La Castellana"},
    {"nombre": "Carlos Gómez", "email": "carlos@example.com", "ciudad": "Pereira", "barrio": "Cuba"},
    {"nombre": "Luisa Fernanda Ríos", "email": "luisa@example.com", "ciudad": "Manizales", "barrio": "Palermo"},
    {"nombre": "Jorge Palacios", "email": "jorge@example.com", "ciudad": "Quibdó", "barrio": "Niño Jesús"},
    {"nombre": "Valentina Mosquera", "email": "valentina@example.com", "ciudad": "Cali", "barrio": "San Fernando"},
]


def main() -> None:
    random.seed(RANDOM_SEED)

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        for datos in USERS:
            session.add(User(**datos))
        session.commit()
        print(f"Seed listo: {len(USERS)} usuarios en data/app.db")
    finally:
        session.close()


if __name__ == "__main__":
    main()
