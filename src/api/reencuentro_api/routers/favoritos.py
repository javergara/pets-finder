"""Favoritos del módulo de adopción (AD-07): guardar una mascota para después.

Tres rutas colgadas de `/api/users/{user_id}`: `POST .../favorites` (201 nuevo,
200 el repetido), `GET .../favorites` (la lista propia) y
`DELETE .../favorites/{pet_id}` (204 siempre). El módulo va en español y las rutas
en inglés plural, como el resto de la API (`docs/conventions.md` §2).

⚠️ **`user_id` es el ADOPTANTE que MIRA**, exactamente al revés que en `pets`,
donde `Pet.user_id` es quien **PUBLICA**. Las dos son FK a `users.id`, así que
ninguna base de datos avisa si se cruzan: el síntoma sería que a quien publica le
salgan sus propias mascotas como "mis favoritas". Ver `models/favorite.py`, y
`test_los_favoritos_no_se_cruzan_con_quien_publico_la_mascota` como candado vivo.

⚠️ **Guardar no es decidir.** Marcar un favorito no inserta un `Swipe`, no crea
una solicitud (`matches`) y **no saca la mascota del deck** — el deck solo excluye
por `Swipe.pet_id`. Confundir los dos mecanismos haría desaparecer una carta por
el gesto más inocente de la pantalla; hay dos tests que lo fijan.

⚠️ Este módulo **importa `_pet_out` y `_publicadores_por_pet` de `.pets`**, el
segundo import router→router del repo (el primero lo abrió
`routers/solicitudes.py`, con el mismo razonamiento). Es a propósito y no un
atajo: `_pet_out` es la forma canónica de una mascota en el contrato HTTP —
publicador incluido, con sus dos queries agregadas contra el N+1— y copiarla aquí
sería tener dos versiones de la misma tarjeta que se separan en la primera
corrección. El olor del import es más barato que ese riesgo, y no hay ciclo:
`pets.py` no importa nada de este módulo. Si un tercer router las necesita, el
movimiento correcto es bajarlas a `services/`, no duplicarlas.
"""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models.favorite import Favorite
from ..models.pet import Pet
from ..models.user import User
from ..schemas.favorito import FavoritoIn
from ..schemas.pet import PetOut
from ..services.db import get_session

# ⚠️ Ver el aviso del docstring del módulo antes de "arreglar" este import.
from .pets import _pet_out, _publicadores_por_pet

router = APIRouter(prefix="/api/users", tags=["favoritos"])

FAVORITOS_AJENOS = "Solo puedes ver las mascotas que guardaste en tu cuenta"


def _favorito_existente(session: Session, user_id: int, pet_id: int) -> Favorite | None:
    """El favorito que esa persona ya tiene sobre esa mascota, si lo hay.

    Lo usan las dos mitades del 200 idempotente (el select previo y el de después
    del `rollback()`) y el DELETE. Está a nivel de módulo por el mismo motivo que
    `_swipe_existente` en `routers/swipes.py`.

    ⚠️ `user_id` es quien mira (ver el aviso del módulo).
    """
    return session.execute(
        select(Favorite).where(Favorite.user_id == user_id, Favorite.pet_id == pet_id)
    ).scalar_one_or_none()


@router.post("/{user_id}/favorites", response_model=PetOut, status_code=status.HTTP_201_CREATED)
def marcar_favorito(
    user_id: int,
    payload: FavoritoIn,
    response: Response,
    session: Session = Depends(get_session),
) -> PetOut:
    """Guarda una mascota en la lista de quien mira.

    Responde **201** la primera vez y **200 el repetido**, con la misma fila y sin
    crear una segunda (mismo patrón que `registrar_swipe`): el doble-tap de un
    corazón en un móvil es un accidente del dedo, no un error del usuario, y un
    409 obligaría a la pantalla a pintar un error por algo que ya está como se
    quería. El status del repetido se pone en el `Response` inyectado y no en el
    decorador, que declara el caso normal.

    La idempotencia necesita **las dos cosas**: el select previo, que da la
    respuesta limpia en el caso normal, y el `IntegrityError` atrapado con
    `rollback()`, que es la garantía real. En serverless (ADR 0007) dos requests
    del mismo dedo corren de verdad a la vez y los dos pueden ver ese select
    vacío; ahí solo decide `uq_favorite_user_pet`, y sin atraparlo el usuario
    recibiría un 500 con traza por haber tocado dos veces.

    ⚠️ Los 404 salen de comprobaciones **en el código**, no de las FK: SQLite no
    las fuerza (gotcha de AD-02), así que confiar en la base dejaría los tests en
    verde e insertaría igual la fila huérfana, para reventar recién en Postgres.

    **No lleva `solicitante_id`**: el `user_id` del path ya es el actor y no hay
    una segunda fuente con la que pueda discrepar. La respuesta es el `PetOut`
    completo con `es_favorito=True` — lo que la tarjeta necesita pintar, sin pedir
    la mascota otra vez.
    """
    pet = session.get(Pet, payload.pet_id)
    if pet is None:
        raise HTTPException(404, f"La mascota {payload.pet_id} no existe")
    if session.get(User, user_id) is None:
        raise HTTPException(404, f"El usuario {user_id} no existe")

    if _favorito_existente(session, user_id, payload.pet_id) is not None:
        response.status_code = status.HTTP_200_OK
        return _pet_out(pet, _publicadores_por_pet(session, [pet]), favoritos={pet.id})

    session.add(Favorite(user_id=user_id, pet_id=payload.pet_id))
    try:
        session.commit()
    except IntegrityError:
        # Carrera: otro request guardó el mismo (adoptante, mascota) entre el
        # select de arriba y este commit, y `uq_favorite_user_pet` lo rechazó. El
        # rollback deshace la fila y se responde con la que dejó el que ganó.
        session.rollback()
        if _favorito_existente(session, user_id, payload.pet_id) is None:
            raise
        response.status_code = status.HTTP_200_OK

    return _pet_out(pet, _publicadores_por_pet(session, [pet]), favoritos={pet.id})


