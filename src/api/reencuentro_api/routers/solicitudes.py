"""Solicitudes de adopción (AD-05): las dos lecturas y las cuatro acciones.

`GET /api/solicitudes` con **exactamente uno** de `adoptante_id`,
`organizacion_id` o `publicador_id`, `GET /api/solicitudes/{id}` con
`solicitante_id`, y `POST /api/solicitudes/{id}/{accion}` con las cuatro
acciones del publicador (paso 3).

⚠️ **Las cuatro acciones son solo de quien publicó la mascota**, nunca del
adoptante: el match no es mutuo (ADR 0002), así que quien pidió la mascota puede
leer su solicitud pero no moverla. El `acciones_disponibles: []` que recibe su
pantalla es una cortesía de UI; la barrera real es el 403 de `_publicador_o_403`.

⚠️ Este módulo **importa `_dueno_user_id` y `_publicadores_por_pet` de
`.pets`** — el primer import router→router del repo. Es a propósito y no un
atajo: `_dueno_user_id` es la regla de autoría de una mascota (el autor de la
organización que la publicó, o el rescatista dueño) y ya autoriza el `PUT` y el
`DELETE` de AD-02. Copiarla aquí sería tener dos reglas que empiezan iguales y
se separan en la primera corrección; y la que se quede vieja es justamente la que
autoriza de más. El olor del import es más barato que ese riesgo. Si algún día un
tercer router la necesita, el movimiento correcto es bajarla a `services/`, no
duplicarla.
"""

from collections.abc import Sequence
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select, update
from sqlalchemy.orm import Session

from ..models.home_profile import HomeProfile
from ..models.match import Match
from ..models.organizacion import Organizacion
from ..models.pet import Pet
from ..models.user import User
from ..schemas.pet import AfinidadOut, PetResumenOut, PublicadorOut
from ..schemas.solicitud import (
    AccionSolicitudIn,
    AdoptanteResumen,
    DescartarIn,
    SolicitudDetalleOut,
    SolicitudOut,
)
from ..schemas.user import HomeProfileOut
from ..services.afinidad import calcular_afinidad
from ..services.db import get_session

# ⚠️ Ver el aviso del docstring del módulo antes de "arreglar" este import.
from ..services.solicitudes import (
    ESTADOS_TERMINALES,
    MOTIVO_ADOPTADA_POR_OTRA,
    TransicionInvalidaError,
    acciones_disponibles,
    calcular_etiqueta_solicitud,
    validar_transicion,
)
from .pets import _dueno_user_id, _publicadores_por_pet

router = APIRouter(prefix="/api/solicitudes", tags=["solicitudes"])

FILTRO_UNICO = (
    "Manda exactamente uno de 'adoptante_id', 'organizacion_id' o 'publicador_id': "
    "son tres preguntas distintas y no se combinan"
)
SOLICITUD_AJENA = "Solo el adoptante o quien publicó la mascota pueden ver esta solicitud"
ACCION_AJENA = "Solo quien publicó la mascota puede gestionar esta solicitud"

#: ⚠️ `ESTADOS_TERMINALES` se define en `services/solicitudes.py` desde AD-09 y
#: aquí solo se importa (ver el aviso de su docstring): `despublicar_mascota`
#: necesita la misma frontera y no puede importar de este router sin cerrar un
#: ciclo. El nombre sigue siendo alcanzable como
#: `routers.solicitudes.ESTADOS_TERMINALES` para quien ya lo usaba.


def _afinidad_out(pet: Pet, home: HomeProfile | None) -> AfinidadOut | None:
    """La afinidad se calcula al vuelo (ADR 0003), nunca se persiste.

    `None` cuando el adoptante no contestó el cuestionario: AD-04 lo dejó
    opcional, así que la solicitud se muestra igual (en `adopta-v1` esa fila
    desaparecía del panel sin error).
    """
    if home is None:
        return None
    resultado = calcular_afinidad(pet, home)
    return AfinidadOut(
        score=resultado.score,
        explicacion=resultado.explicacion,
        razones=list(resultado.razones),
        incompatible=resultado.incompatible,
    )


