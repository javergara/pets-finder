#!/usr/bin/env python3
"""Seed determinista de Adopta: refugios, mascotas, adoptantes con HomeProfile.

Nunca falla por falta de red: si no se puede descargar una foto, genera un
placeholder SVG local. Ver .claude/skills/seed-data/SKILL.md.

Uso: python3 scripts/seed.py
"""

import random
import sys
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src" / "api"))

from adopta_api.models.base import Base, SessionLocal, engine  # noqa: E402
from adopta_api.models.home_profile import HomeProfile  # noqa: E402
from adopta_api.models.pet import Pet  # noqa: E402
from adopta_api.models.shelter import Shelter  # noqa: E402
from adopta_api.models.user import User  # noqa: E402

RANDOM_SEED = 42
DEMO_USER_ID = 1  # Ana Martínez, primer usuario insertado — usado por src/web y por los tests
IMAGES_DIR = REPO_ROOT / "data" / "seed" / "images"
DOWNLOAD_TIMEOUT_SECONDS = 4

# Bogotá: lat ~4.55-4.80, lng ~-74.20 a -74.00 (usado por el filtro de distancia, feature 06-filters).
BOGOTA_LAT_RANGE = (4.55, 4.80)
BOGOTA_LNG_RANGE = (-74.20, -74.00)

# Coordenadas reales aproximadas del centro de cada barrio de los adoptantes semilla — deterministas
# (no generadas al azar) porque el barrio ya es un dato fijo de cada USERS[i].
BARRIO_COORDS = {
    "Usaquén": (4.6946, -74.0307),
    "Chapinero": (4.6486, -74.0629),
    "Suba": (4.7448, -74.0827),
    "Engativá": (4.6900, -74.1170),
    "Kennedy": (4.6280, -74.1497),
}

SHELTERS = [
    dict(
        nombre="Refugio Huellas de Bogotá",
        ciudad="Bogotá",
        verificado=True,
        adopciones_cerradas=42,
        tiempo_respuesta_horas=12,
    ),
    dict(
        nombre="Rescate Patitas Felices",
        ciudad="Bogotá",
        verificado=True,
        adopciones_cerradas=18,
        tiempo_respuesta_horas=24,
    ),
    dict(
        nombre="Fundación Colita Feliz",
        ciudad="Bogotá",
        verificado=True,
        adopciones_cerradas=67,
        tiempo_respuesta_horas=6,
    ),
]

