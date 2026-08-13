"""Registro local de posts procesados: un post nunca se re-extrae (ADR 0010).

El dedup es a nivel de EXTRACCIÓN, no de reporte: como el LLM no es determinista,
re-extraer un post podría dar otro número/orden de mascotas y desalinear los
`idempotency_id` (`<clave>#<indice>`). Por eso la extracción se registra ANTES
de publicar: si una corrida muere a mitad de los POST, el retry reutiliza los
payloads guardados en vez de volver al LLM, y la idempotencia del servidor hace
el resto. La clave es la url del post o, a falta de url, el sha256 del
pantallazo.

Formato: JSONL append-only (crawler/estado/, gitignored); la última entrada de
una clave gana. Una línea corrupta (proceso muerto a mitad de escritura) se
ignora en vez de tumbar la corrida. Suficiente para una máquina; con varios
workers esto se muda a una tabla (anotado en el ADR).
"""

import hashlib
import json
from pathlib import Path
from typing import Any

RUTA_REGISTRO = Path(__file__).parent / "estado" / "procesados.jsonl"


def clave_de(url_post: str | None, ruta_imagen: Path) -> str:
    if url_post and url_post.strip():
        return url_post.strip()
    return "sha256:" + hashlib.sha256(ruta_imagen.read_bytes()).hexdigest()


def obtener(clave: str, registro: Path = RUTA_REGISTRO) -> dict[str, Any] | None:
    """Última entrada registrada para la clave, o None si nunca se procesó."""
    if not registro.exists():
        return None
    entrada = None
    with registro.open() as f:
        for linea in f:
            if not linea.strip():
                continue
            try:
                datos = json.loads(linea)
            except json.JSONDecodeError:
                continue  # línea truncada por un crash a mitad de escritura
            if datos.get("clave") == clave:
                entrada = datos
    return entrada


def registrar_extraccion(
    clave: str, payloads: list[dict[str, Any]], registro: Path = RUTA_REGISTRO
) -> None:
    _append(registro, {"clave": clave, "payloads": payloads, "reporte_ids": None})


def registrar_invalido(clave: str, motivo: str, registro: Path = RUTA_REGISTRO) -> None:
    """Extracción que la validación del contrato rechazó (p. ej. sin camino de
    contacto): se registra para no re-pagar el LLM, con el motivo a la vista."""
    _append(registro, {"clave": clave, "payloads": [], "reporte_ids": None, "motivo": motivo})


def marcar_publicado(clave: str, reporte_ids: list[int], registro: Path = RUTA_REGISTRO) -> None:
    entrada = obtener(clave, registro) or {"clave": clave, "payloads": None}
    _append(registro, {**entrada, "reporte_ids": reporte_ids})


def _append(registro: Path, datos: dict[str, Any]) -> None:
    registro.parent.mkdir(parents=True, exist_ok=True)
    with registro.open("a") as f:
        f.write(json.dumps(datos, ensure_ascii=False) + "\n")
