"""Cálculo de compatibilidad adoptante<->mascota.

Función pura (sin I/O): ver docs/decisions/0003-afinidad-calculada-al-vuelo.md.
Ponderación y reglas duras: docs/product-research.md §5.
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
    score: int
    explicacion: str
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
    if pet.edad_meses > 84:  # mascota senior, > 7 años
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
    return AfinidadResultado(score=score_final, explicacion=explicacion, incompatible=False)


def _explicar(pet: Pet, home: HomeProfile, score_energia: int, score_tamano: int) -> str:
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