# shelter_idx es índice 0-based sobre SHELTERS (se resuelve a shelter_id al insertar)
PETS = [
    dict(
        nombre="Max",
        especie="perro",
        raza="Labrador mestizo",
        sexo="macho",
        edad_meses=18,
        tamano="grande",
        energia="alta",
        shelter_idx=0,
        historia="Max llegó al refugio hace un año tras ser encontrado en la calle. Le encanta correr y jugar con pelotas.",
        tags=["juguetón", "sociable"],
        esterilizado=True,
        vacunas_al_dia=True,
        microchip=True,
        desparasitado=True,
        apto_ninos=True,
        apto_perros=True,
        apto_gatos=False,
    ),
    dict(
        nombre="Luna",
        especie="gato",
        raza="Mestiza",
        sexo="hembra",
        edad_meses=8,
        tamano="pequeño",
        energia="baja",
        shelter_idx=0,
        historia="Luna es tranquila y prefiere las siestas al sol antes que el juego. Ideal para apartamentos.",
        tags=["tranquila", "independiente"],
        esterilizado=True,
        vacunas_al_dia=True,
        microchip=True,
        desparasitado=True,
        apto_ninos=True,
        apto_perros=False,
        apto_gatos=True,
    ),
    dict(
        nombre="Rocky",
        especie="perro",
        raza="Criollo",
        sexo="macho",
        edad_meses=96,
        tamano="mediano",
        energia="baja",
        shelter_idx=0,
        historia="Rocky es un perro senior muy noble que fue entregado por su familia al mudarse. Necesita un hogar paciente.",
        tags=["senior", "necesita experiencia"],
        esterilizado=True,
        vacunas_al_dia=True,
        microchip=False,
        desparasitado=True,
        apto_ninos=True,
        apto_perros=True,
        apto_gatos=True,
    ),
    dict(
        nombre="Mia",
        especie="gato",
        raza="Siamés mestizo",
        sexo="hembra",
        edad_meses=24,
        tamano="pequeño",
        energia="media",
        shelter_idx=0,
        historia="Mia es curiosa y cariñosa, se lleva bien con otros gatos.",
        tags=["cariñosa", "curiosa"],
        esterilizado=True,
        vacunas_al_dia=True,
        microchip=True,
        desparasitado=True,
        apto_ninos=True,
        apto_perros=True,
        apto_gatos=True,
    ),
    dict(
        nombre="Toby",
        especie="perro",
        raza="Beagle mestizo",
        sexo="macho",
        edad_meses=6,
        tamano="pequeño",
        energia="alta",
        shelter_idx=1,
        historia="Toby es un cachorro lleno de energía, ideal para una familia activa.",
        tags=["cachorro", "juguetón"],
        esterilizado=False,
        vacunas_al_dia=True,
        microchip=False,
        desparasitado=True,
        apto_ninos=True,
        apto_perros=True,
        apto_gatos=False,
    ),
    dict(
        nombre="Bella",
        especie="perro",
        raza="Poodle mestizo",
        sexo="hembra",
        edad_meses=36,
        tamano="pequeño",
        energia="media",
        shelter_idx=1,
        historia="Bella es una perrita muy dulce, rescatada de una situación de maltrato. Está lista para confiar de nuevo.",
        tags=["dulce", "necesita experiencia"],
        esterilizado=True,
        vacunas_al_dia=True,
        microchip=True,
        desparasitado=True,
        apto_ninos=False,
        apto_perros=True,
        apto_gatos=True,
    ),
    dict(
        nombre="Simón",
        especie="gato",
        raza="Naranjo criollo",
        sexo="macho",
        edad_meses=14,
        tamano="mediano",
        energia="alta",
        shelter_idx=1,
        historia="Simón es muy activo y le encanta trepar. Necesita espacio para explorar.",
        tags=["activo", "trepador"],
        esterilizado=True,
        vacunas_al_dia=True,
        microchip=True,
        desparasitado=True,
        apto_ninos=True,
        apto_perros=False,
        apto_gatos=False,
    ),
    dict(
        nombre="Nina",
        especie="perro",
        raza="Schnauzer mestizo",
        sexo="hembra",
        edad_meses=60,
        tamano="pequeño",
        energia="baja",
        shelter_idx=1,
        historia="Nina es una perrita tranquila y muy apegada a las personas.",
        tags=["tranquila", "apegada"],
        esterilizado=True,
        vacunas_al_dia=True,
        microchip=True,
        desparasitado=True,
        apto_ninos=True,
        apto_perros=True,
        apto_gatos=True,
    ),
    dict(
        nombre="Duque",
        especie="perro",
        raza="Pastor mestizo",
        sexo="macho",
        edad_meses=30,
        tamano="grande",
        energia="alta",
        shelter_idx=2,
        historia="Duque es muy inteligente y aprende rápido. Necesita ejercicio diario y un dueño con experiencia.",
        tags=["inteligente", "necesita experiencia"],
        esterilizado=True,
        vacunas_al_dia=True,
        microchip=True,
        desparasitado=True,
        apto_ninos=True,
        apto_perros=False,
        apto_gatos=False,
    ),
    dict(
        nombre="Coco",
        especie="gato",
        raza="Mestiza",
        sexo="hembra",
        edad_meses=4,
        tamano="pequeño",
        energia="alta",
        shelter_idx=2,
        historia="Coco es una gatica cachorra muy juguetona, ideal para una casa con tiempo para jugar con ella.",
        tags=["cachorra", "juguetona"],
        esterilizado=False,
        vacunas_al_dia=True,
        microchip=False,
        desparasitado=True,
        apto_ninos=True,
        apto_perros=True,
        apto_gatos=True,
    ),
    dict(
        nombre="Zeus",
        especie="perro",
        raza="Rottweiler mestizo",
        sexo="macho",
        edad_meses=48,
        tamano="grande",
        energia="media",
        shelter_idx=2,
        historia="Zeus es un perro grande pero muy calmado en casa. Fue entrenado en obediencia básica.",
        tags=["calmado", "entrenado"],
        esterilizado=True,
        vacunas_al_dia=True,
        microchip=True,
        desparasitado=True,
        apto_ninos=False,
        apto_perros=True,
        apto_gatos=False,
    ),
    dict(
        nombre="Frida",
        especie="gato",
        raza="Persa mestiza",
        sexo="hembra",
        edad_meses=102,
        tamano="mediano",
        energia="baja",
        shelter_idx=2,
        historia="Frida es una gata senior muy tranquila que busca un hogar calmado para sus últimos años.",
        tags=["senior", "tranquila"],
        esterilizado=True,
        vacunas_al_dia=True,
        microchip=True,
        desparasitado=True,
        apto_ninos=True,
        apto_perros=True,
        apto_gatos=True,
    ),
    dict(
        nombre="Otto",
        especie="perro",
        raza="Bulldog francés mestizo",
        sexo="macho",
        edad_meses=20,
        tamano="pequeño",
        energia="baja",
        shelter_idx=0,
        historia="Otto es un perro relajado que disfruta más de un buen sofá que de correr.",
        tags=["relajado"],
        esterilizado=True,
        vacunas_al_dia=True,
        microchip=True,
        desparasitado=True,
        apto_ninos=True,
        apto_perros=True,
        apto_gatos=True,
    ),
    dict(
        nombre="Pelusa",
        especie="gato",
        raza="Angora mestiza",
        sexo="hembra",
        edad_meses=18,
        tamano="pequeño",
        energia="media",
        shelter_idx=1,
        historia="Pelusa es cariñosa con su familia pero tímida con desconocidos al principio.",
        tags=["cariñosa", "tímida"],
        esterilizado=True,
        vacunas_al_dia=True,
        microchip=True,
        desparasitado=True,
        apto_ninos=True,
        apto_perros=False,
        apto_gatos=True,
    ),
    dict(
        nombre="Rex",
        especie="perro",
        raza="Doberman mestizo",
        sexo="macho",
        edad_meses=15,
        tamano="grande",
        energia="alta",
        shelter_idx=2,
        historia="Rex es un perro joven y atlético que necesita mucho ejercicio y un dueño con experiencia.",
        tags=["atlético", "necesita experiencia"],
        esterilizado=True,
        vacunas_al_dia=True,
        microchip=True,
        desparasitado=True,
        apto_ninos=True,
        apto_perros=True,
        apto_gatos=False,
    ),
    dict(
        nombre="Chispa",
        especie="gato",
        raza="Mestiza",
        sexo="hembra",
        edad_meses=6,
        tamano="pequeño",
        energia="alta",
        shelter_idx=0,
        historia="Chispa es una bola de energía, siempre lista para jugar con cualquier cosa que se mueva.",
        tags=["cachorra", "juguetona"],
        esterilizado=False,
        vacunas_al_dia=True,
        microchip=False,
        desparasitado=True,
        apto_ninos=True,
        apto_perros=True,
        apto_gatos=False,
    ),
    dict(
        nombre="Canela",
        especie="perro",
        raza="Cocker mestizo",
        sexo="hembra",
        edad_meses=42,
        tamano="mediano",
        energia="media",
        shelter_idx=1,
        historia="Canela es equilibrada: le gusta pasear pero también disfruta de días tranquilos en casa.",
        tags=["equilibrada"],
        esterilizado=True,
        vacunas_al_dia=True,
        microchip=True,
        desparasitado=True,
        apto_ninos=True,
        apto_perros=True,
        apto_gatos=True,
    ),
]

