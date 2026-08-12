#!/usr/bin/env python3
"""Seed determinista de Reencuentro: usuarios y reportes de mascotas por zona.

Nunca falla por falta de red: si no se puede descargar una foto, genera un
placeholder SVG local. Ver .claude/skills/seed-data/SKILL.md.

Determinista de verdad: coordenadas y fechas fijas (no random), timestamps
`creado_en`/`resuelto_en` explícitos — dos corridas seguidas producen
exactamente los mismos datos.

Uso: python3 scripts/seed.py
"""

import random
import sys
from datetime import date, datetime
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src" / "api"))

from reencuentro_api.media import subir_a_supabase, supabase_configurado  # noqa: E402
from reencuentro_api.models import Base, Report, SessionLocal, User, engine  # noqa: E402
from reencuentro_api.services.ciudades import ZONAS  # noqa: E402

RANDOM_SEED = 42
DEMO_USER_ID = 1  # Ana Martínez, primer usuario insertado — usado por src/web y por los tests
SEED_IMAGES_DIR = REPO_ROOT / "data" / "media" / "seed"
DOWNLOAD_TIMEOUT_SECONDS = 4

# El primer usuario insertado (id=1) es el usuario demo del frontend
# (src/web/src/lib/constants.ts::DEMO_USER_ID — deben mantenerse en sync).
USERS = [
    dict(nombre="Ana Martínez", email="ana@example.com", ciudad="Armenia", barrio="La Castellana"),
    dict(nombre="Carlos Gómez", email="carlos@example.com", ciudad="Pereira", barrio="Cuba"),
    dict(
        nombre="Luisa Fernanda Ríos",
        email="luisa@example.com",
        ciudad="Manizales",
        barrio="Palermo",
    ),
    dict(nombre="Jorge Palacios", email="jorge@example.com", ciudad="Quibdó", barrio="Niño Jesús"),
    dict(
        nombre="Valentina Mosquera",
        email="valentina@example.com",
        ciudad="Cali",
        barrio="San Fernando",
    ),
]

