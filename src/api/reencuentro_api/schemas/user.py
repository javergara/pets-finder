from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .pet import EnergiaPet, EspeciePet, TamanoPet

# Catálogos propios del hogar: describen a quien adopta, no a la mascota, así que
# no tienen sitio en `schemas/pet.py`. Los valores son exactamente las llaves de
# los diccionarios de `services/afinidad.py` (`capacidad_vivienda`,
# `_EXPERIENCIA_NIVEL`): un valor fuera de catálogo no daría un score raro, haría
# saltar un `KeyError` dentro del deck de esa persona.
ViviendaHogar = Literal["apartamento", "casa"]
EspacioExteriorHogar = Literal["ninguno", "patio", "jardin"]
ExperienciaPreviaHogar = Literal["ninguna", "algo", "mucha"]


class UserIn(BaseModel):
    nombre: str
    email: str
    ciudad: str = "Armenia"
    barrio: str | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    email: str
    ciudad: str
    barrio: str | None
    lat: float | None
    lng: float | None
    avatar_url: str | None
    bio: str | None
    creado_en: datetime
    # ⚠️ **No lleva `home_profile` ni `metricas`**, al revés que el `UserOut` de
    # `adopta-v1`. Portarlos rompería el contrato que hoy leen varias pantallas y
    # añadiría dos queries —una con joins— a un endpoint caliente, para un dato
    # que casi ninguna llamada usa. El hogar tiene su propia ruta y su propio
    # 403; hay un test que fija este conjunto de campos exacto.


class HomeProfileIn(BaseModel):
    """Las respuestas del cuestionario de hogar (AD-04).

    ⚠️ `user_id` es redundante con el de la ruta **a propósito**, igual que en
    `PetIn` y `OrganizacionUpdate`: comparar los dos es lo único que separa
    "edito mi hogar" de "sobrescribo el de otra persona" (403). Sin contraseñas
    (ADR 0005) esa comparación es toda la autorización que hay, así que ninguno
    de los dos sobra.

    Los catálogos de la mascota se **importan** de `schemas/pet.py` en vez de
    reescribirse: dos listas de especies que se separen dejarían al cuestionario
    ofreciendo una preferencia que ninguna mascota puede cumplir.

    Los tres booleanos de convivencia son **requeridos**, sin default: un `False`
    implícito por un campo que el cliente olvidó mandar diría "no viven niños
    aquí", y eso levanta una regla dura de `afinidad.py` — la mascota no apta con
    niños dejaría de excluirse.
    """

    user_id: int
    vivienda: ViviendaHogar
    espacio_exterior: EspacioExteriorHogar
    # `ge=1`: siempre vive al menos quien responde. Cero es un dato imposible.
    personas_en_casa: int = Field(ge=1)
    tiene_ninos: bool
    tiene_otros_perros: bool
    tiene_otros_gatos: bool
    horas_fuera_dia: int = Field(ge=0, le=24)
    experiencia_previa: ExperienciaPreviaHogar
    # Opcional de verdad (decisión de producto, ver `models/home_profile.py`):
    # pedir COP en plena emergencia añade fricción y tono equivocado. `afinidad.py`
    # degrada a solo-experiencia cuando falta. El `| None` importa tanto como el
    # `default`: el wizard manda `null` explícito cuando alguien borra el valor.
    presupuesto_mensual_cop: int | None = Field(default=None, ge=0, le=10_000_000)
    preferencia_especies: list[EspeciePet] = Field(default_factory=list)
    preferencia_tamanos: list[TamanoPet] = Field(default_factory=list)
    preferencia_energia: EnergiaPet


class HomeProfileOut(BaseModel):
    """Las 12 respuestas del cuestionario, sin `user_id`.

    Quien lo recibe es siempre su dueño (el router responde 403 antes de llegar
    aquí), así que devolver el id sería repetirle lo que acaba de poner en la URL.

    ⚠️ Las preferencias salen como `list[str]` y no con los `Literal`: son
    columnas JSON, y una fila vieja con un valor que ya no esté en catálogo tiene
    que poder leerse y corregirse desde el wizard, no responder 500 al serializar.
    """

    model_config = ConfigDict(from_attributes=True)

    vivienda: str
    espacio_exterior: str
    personas_en_casa: int
    tiene_ninos: bool
    tiene_otros_perros: bool
    tiene_otros_gatos: bool
    horas_fuera_dia: int
    experiencia_previa: str
    presupuesto_mensual_cop: int | None
    preferencia_especies: list[str]
    preferencia_tamanos: list[str]
    preferencia_energia: str