# HomeProfiles diseñados a propósito para cubrir casos de alta/baja afinidad y regla dura
# (ver tests/api/test_affinity.py y feature 05-affinity-score en feature_list.json)
USERS = [
    dict(
        nombre="Ana Martínez",
        email="ana.martinez@example.co",
        ciudad="Bogotá",
        barrio="Usaquén",
        bio="Busco un compañero tranquilo para las tardes en el parque.",
        home=dict(
            vivienda="casa",
            espacio_exterior="patio",
            personas_en_casa=3,
            tiene_ninos=True,
            tiene_otros_perros=False,
            tiene_otros_gatos=False,
            horas_fuera_dia=5,
            experiencia_previa="algo",
            presupuesto_mensual_cop=200_000,
            preferencia_especies=["perro"],
            preferencia_tamanos=["mediano", "grande"],
            preferencia_energia="media",
        ),
    ),
    dict(
        nombre="Carlos Pérez",
        email="carlos.perez@example.co",
        ciudad="Bogotá",
        barrio="Chapinero",
        bio="Trabajo desde casa, tengo mucho tiempo y experiencia con mascotas.",
        home=dict(
            vivienda="apartamento",
            espacio_exterior="ninguno",
            personas_en_casa=1,
            tiene_ninos=False,
            tiene_otros_perros=False,
            tiene_otros_gatos=False,
            horas_fuera_dia=2,
            experiencia_previa="mucha",
            presupuesto_mensual_cop=300_000,
            preferencia_especies=["gato"],
            preferencia_tamanos=["pequeño"],
            preferencia_energia="baja",
        ),
    ),
    dict(
        nombre="Laura Gómez",
        email="laura.gomez@example.co",
        ciudad="Bogotá",
        barrio="Suba",
        bio="Tengo dos gatos en casa y busco ampliar la familia con cuidado.",
        home=dict(
            vivienda="casa",
            espacio_exterior="jardin",
            personas_en_casa=2,
            tiene_ninos=False,
            tiene_otros_perros=False,
            tiene_otros_gatos=True,
            horas_fuera_dia=6,
            experiencia_previa="mucha",
            presupuesto_mensual_cop=250_000,
            preferencia_especies=["gato", "perro"],
            preferencia_tamanos=["mediano"],
            preferencia_energia="media",
        ),
    ),
    dict(
        nombre="Diego Ramírez",
        email="diego.ramirez@example.co",
        ciudad="Bogotá",
        barrio="Engativá",
        bio="Vivimos en familia con niños pequeños y queremos un compañero paciente.",
        home=dict(
            vivienda="apartamento",
            espacio_exterior="patio",
            personas_en_casa=4,
            tiene_ninos=True,
            tiene_otros_perros=False,
            tiene_otros_gatos=False,
            horas_fuera_dia=4,
            experiencia_previa="algo",
            presupuesto_mensual_cop=180_000,
            preferencia_especies=["perro"],
            preferencia_tamanos=["pequeño", "mediano"],
            preferencia_energia="baja",
        ),
    ),
    dict(
        nombre="Sofía Torres",
        email="sofia.torres@example.co",
        ciudad="Bogotá",
        barrio="Kennedy",
        bio="Primera vez adoptando, quiero aprender y dar un buen hogar.",
        home=dict(
            vivienda="apartamento",
            espacio_exterior="ninguno",
            personas_en_casa=1,
            tiene_ninos=False,
            tiene_otros_perros=False,
            tiene_otros_gatos=False,
            horas_fuera_dia=10,
            experiencia_previa="ninguna",
            presupuesto_mensual_cop=50_000,
            preferencia_especies=[],
            preferencia_tamanos=[],
            preferencia_energia="baja",
        ),
    ),
]