# Reportes alrededor del sismo del 2026-08-10, mayoría en el Eje Cafetero.
# Coordenadas fijas dentro del bounding box de cada zona (services/ciudades.py —
# verificado al final de main()). `user_idx` indexa USERS. Los dos primeros
# forman el par de coincidencia obvia (mismo tipo opuesto, misma especie, misma
# zona, ~600 m y un día de diferencia) que usan la demo y los tests de la
# feature 08. Los dos últimos están "reunidos" para la franja de la landing (09).
REPORTS = [
    dict(
        user_idx=0,
        tipo="perdido",
        especie="perro",
        nombre_mascota="Rocky",
        descripcion="Criollo mediano color miel, collar rojo. Saltó la reja cuando empezó el temblor.",
        zona="Armenia",
        barrio="La Castellana",
        lat=4.540,
        lng=-75.680,
        fecha_evento=date(2026, 8, 10),
        telefono_contacto="3001234561",
    ),
    dict(
        user_idx=1,
        tipo="encontrado",
        especie="perro",
        situacion="conmigo",
        descripcion="Perro criollo color miel con collar rojo, asustado pero sano. Lo tengo en mi casa.",
        zona="Armenia",
        barrio="Granada",
        lat=4.545,
        lng=-75.678,
        fecha_evento=date(2026, 8, 11),
        telefono_contacto="3001234562",
    ),
    dict(
        user_idx=0,
        tipo="perdido",
        especie="gato",
        nombre_mascota="Mishi",
        descripcion="Gata gris de ojos verdes, muy tímida. Se escondió tras la réplica y no volvió.",
        zona="Armenia",
        barrio="La Castellana",
        lat=4.525,
        lng=-75.700,
        fecha_evento=date(2026, 8, 10),
        telefono_contacto="3001234561",
    ),
    dict(
        user_idx=2,
        tipo="encontrado",
        especie="gato",
        situacion="vista",
        descripcion="Gato naranja merodeando un edificio evacuado. No se deja atrapar, le dejo comida.",
        zona="Armenia",
        barrio="Centro",
        lat=4.560,
        lng=-75.660,
        fecha_evento=date(2026, 8, 11),
        telefono_contacto="3001234563",
    ),
    dict(
        user_idx=3,
        tipo="perdido",
        especie="perro",
        nombre_mascota="Luna",
        descripcion="Labradora negra con mancha blanca en el pecho. Se soltó durante la evacuación.",
        zona="Armenia",
        barrio="La Fachada",
        lat=4.500,
        lng=-75.740,
        fecha_evento=date(2026, 8, 9),
        telefono_contacto="3001234564",
    ),
    dict(
        user_idx=1,
        tipo="perdido",
        especie="perro",
        nombre_mascota="Toby",
        descripcion="Beagle tricolor con placa. Escapó del patio la noche del sismo.",
        zona="Pereira",
        barrio="Cuba",
        lat=4.810,
        lng=-75.700,
        fecha_evento=date(2026, 8, 10),
        telefono_contacto="3001234562",
    ),
    dict(
        user_idx=2,
        tipo="encontrado",
        especie="perro",
        situacion="conmigo",
        descripcion="Perra pequeña blanca sin collar, la resguardé de los escombros del centro.",
        zona="Pereira",
        barrio="Centro",
        lat=4.800,
        lng=-75.690,
        fecha_evento=date(2026, 8, 12),
        telefono_contacto="3001234563",
    ),
    dict(
        user_idx=4,
        tipo="perdido",
        especie="gato",
        nombre_mascota="Nube",
        descripcion="Gato blanco esponjoso. Salió por la ventana rota tras la réplica del martes.",
        zona="Pereira",
        barrio="Pinares",
        lat=4.820,
        lng=-75.740,
        fecha_evento=date(2026, 8, 11),
        telefono_contacto="3001234565",
    ),
    dict(
        user_idx=3,
        tipo="encontrado",
        especie="otro",
        situacion="vista",
        descripcion="Loro verde con anillo en la pata, en un árbol del parque. Parece de casa.",
        zona="Pereira",
        barrio="El Lago",
        lat=4.780,
        lng=-75.660,
        fecha_evento=date(2026, 8, 10),
        telefono_contacto="3001234564",
    ),
    dict(
        user_idx=2,
        tipo="perdido",
        especie="perro",
        nombre_mascota="Max",
        descripcion="Pastor alemán adulto, manso. Se perdió cerca del estadio tras el derrumbe.",
        zona="Manizales",
        barrio="Palermo",
        lat=5.060,
        lng=-75.500,
        fecha_evento=date(2026, 8, 10),
        telefono_contacto="3001234563",
    ),
    dict(
        user_idx=0,
        tipo="encontrado",
        especie="gato",
        situacion="conmigo",
        descripcion="Gatita carey juvenil, hambrienta pero sana. La tengo en un guacal en casa.",
        zona="Manizales",
        barrio="Chipre",
        lat=5.070,
        lng=-75.520,
        fecha_evento=date(2026, 8, 11),
        telefono_contacto="3001234561",
    ),
    dict(
        user_idx=4,
        tipo="perdido",
        especie="gato",
        nombre_mascota="Simba",
        descripcion="Gato atigrado con collar azul y cascabel. No volvió después del temblor.",
        zona="Cali",
        barrio="San Fernando",
        lat=3.450,
        lng=-76.530,
        fecha_evento=date(2026, 8, 10),
        telefono_contacto="3001234565",
    ),
    dict(
        user_idx=1,
        tipo="encontrado",
        especie="perro",
        situacion="vista",
        descripcion="Perro grande café deambulando por el parque del barrio, cojea de una pata.",
        zona="Cali",
        barrio="El Peñón",
        lat=3.420,
        lng=-76.520,
        fecha_evento=date(2026, 8, 11),
        telefono_contacto="3001234562",
    ),
    dict(
        user_idx=3,
        tipo="perdido",
        especie="perro",
        nombre_mascota="Canela",
        descripcion="Criolla color canela, orejas caídas. Se perdió camino al albergue temporal.",
        zona="Quibdó",
        barrio="Niño Jesús",
        lat=5.695,
        lng=-76.660,
        fecha_evento=date(2026, 8, 11),
        telefono_contacto="3001234564",
    ),
    dict(
        user_idx=4,
        tipo="encontrado",
        especie="gato",
        situacion="conmigo",
        descripcion="Gato siamés muy dócil, apareció en mi balcón la noche del sismo.",
        zona="Bogotá",
        barrio="Chapinero",
        lat=4.650,
        lng=-74.060,
        fecha_evento=date(2026, 8, 10),
        telefono_contacto="3001234565",
    ),
    dict(
        user_idx=0,
        tipo="perdido",
        especie="perro",
        nombre_mascota="Firulais",
        descripcion="Criollo blanco y negro. Su familia lo encontró gracias a un reporte de la app.",
        zona="Armenia",
        barrio="La Castellana",
        lat=4.550,
        lng=-75.690,
        fecha_evento=date(2026, 8, 10),
        telefono_contacto="3001234561",
        estado="reunido",
        resuelto_en=datetime(2026, 8, 11, 15, 0),
    ),
    dict(
        user_idx=1,
        tipo="encontrado",
        especie="gato",
        situacion="conmigo",
        descripcion="Gata negra con mancha blanca. Su dueña la reconoció por la foto del reporte.",
        zona="Pereira",
        barrio="Cuba",
        lat=4.815,
        lng=-75.695,
        fecha_evento=date(2026, 8, 10),
        telefono_contacto="3001234562",
        estado="reunido",
        resuelto_en=datetime(2026, 8, 11, 18, 30),
    ),
]


