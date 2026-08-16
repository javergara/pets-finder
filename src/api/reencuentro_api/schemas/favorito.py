"""Contrato HTTP de los favoritos del módulo de adopción (AD-07).

La tabla se llama `favorites` y las rutas van en inglés plural
(`docs/conventions.md` §2), pero en el copy y en las pantallas esto es siempre
"guardar" / "mis favoritas".
"""

from pydantic import BaseModel


class FavoritoIn(BaseModel):
    """Payload de "guardar esta mascota": solo la mascota.

    ⚠️ **Quién guarda no viaja en el body**: es el `{user_id}` de la ruta. Tenerlo
    en los dos sitios crearía una segunda fuente de verdad con la que el path
    podría discrepar, y entonces habría que decidir cuál manda (en `PetIn` esa
    ambigüedad ya cuesta un `model_validator` entero). Por eso tampoco lleva
    `solicitante_id`: el actor es el del path y no hay nada que comparar.

    No existe un `FavoritoOut`. La respuesta del POST es el `PetOut` completo con
    `es_favorito=True` —lo mismo que pinta la tarjeta— en vez de un eco de la fila
    creada, que obligaría a la pantalla a pedir la mascota otra vez.
    """

    pet_id: int