def _campos_solicitud(
    match: Match,
    pet: Pet,
    publicador: PublicadorOut | None,
    adoptante: User,
    home: HomeProfile | None,
    es_publicador: bool,
) -> dict:
    """Los campos comunes a la lista y al detalle, ya resueltos.

    Es un `dict` y no un `SolicitudOut` para que el detalle pueda ampliarlo sin
    reconstruir el objeto entero ni repetir aquí la lista de campos.
    """
    return {
        "id": match.id,
        "estado": match.estado,
        "etiqueta": calcular_etiqueta_solicitud(match.estado, match.creado_en),
        "creado_en": match.creado_en,
        "actualizado_en": match.actualizado_en,
        "pet": PetResumenOut.model_validate(pet),
        "publicador": publicador,
        "adoptante": AdoptanteResumen(id=adoptante.id, nombre=adoptante.nombre),
        "afinidad": _afinidad_out(pet, home),
        # Lo decide el backend para quien pregunta: para el adoptante siempre
        # `[]` (ADR 0002). En `adopta-v1` la pantalla reimplementaba la matriz de
        # transiciones y las dos fuentes de verdad se separaron.
        "acciones_disponibles": acciones_disponibles(match.estado, es_publicador),
    }


def _solicitudes_out(
    session: Session, matches: Sequence[Match], es_publicador: bool
) -> list[SolicitudOut]:
    """Arma la lista con **un lote por tipo de entidad**, nunca un `session.get`
    por fila.

    Son cuatro accesos fijos —mascotas, publicadores (dos queries dentro de
    `_publicadores_por_pet`), adoptantes y perfiles de hogar— y ninguno crece con
    el número de solicitudes: contra el pooler de Supabase, un panel de 40
    solicitudes serían si no ~160 round-trips. Lo vigila
    `test_el_listado_no_hace_una_consulta_por_solicitud`.
    """
    if not matches:
        return []

    ids_pet = {m.pet_id for m in matches}
    ids_adoptante = {m.user_id for m in matches}

    pets = {
        p.id: p for p in session.execute(select(Pet).where(Pet.id.in_(ids_pet))).scalars().all()
    }
    publicadores = _publicadores_por_pet(session, list(pets.values()))
    adoptantes = {
        u.id: u
        for u in session.execute(select(User).where(User.id.in_(ids_adoptante))).scalars().all()
    }
    hogares = {
        h.user_id: h
        for h in session.execute(select(HomeProfile).where(HomeProfile.user_id.in_(ids_adoptante)))
        .scalars()
        .all()
    }

    resultado: list[SolicitudOut] = []
    for match in matches:
        pet = pets.get(match.pet_id)
        adoptante = adoptantes.get(match.user_id)
        if pet is None or adoptante is None:
            # Fila colgando de una mascota o de una cuenta que ya no existen.
            # SQLite no fuerza las FK (gotcha de AD-02 paso 3), así que en dev
            # puede pasar de verdad: se omite esa fila en vez de tumbar la lista
            # entera con un 500.
            continue
        resultado.append(
            SolicitudOut(
                **_campos_solicitud(
                    match,
                    pet,
                    publicadores.get(pet.id),
                    adoptante,
                    hogares.get(match.user_id),
                    es_publicador,
                )
            )
        )
    return resultado


def _cargar_solicitud_o_404(session: Session, solicitud_id: int) -> tuple[Match, Pet, User]:
    """La solicitud con sus dos extremos, o 404.

    Devuelve también la mascota y el adoptante porque sin la mascota no se puede
    resolver quién autoriza, y sin el adoptante no hay nada que mostrar. Que
    falte cualquiera de los dos es la misma respuesta —la solicitud no existe
    como tal— y nunca un 500 (SQLite no fuerza las FK).

    Es un `session.get` por entidad y no un lote a propósito: aquí hay **una**
    fila, así que no existe el N+1 que hace falta batchear en el listado.
    """
    match = session.get(Match, solicitud_id)
    pet = session.get(Pet, match.pet_id) if match is not None else None
    adoptante = session.get(User, match.user_id) if match is not None else None
    if match is None or pet is None or adoptante is None:
        raise HTTPException(404, f"La solicitud {solicitud_id} no existe")
    return match, pet, adoptante


