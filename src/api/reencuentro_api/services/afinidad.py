"""Compatibilidad adoptante ↔ mascota (AD-03).

Función pura (sin I/O): ver `docs/decisions/0003-afinidad-calculada-al-vuelo.md`.
Ponderación y reglas duras: `docs/product-research.md` §5. Portada de la era
Adopta (`adopta-v1:src/api/adopta_api/services/affinity.py`) con los pesos y las
reglas duras **intactos** — lo que cambió está anotado abajo.

Trabaja sobre los **modelos** (`Pet`, `HomeProfile`), no sobre los schemas, igual
que `titulos.py`. Esa dirección importa: `descubrir.py` y `filtros.py` trabajan
sobre `PetOut`, así que pueden depender de este archivo pero nunca al revés (ver
`_dificultad_mascota`).
"""

from dataclasses import dataclass

from ..models.home_profile import HomeProfile
from ..models.pet import Pet

_ENERGIA_NIVEL = {"baja": 1, "media": 2, "alta": 3}
_TAMANO_NIVEL = {"pequeño": 1, "mediano": 2, "grande": 3}
_EXPERIENCIA_NIVEL = {"ninguna": 1, "algo": 2, "mucha": 3}
_COSTO_MENSUAL_ESTIMADO_COP = {"pequeño": 80_000, "mediano": 150_000, "grande": 220_000}
_HORAS_FUERA_MAX_OK = {1: 10, 2: 6, 3: 4}  # por nivel de energía de la mascota


@dataclass(frozen=True)
class AfinidadResultado:
    """Lo que el router traduce a `AfinidadOut`.

    ⚠️ `razones` es una **tupla**, no una lista: el dataclass es `frozen=True` y
    una lista dentro sería un campo inmutable con contenido mutable. La
    conversión a lista ocurre al construir `AfinidadOut(razones=list(...))`.
    """

    score: int
    explicacion: str
    razones: tuple[str, ...]
    incompatible: bool


def _score_energia(pet: Pet, home: HomeProfile) -> int:
    nivel = _ENERGIA_NIVEL[pet.energia]
    max_horas_ok = _HORAS_FUERA_MAX_OK[nivel]
    if home.horas_fuera_dia <= max_horas_ok:
        return 100
    exceso = home.horas_fuera_dia - max_horas_ok
    return max(0, 100 - exceso * 20)


def _score_tamano(pet: Pet, home: HomeProfile) -> int:
    nivel_mascota = _TAMANO_NIVEL[pet.tamano]
    capacidad_vivienda = {
        ("apartamento", "ninguno"): 1,
        ("apartamento", "patio"): 2,
        ("apartamento", "jardin"): 2,
        ("casa", "ninguno"): 2,
        ("casa", "patio"): 3,
        ("casa", "jardin"): 3,
    }.get((home.vivienda, home.espacio_exterior), 2)
    diferencia = abs(nivel_mascota - capacidad_vivienda)
    return max(0, 100 - diferencia * 30)


def _score_convivencia(pet: Pet, home: HomeProfile) -> int:
    score = 100
    if home.tiene_otros_perros and not pet.apto_perros:
        score -= 60
    return max(0, score)


def _score_preferencia(pet: Pet, home: HomeProfile) -> int:
    especies_pref = home.preferencia_especies or []
    tamanos_pref = home.preferencia_tamanos or []
    especie_ok = (not especies_pref) or (pet.especie in especies_pref)
    tamano_ok = (not tamanos_pref) or (pet.tamano in tamanos_pref)
    return (50 if especie_ok else 0) + (50 if tamano_ok else 0)


def _dificultad_mascota(pet: Pet) -> int:
    if "necesita experiencia" in (pet.tags or []) or pet.energia == "alta":
        return 3
    # 84 meses = 7 años. El literal se repite a propósito: `EDAD_MESES_SENIOR`
    # vive en el servicio de ordenamiento del deck, que trabaja sobre `PetOut`.
    # Importarlo desde aquí invertiría la capa (modelos → schemas) y crearía una
    # dependencia que el resto del repo no tiene. Si el umbral cambia, cambia en
    # los dos sitios; hay un test que fija esta separación.
    if pet.edad_meses > 84:
        return 2
    return 1


def _score_experiencia_presupuesto(pet: Pet, home: HomeProfile) -> int:
    nivel_experiencia = _EXPERIENCIA_NIVEL[home.experiencia_previa]
    dificultad = _dificultad_mascota(pet)
    score_experiencia = (
        100
        if nivel_experiencia >= dificultad
        else max(0, 100 - (dificultad - nivel_experiencia) * 40)
    )

    # El presupuesto es opcional (ver `models/home_profile.py`): quien no lo
    # declara conserva su afinidad calculada solo con la experiencia. Sin esta
    # línea, `None >= costo_estimado` lanza TypeError y revienta el deck entero
    # de cualquiera que haya dejado el campo vacío.
    if home.presupuesto_mensual_cop is None:
        return score_experiencia

    costo_estimado = _COSTO_MENSUAL_ESTIMADO_COP[pet.tamano]
    if home.presupuesto_mensual_cop >= costo_estimado:
        score_presupuesto = 100
    else:
        deficit = (costo_estimado - home.presupuesto_mensual_cop) / costo_estimado
        score_presupuesto = max(0, round(100 - deficit * 100))

    return round((score_experiencia + score_presupuesto) / 2)


