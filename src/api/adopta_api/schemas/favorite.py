from pydantic import BaseModel


class FavoriteIn(BaseModel):
    """Body de `POST /api/users/{user_id}/favorites` (feature `13-favorites`).

    El `user_id` va en el path, no en el body (mismo criterio que otros
    endpoints anidados bajo `/api/users/{user_id}/...`).
    """

    pet_id: int
