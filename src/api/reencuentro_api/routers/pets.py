"""Mascotas en adopción (AD-01/AD-02/AD-03), el módulo `/adoptar`.

⚠️ Orden obligatorio de las rutas en este archivo: **literal antes que
dinámica**. `POST ""` → `GET ""` → `GET "/adopciones"` → `GET "/deck"` →
`GET "/{pet_id}"` → `PUT "/{pet_id}"` → `DELETE "/{pet_id}"`. Si `/adopciones` o
`/deck` se registraran después de `/{pet_id}`, FastAPI intentaría parsearlas como
int y responderían 422 (misma regla que ya sigue `routers/reports.py`).
"""

import math
from collections.abc import Sequence
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import false, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from ..media import borrar_foto
from ..models.home_profile import HomeProfile
from ..models.organizacion import Organizacion
from ..models.pet import Pet
from ..models.report import Report
from ..models.swipe import Swipe
from ..models.user import User
from ..schemas.pet import (
    AdopcionesResumenOut,
    AfinidadOut,
    PetIn,
    PetOut,
    PetResumenOut,
    PetUpdate,
    PublicadorOut,
)
from ..services.afinidad import calcular_afinidad
from ..services.db import get_session
from ..services.descubrir import ordenar_deck
from ..services.filtros import EDAD_CATEGORIA_RANGOS, FiltrosDeck, aplicar_filtros

router = APIRouter(prefix="/api/pets", tags=["pets"])

REPORTE_YA_PUBLICADO = "Este reporte ya tiene una mascota publicada en adopción"
REPORTE_NO_ES_ENCONTRADA_CONMIGO = (
    "Solo se puede dar en adopción una mascota encontrada que tengas contigo"
)
REPORTE_DE_OTRA_PERSONA = "Solo quien publicó el reporte puede darla en adopción"


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


def _condicion_edad(categorias: Sequence[str]) -> ColumnElement[bool]:
    """Traduce los tramos de edad (`cachorro`/`joven`/`adulto`/`senior`) a un
    `OR` de rangos sobre `Pet.edad_meses`, a partir de `EDAD_CATEGORIA_RANGOS`.

    ⚠️ **Tiene que ser SQL, no un filtro en Python.** `listar_mascotas` cuenta el
    total con la query sin paginar y recién después aplica el `LIMIT`: recortar
    tramos de edad sobre la página ya traída haría que `X-Total-Count` mintiera
    (diría 40 y la UI pintaría 3), y además dejaría páginas de tamaño irregular.

    Los cortes no se repiten aquí: salen del diccionario de `services/filtros.py`,
    que es la fuente de verdad única (y que ya importa el 84 de `descubrir.py`).
    Una categoría fuera de catálogo no encuentra a nadie —mismo trato que
    `?especie=dinosaurio`—, en vez de ignorarse y devolver el catálogo entero como
    si el filtro hubiera funcionado.
    """
    condiciones: list[ColumnElement[bool]] = []
    for categoria in categorias:
        rango = EDAD_CATEGORIA_RANGOS.get(categoria)
        if rango is None:
            continue
        minimo, maximo = rango
        if math.isinf(maximo):
            condiciones.append(Pet.edad_meses >= minimo)
        else:
            condiciones.append(Pet.edad_meses.between(minimo, int(maximo)))
    if not condiciones:
        return false()
    return or_(*condiciones)


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


