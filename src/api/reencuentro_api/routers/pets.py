"""Mascotas en adopción (AD-01/AD-02), el módulo `/adoptar`.

⚠️ Orden obligatorio de las rutas en este archivo: **literal antes que
dinámica**. `POST ""` → `GET ""` → `GET "/adopciones"` → `GET "/{pet_id}"` →
`PUT "/{pet_id}"`. Si `/adopciones` se registrara después de `/{pet_id}`,
FastAPI intentaría parsearla como int y respondería 422 (misma regla que ya
sigue `routers/reports.py`).
"""

from collections.abc import Sequence
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models.organizacion import Organizacion
from ..models.pet import Pet
from ..models.report import Report
from ..models.user import User
from ..schemas.pet import (
    AdopcionesResumenOut,
    PetIn,
    PetOut,
    PetResumenOut,
    PetUpdate,
    PublicadorOut,
)
from ..services.db import get_session

router = APIRouter(prefix="/api/pets", tags=["pets"])

REPORTE_YA_PUBLICADO = "Este reporte ya tiene una mascota publicada en adopción"


def _dueno_user_id(session: Session, pet: Pet) -> int | None:
    """Quién puede gestionar esta mascota: el autor de la organización que la
    publicó, o el rescatista dueño (`Pet.user_id`). Lo reusan las lecturas del
    paso 6 y la edición/borrado de AD-02.

    Devuelve `None` si la mascota cuelga de una organización que ya no existe
    (se puede eliminar, feature 32, y SQLite no fuerza las FK): así nadie queda
    autorizado, en vez de reventar con un 500 o autorizar de más.
    """
    if pet.organizacion_id is not None:
        organizacion = session.get(Organizacion, pet.organizacion_id)
        return organizacion.user_id if organizacion is not None else None
    return pet.user_id


def _mascota_del_reporte(session: Session, report_id: int) -> Pet | None:
    return session.scalar(select(Pet).where(Pet.report_id == report_id))


def _publicadores_por_pet(session: Session, pets: Sequence[Pet]) -> dict[int, PublicadorOut]:
    """Quién publica cada mascota, en **dos** queries agregadas con `IN`.

    Una `session.get(Organizacion, ...)` por mascota serían ~40 round-trips por
    página contra el pooler de Supabase: el N+1 clásico de un catálogo. Mismo
    patrón que los `conteos` de `routers/organizaciones.py::listar_organizaciones`.

    El teléfono es lo asimétrico: el modelo `User` no tiene teléfono, así que el
    de un rescatista sale siempre de `Pet.telefono_contacto` (obligatorio para
    él, ver `PetIn`); el de una organización cae al suyo, salvo que la mascota
    traiga uno propio (un hogar de paso con otro contacto).

    Una mascota cuyo publicador ya no existe (la organización se puede eliminar,
    feature 32) simplemente no queda en el diccionario: `publicador` viaja como
    `None` en vez de romper el listado entero.
    """
    ids_organizacion = {p.organizacion_id for p in pets if p.organizacion_id is not None}
    ids_usuario = {p.user_id for p in pets if p.user_id is not None}

    organizaciones: dict[int, Organizacion] = {}
    if ids_organizacion:
        filas = session.execute(select(Organizacion).where(Organizacion.id.in_(ids_organizacion)))
        organizaciones = {o.id: o for o in filas.scalars()}

    usuarios: dict[int, User] = {}
    if ids_usuario:
        filas = session.execute(select(User).where(User.id.in_(ids_usuario)))
        usuarios = {u.id: u for u in filas.scalars()}

    publicadores: dict[int, PublicadorOut] = {}
    for pet in pets:
        if pet.organizacion_id is not None:
            organizacion = organizaciones.get(pet.organizacion_id)
            if organizacion is None:
                continue
            publicadores[pet.id] = PublicadorOut(
                tipo="organizacion",
                id=organizacion.id,
                nombre=organizacion.nombre,
                telefono_contacto=pet.telefono_contacto or organizacion.telefono_contacto,
                zona=organizacion.zona,
                ciudad_texto=organizacion.ciudad_texto,
                barrio=organizacion.barrio,
                foto_url=organizacion.foto_url,
            )
        elif pet.user_id is not None:
            usuario = usuarios.get(pet.user_id)
            if usuario is None:
                continue
            # `zona` queda en None: el `User` no la tiene y la de la mascota ya
            # viaja en `PetOut.zona` (puede estar en hogar de paso en otra).
            publicadores[pet.id] = PublicadorOut(
                tipo="rescatista",
                id=usuario.id,
                nombre=usuario.nombre,
                telefono_contacto=pet.telefono_contacto,
                ciudad_texto=usuario.ciudad,
                barrio=usuario.barrio,
                foto_url=usuario.avatar_url,
            )
    return publicadores


