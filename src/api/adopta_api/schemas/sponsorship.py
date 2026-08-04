from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

PERIODICIDADES_VALIDAS = {"mensual", "unico"}


class SponsorshipIn(BaseModel):
    """Body de `POST /api/sponsorships` (feature 12-sponsorship).

    Registro de compromiso, sin movimiento de dinero real: no hay integración de
    pasarela de pago (design/prototypes/HANDOFF.md §11).
    """

    user_id: int
    pet_id: int
    monto_cop: int
    periodicidad: str

    @field_validator("monto_cop")
    @classmethod
    def monto_positivo(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("El monto debe ser mayor que 0")
        return v

    @field_validator("periodicidad")
    @classmethod
    def periodicidad_valida(cls, v: str) -> str:
        if v not in PERIODICIDADES_VALIDAS:
            raise ValueError(f"periodicidad debe ser una de {sorted(PERIODICIDADES_VALIDAS)}")
        return v


class SponsorshipPetResumen(BaseModel):
    id: int
    nombre: str
    fotos: list[str]


class SponsorshipOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pet: SponsorshipPetResumen
    monto_cop: int
    periodicidad: str
    activo: bool
    iniciado_en: datetime
    # Se asigna en el router (novedad de plantilla estática, sin scheduler real):
    # no viene de from_attributes.
    novedad: str | None = None


class MascotaNecesitaApoyoOut(BaseModel):
    """Resumen público de una mascota difícil de ubicar (feature 12-sponsorship).

    No hereda `PetOut`: esta lista es pública (sin `user_id`), no necesita cargar
    `afinidad` ni `shelter`.
    """

    id: int
    nombre: str
    fotos: list[str]
    historia: str
    monto_recaudado_cop: int
    porcentaje_cubierto: int
