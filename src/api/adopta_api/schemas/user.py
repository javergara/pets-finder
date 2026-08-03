from datetime import datetime

from pydantic import BaseModel, ConfigDict


class HomeProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    vivienda: str
    espacio_exterior: str
    personas_en_casa: int
    tiene_ninos: bool
    tiene_otros_perros: bool
    tiene_otros_gatos: bool
    horas_fuera_dia: int
    experiencia_previa: str
    presupuesto_mensual_cop: int
    preferencia_especies: list[str]
    preferencia_tamanos: list[str]
    preferencia_energia: str


class UserMetricsOut(BaseModel):
    matches_activos: int
    visitas_agendadas: int
    # Siempre 0: no existe tabla Sponsorship todavía (feature 12-sponsorship, backlog).
    apadrinamientos: int


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    email: str
    ciudad: str
    barrio: str | None
    avatar_url: str | None
    bio: str | None
    creado_en: datetime
    # Se asignan en el router (requieren cálculo/join), no vienen directo de from_attributes.
    home_profile: HomeProfileOut | None = None
    metricas: UserMetricsOut | None = None