def _detalle_out(
    session: Session, match: Match, pet: Pet, adoptante: User, es_publicador: bool
) -> SolicitudDetalleOut:
    """El detalle completo, ya resuelto: lo devuelven el `GET` y las cuatro acciones.

    Que las acciones respondan esto —y no un 204 mudo— le ahorra a la pantalla un
    `GET` inmediato después de cada botón y, sobre todo, le devuelve
    `acciones_disponibles` recalculadas: quién puede hacer qué lo decide el
    backend, nunca el frontend (ADR 0002).
    """
    home = session.get(HomeProfile, match.user_id)
    publicador = _publicadores_por_pet(session, [pet]).get(pet.id)

    return SolicitudDetalleOut(
        **_campos_solicitud(match, pet, publicador, adoptante, home, es_publicador),
        bio=adoptante.bio,
        mensaje=match.mensaje,
        telefono_contacto=match.telefono_contacto,
        home_profile=HomeProfileOut.model_validate(home) if home is not None else None,
    )


def _publicador_o_403(session: Session, solicitud_id: int, user_id: int) -> tuple[Match, Pet, User]:
    """Carga la solicitud y exige que `user_id` sea **quien publicó la mascota**.

    Es la única autorización de las cuatro acciones: sin contraseñas (ADR 0005),
    comparar el `user_id` del body con `_dueno_user_id` es todo lo que hay. El
    adoptante cae aquí igual que un desconocido —el match no es mutuo—, y una
    mascota cuya organización ya no existe no autoriza a nadie (`_dueno_user_id`
    devuelve `None`), en vez de autorizar de más.
    """
    match, pet, adoptante = _cargar_solicitud_o_404(session, solicitud_id)
    if user_id != _dueno_user_id(session, pet):
        raise HTTPException(403, ACCION_AJENA)
    return match, pet, adoptante


def _validar_o_409(match: Match, accion: str) -> None:
    """Traduce la regla pura de `services/solicitudes.py` al contrato HTTP.

    Va **antes** de tocar una sola columna: un 409 que ya hubiera escrito dejaría
    la solicitud en un estado que la matriz prohíbe.
    """
    try:
        validar_transicion(match.estado, accion)
    except TransicionInvalidaError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.get("", response_model=list[SolicitudOut])
def listar_solicitudes(
    adoptante_id: int | None = Query(default=None),
    organizacion_id: int | None = Query(default=None),
    publicador_id: int | None = Query(default=None),
    session: Session = Depends(get_session),
) -> list[SolicitudOut]:
    """Las solicitudes de una persona (las que envió) o de quien publica (las que
    recibió), lo más reciente primero.

    ⚠️ **Exactamente uno de los tres filtros, y el 422 lo lanza este código a
    mano**: FastAPI sabe exigir un parámetro requerido, pero no "uno de tres".
    Sin este guard, una llamada sin filtros devolvería **todas** las solicitudes
    de la app a cualquiera, y una con dos obligaría al router a inventar cuál
    gana. Un id inexistente es 404 (dato equivocado); una lista vacía es 200 —una
    fundación recién registrada legítimamente no tiene ninguna—.

    ⚠️ **`publicador_id` cubre las dos vías**: las mascotas donde esa persona es
    el rescatista dueño (`Pet.user_id`) **y** las de las organizaciones que ella
    registró. Es el mismo criterio de `_dueno_user_id`, que es quien decide
    después si puede o no gestionarlas. Con una sola vía, quien registró una
    fundación y además publicó a su nombre tendría que mirar en dos sitios y "las
    que recibí" mentiría sin dar ningún error.

    El orden es `creado_en desc, id desc`: el desempate por id no es cosmético
    —en Postgres el orden de base es arbitrario y dos solicitudes creadas en el
    mismo segundo podrían intercambiarse entre dos recargas—, la misma corrección
    que necesitó el deck.
    """
    filtros = (adoptante_id, organizacion_id, publicador_id)
    if sum(filtro is not None for filtro in filtros) != 1:
        raise HTTPException(422, FILTRO_UNICO)

    query = select(Match)
    if adoptante_id is not None:
        if session.get(User, adoptante_id) is None:
            raise HTTPException(404, f"El usuario {adoptante_id} no existe")
        # ⚠️ `Match.user_id` es el ADOPTANTE (ver `models/match.py`), al revés que
        # `Pet.user_id`. Cruzarlas mostraría a alguien las solicitudes de otro.
        query = query.where(Match.user_id == adoptante_id)
        es_publicador = False
    elif organizacion_id is not None:
        if session.get(Organizacion, organizacion_id) is None:
            raise HTTPException(404, f"La organización {organizacion_id} no existe")
        query = query.join(Pet, Pet.id == Match.pet_id).where(
            Pet.organizacion_id == organizacion_id
        )
        es_publicador = True
    else:
        if session.get(User, publicador_id) is None:
            raise HTTPException(404, f"El usuario {publicador_id} no existe")
        organizaciones_propias = select(Organizacion.id).where(
            Organizacion.user_id == publicador_id
        )
        query = query.join(Pet, Pet.id == Match.pet_id).where(
            or_(
                Pet.user_id == publicador_id,
                Pet.organizacion_id.in_(organizaciones_propias),
            )
        )
        es_publicador = True

    matches = list(
        session.execute(query.order_by(Match.creado_en.desc(), Match.id.desc())).scalars().all()
    )
    return _solicitudes_out(session, matches, es_publicador)


