from datetime import date, datetime, timezone

from sqlalchemy import JSON, Date, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Report(Base):
    """Reporte de mascota perdida (dueño) o encontrada (rescatista).

    Un solo modelo para ambos tipos (ADR 0005 §2): los únicos campos asimétricos
    son `nombre_mascota` (solo tiene sentido en "perdido") y `situacion` (solo en
    "encontrado": "conmigo" = la tiene resguardada, "vista" = la vio pero no pudo
    atraparla). La validación condicional vive en el schema (ReportIn), no aquí.

    `zona` es una de las claves de services/ciudades.py::ZONAS o "Otro" (con la
    ciudad real en `ciudad_texto`). `estado` solo tiene dos valores: "activo" y
    "reunido" — nunca hay un estado de fracaso (docs/product-research.md §4).
    """

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    tipo: Mapped[str] = mapped_column(String(20))  # "perdido" | "encontrado"
    especie: Mapped[str] = mapped_column(String(20))  # "perro" | "gato" | "otro"
    nombre_mascota: Mapped[str | None] = mapped_column(String(80), nullable=True)
    # Características predefinidas para filtrar (feature 15): opcionales, con las
    # opciones definidas en el frontend (lib/caracteristicas.ts). Nullable también
    # porque los reportes anteriores a la feature no las tienen.
    raza: Mapped[str | None] = mapped_column(String(40), nullable=True)
    color: Mapped[str | None] = mapped_column(String(40), nullable=True)
    tamano: Mapped[str | None] = mapped_column(String(20), nullable=True)  # pequeño|mediano|grande
    descripcion: Mapped[str] = mapped_column(String(2000))
    foto_url: Mapped[str | None] = mapped_column(String(300), nullable=True)
    zona: Mapped[str] = mapped_column(String(40))
    ciudad_texto: Mapped[str | None] = mapped_column(String(80), nullable=True)
    barrio: Mapped[str | None] = mapped_column(String(80), nullable=True)
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    situacion: Mapped[str | None] = mapped_column(String(20), nullable=True)
    fecha_evento: Mapped[date] = mapped_column(Date)
    # Nullable desde el crawler (ADR 0010): un reporte con fuente "crawl" puede no
    # traer teléfono — el contacto es la publicación original (crawl_metadata).
    # Para fuente "manual" sigue siendo obligatorio (validación en el schema).
    telefono_contacto: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # Canales opcionales de contacto (feature 40): handle de Instagram y
    # nombre/URL de perfil de Facebook — el teléfono sigue siendo el principal.
    instagram: Mapped[str | None] = mapped_column(String(120), nullable=True)
    facebook: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # Procedencia del reporte (ADR 0010): "manual" (formulario) o "crawl" (el
    # rastreador de redes publica vía la API). JSON es portable: nativo en
    # Postgres y TEXT serializado en SQLite — única excepción a la regla de
    # tipos simples de los modelos, anotada en el ADR.
    fuente: Mapped[str] = mapped_column(String(20), default="manual")  # "manual" | "crawl"
    crawl_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Idempotencia de creación (ADR 0010): el crawler manda una clave estable por
    # mascota (`<clave_post>#<indice>`); repetir el POST con la misma clave
    # devuelve el reporte existente en vez de duplicarlo. El índice único es la
    # garantía real (los NULL no chocan entre sí — reportes manuales no la usan).
    idempotency_id: Mapped[str | None] = mapped_column(
        String(300), nullable=True, unique=True, index=True
    )
    estado: Mapped[str] = mapped_column(String(20), default="activo")  # "activo" | "reunido"
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    resuelto_en: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
