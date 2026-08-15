#!/usr/bin/env python3
"""Seed determinista de Reencuentro: usuarios, reportes, organizaciones y adopción.

Nunca falla por falta de red: si no se puede descargar una foto, genera un
placeholder SVG local. Ver .claude/skills/seed-data/SKILL.md.

Determinista de verdad: coordenadas y fechas fijas (no random), timestamps
`creado_en`/`resuelto_en`/`publicado_en` explícitos — dos corridas seguidas
producen exactamente los mismos datos.

⚠️ Hace `drop_all`: **jamás** se corre contra la base de producción.

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
from reencuentro_api.models import (  # noqa: E402
    Base,
    HomeProfile,
    Organizacion,
    Pet,
    Report,
    SessionLocal,
    User,
    engine,
)
from reencuentro_api.services.ciudades import ZONA_OTRO, ZONAS, zona_valida  # noqa: E402

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
        raza="Criollo / mestizo",
        color="Miel / dorado",
        tamano="mediano",
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
        raza="Criollo / mestizo",
        color="Miel / dorado",
        tamano="mediano",
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
        raza="Criollo / mestizo",
        color="Gris",
        tamano="pequeño",
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
        raza="Criollo / mestizo",
        color="Naranja",
        tamano="mediano",
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
        raza="Labrador",
        color="Negro",
        tamano="grande",
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
        raza="Beagle",
        color="Tricolor",
        tamano="mediano",
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
        raza="Criollo / mestizo",
        color="Blanco",
        tamano="pequeño",
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
        raza="Criollo / mestizo",
        color="Blanco",
        tamano="mediano",
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
        raza="Pastor Alemán",
        color="Café",
        tamano="grande",
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
        raza="Criollo / mestizo",
        color="Tricolor",
        tamano="pequeño",
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
        raza="Criollo / mestizo",
        color="Atigrado",
        tamano="mediano",
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
        raza="Criollo / mestizo",
        color="Café",
        tamano="grande",
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
        raza="Criollo / mestizo",
        color="Miel / dorado",
        tamano="mediano",
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
        raza="Siamés",
        color="Gris",
        tamano="mediano",
        descripcion="Gato siamés muy dócil, apareció en mi balcón la noche del sismo.",
        zona="Bogotá",
        barrio="Chapinero",
        lat=4.650,
        lng=-74.060,
        fecha_evento=date(2026, 8, 10),
        telefono_contacto="3001234565",
    ),
    # Medellín (feature 26): un par perdido/encontrado cercano en el Valle de Aburrá.
    dict(
        user_idx=2,
        tipo="perdido",
        especie="perro",
        nombre_mascota="Simón",
        raza="Golden Retriever",
        color="Miel / dorado",
        tamano="grande",
        descripcion="Golden dorado con pañoleta verde. Se asustó con una réplica en Laureles.",
        zona="Medellín",
        barrio="Laureles",
        lat=6.245,
        lng=-75.595,
        fecha_evento=date(2026, 8, 11),
        telefono_contacto="3001234563",
    ),
    dict(
        user_idx=4,
        tipo="encontrado",
        especie="perro",
        situacion="vista",
        raza="Golden Retriever",
        color="Miel / dorado",
        tamano="grande",
        descripcion="Perro dorado grande con pañoleta, ronda el parque de El Poblado. No se deja atrapar.",
        zona="Medellín",
        barrio="El Poblado",
        lat=6.209,
        lng=-75.567,
        fecha_evento=date(2026, 8, 12),
        telefono_contacto="3001234565",
    ),
    dict(
        user_idx=0,
        tipo="perdido",
        especie="perro",
        nombre_mascota="Firulais",
        raza="Criollo / mestizo",
        color="Bicolor (manchas)",
        tamano="mediano",
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
        raza="Criollo / mestizo",
        color="Bicolor (manchas)",
        tamano="pequeño",
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


# Red de apoyo (feature 32) que además publica mascotas en adopción (AD-01).
# `user_idx` indexa USERS: la organización la registra un usuario real del seed,
# que es el único que puede publicar mascotas a su nombre (403 en el router).
ORGANIZACIONES = [
    dict(
        user_idx=0,
        tipo="fundacion",
        nombre="Fundación Huellitas del Quindío",
        descripcion="Refugio temporal para mascotas rescatadas del sismo. Damos alojamiento, comida y atención veterinaria mientras aparecen sus familias o llega una nueva.",
        zona="Armenia",
        barrio="La Castellana",
        direccion="Cra 14 #10-25, Armenia",
        lat=4.535,
        lng=-75.681,
        telefono_contacto="3001234561",
        horario="Lunes a sábado, 8:00 a 17:00",
        como_donar="Nequi 300 123 4561 o llevando alimento al refugio",
    ),
    dict(
        user_idx=1,
        tipo="fundacion",
        nombre="Refugio Patas del Otún",
        descripcion="Hogar de paso comunitario en Pereira. Trabajamos con familias voluntarias que reciben mascotas mientras se recuperan del sismo.",
        zona="Pereira",
        barrio="Cuba",
        direccion="Calle 72 #26-14, Pereira",
        lat=4.813,
        lng=-75.696,
        telefono_contacto="3001234562",
        horario="Todos los días, 9:00 a 18:00",
        como_donar="Nequi 300 123 4562",
    ),
    dict(
        user_idx=2,
        tipo="veterinaria",
        nombre="Veterinaria San Francisco",
        descripcion="Atendemos gratis a las mascotas rescatadas del sismo y damos en adopción las que nadie reclamó tras la valoración médica.",
        zona="Manizales",
        barrio="Palermo",
        direccion="Av. Santander #48-30, Manizales",
        lat=5.070,
        lng=-75.514,
        telefono_contacto="3001234563",
        horario="Lunes a viernes, 7:00 a 19:00",
    ),
]

# Mascotas en adopción (AD-01). Cada una cuelga de una organización
# (`organizacion_idx` → ORGANIZACIONES) **o** de un rescatista individual
# (`user_idx` → USERS), nunca de ambos: `ck_pets_publicador_exclusivo` rechaza
# la fila si se meten las dos claves. Las de rescatista llevan
# `telefono_contacto` obligatorio porque el modelo `User` no tiene teléfono.
# Cobertura que consumen las features siguientes (fijada en
# tests/api/test_seed_pets.py): al menos una senior (`edad_meses > 84`) y una
# con tag "necesita experiencia" para el deck de AD-03, y una adoptada con
# `adoptado_en` para la franja de celebración de AD-05.
PETS = [
    dict(
        organizacion_idx=0,
        nombre="Nala",
        especie="perro",
        raza="Criollo / mestizo",
        sexo="hembra",
        edad_meses=18,
        tamano="mediano",
        energia="alta",
        historia="Llegó al refugio dos días después del sismo, flaca y con una pata raspada. Ya está recuperada y es pura fiesta: saluda a todo el que entra y aprende trucos por una galleta.",
        tags=["juguetona", "buena con niños"],
        esterilizado=True,
        vacunas_al_dia=True,
        desparasitado=True,
        zona="Armenia",
        barrio="La Castellana",
        lat=4.536,
        lng=-75.679,
    ),
    dict(
        organizacion_idx=0,
        nombre="Tomás",
        especie="gato",
        raza="Criollo / mestizo",
        sexo="macho",
        edad_meses=96,
        tamano="pequeño",
        energia="baja",
        historia="Gato adulto que apareció en un edificio evacuado del centro. Nadie lo reclamó. Duerme casi todo el día, se deja cepillar y busca regazo apenas alguien se sienta.",
        tags=["senior", "tranquilo"],
        esterilizado=True,
        vacunas_al_dia=True,
        microchip=True,
        desparasitado=True,
        apto_perros=False,
        zona="Armenia",
        barrio="Centro",
        lat=4.541,
        lng=-75.671,
    ),
    dict(
        organizacion_idx=1,
        nombre="Bonita",
        especie="perro",
        raza="Pastor Alemán",
        sexo="hembra",
        edad_meses=60,
        tamano="grande",
        energia="media",
        historia="Cuidaba una bodega que se vino abajo. Es leal y obediente, pero desconfía de los desconocidos y no tolera a otros perros: necesita una familia con experiencia y patio propio.",
        tags=["necesita experiencia"],
        esterilizado=True,
        vacunas_al_dia=True,
        desparasitado=True,
        apto_ninos=False,
        apto_perros=False,
        apto_gatos=False,
        zona="Pereira",
        barrio="Centro",
        lat=4.812,
        lng=-75.702,
        # Está en un hogar de paso con su propio contacto, no en la sede.
        telefono_contacto="3001234572",
    ),
    dict(
        organizacion_idx=2,
        nombre="Pelusa",
        especie="gato",
        raza="Criollo / mestizo",
        sexo="hembra",
        edad_meses=8,
        tamano="pequeño",
        energia="media",
        historia="Llegó a la veterinaria en una caja, con tres semanas de nacida. Se crió entre las manos del equipo y encontró familia en Manizales: la primera adopción del módulo.",
        tags=["juguetona", "sociable"],
        esterilizado=True,
        vacunas_al_dia=True,
        desparasitado=True,
        zona="Manizales",
        barrio="Palermo",
        lat=5.066,
        lng=-75.509,
        estado="adoptado",
        adoptado_en=datetime(2026, 8, 14, 16, 30),
    ),
    dict(
        user_idx=3,
        nombre="Copito",
        especie="perro",
        raza="Criollo / mestizo",
        sexo="macho",
        edad_meses=4,
        tamano="pequeño",
        energia="alta",
        historia="Lo saqué de debajo de una placa caída en Quibdó, con su hermano. El hermano ya tiene casa; él sigue conmigo, mordiendo cordones y persiguiendo gallinas.",
        tags=["cachorro", "juguetón"],
        vacunas_al_dia=True,
        desparasitado=True,
        zona="Quibdó",
        barrio="Niño Jesús",
        lat=5.693,
        lng=-76.658,
        telefono_contacto="3001234564",
    ),
    dict(
        user_idx=4,
        nombre="Manchas",
        especie="perro",
        raza="Beagle",
        sexo="macho",
        edad_meses=36,
        tamano="mediano",
        energia="media",
        historia="Apareció en mi cuadra la semana del sismo y nunca se fue. Preguntamos casa por casa y nadie lo reconoció. Es tragón, dormilón y bueno con los niños del edificio.",
        tags=["sociable", "buena con niños"],
        esterilizado=True,
        vacunas_al_dia=True,
        desparasitado=True,
        zona="Cali",
        barrio="San Fernando",
        lat=3.448,
        lng=-76.535,
        telefono_contacto="3001234565",
    ),
    dict(
        user_idx=1,
        nombre="Lía",
        especie="gato",
        raza="Siamés",
        sexo="hembra",
        edad_meses=24,
        tamano="mediano",
        energia="media",
        historia="La recogí de una terraza el día de la réplica. Es habladora, sigue a la gente por la casa y se lleva bien con el otro gato de mi apartamento.",
        tags=["sociable"],
        esterilizado=True,
        vacunas_al_dia=True,
        desparasitado=True,
        apto_perros=False,
        zona="Pereira",
        barrio="Cuba",
        lat=4.806,
        lng=-75.688,
        telefono_contacto="3001234562",
    ),
    dict(
        user_idx=2,
        nombre="Duque",
        especie="perro",
        raza="Labrador",
        sexo="macho",
        edad_meses=108,
        tamano="grande",
        energia="baja",
        historia="Su familia se fue a un albergue donde no aceptan mascotas y me pidieron cuidarlo. Nunca volvieron. Camina despacio, ronca fuerte y solo quiere una cama y compañía.",
        tags=["senior", "tranquilo"],
        esterilizado=True,
        vacunas_al_dia=True,
        microchip=True,
        desparasitado=True,
        zona="Manizales",
        barrio="Chipre",
        lat=5.072,
        lng=-75.522,
        telefono_contacto="3001234563",
    ),
]

# Perfil de hogar de la usuaria demo (AD-03 paso 2). Uno solo, el de Ana
# Martínez (`user_idx=0` → id 1, el DEMO_USER_ID del frontend): sin él, el score
# de afinidad con sus razones no se puede ver en el recorrido manual ni probar
# de extremo a extremo, porque quien no tiene perfil recibe `afinidad: null`.
#
# Los valores están elegidos para que el deck muestre **variedad** contra las 8
# mascotas de PETS, no todo 100 ni todo incompatible: casa con patio favorece a
# las medianas y grandes por encima de las pequeñas, 6 horas fuera al día
# penaliza a las de energía alta pero no a las demás, la experiencia "algo" no
# alcanza para las difíciles, y `tiene_ninos` deja fuera por regla dura a la
# única con `apto_ninos=False` (Bonita) sin vaciar el deck.
# Cobertura fijada en tests/api/test_seed_pets.py.
HOME_PROFILE = dict(
    user_idx=0,
    vivienda="casa",
    espacio_exterior="patio",
    personas_en_casa=3,
    tiene_ninos=True,
    tiene_otros_perros=False,
    tiene_otros_gatos=False,
    horas_fuera_dia=6,
    experiencia_previa="algo",
    presupuesto_mensual_cop=180_000,
    preferencia_especies=["perro", "gato"],
    preferencia_tamanos=["mediano", "grande"],
    preferencia_energia="media",
)

# placedog.net elige la foto por `id`: las mascotas en adopción desplazan el
# suyo para no repetir exactamente las fotos de los reportes (los gatos ya
# varían solos, cataas.com devuelve uno distinto en cada petición).
DESPLAZAMIENTO_FOTO_POR_PREFIJO = {"report": 0, "pet": 100}


def _validar_pin(descripcion: str, zona: str, lat: float | None, lng: float | None) -> None:
    """Aborta el seed si el pin cae fuera del bounding box de su zona.

    Misma validación para reportes, organizaciones y mascotas: la fuente de
    verdad de las cajas es `services/ciudades.py`, nunca constantes duplicadas
    aquí. La zona "Otro" no tiene caja propia (el pin va sobre el mapa
    nacional), y las mascotas pueden no tener pin — en ambos casos no hay nada
    que verificar.
    """
    if not zona_valida(zona):
        raise SystemExit(f"{descripcion}: zona desconocida '{zona}'")
    if zona == ZONA_OTRO or lat is None or lng is None:
        return

    caja = ZONAS[zona]
    dentro = caja["lat_min"] <= lat <= caja["lat_max"] and (
        caja["lng_min"] <= lng <= caja["lng_max"]
    )
    if not dentro:
        raise SystemExit(f"{descripcion} fuera del bounding box de {zona}: {lat},{lng}")


def _obtener_foto(
    entidad_id: int, etiqueta: str, especie: str, prefijo: str = "report"
) -> tuple[str, bytes, str]:
    """(nombre, contenido, content_type) de la foto: descarga o placeholder SVG.

    `prefijo` decide el nombre del archivo: `report_{id}` para los reportes (el
    default histórico, no se puede cambiar sin dejar huérfanas las fotos ya
    generadas en `data/media/seed/`) y `pet_{id}` para las mascotas en adopción.

    La especie "otro" no tiene fuente de placeholders — va directo al SVG.
    """
    if especie in ("perro", "gato"):
        foto_id = entidad_id + DESPLAZAMIENTO_FOTO_POR_PREFIJO.get(prefijo, 0)
        url = (
            f"https://placedog.net/500/375?id={foto_id}"
            if especie == "perro"
            else "https://cataas.com/cat?width=500&height=375"
        )
        try:
            response = requests.get(url, timeout=DOWNLOAD_TIMEOUT_SECONDS)
            response.raise_for_status()
            return f"{prefijo}_{entidad_id}.jpg", response.content, "image/jpeg"
        except (requests.RequestException, OSError):
            pass

    colors = {"perro": "#E8EFE9", "gato": "#F3EDE0"}
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="500" height="375">
  <rect width="100%" height="100%" fill="{colors.get(especie, '#EFE9DC')}"/>
  <text x="50%" y="50%" font-family="sans-serif" font-size="28" fill="#3D3931"
        text-anchor="middle" dominant-baseline="middle">foto · {etiqueta}</text>
</svg>"""
    return f"{prefijo}_{entidad_id}.svg", svg.encode("utf-8"), "image/svg+xml"