@router.get("/{user_id}/favorites", response_model=list[PetOut])
def listar_favoritos(
    user_id: int, solicitante_id: int, session: Session = Depends(get_session)
) -> list[PetOut]:
    """Las mascotas guardadas por esa persona, lo último guardado primero.

    ⚠️ **El 403 va antes que cualquier consulta**, incluida la del usuario, igual
    que en `obtener_perfil_hogar`. Al revés, la respuesta sería un oráculo de
    enumeración: 404 diría "ese id no existe" y 403 "ese id sí existe", y los ids
    de esta app son secuenciales y adivinables. Una lista de favoritos es un
    historial de navegación con nombre propio.

    ⚠️ **Esto NO es autenticación, y tampoco tapa el `DEMO_USER_ID`.** La app no
    tiene login (ADR 0005) y `solicitante_id` es autodeclarado: quien quiera leer
    favoritos ajenos solo tiene que cambiar un número. Y ojo con lo que este
    parámetro NO hace: `listarFavoritas(userId)` manda el mismo valor en el path y
    en la query, así que si el frontend cayera a `DEMO_USER_ID = 1` —una persona
    real en producción— los dos serían 1 y este 403 no dispararía nunca. Lo que
    evita esa fuga es el `hasActiveUser()` de la pantalla, que está y está
    testeado; esto no lo sustituye.

    Lo que sí aporta: es requerido y sin default, así que olvidarlo es un 422 y no
    una lista ajena servida sin más, y deja el sitio donde colgar la comprobación
    real el día que haya autenticación.

    ⚠️ **Una sola query con join y `ORDER BY` explícito.** `adopta-v1` hacía dos
    (los ids primero, las mascotas después) y **sin orden**: en SQLite parece
    estable por `rowid` y en Postgres el orden es arbitrario, así que la rejilla se
    barajaría entre recargas sin que nadie hubiera hecho nada. El desempate por
    `pet_id` desc existe porque dos favoritos guardados en el mismo instante
    (mismo `creado_en`) volverían a dejar el orden en manos del motor.

    Las adoptadas **no** se excluyen: guardaste esa mascota, tienes derecho a ver
    cómo terminó. Y no exige `HomeProfile` — sin perfil la lista sale igual, con
    `afinidad: null` (mismo criterio que el deck de AD-03).
    """
    if solicitante_id != user_id:
        raise HTTPException(403, FAVORITOS_AJENOS)

    if session.get(User, user_id) is None:
        raise HTTPException(404, f"El usuario {user_id} no existe")

    pets = list(
        session.execute(
            select(Pet)
            .join(Favorite, Favorite.pet_id == Pet.id)
            .where(Favorite.user_id == user_id)
            .order_by(Favorite.creado_en.desc(), Favorite.pet_id.desc())
        )
        .scalars()
        .all()
    )
    publicadores = _publicadores_por_pet(session, pets)
    favoritos = {pet.id for pet in pets}
    return [_pet_out(pet, publicadores, favoritos=favoritos) for pet in pets]


@router.delete("/{user_id}/favorites/{pet_id}", status_code=status.HTTP_204_NO_CONTENT)
def desmarcar_favorito(user_id: int, pet_id: int, session: Session = Depends(get_session)) -> None:
    """Quita una mascota de la lista. **204 siempre**, incluso si no estaba.

    Que no valide nada es una decisión, no un olvido: el resultado que pide quien
    apaga el corazón —"esta mascota ya no está en mi lista"— se cumple igual si la
    fila no existía, si la mascota se despublicó o si el usuario no existe. Un 404
    ahí solo serviría para que la pantalla pintara un error rojo por un doble-tap,
    y de paso confirmaría qué ids existen a quien pruebe con números al azar.

    **No lleva `solicitante_id`** por el mismo motivo que el POST: el `user_id`
    del path ya es el actor. Como no hay autenticación, ese path es también todo
    lo que hace falta para borrar el favorito de otra persona — el daño posible es
    el mínimo del módulo: quitar una tarjeta de una lista privada, sin perder nada
    que no se pueda volver a guardar con un toque.

    Precisión que conviene no perder: esto **no** es lo que hacen los otros DELETE
    de la app. `eliminar_reporte` y `despublicar_mascota` sí comparan la autoría y
    responden 403. Sin autenticación las tres son igual de falsificables, así que
    el riesgo práctico no cambia; lo que cambia es que aquí no queda ningún sitio
    donde colgar esa comprobación cuando haya login. Si algún día se añade, este
    endpoint es el que hay que revisar primero.
    """
    favorito = _favorito_existente(session, user_id, pet_id)
    if favorito is None:
        return

    session.delete(favorito)
    session.commit()