def _pet_out(
    pet: Pet, publicadores: dict[int, PublicadorOut], home: HomeProfile | None = None
) -> PetOut:
    """`PetOut` con lo que el ORM no sabe calcular (patrón de
    `OrganizacionOut.necesidades_pendientes`).

    `home` llega solo desde el deck y **es opcional a propósito**: sin perfil de
    hogar la afinidad no se puede calcular, así que `afinidad` viaja en `None` y
    la tarjeta se muestra igual (decisión de AD-03; `adopta-v1` devolvía 404 y
    eso rompía el onboarding entero). `es_favorito` y `ya_solicitada` se quedan
    en su default hasta AD-05/07.

    `razones` se convierte a lista aquí: `AfinidadResultado` es un dataclass
    `frozen` y las guarda como tupla.
    """
    out = PetOut.model_validate(pet)
    out.publicador = publicadores.get(pet.id)
    if home is not None:
        resultado = calcular_afinidad(pet, home)
        out.afinidad = AfinidadOut(
            score=resultado.score,
            explicacion=resultado.explicacion,
            razones=list(resultado.razones),
            incompatible=resultado.incompatible,
        )
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

    `report_id` es el puente con un "encontrado" que nadie reclamó, y se valida
    en este orden exacto (AD-02): **404** si el reporte no existe → **422** si no
    es un "encontrado" con `situacion="conmigo"` → **403** si no es de quien
    pide → **409** si ese reporte ya tiene mascota. La naturaleza del reporte se
    juzga antes que su autoría a propósito: una mascota perdida (o vista pero no
    atrapada) no se puede dar en adopción **por nadie**, ni siquiera por su
    autor, así que ese es el 422 que corresponde.
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
        report = session.get(Report, payload.report_id)
        if report is None:
            raise HTTPException(404, f"El reporte {payload.report_id} no existe")
        # El orden importa y está testeado: primero QUÉ reporte es, después DE
        # QUIÉN. Un reporte ajeno y además perdido responde 422, no 403 — al
        # revés, el mensaje daría a entender que al autor sí se le permitiría
        # dar en adopción una mascota que otra familia está buscando.
        if report.tipo != "encontrado" or report.situacion != "conmigo":
            raise HTTPException(422, REPORTE_NO_ES_ENCONTRADA_CONMIGO)
        if report.user_id != payload.user_id:
            raise HTTPException(403, REPORTE_DE_OTRA_PERSONA)
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
    edad_categoria: list[str] | None = Query(default=None),
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

    **`especie`, `tamano`, `energia`, `sexo` y `edad_categoria` son multivalor**:
    se repite el parámetro (`?especie=perro&especie=gato`) y se aplica **OR dentro
    de cada criterio y AND entre criterios** — "perros o gatos, y además grandes".
    Sin el parámetro (o con la lista vacía) el criterio no restringe nada, igual
    que `estado=todos`. Declararlos como `str` en vez de `list[str]` hacía que
    Starlette entregara **solo el último** valor repetido: el catálogo filtraba
    por uno y descartaba el resto en silencio, sin error (defecto del paso 6,
    corregido en el 6b).

    `zona` sí es de valor único a propósito: el selector de zona lo es en toda la
    app (`SelectorCiudad`), y "Todo Colombia" se pide omitiendo el parámetro.

    `edad_categoria` (cachorro/joven/adulto/senior) es un tramo derivado de
    `edad_meses`, no una columna: lo traduce a SQL `_condicion_edad` con los
    cortes de `services/filtros.py`. ⚠️ Se filtra en la base **antes** de contar y
    paginar, nunca en Python sobre la página ya traída — ver el aviso de ese
    helper: el `X-Total-Count` de abajo mentiría.

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
    Postgres) y ni `LIKE` ni `->>` son portables entre las dos. Ese criterio vive
    en Python, en `services/filtros.py`, y solo lo usa el deck — por eso tampoco
    se ofrece como chip en el catálogo.
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
    if edad_categoria:
        query = query.where(_condicion_edad(edad_categoria))
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