@router.get("/{solicitud_id}", response_model=SolicitudDetalleOut)
def obtener_solicitud(
    solicitud_id: int,
    solicitante_id: int,
    session: Session = Depends(get_session),
) -> SolicitudDetalleOut:
    """El detalle: el cuestionario del hogar, el mensaje y el teléfono.

    `solicitante_id` es requerido y solo lo pasan dos personas: el adoptante que
    la envió y quien publicó la mascota (`_dueno_user_id`). Cualquier otra recibe
    **403**, no una respuesta recortada: los ids son secuenciales y adivinables,
    así que sin este corte cualquiera leería el cuestionario completo y el
    teléfono de una persona ajena.

    Quien publica ve las acciones que puede ejecutar; el adoptante, ninguna (ADR
    0002). Si el dueño de la mascota no se puede resolver —la organización que la
    publicó fue eliminada, feature 32— nadie queda autorizado como publicador, en
    vez de autorizar de más.
    """
    match, pet, adoptante = _cargar_solicitud_o_404(session, solicitud_id)

    dueno_id = _dueno_user_id(session, pet)
    es_publicador = dueno_id is not None and solicitante_id == dueno_id
    if not es_publicador and solicitante_id != match.user_id:
        raise HTTPException(403, SOLICITUD_AJENA)

    return _detalle_out(session, match, pet, adoptante, es_publicador)


@router.post("/{solicitud_id}/agendar-visita", response_model=SolicitudDetalleOut)
def agendar_visita(
    solicitud_id: int, payload: AccionSolicitudIn, session: Session = Depends(get_session)
) -> SolicitudDetalleOut:
    """Cita para conocer a la mascota: válido desde `solicitado` o `en_revision`."""
    match, pet, adoptante = _publicador_o_403(session, solicitud_id, payload.user_id)
    _validar_o_409(match, "agendar-visita")

    match.estado = "visita_agendada"
    match.actualizado_en = datetime.now(timezone.utc)
    session.commit()

    return _detalle_out(session, match, pet, adoptante, es_publicador=True)


@router.post("/{solicitud_id}/pedir-informacion", response_model=SolicitudDetalleOut)
def pedir_informacion(
    solicitud_id: int, payload: AccionSolicitudIn, session: Session = Depends(get_session)
) -> SolicitudDetalleOut:
    """Deja la solicitud `en_revision`: válido **solo** desde `solicitado`.

    No es un no-op idempotente: pedirla dos veces es 409, porque el segundo
    intento suele ser una pantalla desincronizada y no una decisión.
    """
    match, pet, adoptante = _publicador_o_403(session, solicitud_id, payload.user_id)
    _validar_o_409(match, "pedir-informacion")

    match.estado = "en_revision"
    match.actualizado_en = datetime.now(timezone.utc)
    session.commit()

    return _detalle_out(session, match, pet, adoptante, es_publicador=True)