def _download_or_placeholder(pet_id: int, nombre: str, especie: str) -> str:
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    jpg_path = IMAGES_DIR / f"pet_{pet_id}.jpg"
    svg_path = IMAGES_DIR / f"pet_{pet_id}.svg"

    if jpg_path.exists():
        return f"/media/{jpg_path.name}"
    if svg_path.exists():
        return f"/media/{svg_path.name}"

    url = (
        f"https://placedog.net/500/375?id={pet_id}"
        if especie == "perro"
        else "https://cataas.com/cat?width=500&height=375"
    )
    try:
        response = requests.get(url, timeout=DOWNLOAD_TIMEOUT_SECONDS)
        response.raise_for_status()
        jpg_path.write_bytes(response.content)
        return f"/media/{jpg_path.name}"
    except (requests.RequestException, OSError):
        colors = {"perro": "#E8EFE9", "gato": "#F3EDE0"}
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="500" height="375">
  <rect width="100%" height="100%" fill="{colors.get(especie, '#EFE9DC')}"/>
  <text x="50%" y="50%" font-family="sans-serif" font-size="28" fill="#3D3931"
        text-anchor="middle" dominant-baseline="middle">foto · {nombre}</text>
</svg>"""
        svg_path.write_text(svg, encoding="utf-8")
        return f"/media/{svg_path.name}"


def main() -> None:
    random.seed(RANDOM_SEED)

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        shelters = [Shelter(**data) for data in SHELTERS]
        session.add_all(shelters)
        session.flush()

        pets = []
        for pet_data in PETS:
            shelter_idx = pet_data.pop("shelter_idx")
            lat = round(random.uniform(*BOGOTA_LAT_RANGE), 6)
            lng = round(random.uniform(*BOGOTA_LNG_RANGE), 6)
            pets.append(Pet(shelter_id=shelters[shelter_idx].id, lat=lat, lng=lng, **pet_data))
        session.add_all(pets)
        session.flush()

        for pet in pets:
            foto_url = _download_or_placeholder(pet.id, pet.nombre, pet.especie)
            pet.fotos = [foto_url]
        session.flush()

        for user_data in USERS:
            home_data = user_data.pop("home")
            lat, lng = BARRIO_COORDS[user_data["barrio"]]
            user = User(lat=lat, lng=lng, **user_data)
            session.add(user)
            session.flush()
            session.add(HomeProfile(user_id=user.id, **home_data))

        session.commit()

        print(
            f"Seed completo: {len(shelters)} refugios, {len(pets)} mascotas, {len(USERS)} adoptantes."
        )
        print(f"Usuario demo (id={DEMO_USER_ID}): Ana Martínez")
    finally:
        session.close()


if __name__ == "__main__":
    main()
