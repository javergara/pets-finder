"""Juez LLM para los pares ambiguos del dedup (nivel 'posible' / 'aporta').

Un modelo pequeño y rápido (default: GPT-5.6 Luna) compara señas y fotos de
dos reportes de la MISMA persona y opina lo que la heurística no puede: ¿el
mismo animal dos veces, o dos animales distintos? Su veredicto ANOTA y ordena
la cola de revisión humana — nunca borra: la asimetría de costos sigue
mandando (un caso real perdido es peor que un duplicado tolerado).

Requiere OPENAI_API_KEY. Modelo configurable con DEDUP_JUEZ_MODELO. Volumen y
costo triviales: decenas de pares por corrida, dos textos cortos y dos fotos.
"""

import json
import os
from typing import Any

import requests

Reporte = dict[str, Any]

MODELO_DEFAULT = "gpt-5.6-luna"
_URL = "https://api.openai.com/v1/chat/completions"

_CAMPOS = (
    "tipo",
    "especie",
    "nombre_mascota",
    "raza",
    "color",
    "tamano",
    "descripcion",
    "barrio",
    "fecha_evento",
)

_INSTRUCCION = (
    "Dos reportes de mascotas publicados por la MISMA persona (mismo teléfono). "
    "Decide si describen al MISMO animal reportado dos veces, o a DOS animales "
    "distintos de esa persona. Compara señas físicas, nombre, y las fotos si "
    "vienen. Responde SOLO un JSON: "
    '{"mismo_caso": true|false, "confianza": 0.0-1.0, "razon": "una frase", '
    '"fusion": {...} | null}. '
    "Si mismo_caso es true, 'fusion' es la MEJOR versión combinada del caso: "
    "descripcion que reúna TODAS las señas de ambos reportes (sin inventar "
    "nada), y nombre_mascota/raza/color/tamano/barrio tomando el dato del "
    "reporte que lo tenga. Si mismo_caso es false, fusion es null."
)

CAMPOS_FUSION = ("descripcion", "nombre_mascota", "raza", "color", "tamano", "barrio")


def _resumen(reporte: Reporte) -> dict[str, Any]:
    return {campo: reporte.get(campo) for campo in _CAMPOS if reporte.get(campo)}


def construir_mensaje(a: Reporte, b: Reporte) -> list[dict[str, Any]]:
    """Contenido multimodal del par: señas de ambos + sus fotos si existen."""
    contenido: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": (
                f"{_INSTRUCCION}\n"
                f"Reporte A: {json.dumps(_resumen(a), ensure_ascii=False)}\n"
                f"Reporte B: {json.dumps(_resumen(b), ensure_ascii=False)}"
            ),
        }
    ]
    for reporte in (a, b):
        if reporte.get("foto_url"):
            contenido.append({"type": "image_url", "image_url": {"url": reporte["foto_url"]}})
    return contenido


_INSTRUCCION_REESCRITURA = (
    "Descripción BASE de un reporte de mascota y las descripciones de N "
    "reportes duplicados del MISMO animal. Redacta UNA sola descripción "
    "combinada en español con TODAS las señas útiles de todas las versiones, "
    "sin inventar nada y sin repetir. Máximo 1800 caracteres. "
    'Responde SOLO JSON: {"descripcion": "..."}'
)


def _llamar(instruccion: str, datos: dict[str, Any], timeout: int) -> dict[str, Any]:
    respuesta = requests.post(
        _URL,
        headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
        json={
            "model": os.environ.get("DEDUP_JUEZ_MODELO", MODELO_DEFAULT),
            "messages": [
                {
                    "role": "user",
                    "content": f"{instruccion}\n{json.dumps(datos, ensure_ascii=False)}",
                }
            ],
            "response_format": {"type": "json_object"},
        },
        timeout=timeout,
    )
    respuesta.raise_for_status()
    return json.loads(respuesta.json()["choices"][0]["message"]["content"])


def redactar_combinada(canonico: Reporte, sobrantes: list[Reporte], timeout: int = 60) -> str:
    """Descripción única con todas las señas del cluster (reescritura completa
    para cualquier canónico — decisión del operador: mejor una descripción
    coherente que N bloques apilados)."""
    datos = {
        "base": canonico.get("descripcion"),
        "duplicados": [s.get("descripcion") for s in sobrantes],
    }
    return str(_llamar(_INSTRUCCION_REESCRITURA, datos, timeout).get("descripcion", "")).strip()


def juzgar_par(a: Reporte, b: Reporte, timeout: int = 60) -> dict[str, Any]:
    """Veredicto del juez para un par: {'mismo_caso', 'confianza', 'razon'}."""
    respuesta = requests.post(
        _URL,
        headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
        json={
            "model": os.environ.get("DEDUP_JUEZ_MODELO", MODELO_DEFAULT),
            "messages": [{"role": "user", "content": construir_mensaje(a, b)}],
            "response_format": {"type": "json_object"},
        },
        timeout=timeout,
    )
    respuesta.raise_for_status()
    datos = json.loads(respuesta.json()["choices"][0]["message"]["content"])
    fusion_cruda = datos.get("fusion") or {}
    fusion = {c: fusion_cruda[c] for c in CAMPOS_FUSION if fusion_cruda.get(c)}
    return {
        "mismo_caso": bool(datos.get("mismo_caso")),
        "confianza": float(datos.get("confianza", 0.0)),
        "razon": str(datos.get("razon", "")),
        "fusion": fusion or None,
    }