def _regla_dura_incompatible(pet: Pet, home: HomeProfile) -> str | None:
    if home.tiene_ninos and not pet.apto_ninos:
        return "no es apta para hogares con niños"
    if home.tiene_otros_gatos and not pet.apto_gatos:
        return "no es apta para hogares con gatos"
    return None


def calcular_afinidad(pet: Pet, home: HomeProfile) -> AfinidadResultado:
    motivo_incompatible = _regla_dura_incompatible(pet, home)
    if motivo_incompatible:
        return AfinidadResultado(
            score=0,
            explicacion=f"Incompatible: {pet.nombre} {motivo_incompatible}.",
            # Una sola razón basta: la tarjeta se excluye del deck, no se está
            # argumentando a favor de un encuentro que no va a ocurrir.
            razones=(motivo_incompatible.capitalize(),),
            incompatible=True,
        )

    score_energia = _score_energia(pet, home)
    score_tamano = _score_tamano(pet, home)
    score_convivencia = _score_convivencia(pet, home)
    score_preferencia = _score_preferencia(pet, home)
    score_exp_presupuesto = _score_experiencia_presupuesto(pet, home)

    score_final = round(
        score_energia * 0.30
        + score_tamano * 0.20
        + score_convivencia * 0.20
        + score_preferencia * 0.15
        + score_exp_presupuesto * 0.15
    )

    explicacion = _explicar(pet, home, score_energia, score_tamano)
    razones = _razones(pet, home, score_energia, score_tamano)
    return AfinidadResultado(
        score=score_final,
        explicacion=explicacion,
        razones=razones,
        incompatible=False,
    )


_ENERGIA_FRASE = {
    "baja": "Energía tranquila",
    "media": "Energía media",
    "alta": "Mucha energía",
}

_RAZON_ESPECIE_PREFERIDA = {
    "perro": "Es un perro, como buscas",
    "gato": "Es un gato, como buscas",
    "otro": "Es de la especie que buscas",
}


def _explicar(pet: Pet, home: HomeProfile, score_energia: int, score_tamano: int) -> str:
    """El texto largo, en una sola frase — se conserva tal cual de adopta-v1."""
    energia_frase = {
        "baja": "energía tranquila",
        "media": "energía media",
        "alta": "mucha energía",
    }[pet.energia]
    if score_energia >= 70:
        rutina_frase = f"que encaja con tus {home.horas_fuera_dia} horas fuera al día"
    else:
        rutina_frase = f"que puede ser exigente con tus {home.horas_fuera_dia} horas fuera al día"

    if score_tamano >= 70:
        vivienda_frase = f"tamaño adecuado para tu {home.vivienda}"
    else:
        vivienda_frase = f"tamaño que puede quedar justo en tu {home.vivienda}"

    return f"{energia_frase.capitalize()} {rutina_frase}, y {vivienda_frase}."


def _razones(pet: Pet, home: HomeProfile, score_energia: int, score_tamano: int) -> tuple[str, ...]:
    """El porqué en frases cortas, para chips de tarjeta (estilo feature 38).

    Siempre devuelve **al menos tres**: energía, rutina y vivienda no dependen de
    ninguna condición, así que el acceptance de "≥2 razones" se cumple por
    construcción y no por suerte del hogar que consulte. Las demás se suman solo
    cuando el hogar las necesita — un hogar sin gatos no gana nada leyendo que la
    mascota se lleva bien con gatos.

    Son honestas, no publicitarias: cuando el encaje es malo lo dicen. El texto
    largo de `_explicar()` sigue existiendo para el detalle de la ficha.
    """
    energia_base = _ENERGIA_FRASE[pet.energia]
    if pet.energia == home.preferencia_energia:
        razones = [f"{energia_base}, como buscas"]
    else:
        razones = [f"{energia_base}, distinta de la que buscas"]

    if score_energia >= 70:
        razones.append(f"Encaja con tus {home.horas_fuera_dia} horas fuera al día")
    else:
        razones.append(f"Exigente para tus {home.horas_fuera_dia} horas fuera al día")

    if score_tamano >= 70:
        razones.append(f"Tamaño adecuado para tu {home.vivienda}")
    else:
        razones.append(f"Tamaño justo para tu {home.vivienda}")

    # Llegar hasta aquí ya significa que las reglas duras pasaron: si el hogar
    # tiene niños o gatos, la mascota es apta con ellos.
    if home.tiene_ninos:
        razones.append("Le va bien con niños, como necesitas")
    if home.tiene_otros_gatos:
        razones.append("Se lleva bien con gatos, como necesitas")
    if home.tiene_otros_perros:
        if pet.apto_perros:
            razones.append("Se lleva bien con otros perros, como necesitas")
        else:
            razones.append("Prefiere ser el único perro de la casa")

    if (home.preferencia_especies or []) and pet.especie in home.preferencia_especies:
        razones.append(_RAZON_ESPECIE_PREFERIDA[pet.especie])

    return tuple(razones)