@router.post("/{solicitud_id}/descartar", response_model=SolicitudDetalleOut)
def descartar_solicitud(
    solicitud_id: int, payload: DescartarIn, session: Session = Depends(get_session)
) -> SolicitudDetalleOut:
    """Cierra la solicitud con un motivo obligatorio (ya recortado por `DescartarIn`).

    El motivo se persiste pero **no sale en ninguna respuesta**: es la nota
    interna de quien publica, y quien no se quedó con la mascota no tiene por qué
    leer por qué (ADR 0002, cabecera de `schemas/solicitud.py`).
    """
    match, pet, adoptante = _publicador_o_403(session, solicitud_id, payload.user_id)
    _validar_o_409(match, "descartar")

    match.estado = "cerrado"
    match.motivo_descarte = payload.motivo
    match.actualizado_en = datetime.now(timezone.utc)
    session.commit()

    return _detalle_out(session, match, pet, adoptante, es_publicador=True)


@router.post("/{solicitud_id}/aprobar", response_model=SolicitudDetalleOut)
def aprobar_solicitud(
    solicitud_id: int, payload: AccionSolicitudIn, session: Session = Depends(get_session)
) -> SolicitudDetalleOut:
    """La adopción se cierra: esta solicitud gana, la mascota sale del catálogo y
    **las demás de esa mascota se cierran solas**.

    Dejarlas abiertas mandaría a varias familias a esperar por algo que ya no
    puede pasar, y el publicador tendría que descartarlas una por una.

    ⚠️ **Es una sola transacción y una sola query de cierre.** El `UPDATE` masivo
    no es una optimización prematura: un bucle sobre las hermanas es una escritura
    por familia interesada, y cada una es un round-trip contra el pooler de
    Supabase dentro de la transacción abierta — justo el momento en que más caro
    sale. Con un único `commit()` no existe el estado intermedio en el que la
    mascota ya figura adoptada y la mitad de las solicitudes siguen abiertas.
    Lo vigila `test_aprobar_cierra_las_demas_con_una_sola_query`, que cuenta
    **filas** actualizadas.

    ⚠️ `synchronize_session=False` es obligatorio aquí (el `UPDATE` masivo no se
    puede sincronizar fila a fila sin volver a leerlas, que es lo que se quiere
    evitar) y tiene un precio: las instancias de esas hermanas que ya estuvieran
    cargadas en la sesión quedan rancias. En producción no importa —cada request
    tiene su sesión y esta termina aquí—, pero los tests comparten la sesión con
    el cliente y tienen que releer antes de aseverar.

    El `NOT IN` de `ESTADOS_TERMINALES` evita pisarle el motivo a una solicitud ya
    cerrada por su propia razón (y a una `adoptado`, que diría "fue adoptada por
    otra familia" sobre la que sí se adoptó).
    """
    match, pet, adoptante = _publicador_o_403(session, solicitud_id, payload.user_id)
    _validar_o_409(match, "aprobar")

    ahora = datetime.now(timezone.utc)
    session.execute(
        update(Match)
        .where(
            Match.pet_id == match.pet_id,
            Match.id != match.id,
            Match.estado.not_in(ESTADOS_TERMINALES),
        )
        .values(
            estado="cerrado",
            motivo_descarte=MOTIVO_ADOPTADA_POR_OTRA,
            actualizado_en=ahora,
        ),
        execution_options={"synchronize_session": False},
    )

    match.estado = "adoptado"
    match.actualizado_en = ahora
    # Misma pareja de columnas que sella el `PUT /api/pets/{id}`: sin
    # `adoptado_en` la mascota no aparece en la franja de `/api/pets/adopciones`.
    pet.estado = "adoptado"
    pet.adoptado_en = ahora
    session.commit()

    return _detalle_out(session, match, pet, adoptante, es_publicador=True)