# Segunda ruta literal, también ANTES de /{pet_id} (ver el docstring del módulo):
# si quedara después, "deck" se parsearía como pet_id y esto sería un 422.
# `test_deck_no_se_parsea_como_pet_id_y_responde_200` es la garantía viva.
@router.get("/deck", response_model=list[PetOut])
def deck_de_descubrimiento(
    adoptante_id: int | None = None,
    especie: list[str] | None = Query(default=None),
    tamano: list[str] | None = Query(default=None),
    energia: list[str] | None = Query(default=None),
    edad_categoria: list[str] | None = Query(default=None),
    zona: list[str] | None = Query(default=None),
    apto_ninos: bool | None = None,
    apto_perros: bool | None = None,
    apto_gatos: bool | None = None,
    distancia_km: float | None = None,
    incluir_incompatibles: bool = False,
    limit: int = Query(default=20, ge=1, le=50),
    session: Session = Depends(get_session),
) -> list[PetOut]:
    """El deck de descubrimiento: qué mascotas ve quien está buscando adoptar.

    Pipeline, en este orden exacto: solo `disponible` → quitar las que ese
    adoptante ya swipeó → `_pet_out` con su perfil de hogar si lo tiene →
    `aplicar_filtros` (que además calcula `distancia_km`) → quitar incompatibles
    → `ordenar_deck` → recortar a `limit`.

    ⚠️ **`adoptante_id` es opcional**, no requerido como en el plan original.
    Exigirlo forzaría al frontend a mandar el id de una persona real cuando no
    hay cuenta —`getActiveUserId()` cae al `DEMO_USER_ID = 1`—, que es
    exactamente el bug de autoría del fix `cc4de85`. Sin él: 200, sin excluir
    swipeadas y sin afinidad. Con un id inexistente sí es 404: es un dato
    equivocado, no la ausencia del dato.

    ⚠️ **Sin `HomeProfile` responde 200 con `afinidad: null`**, no 404 como
    `adopta-v1`: un guard bloqueante rompe el onboarding entero y contradice el
    acceptance de AD-04 (la cuenta liviana del ADR 0005). La invitación a
    completar el cuestionario la decide el frontend viendo `afinidad === null`.

    ⚠️ **`ordenar_deck` se llama SIEMPRE**, también sin perfil. `adopta-v1` solo
    ordenaba cuando había `home`, y sin eso las mascotas difíciles de ubicar no
    se intercalan para quien no completó el cuestionario —la mayoría de la
    gente— y quedan enterradas al final. Con las afinidades empatadas en `None`
    la inserción de difíciles es lo único que ordena algo.

    `user_lat`/`user_lng` salen del `User` y **pueden ser `None`**: la mayoría no
    tiene coordenadas. `services/filtros.py` degrada con elegancia (nadie se
    excluye por distancia) en vez de devolver un deck vacío.

    Los filtros se aplican en Python y no en SQL, al revés que en el catálogo:
    aquí no hay paginación que hacer mentir a un `X-Total-Count`, `tags` no es
    filtrable en SQL de forma portable, y la distancia se calcula al vuelo.
    """
    home: HomeProfile | None = None
    user_lat: float | None = None
    user_lng: float | None = None

    query = select(Pet).where(Pet.estado == "disponible")

    if adoptante_id is not None:
        adoptante = session.get(User, adoptante_id)
        if adoptante is None:
            raise HTTPException(404, f"El usuario {adoptante_id} no existe")
        user_lat, user_lng = adoptante.lat, adoptante.lng
        home = session.get(HomeProfile, adoptante_id)
        # ⚠️ `Swipe.user_id` es el ADOPTANTE, no quien publicó la mascota (esa es
        # `Pet.user_id`). Confundirlas mostraría el deck de una persona a otra.
        ya_swipeadas = select(Swipe.pet_id).where(Swipe.user_id == adoptante_id)
        query = query.where(Pet.id.not_in(ya_swipeadas))

    # Orden base determinista, el mismo criterio de `listar_mascotas`. ⚠️ No es
    # cosmético ni redundante con `ordenar_deck`: `sorted` es estable, así que lo
    # que sale de la base es exactamente lo que decide el orden de todas las
    # mascotas empatadas — y **sin perfil de hogar empatan todas** (afinidad
    # `None` → 0). Sin `ORDER BY`, SQLite las devuelve por `rowid` y parece
    # estable, pero en Postgres el orden de base es arbitrario: dos requests
    # seguidos pueden barajar el deck y quien recarga vería otra carta encima sin
    # haber hecho nada. Es una diferencia de motor que los tests, que corren
    # sobre SQLite, no verían por sí solos.
    query = query.order_by(Pet.publicado_en.desc(), Pet.id.desc())

    pets = list(session.execute(query).scalars().all())
    publicadores = _publicadores_por_pet(session, pets)
    resultados = [_pet_out(pet, publicadores, home) for pet in pets]

    resultados = aplicar_filtros(
        resultados,
        FiltrosDeck(
            especie=especie,
            tamano=tamano,
            energia=energia,
            edad_categoria=edad_categoria,
            zona=zona,
            apto_ninos=apto_ninos,
            apto_perros=apto_perros,
            apto_gatos=apto_gatos,
            distancia_km=distancia_km,
        ),
        user_lat,
        user_lng,
    )

    if not incluir_incompatibles:
        resultados = [r for r in resultados if not (r.afinidad and r.afinidad.incompatible)]

    return ordenar_deck(resultados)[:limit]


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


@router.delete("/{pet_id}", status_code=status.HTTP_204_NO_CONTENT)
def despublicar_mascota(pet_id: int, user_id: int, session: Session = Depends(get_session)) -> None:
    """Despublica (borra) una mascota, solo por quien la publicó.

    `user_id` viaja como **query param**, no en el body: es la convención del
    repo para los DELETE (`eliminar_reporte`, `eliminar_organizacion`). La
    autoría la resuelve `_dueno_user_id`, igual que el `PUT`, incluido su caso
    `None` (organización eliminada) → 403 y nunca un 500.

    ⚠️ Las fotos solo se borran si la mascota **no** vino de un reporte. Cuando
    `report_id` no es nulo, esas URLs son las del reporte de "encontrada", que
    sigue vivo en la app: borrarlas del bucket dejaría al reporte con imágenes
    rotas en producción. Y no se notaría desde aquí, porque `borrar_foto` nunca
    lanza (tolerante a fallos por diseño, feature 20) — el 204 saldría igual de
    limpio. De ahí que el test espíe las llamadas en vez de mirar solo el
    status. El costo asumido es el simétrico: si la mascota se copió las fotos y
    después se borra el reporte, quedan huérfanas en el bucket (feature 20 ya
    acepta ese trueque; una foto huérfana es barata, una rota no).

    Al borrar la fila se libera el `unique` de `report_id`: el mismo reporte se
    puede volver a dar en adopción sin chocar con el 409.
    """
    pet = session.get(Pet, pet_id)
    if pet is None:
        raise HTTPException(404, f"La mascota {pet_id} no existe")
    if user_id != _dueno_user_id(session, pet):
        raise HTTPException(403, "Solo quien publicó la mascota puede despublicarla")

    if pet.report_id is None:
        for foto in pet.fotos:
            borrar_foto(foto)
    session.delete(pet)
    session.commit()
