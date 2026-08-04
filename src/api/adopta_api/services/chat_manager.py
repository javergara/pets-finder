"""Registro en memoria de conexiones WebSocket activas por hilo (ADR 0004).

Un solo proceso `uvicorn` sin `--workers` (`dev.sh`) hace que un dict en memoria
sea correcto y suficiente para este alcance -- sin Redis pub/sub, limitación
documentada explícitamente en `docs/decisions/0004-chat-websockets-fastapi.md`.

`connection_manager` es una instancia única a nivel de módulo: `routers/chat.py`
la importa y comparte el mismo estado entre todos los requests/conexiones del
proceso.
"""

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._conexiones: dict[int, list[WebSocket]] = {}

    async def conectar(self, match_id: int, ws: WebSocket) -> None:
        """Acepta el handshake y registra la conexión bajo `match_id`.

        El `accept()` vive aquí (no en el router) para que el router no tenga
        que recordar llamarlo antes de registrar la conexión -- conectar()
        deja el WebSocket listo para usarse de inmediato."""
        await ws.accept()
        self._conexiones.setdefault(match_id, []).append(ws)

    def desconectar(self, match_id: int, ws: WebSocket) -> None:
        conexiones = self._conexiones.get(match_id)
        if conexiones is None:
            return
        if ws in conexiones:
            conexiones.remove(ws)
        if not conexiones:
            del self._conexiones[match_id]

    async def difundir(self, match_id: int, payload: dict) -> None:
        """Envía `payload` a todas las conexiones activas de `match_id`.

        Un fallo al enviar a una conexión individual (p. ej. ya cerrada del
        otro lado pero todavía no limpiada por `desconectar`) se descarta y no
        bloquea el envío al resto -- el propio handler del WS es responsable
        de llamar `desconectar` cuando detecte su propia desconexión."""
        for ws in list(self._conexiones.get(match_id, [])):
            try:
                await ws.send_json(payload)
            except Exception:
                continue


connection_manager = ConnectionManager()
