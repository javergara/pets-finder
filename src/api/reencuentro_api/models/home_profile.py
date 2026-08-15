from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class HomeProfile(Base):
    """Perfil de hogar del adoptante: el input del cálculo de afinidad.

    Portado de la era Adopta (`adopta-v1`) y adaptado al stack actual. Se
    adelanta de AD-04 a AD-03 por una razón de código: `calcular_afinidad(pet:
    Pet, home: HomeProfile)` no puede existir sin este modelo, y si el deck
    consultara `home_profiles` sin que la tabla exista en producción la ruta
    respondería 500 (`SKIP_DB_CREATE_ALL=1` no crea ninguna tabla por su
    cuenta). El contrato HTTP y el wizard son de AD-04.

    **`user_id` es la llave primaria**, sin `id` propio: hay como máximo un
    perfil por persona, y la existencia de la fila *es* la señal de
    "cuestionario completo" — no hace falta una columna `completado_en`.
    Guardar de nuevo reemplaza la misma fila (el upsert de AD-04).

    ⚠️ **No declara `relationship()` con `User`, y es deliberado.** El modelo de
    `adopta-v1` traía `user: Mapped["User"] = relationship(back_populates=
    "home_profile")`; el `User` de este repo no tiene ese atributo, así que
    copiarlo tal cual hace saltar `InvalidRequestError` al configurar los
    mappers y rompe el **import de toda la app**, no un endpoint. Ningún modelo
    de este stack declara relaciones salvo `Report.fotos_adicionales`: se
    resuelve con queries explícitas.

    `presupuesto_mensual_cop` es **opcional** (decisión de producto): pedirle a
    alguien un presupuesto mensual en COP en plena emergencia añade fricción y
    tono equivocado. Quien no lo dé conserva el resto de su perfil y
    `services/afinidad.py` degrada a solo-experiencia en vez de comparar contra
    `None` (que sería un `TypeError` y reventaría el deck).

    ⚠️ `preferencia_especies` y `preferencia_tamanos` son columnas JSON **sin
    `MutableList`**, igual que `Pet.fotos`/`Pet.tags`: nunca se mutan in-place
    (`home.preferencia_especies.append(...)` no se persiste), se reasigna la
    lista completa.
    """

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
    presupuesto_mensual_cop: Mapped[int | None] = mapped_column(Integer, nullable=True)
    preferencia_especies: Mapped[list[str]] = mapped_column(JSON, default=list)
    preferencia_tamanos: Mapped[list[str]] = mapped_column(JSON, default=list)
    preferencia_energia: Mapped[str] = mapped_column(String(20))  # "baja"|"media"|"alta"