def _pet_out(pet: Pet, publicadores: dict[int, PublicadorOut]) -> PetOut:
    """`PetOut` con lo que el ORM no sabe calcular (patrón de
    `OrganizacionOut.necesidades_pendientes`).

    En AD-01 solo se llena `publicador`; `afinidad`, `es_favorito` y
    `ya_solicitada` se quedan en su default hasta AD-03/05/07.
    """
    out = PetOut.model_validate(pet)
    out.publicador = publicadores.get(pet.id)
    return out


@router.post("", response_model=PetOut, status_code=status.HTTP_201_CREATED)
def publicar_mascota(payload: PetIn, session: Session = Depends(get_session)) -> PetOut:
    """Publica una mascota en adopción: cuelga de una organización O de un
    rescatista, nunca de ambos (el XOR lo rechaza `PetIn` con 422 en español).

    ⚠️ Colisión de nombres a tener presente: `payload.user_id` es **quien hace
    el request** (sirve para la autoría → 403), mientras que la columna
    `Pet.user_id` es **el rescatista dueño** de la mascota, que en el contrato
    HTTP viaja como `payload.rescatista_id`. Cuando publica una organización,
    `Pet.user_id` queda en `None`: nunca se guardan los dos.

    `report_id` (puente con un "encontrado" que nadie reclamó) aquí solo se
    valida como existente y no repetido; las reglas de tipo/situación/autoría
    del reporte son de AD-02.
    """
    if payload.organizacion_id is not None:
        organizacion = session.get(Organizacion, payload.organizacion_id)
        if organizacion is None:
            raise HTTPException(404, f"La organización {payload.organizacion_id} no existe")
        if organizacion.user_id != payload.user_id:
            raise HTTPException(
                403, "Solo quien registró la organización puede publicar mascotas en adopción"
            )

    if payload.rescatista_id is not None and session.get(User, payload.rescatista_id) is None:
        raise HTTPException(404, f"El usuario {payload.rescatista_id} no existe")

    if payload.report_id is not None:
        if session.get(Report, payload.report_id) is None:
            raise HTTPException(404, f"El reporte {payload.report_id} no existe")
        if _mascota_del_reporte(session, payload.report_id) is not None:
            raise HTTPException(409, REPORTE_YA_PUBLICADO)

    # El dueño rescatista se persiste en la columna `Pet.user_id` (ver el aviso
    # del docstring); `payload.user_id`, que es quien pide la operación, no se
    # guarda en ningún lado.
    pet = Pet(
        **payload.model_dump(exclude={"user_id", "rescatista_id"}),
        user_id=payload.rescatista_id,
    )
    session.add(pet)
    try:
        session.commit()
    except IntegrityError:
        # Carrera: otro request publicó el mismo `report_id` entre el select de
        # arriba y este commit. El índice único de la columna es la garantía
        # real; el select solo da el 409 limpio en el caso normal.
        session.rollback()
        if payload.report_id is not None and _mascota_del_reporte(session, payload.report_id):
            raise HTTPException(409, REPORTE_YA_PUBLICADO) from None
        raise
    session.refresh(pet)

    return _pet_out(pet, _publicadores_por_pet(session, [pet]))


