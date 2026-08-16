"""Posibles coincidencias entre reportes perdidos y encontrados.

Función pura (sin I/O, sin DB): recibe el reporte de referencia y los candidatos
ya cargados, y devuelve los que podrían ser la misma mascota, ordenados del más
probable al menos probable.

Dos señales (razonamiento completo y calibración en el ADR 0012):

    cercania = 1 / (1 + distancia_km + PESO_DIAS * |Δdías|)      → (0, 1]
    bono     = max(0, similitud - UMBRAL_MEDIO) / (1 - UMBRAL_MEDIO)
    afinidad = cercania + BONO_VISUAL * bono

Que el parecido solo **sume** y nunca reste es la decisión de diseño central: el
modelo tiene ~72% de top-1, así que un parecido bajo no es evidencia de que sean
mascotas distintas, solo ausencia de evidencia. Si restara, publicar una foto
mala hundiría un reporte que hoy sale bien por cercanía.

De ahí sale la propiedad que fija el test `test_sin_embeddings_el_orden_es_...`:
**sin vectores el orden es EXACTAMENTE el de antes del ADR 0012**, porque
`cercania` es monótona decreciente del puntaje viejo. La degradación elegante es
aritmética, no un `if` de emergencia.

El puntaje sigue sin ser una probabilidad: por eso la UI habla de "posibles
coincidencias" y muestra una banda, nunca un porcentaje.
"""

from ..models.report import Report
from .geo import distancia_km

PESO_DIAS = 0.5

# Umbrales calibrados contra las fotos reales de producción — la tabla de
# medición y su porqué viven en el ADR 0012 §1, no se duplican aquí.
UMBRAL_MEDIO = 0.80
UMBRAL_ALTO = 0.90
# Por encima de esto no son dos fotos parecidas: son la MISMA imagen (ver
# `parecido_visual`). El verdadero positivo real medido fue 0.997, así que el
# umbral va bien por encima para no descartar reencuentros de verdad.
UMBRAL_MISMA_IMAGEN = 0.9999
# `cercania` vale como máximo 1.0, así que con 2.0 un parecido "alto" (0.90 →
# +1.0) iguala al candidato pegado y uno casi idéntico manda sin discusión.
BONO_VISUAL = 2.0


def _tipo_opuesto(tipo: str) -> str:
    return "encontrado" if tipo == "perdido" else "perdido"


def similitud_coseno(a: list[float] | None, b: list[float] | None) -> float | None:
    """Coseno entre dos vectores ya normalizados, o None si no se pueden comparar.

    384 dimensiones en Python puro: unos cientos de microsegundos por candidato.
    No amerita numpy (que además no cabría en la función serverless) ni pgvector
    — ver ADR 0012.

    El `isinstance` es defensa en profundidad: hoy solo el worker escribe la
    columna y siempre escribe `list[float]`, pero es JSON leído de la base y un
    valor raro reventaría un endpoint público con un 500 en vez de degradar.
    """
    if not a or not b or len(a) != len(b):
        return None
    if not all(isinstance(x, int | float) for x in a):
        return None
    if not all(isinstance(x, int | float) for x in b):
        return None
    return sum(x * y for x, y in zip(a, b, strict=True))


def parecido_visual(reporte: Report, candidato: Report) -> float | None:
    """Similitud utilizable entre dos reportes, o None si no hay evidencia visual.

    Devuelve None cuando falta un vector, cuando vienen de pipelines distintos
    (espacios vectoriales no comparables — mezclarlos sería un bug silencioso),
    o cuando los dos reportes son en realidad **la misma imagen**.

    Ese último caso se detecta por vector, no por URL, y es una defensa de
    seguridad además de una de calidad:

    - El crawler saca N mascotas de un mismo pantallazo (ADR 0010 §6) y ahí un
      coseno de 1.0 dice "es la misma imagen", no "es la misma mascota".
    - Sin auth real (ADR 0005 §4), cualquiera puede bajar la foto pública de un
      reporte perdido, volver a subirla —lo que le da una URL nueva— y publicar
      un "encontrado" que quedaría clavado en el primer puesto con parecido
      máximo. Comparar URLs no lo frena; comparar vectores sí.

    Techo conocido: quien recorte o recomprima la foto ajena baja de este umbral
    y vuelve a pasar. Contra eso la respuesta es moderación (feature 23 del
    backlog), no un umbral más agresivo que empezaría a descartar reencuentros
    reales — el verdadero positivo medido en la calibración fue 0.997.
    """
    if reporte.embedding_modelo != candidato.embedding_modelo:
        return None
    if reporte.foto_url is not None and reporte.foto_url == candidato.foto_url:
        return None
    similitud = similitud_coseno(reporte.embedding, candidato.embedding)
    if similitud is not None and similitud >= UMBRAL_MISMA_IMAGEN:
        return None
    return similitud


