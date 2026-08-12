"""Extractor: pantallazo → PostExtraido vía LlamaExtract (SDK v2, `llama-cloud`).

Único módulo que habla con LlamaCloud. La extracción es stateless: el esquema
de crawler/schema.py viaja en cada request como JSON Schema — no hay agente ni
estado que sincronizar en LlamaCloud. (El paquete `llama-cloud-services` y su
API de agentes quedaron deprecados en mayo de 2026.)

Imports perezosos a propósito: el resto del paquete (y sus tests) no necesita
`llama-cloud` instalado. Requiere LLAMA_CLOUD_API_KEY en el entorno.
"""

from pathlib import Path

from .schema import PostExtraido


def extraer(ruta_imagen: Path) -> PostExtraido:
    # Imports perezosos: solo al extraer de verdad.
    from llama_cloud import LlamaCloud
    from llama_cloud.types import ExtractConfigurationParam

    client = LlamaCloud()  # lee LLAMA_CLOUD_API_KEY del entorno
    with ruta_imagen.open("rb") as f:
        archivo = client.files.create(file=f, purpose="extract")
    job = client.extract.create(
        file_input=archivo.id,
        configuration=ExtractConfigurationParam(
            data_schema=PostExtraido.model_json_schema(),
            extraction_target="per_doc",
            # agentic_plus: el tier con más razonamiento multimodal — los
            # pantallazos mezclan texto sobre fotos y UI, y el tier estándar
            # confundió el color del collar con el del animal (corrida C3).
            tier="agentic_plus",
        ),
    )
    job = client.extract.wait_for_completion(job.id)
    if job.status != "COMPLETED":
        raise RuntimeError(
            f"La extracción de {ruta_imagen.name} terminó en {job.status}: {job.error_message}"
        )

    datos = job.extract_result
    if isinstance(datos, list):  # per_doc: un resultado por documento
        datos = datos[0]
    return PostExtraido.model_validate(datos)