@router.get("", response_model=list[PetOut])
def listar_mascotas(
    response: Response,
    especie: list[str] | None = Query(default=None),
    tamano: list[str] | None = Query(default=None),
    energia: list[str] | None = Query(default=None),
    sexo: list[str] | None = Query(default=None),
    zona: str | None = None,
    estado: str = "disponible",
    organizacion_id: int | None = None,
    user_id: int | None = None,
    adoptante_id: int | None = None,
    limit: int | None = Query(default=None, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
) -> list[PetOut]:
    """Catálogo de adopción, lo más recién publicado primero.

    **`especie`, `tamano`, `energia` y `sexo` son multivalor**: se repite el
    parámetro (`?especie=perro&especie=gato`) y se aplica **OR dentro de cada
    criterio y AND entre criterios** — "perros o gatos, y además grandes". Sin el
    parámetro (o con la lista vacía) el criterio no restringe nada, igual que
    `estado=todos`. Declararlos como `str` en vez de `list[str]` hacía que
    Starlette entregara **solo el último** valor repetido: el catálogo filtraba
    por uno y descartaba el resto en silencio, sin error (defecto del paso 6,
    corregido en el 6b).

    `zona` sí es de valor único a propósito: el selector de zona lo es en toda la
    app (`SelectorCiudad`), y "Todo Colombia" se pide omitiendo el parámetro.

    ⚠️ Este listado **todavía no filtra por edad**: `edad_categoria`
    (cachorra/joven/adulta/senior) es un tramo derivado de `edad_meses`, no una
    columna, y su dueño es `services/filtros.py` en AD-03. Si llega en la query
    se ignora — la UI no debe ofrecer ese chip hasta entonces.

    `estado` por defecto es "disponible": una mascota adoptada o en proceso sale
    del catálogo — se piden explícitamente (`estado=adoptado`) o todas con
    `estado=todos` (así arma el panel de la organización su vista completa).

    ⚠️ `user_id` aquí es **el rescatista que publicó** la mascota, nunca el
    adoptante que mira (en `adopta-v1` significaba justo lo contrario, y
    confundirlos filtra "mis mascotas" por quien no es). El adoptante viaja como
    `adoptante_id`, que en AD-01 se acepta pero **no altera la respuesta**:
    `afinidad`, `es_favorito` y `ya_solicitada` se quedan en su default hasta
    AD-03/05/07. Filtrar por `organizacion_id` y por `user_id` son cosas
    distintas y excluyentes por el CHECK del modelo.

    El total sin paginar viaja SIEMPRE en el header `X-Total-Count`; sin `limit`
    la respuesta es la lista completa (patrón de `listar_reportes`).

    `tags` no se filtra aquí: la columna es JSON (TEXT en SQLite, `json` en
    Postgres) y ni `LIKE` ni `->>` son portables entre las dos — ese filtro llega
    en AD-03, en Python, con `services/filtros.py`.
    """
    query = select(Pet)
    if estado != "todos":
        query = query.where(Pet.estado == estado)
    # `if lista:` y no `is not None`: una lista vacía (ningún chip marcado) no
    # restringe, en vez de generar un `IN ()` que no devolvería nada.
    if especie:
        query = query.where(Pet.especie.in_(especie))
    if tamano:
        query = query.where(Pet.tamano.in_(tamano))
    if energia:
        query = query.where(Pet.energia.in_(energia))
    if sexo:
        query = query.where(Pet.sexo.in_(sexo))
    if zona is not None:
        query = query.where(Pet.zona == zona)
    if organizacion_id is not None:
        query = query.where(Pet.organizacion_id == organizacion_id)
    if user_id is not None:
        query = query.where(Pet.user_id == user_id)

    total = session.execute(select(func.count()).select_from(query.subquery())).scalar_one()
    response.headers["X-Total-Count"] = str(total)

    query = query.order_by(Pet.publicado_en.desc(), Pet.id.desc())
    if limit is not None:
        query = query.offset(offset).limit(limit)

    pets = list(session.execute(query).scalars().all())
    publicadores = _publicadores_por_pet(session, pets)
    return [_pet_out(p, publicadores) for p in pets]


# Ruta literal declarada ANTES que la dinámica /{pet_id} (regla del docstring del
# módulo): al revés, "adopciones" se parsearía como un pet_id inválido y esto
# respondería 422 — un bug que parece "la ruta no existe".
@router.get("/adopciones", response_model=AdopcionesResumenOut)
def resumen_adopciones(session: Session = Depends(get_session)) -> AdopcionesResumenOut:
    """La métrica de esperanza del catálogo, espejo de `GET /api/reports/reunidos`:
    cuántas mascotas ya tienen hogar y las últimas seis."""
    total = session.execute(
        select(func.count()).select_from(Pet).where(Pet.estado == "adoptado")
    ).scalar_one()

    recientes = (
        session.execute(
            select(Pet)
            .where(Pet.estado == "adoptado")
            .order_by(Pet.adoptado_en.desc(), Pet.id.desc())
            .limit(6)
        )
        .scalars()
        .all()
    )

    return AdopcionesResumenOut(
        total=total, recientes=[PetResumenOut.model_validate(p) for p in recientes]
    )


@router.get("/{pet_id}", response_model=PetOut)
def obtener_mascota(
    pet_id: int,
    adoptante_id: int | None = None,
    session: Session = Depends(get_session),
) -> PetOut:
    """Ficha completa con su publicador.

    `adoptante_id` se acepta desde ya (el cliente lo manda igual) pero en AD-01
    no cambia la respuesta: la afinidad, el favorito y la solicitud los llenan
    AD-03/05/07.
    """
    pet = session.get(Pet, pet_id)
    if pet is None:
        raise HTTPException(404, f"La mascota {pet_id} no existe")

    return _pet_out(pet, _publicadores_por_pet(session, [pet]))


@router.put("/{pet_id}", response_model=PetOut)
def editar_mascota(
    pet_id: int, payload: PetUpdate, session: Session = Depends(get_session)
) -> PetOut:
    """Edición parcial solo por quien publicó (patrón de `editar_organizacion`).

    Autoriza `_dueno_user_id`: el autor de la organización que la publicó, o el
    rescatista dueño. Ese helper puede devolver `None` (organización eliminada,
    feature 32) y entonces **nadie** queda autorizado — 403, nunca un 500.

    Marcarla `adoptado` sella `adoptado_en`; devolverla a `disponible` o
    `en_proceso` (una adopción que no cuajó) lo limpia, para que el resumen de
    `/api/pets/adopciones` no cuente finales felices que no ocurrieron.

    ⚠️ `exclude_none=True` significa que **mandar `null` no vacía un campo**: se
    ignora, igual que no mandarlo. Así, un formulario que no toca el teléfono no
    lo borra sin querer. La contrapartida es que hoy no hay forma de vaciar un
    opcional por esta vía, y no se inventa un centinela para eso.

    ⚠️ `fotos` y `tags` se **reasignan** con la lista completa que llega en el
    body: mutarlas in-place (`pet.fotos.append(...)`) no se persistiría, porque
    las columnas JSON no llevan `MutableList`.

    Lo que este endpoint no puede cambiar (`PetUpdate` no los declara): el
    publicador, la zona y `ciudad_texto`. Mudar de dueño o de zona cambiaría el
    encuadre en el mapa; para eso se despublica y se vuelve a publicar.
    """
    pet = session.get(Pet, pet_id)
    if pet is None:
        raise HTTPException(404, f"La mascota {pet_id} no existe")
    if payload.user_id != _dueno_user_id(session, pet):
        raise HTTPException(403, "Solo quien publicó la mascota puede editarla")

    cambios = payload.model_dump(exclude={"user_id"}, exclude_none=True)
    for campo, valor in cambios.items():
        setattr(pet, campo, valor)
    if "estado" in cambios:
        pet.adoptado_en = datetime.now(timezone.utc) if cambios["estado"] == "adoptado" else None
    session.commit()
    session.refresh(pet)

    return _pet_out(pet, _publicadores_por_pet(session, [pet]))