def banda_de_parecido(similitud: float | None) -> str | None:
    """Similitud → etiqueta para la UI. Nunca un porcentaje (ADR 0012)."""
    if similitud is None:
        return None
    if similitud >= UMBRAL_ALTO:
        return "alto"
    if similitud >= UMBRAL_MEDIO:
        return "medio"
    return None


def ordenar_coincidencias(
    reporte: Report, candidatos: list[Report]
) -> list[tuple[Report, float, float | None]]:
    """Filtra y ordena candidatos; devuelve (candidato, distancia_km, similitud).

    Filtro: tipo opuesto al del reporte, misma especie y estado "activo" (el
    propio reporte nunca es candidato de sí mismo, lo excluye el filtro de
    tipo). La **zona** dejó de ser un filtro duro: un candidato de otra zona
    entra si su parecido visual llega al menos a `UMBRAL_MEDIO`. Sin evidencia
    visual el alcance es el de siempre — la misma zona.

    La distancia devuelta es la geográfica real (sin la penalización por fecha)
    — es lo que se muestra en la UI.
    """
    tipo_buscado = _tipo_opuesto(reporte.tipo)

    puntuados: list[tuple[Report, float, float | None, float]] = []
    for candidato in candidatos:
        if candidato.tipo != tipo_buscado:
            continue
        if candidato.especie != reporte.especie:
            continue
        if candidato.estado != "activo":
            continue

        similitud = parecido_visual(reporte, candidato)
        misma_zona = candidato.zona == reporte.zona
        if not misma_zona and (similitud is None or similitud < UMBRAL_MEDIO):
            continue

        distancia = distancia_km(reporte.lat, reporte.lng, candidato.lat, candidato.lng)
        dias = abs((reporte.fecha_evento - candidato.fecha_evento).days)
        cercania = 1 / (1 + distancia + PESO_DIAS * dias)

        afinidad = cercania
        if similitud is not None and similitud > UMBRAL_MEDIO:
            afinidad += BONO_VISUAL * (similitud - UMBRAL_MEDIO) / (1 - UMBRAL_MEDIO)

        puntuados.append((candidato, distancia, similitud, afinidad))

    # Mayor afinidad primero. El id desempata para que el orden sea estable
    # entre requests (dos candidatos pueden empatar exacto: misma foto, mismo día).
    puntuados.sort(key=lambda item: (-item[3], item[0].id))
    return [
        (candidato, round(distancia, 2), similitud)
        for candidato, distancia, similitud, _ in puntuados
    ]


ETIQUETA_ESPECIE = {"perro": "perro", "gato": "gato", "otro": "otro animal"}


def razones_coincidencia(reporte: Report, candidato: Report, distancia: float) -> list[str]:
    """Por qué este candidato coincide, en frases cortas para chips de UI.

    Solo informa — el orden lo decide `ordenar_coincidencias` y no cambia
    (feature 37): la especie es filtro (siempre coincide), distancia y días son
    el puntaje, y color/tamaño se agregan cuando ambos los declaran iguales.
    Benchmark encontradogs (product-research §9): mostrar el porqué da confianza
    sin volver el motor una caja negra.

    La zona **ya no** es filtro duro desde el ADR 0012: el parecido visual puede
    traer un candidato de otra ciudad, y en ese caso la razón lo dice en vez de
    afirmar algo falso. El chip de "Parecido alto/medio" que va al lado es el
    que explica por qué ese candidato está ahí pese a la distancia.
    """
    razones = [f"mismo {ETIQUETA_ESPECIE.get(reporte.especie, 'animal')}"]

    # La zona dejó de ser un filtro duro (ADR 0012): un candidato puede entrar
    # desde otra zona si su parecido visual lo justifica, así que esta razón ya
    # no puede darse por sentada — decirla mal sería peor que no decirla.
    if candidato.zona == reporte.zona:
        razones.append(f"misma zona ({reporte.zona})")
    else:
        razones.append(f"otra zona ({candidato.zona})")
    razones.append(f"a {distancia} km")

    dias = abs((reporte.fecha_evento - candidato.fecha_evento).days)
    if dias == 0:
        razones.append("el mismo día")
    elif dias == 1:
        razones.append("1 día de diferencia")
    else:
        razones.append(f"{dias} días de diferencia")

    if reporte.color and reporte.color != "Otro" and reporte.color == candidato.color:
        razones.append("mismo color")
    if reporte.tamano and reporte.tamano == candidato.tamano:
        razones.append("mismo tamaño")

    return razones