def _download_or_placeholder(
    entidad_id: int, etiqueta: str, especie: str, prefijo: str = "report"
) -> str:
    """Foto de un reporte (`prefijo="report"`) o de una mascota en adopción
    (`prefijo="pet"`): al bucket de Supabase si está configurado (despliegue,
    ADR 0006), o al filesystem local con caché como siempre (dev)."""
    if supabase_configurado():
        nombre, contenido, content_type = _obtener_foto(entidad_id, etiqueta, especie, prefijo)
        return subir_a_supabase(nombre, contenido, content_type)

    SEED_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    jpg_path = SEED_IMAGES_DIR / f"{prefijo}_{entidad_id}.jpg"
    svg_path = SEED_IMAGES_DIR / f"{prefijo}_{entidad_id}.svg"

    if jpg_path.exists():
        return f"/media/seed/{jpg_path.name}"
    if svg_path.exists():
        return f"/media/seed/{svg_path.name}"

    nombre, contenido, _content_type = _obtener_foto(entidad_id, etiqueta, especie, prefijo)
    (SEED_IMAGES_DIR / nombre).write_bytes(contenido)
    return f"/media/seed/{nombre}"


def main() -> None:
    random.seed(RANDOM_SEED)

    for datos in REPORTS:
        _validar_pin(
            f"Reporte de {datos.get('nombre_mascota') or datos['especie']}",
            datos["zona"],
            datos["lat"],
            datos["lng"],
        )
    for datos in ORGANIZACIONES:
        _validar_pin(datos["nombre"], datos["zona"], datos["lat"], datos["lng"])
    for datos in PETS:
        _validar_pin(datos["nombre"], datos["zona"], datos.get("lat"), datos.get("lng"))
        # Mismo invariante que `ck_pets_publicador_exclusivo` y `PetIn`, pero
        # con un mensaje legible: si no, el seed muere con un IntegrityError.
        de_organizacion = datos.get("organizacion_idx") is not None
        de_rescatista = datos.get("user_idx") is not None
        if de_organizacion == de_rescatista:
            raise SystemExit(
                f"{datos['nombre']}: una mascota en adopción cuelga de una "
                "organización O de un rescatista, exactamente uno"
            )
        if de_rescatista and not (datos.get("telefono_contacto") or "").strip():
            raise SystemExit(f"{datos['nombre']}: un rescatista necesita teléfono de contacto")

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        # `creado_en` explícito también en los usuarios: el default `datetime.now`
        # del modelo rompería el determinismo entre corridas (hallazgo del revisor).
        users = [User(creado_en=datetime(2026, 8, 12, 8, 0), **datos) for datos in USERS]
        session.add_all(users)
        session.flush()

        # El perfil de hogar cuelga del usuario y su PK **es** `user_id`: no hay
        # id propio ni fecha de completado, la fila existiendo ya es la señal.
        datos_hogar = dict(HOME_PROFILE)
        session.add(HomeProfile(user_id=users[datos_hogar.pop("user_idx")].id, **datos_hogar))
        session.flush()

        # Orden de inserción: usuarios → organizaciones (cuelgan de usuarios) →
        # mascotas (cuelgan de organizaciones o de usuarios) → reportes. Cada
        # `flush()` es el que da los ids que necesita el nivel siguiente.
        organizaciones = []
        for datos in ORGANIZACIONES:
            datos = dict(datos)
            user = users[datos.pop("user_idx")]
            organizaciones.append(
                Organizacion(user_id=user.id, creado_en=datetime(2026, 8, 12, 8, 0), **datos)
            )
        session.add_all(organizaciones)
        session.flush()

        pets = []
        for datos in PETS:
            datos = dict(datos)
            organizacion_idx = datos.pop("organizacion_idx", None)
            user_idx = datos.pop("user_idx", None)
            pets.append(
                Pet(
                    organizacion_id=(
                        organizaciones[organizacion_idx].id
                        if organizacion_idx is not None
                        else None
                    ),
                    user_id=users[user_idx].id if user_idx is not None else None,
                    # Explícito por lo mismo que `creado_en` de los usuarios: el
                    # default del modelo es `datetime.now`, que rompe el determinismo.
                    publicado_en=datetime(2026, 8, 12, 8, 0),
                    **datos,
                )
            )
        session.add_all(pets)
        session.flush()

        for pet in pets:
            # `fotos` es una lista JSON sin MutableList: se reasigna completa,
            # nunca se muta in-place (no se persistiría).
            pet.fotos = [_download_or_placeholder(pet.id, pet.nombre, pet.especie, prefijo="pet")]

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
        adoptadas = sum(1 for p in pets if p.estado == "adoptado")
        destino = "Postgres remoto" if engine.dialect.name == "postgresql" else "data/app.db"
        print(
            f"Seed listo: {len(users)} usuarios, {len(reports)} reportes "
            f"({activos} activos, {reunidos} reunidos), {len(organizaciones)} organizaciones, "
            f"{len(pets)} mascotas en adopción ({len(pets) - adoptadas} disponibles, "
            f"{adoptadas} adoptadas) en {destino}"
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
