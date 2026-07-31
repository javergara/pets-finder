from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .user import User


class HomeProfile(Base):
    """Cuestionario de hogar. En el MVP se siembra sintético (feature 08 lo hace interactivo)."""

    __tablename__ = "home_profiles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    vivienda: Mapped[str] = mapped_column(String(40))  # "apartamento" | "casa"
    espacio_exterior: Mapped[str] = mapped_column(String(40))  # "ninguno" | "patio" | "jardin"
    personas_en_casa: Mapped[int] = mapped_column(Integer, default=1)
    tiene_ninos: Mapped[bool] = mapped_column(Boolean, default=False)
    tiene_otros_perros: Mapped[bool] = mapped_column(Boolean, default=False)
    tiene_otros_gatos: Mapped[bool] = mapped_column(Boolean, default=False)
    horas_fuera_dia: Mapped[int] = mapped_column(Integer)
    experiencia_previa: Mapped[str] = mapped_column(String(40))  # "ninguna"|"algo"|"mucha"
    presupuesto_mensual_cop: Mapped[int] = mapped_column(Integer)
    preferencia_especies: Mapped[list[str]] = mapped_column(JSON, default=list)
    preferencia_tamanos: Mapped[list[str]] = mapped_column(JSON, default=list)
    preferencia_energia: Mapped[str] = mapped_column(String(20))  # "baja"|"media"|"alta"

    user: Mapped["User"] = relationship(back_populates="home_profile")
