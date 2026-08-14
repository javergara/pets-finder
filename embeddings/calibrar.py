"""Calibración del pipeline visual: ¿separa "misma mascota" de "otra mascota"?

Es la compuerta de la feature 24 y la herramienta que hay que volver a correr
cada vez que cambie PIPELINE (otro detector, otro embedder, otro umbral de
recorte): los umbrales de services/coincidencias.py salen de aquí, no de la
intuición.

Sin etiquetas humanas fiables (los nombres de mascota se repiten: hay varias
"Luna" distintas), la separación se mide de dos formas honestas:

  A. LÍNEA BASE (negativos): todos los pares de la MISMA especie entre reportes
     distintos. La enorme mayoría son animales distintos, así que esta
     distribución es el ruido contra el que hay que separar.
  B. CONTROL POSITIVO: la misma foto bajo transformaciones realistas (recorte,
     rotación, brillo, espejo, recompresión). Si el modelo no le da alta
     similitud a ESTO, no se la va a dar a dos fotos distintas del mismo animal.

Los pares con coseno ~1.0 se excluyen del análisis: son la MISMA imagen (el
crawler saca N mascotas de un pantallazo, ADR 0010 §6), no una coincidencia.

Uso (solo lectura sobre el API público; nunca escribe nada):

    python -m embeddings.calibrar --salida embeddings/ejemplos/calibracion.json
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

import requests

# El umbral de "esto es la misma imagen, no una coincidencia" es el mismo que
# usa la API en producción: una sola fuente de verdad.
from reencuentro_api.services.coincidencias import UMBRAL_MISMA_IMAGEN

from .modelo import PIPELINE, vector_de_foto

API_PUBLICA = "https://petfinder-col.com/api/reports?estado=todos"
TIMEOUT = 30

# Los "casos de prueba definidos antes de implementar" del acceptance 2 de la
# feature 24. Son los dos pares que decidieron el diseño de dos etapas, y por eso
# se miden CON y SIN recorte en cada corrida: si el recorte deja de arreglar el
# falso positivo, o empieza a romper el verdadero positivo, se ve aquí.
# (Si algún reporte se elimina de producción, su par se reporta como ausente.)
PARES_DEL_ACCEPTANCE = [
    (61, 141, "falso positivo: perra dorada vs perro crema, ambos en imagen compuesta"),
    (26, 61, "verdadero positivo: la misma perra (Mila) en dos reportes distintos"),
]


def percentiles(valores: list[float], ps=(50, 90, 95, 99)) -> dict[str, float]:
    ordenados = sorted(valores)
    return {
        f"p{p}": round(ordenados[min(len(ordenados) - 1, int(len(ordenados) * p / 100))], 4)
        for p in ps
    }


def variantes(imagen):
    """La misma mascota fotografiada distinto: el positivo que sí podemos fabricar."""
    from io import BytesIO

    from PIL import Image, ImageEnhance

    ancho, alto = imagen.size
    buffer = BytesIO()
    imagen.save(buffer, format="JPEG", quality=45)
    buffer.seek(0)
    return {
        "recorte 80%": imagen.crop(
            (int(ancho * 0.1), int(alto * 0.1), int(ancho * 0.9), int(alto * 0.9))
        ),
        "rotada 8°": imagen.rotate(8, resample=Image.BICUBIC),
        "brillo 0.75": ImageEnhance.Brightness(imagen).enhance(0.75),
        "espejo": imagen.transpose(Image.FLIP_LEFT_RIGHT),
        "jpeg q45": Image.open(buffer).convert("RGB"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", type=Path, default=None, help="JSON con el resultado")
    parser.add_argument("--api", default=API_PUBLICA, help="de dónde leer los reportes")
    parser.add_argument("--limite", type=int, default=None, help="usar solo las N primeras fotos")
    args = parser.parse_args(argv)

    import io

    from PIL import Image

    print(f"Leyendo reportes de {args.api} (solo lectura)…")
    reportes = [r for r in requests.get(args.api, timeout=TIMEOUT).json() if r.get("foto_url")]
    if args.limite:
        reportes = reportes[: args.limite]
    print(f"  {len(reportes)} reportes con foto")

    vectores: dict[int, list[float]] = {}
    crudas: dict[int, bytes] = {}
    for n, reporte in enumerate(reportes, 1):
        try:
            respuesta = requests.get(reporte["foto_url"], timeout=TIMEOUT)
        except requests.RequestException:
            continue
        if respuesta.status_code != 200:
            continue
        vector = vector_de_foto(respuesta.content)
        if vector is not None:
            vectores[reporte["id"]] = vector
            crudas[reporte["id"]] = respuesta.content
        print(f"  {n}/{len(reportes)}", end="\r")
    print(
        f"\n  {len(vectores)} vectores ({len(vectores) / max(len(reportes), 1):.0%} de cobertura)"
    )

    por_id = {r["id"]: r for r in reportes}

    def coseno(a, b):
        return sum(x * y for x, y in zip(a, b, strict=True))

    print("A. Línea base (animales distintos, misma especie)…")
    base: dict[str, list[float]] = {}
    ids = sorted(vectores)
    for i, a in enumerate(ids):
        for b in ids[i + 1 :]:
            if por_id[a]["especie"] != por_id[b]["especie"]:
                continue
            if por_id[a]["foto_url"] == por_id[b]["foto_url"]:
                continue
            s = coseno(vectores[a], vectores[b])
            if s >= UMBRAL_MISMA_IMAGEN:
                continue  # misma imagen re-subida: no es un negativo
            base.setdefault(por_id[a]["especie"], []).append(s)

    print("B. Control positivo (misma foto transformada)…")
    positivos: list[float] = []
    for rid in sorted(crudas)[:20]:
        imagen = Image.open(io.BytesIO(crudas[rid])).convert("RGB")
        for variante in variantes(imagen).values():
            buffer = io.BytesIO()
            variante.save(buffer, format="JPEG", quality=92)
            vector = vector_de_foto(buffer.getvalue())
            if vector is not None:
                positivos.append(coseno(vectores[rid], vector))

    print("C. Pares del acceptance 2 (con y sin recorte)…")
    pares_fijos = []
    for id_a, id_b, etiqueta in PARES_DEL_ACCEPTANCE:
        if id_a not in crudas or id_b not in crudas:
            pares_fijos.append({"par": [id_a, id_b], "etiqueta": etiqueta, "estado": "ausente"})
            continue
        sin_recorte = [vector_de_foto(crudas[i], recortar=False) for i in (id_a, id_b)]
        pares_fijos.append(
            {
                "par": [id_a, id_b],
                "etiqueta": etiqueta,
                "con_recorte": round(coseno(vectores[id_a], vectores[id_b]), 4),
                "sin_recorte": (
                    round(coseno(*sin_recorte), 4)
                    if all(v is not None for v in sin_recorte)
                    else None
                ),
            }
        )

    resultado = {
        "pipeline": PIPELINE,
        "reportes_con_foto": len(reportes),
        "vectores_obtenidos": len(vectores),
        "pares_del_acceptance": pares_fijos,
        "linea_base_negativos": {
            especie: {"n": len(v), "media": round(statistics.mean(v), 4), **percentiles(v)}
            for especie, v in sorted(base.items())
        },
        "control_positivo": {
            "n": len(positivos),
            "media": round(statistics.mean(positivos), 4) if positivos else None,
            "min": round(min(positivos), 4) if positivos else None,
            **(percentiles(positivos, (10, 50)) if positivos else {}),
        },
    }

    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    if args.salida:
        args.salida.parent.mkdir(parents=True, exist_ok=True)
        args.salida.write_text(
            json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"\nGuardado en {args.salida}")

    print(
        "\nLectura: los umbrales de services/coincidencias.py deben quedar por ENCIMA"
        "\ndel p99 de la línea base y por DEBAJO del p10 del control positivo."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