def _obtener_foto(report_id: int, etiqueta: str, especie: str) -> tuple[str, bytes, str]:
    """(nombre, contenido, content_type) de la foto: descarga o placeholder SVG.

    La especie "otro" no tiene fuente de placeholders — va directo al SVG.
    """
    if especie in ("perro", "gato"):
        url = (
            f"https://placedog.net/500/375?id={report_id}"
            if especie == "perro"
            else "https://cataas.com/cat?width=500&height=375"
        )
        try:
            response = requests.get(url, timeout=DOWNLOAD_TIMEOUT_SECONDS)
            response.raise_for_status()
            return f"report_{report_id}.jpg", response.content, "image/jpeg"
        except (requests.RequestException, OSError):
            pass

    colors = {"perro": "#E8EFE9", "gato": "#F3EDE0"}
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="500" height="375">
  <rect width="100%" height="100%" fill="{colors.get(especie, '#EFE9DC')}"/>
  <text x="50%" y="50%" font-family="sans-serif" font-size="28" fill="#3D3931"
        text-anchor="middle" dominant-baseline="middle">foto · {etiqueta}</text>
</svg>"""
    return f"report_{report_id}.svg", svg.encode("utf-8"), "image/svg+xml"


def _download_or_placeholder(report_id: int, etiqueta: str, especie: str) -> str:
    """Foto del reporte: al bucket de Supabase si está configurado (despliegue,
    ADR 0006), o al filesystem local con caché como siempre (dev)."""
    if supabase_configurado():
        nombre, contenido, content_type = _obtener_foto(report_id, etiqueta, especie)
        return subir_a_supabase(nombre, contenido, content_type)

    SEED_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    jpg_path = SEED_IMAGES_DIR / f"report_{report_id}.jpg"
    svg_path = SEED_IMAGES_DIR / f"report_{report_id}.svg"

    if jpg_path.exists():
        return f"/media/seed/{jpg_path.name}"
    if svg_path.exists():
        return f"/media/seed/{svg_path.name}"

    nombre, contenido, _content_type = _obtener_foto(report_id, etiqueta, especie)
    (SEED_IMAGES_DIR / nombre).write_bytes(contenido)
    return f"/media/seed/{nombre}"


def main() -> None:
    random.seed(RANDOM_SEED)

    for datos in REPORTS:
        caja = ZONAS[datos["zona"]]
        dentro = caja["lat_min"] <= datos["lat"] <= caja["lat_max"] and (
            caja["lng_min"] <= datos["lng"] <= caja["lng_max"]
        )
        if not dentro:
            raise SystemExit(
                f"Reporte fuera del bounding box de {datos['zona']}: {datos['lat']},{datos['lng']}"
            )

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        # `creado_en` explícito también en los usuarios: el default `datetime.now`
        # del modelo rompería el determinismo entre corridas (hallazgo del revisor).
        users = [User(creado_en=datetime(2026, 8, 12, 8, 0), **datos) for datos in USERS]
        session.add_all(users)
        session.flush()

        reports = []
        for datos in REPORTS:
            datos = dict(datos)
            user = users[datos.pop("user_idx")]
            reports.append(Report(user_id=user.id, creado_en=datetime(2026, 8, 12, 8, 0), **datos))
        session.add_all(reports)
        session.flush()

        for report in reports:
            etiqueta = report.nombre_mascota or report.especie
            report.foto_url = _download_or_placeholder(report.id, etiqueta, report.especie)

        session.commit()
        activos = sum(1 for r in reports if r.estado == "activo")
        reunidos = len(reports) - activos
        destino = "Postgres remoto" if engine.dialect.name == "postgresql" else "data/app.db"
        print(
            f"Seed listo: {len(users)} usuarios, {len(reports)} reportes "
            f"({activos} activos, {reunidos} reunidos) en {destino}"
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
