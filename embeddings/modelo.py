"""Foto → vector de parecido visual (ADR 0012).

Único módulo que habla con torch/transformers. Los imports son **perezosos**
(dentro de las funciones) para que la suite de tests y el resto del repo puedan
importar este paquete sin tener instalado `embeddings/requirements.txt` —
mismo patrón que `crawler/extractor.py` con llama-cloud.

El pipeline tiene dos etapas y las dos importan:

1. **Recorte al animal** (`hustvl/yolos-tiny`, COCO). Sin este paso el vector
   describe la maqueta y no la mascota: en producción abundan los pósters
   diseñados ("¡SE PERDIÓ!") y los pantallazos de story con chrome del
   teléfono. Medido sobre las fotos reales de prod, el recorte tumbó un falso
   positivo de 0.885 a 0.461 y dejó intacto el verdadero positivo (0.997).
2. **Embedding** (`AvitoTech/DINO-v2-small-for-animal-identification`, Apache
   2.0): DINOv2-small afinado para identidad individual de perros y gatos,
   384 dims, token CLS normalizado tal como indica su model card.

Cambiar cualquiera de las dos etapas cambia el espacio vectorial: por eso
`PIPELINE` versiona el conjunto y se guarda junto a cada vector.
"""

from __future__ import annotations

import logging

DETECTOR_ID = "hustvl/yolos-tiny"
EMBEDDER_ID = "AvitoTech/DINO-v2-small-for-animal-identification"

# Identidad del pipeline COMPLETO — se guarda en Report.embedding_modelo y solo
# se comparan vectores que la comparten. Subir la versión al cambiar cualquier
# etapa, umbral de detección o margen de recorte: son vectores distintos.
PIPELINE = "yolos-tiny+dinov2-animal-id/v1"

DIMENSIONES = 384

# Clases COCO que cuentan como "la mascota del reporte". Se incluyen algunas
# ajenas a perro/gato porque la especie "otro" existe en el modelo de datos y
# porque un peluche junto al animal no debe ganarle la caja al animal.
CLASES_ANIMAL = frozenset({"cat", "dog", "bird", "horse", "sheep", "cow"})
UMBRAL_DETECCION = 0.25
# El recorte se agranda un 8% por lado: la caja de COCO corta pegada al cuerpo y
# se come orejas y cola, que son justamente señas de identidad.
MARGEN_RECORTE = 0.08
# 6 decimales sobre un vector normalizado: el error en el coseno queda ~1e-6,
# invisible frente a umbrales de 0.80/0.90, y la fila de JSON pesa la mitad.
DECIMALES = 6

logger = logging.getLogger("embeddings")

_modelos_cargados = None


def _modelos():
    """Carga perezosa y única de los dos modelos (tarda ~10 s la primera vez)."""
    global _modelos_cargados
    if _modelos_cargados is None:
        from transformers import AutoImageProcessor, AutoModel, AutoModelForObjectDetection

        logger.info("Cargando %s y %s…", DETECTOR_ID, EMBEDDER_ID)
        _modelos_cargados = (
            AutoImageProcessor.from_pretrained(DETECTOR_ID),
            AutoModelForObjectDetection.from_pretrained(DETECTOR_ID).eval(),
            AutoImageProcessor.from_pretrained(EMBEDDER_ID),
            AutoModel.from_pretrained(EMBEDDER_ID).eval(),
        )
    return _modelos_cargados


def abrir_imagen(contenido: bytes):
    """bytes → imagen RGB, o None si el archivo no es legible.

    Producción tiene al menos una foto truncada (reporte 29): una foto rota no
    puede tumbar la corrida entera, solo se queda sin vector.
    """
    import warnings
    from io import BytesIO

    from PIL import Image

    try:
        with warnings.catch_warnings():
            # PIL solo AVISA de una bomba de descompresión entre su límite y el
            # doble, y solo lanza por encima: un PNG de pocos KB puede pedir
            # cientos de MB al convertir. Aquí el aviso es error y se trata como
            # cualquier otra foto ilegible.
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            return Image.open(BytesIO(contenido)).convert("RGB")
    except Exception:  # noqa: BLE001 — cualquier fallo de decodificación es "sin vector"
        logger.warning("Imagen ilegible (truncada, bomba de descompresión o formato raro)")
        return None


def recortar_animal(imagen):
    """Recorta a la caja del animal más confiable, o None si no hay ninguno."""
    import torch

    det_proc, detector, _, _ = _modelos()
    with torch.no_grad():
        entradas = det_proc(images=imagen, return_tensors="pt")
        salida = detector(**entradas)
        detecciones = det_proc.post_process_object_detection(
            salida,
            target_sizes=torch.tensor([imagen.size[::-1]]),
            threshold=UMBRAL_DETECCION,
        )[0]

    mejor_caja, mejor_score = None, 0.0
    for score, etiqueta, caja in zip(
        detecciones["scores"], detecciones["labels"], detecciones["boxes"], strict=True
    ):
        if detector.config.id2label[int(etiqueta)] in CLASES_ANIMAL and float(score) > mejor_score:
            mejor_caja, mejor_score = caja.tolist(), float(score)

    if mejor_caja is None:
        return None

    x0, y0, x1, y1 = mejor_caja
    ancho, alto = x1 - x0, y1 - y0
    return imagen.crop(
        (
            max(0, x0 - ancho * MARGEN_RECORTE),
            max(0, y0 - alto * MARGEN_RECORTE),
            min(imagen.size[0], x1 + ancho * MARGEN_RECORTE),
            min(imagen.size[1], y1 + alto * MARGEN_RECORTE),
        )
    )


def vector_de_foto(contenido: bytes, *, recortar: bool = True) -> list[float] | None:
    """bytes de una foto → vector normalizado de `DIMENSIONES`, o None.

    Devuelve None (y lo registra) cuando la foto no se puede leer o no se le
    detecta ningún animal — el reporte simplemente se queda sin parecido visual
    y sus coincidencias siguen saliendo por cercanía, como antes del ADR 0012.

    `recortar=False` embebe la imagen COMPLETA. No lo usa el worker: existe para
    que `calibrar.py` pueda medir el efecto del recorte y dejar reproducible la
    evidencia del ADR (el póster de "¡SE PERDIÓ!" contamina el vector).
    """
    import torch
    import torch.nn.functional as F

    imagen = abrir_imagen(contenido)
    if imagen is None:
        return None

    if recortar:
        recorte = recortar_animal(imagen)
        if recorte is None:
            logger.info("Sin animal detectable en la foto — se deja sin vector")
            return None
    else:
        recorte = imagen

    _, _, emb_proc, embedder = _modelos()
    with torch.no_grad():
        entradas = emb_proc(images=recorte, return_tensors="pt")
        cls = embedder(**entradas).last_hidden_state[:, 0, :]
        vector = F.normalize(cls, dim=1)[0].tolist()

    # Apuntar EMBEDDER_ID a un modelo de otra dimensión llenaría la columna de
    # vectores incomparables sin que nada fallara: el error humano más caro de
    # este pipeline, y cuesta una línea atraparlo.
    if len(vector) != DIMENSIONES:
        logger.error(
            "El modelo devolvió %d dims y se esperaban %d — no se guarda nada",
            len(vector),
            DIMENSIONES,
        )
        return None

    return [round(valor, DECIMALES) for valor in vector]
