"""CLI de la pipeline de pantallazos: procesa un pantallazo O una carpeta.

El crawler está organizado en pipelines (ADR 0010 §3); esta es la primera:
pantallazos aportados a mano. Uso típico (ver crawler/README.md):

    python -m crawler.cli captura.png --url-post https://instagram.com/p/ABC/
    python -m crawler.cli pantallazos/            # carpeta completa
    python -m crawler.cli pantallazos/ --publicar

Sin --publicar es un dry-run: imprime los payloads que crearía y no publica
nada (la extracción SÍ queda registrada para no pagar el LLM dos veces).
Env vars: LLAMA_CLOUD_API_KEY (extracción), CRAWLER_USER_ID (autor de los
reportes), PETFINDER_API_URL (default http://127.0.0.1:8000 — apuntar a
https://petfinder-col.com SOLO con autorización explícita del dueño).
"""

import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from pydantic import ValidationError

from . import dedup, extractor, publicador
from .schema import PostExtraido

EXTENSIONES_IMAGEN = {".png", ".jpg", ".jpeg", ".webp"}
# Extracciones LlamaExtract en vuelo a la vez: un pool de N hilos es el
# semáforo — solo la llamada de red es concurrente; el dedup y la salida
# corren siempre en el hilo principal (sin locks, output legible).
EXTRACCIONES_CONCURRENTES = 5


def listar_imagenes(entrada: Path) -> list[Path]:
    """Un archivo → [archivo]; una carpeta → sus imágenes en orden estable."""
    if entrada.is_dir():
        return sorted(p for p in entrada.iterdir() if p.suffix.lower() in EXTENSIONES_IMAGEN)
    return [entrada]


def necesita_extraccion(imagen: Path, url_post: str | None) -> bool:
    """True si el dedup no tiene nada aprovechable para esta imagen."""
    entrada = dedup.obtener(dedup.clave_de(url_post, imagen))
    return not entrada or not (
        entrada.get("reporte_ids") or entrada.get("motivo") or entrada.get("payloads")
    )


def extraer_concurrente(
    imagenes: list[Path], url_post: str | None
) -> dict[Path, PostExtraido | Exception]:
    """Extrae en paralelo (máximo EXTRACCIONES_CONCURRENTES en vuelo).

    Una imagen que falle no tumba la corrida: su excepción viaja en el
    resultado y se reporta al procesarla, en orden."""
    pendientes = [img for img in imagenes if necesita_extraccion(img, url_post)]
    posts: dict[Path, PostExtraido | Exception] = {}
    if not pendientes:
        return posts
    with ThreadPoolExecutor(max_workers=EXTRACCIONES_CONCURRENTES) as pool:
        futuros = {pool.submit(extractor.extraer, img): img for img in pendientes}
        for futuro in as_completed(futuros):
            imagen = futuros[futuro]
            try:
                posts[imagen] = futuro.result()
            except Exception as exc:  # noqa: BLE001 — se reporta por imagen, no se oculta
                posts[imagen] = exc
    return posts


def procesar_imagen(
    imagen: Path,
    url_post: str | None,
    foto_url: str | None,
    publicar: bool,
    ciudad: str | None = None,
    post_extraido: PostExtraido | Exception | None = None,
) -> None:
    clave = dedup.clave_de(url_post, imagen)
    entrada = dedup.obtener(clave)
    if entrada and entrada.get("reporte_ids"):
        print(f"[{imagen.name}] ya publicado (dedup) → reportes {entrada['reporte_ids']}")
        return
    if entrada and entrada.get("motivo"):
        print(f"[{imagen.name}] ⚠️ ya extraído pero no publicable: {entrada['motivo']}")
        return

    if entrada and entrada.get("payloads"):
        # Corrida anterior extrajo pero no terminó de publicar: se reutilizan
        # los payloads guardados — re-extraer podría dar otro orden/número de
        # mascotas y desalinear los idempotency_id.
        payloads = publicador.desde_json(entrada["payloads"])
        print(f"[{imagen.name}] retomando extracción registrada ({len(payloads)} payload(s))")
    else:
        user_id = int(os.environ["CRAWLER_USER_ID"])
        post = post_extraido if post_extraido is not None else extractor.extraer(imagen)
        if isinstance(post, Exception):
            print(f"[{imagen.name}] ⚠️ la extracción falló: {post} — se reintenta re-corriendo")
            return
        resumen = f"{len(post.mascotas)} mascota(s), confianza {post.confianza:.2f}"
        print(f"[{imagen.name}] extraído: {resumen}")
        if not post.es_publicacion:
            # Hallazgo de la corrida real: una foto sin texto no trae señal de
            # tipo/nombre/contacto — el LLM adivinaría. No publicable, y queda
            # registrado con motivo (el dedup no re-paga el LLM por ella).
            motivo = "no es una publicación (foto sin texto): los datos serían adivinados"
            print(f"[{imagen.name}] ⚠️ {motivo} — crear el reporte a mano si aplica.")
            dedup.registrar_invalido(clave, motivo)
            return
        try:
            payloads = publicador.convertir(
                post,
                user_id=user_id,
                url_post=url_post,
                foto_url=foto_url,
                clave_post=clave,
                ciudad_fallback=ciudad,
            )
        except ValidationError as exc:
            # El contrato real de la API rechazó la extracción (p. ej. sin
            # camino de contacto) — mismo mensaje que daría el backend, pero
            # local y antes de publicar nada.
            motivo = "; ".join(e["msg"].removeprefix("Value error, ") for e in exc.errors())
            print(f"[{imagen.name}] ⚠️ extracción no publicable: {motivo}")
            dedup.registrar_invalido(clave, motivo)
            return
        if not payloads:
            # Extraer cero mascotas no es un éxito silencioso: se registra con
            # motivo — payloads vacíos en el registro re-pagarían el LLM en
            # cada corrida (bug real de la corrida C3).
            motivo = "la extracción no encontró mascotas en la imagen"
            print(f"[{imagen.name}] ⚠️ {motivo}")
            dedup.registrar_invalido(clave, motivo)
            return
        dedup.registrar_extraccion(clave, publicador.a_json(payloads))

    print(json.dumps(publicador.a_json(payloads), indent=2, ensure_ascii=False))

    if not publicar:
        print(f"[{imagen.name}] dry-run: nada publicado. Añade --publicar para crear los reportes.")
        return

    api_url = os.environ.get("PETFINDER_API_URL", "http://127.0.0.1:8000")
    ids = publicador.publicar(payloads, api_url=api_url)
    dedup.marcar_publicado(clave, ids)
    print(f"[{imagen.name}] publicados {len(ids)} reporte(s) en {api_url}: {ids}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Pipeline de pantallazos: extrae y publica reportes de mascotas"
    )
    parser.add_argument("entrada", type=Path, help="Un pantallazo, o una carpeta de pantallazos")
    parser.add_argument(
        "--url-post",
        default=None,
        help="URL del post original (clave de dedup; solo con un pantallazo único)",
    )
    parser.add_argument("--foto-url", default=None, help="URL pública de la foto para el reporte")
    parser.add_argument(
        "--ciudad",
        default=None,
        help="Ciudad de los pantallazos si los posts no la dicen (quien recolecta la sabe)",
    )
    parser.add_argument(
        "--publicar", action="store_true", help="Publica de verdad (sin esto: dry-run)"
    )
    args = parser.parse_args(argv)

    if not args.entrada.exists():
        print(f"No existe: {args.entrada}", file=sys.stderr)
        return 2
    imagenes = listar_imagenes(args.entrada)
    if not imagenes:
        print(
            f"No hay imágenes ({'/'.join(sorted(EXTENSIONES_IMAGEN))}) en {args.entrada}",
            file=sys.stderr,
        )
        return 2
    if args.entrada.is_dir() and args.url_post:
        # En carpeta cada pantallazo es un post distinto: una sola URL mentiría
        # y colapsaría el dedup de todos en una clave.
        print("--url-post solo aplica procesando un pantallazo único", file=sys.stderr)
        return 2
    if not os.environ.get("CRAWLER_USER_ID"):
        print("Falta CRAWLER_USER_ID en el entorno (usuario sistema del crawler)", file=sys.stderr)
        return 2

    # Fase concurrente: solo las llamadas al LLM. Todo lo demás (dedup,
    # impresión, publicación) sigue secuencial y en orden estable.
    posts = extraer_concurrente(imagenes, args.url_post)
    for imagen in imagenes:
        procesar_imagen(
            imagen,
            url_post=args.url_post,
            foto_url=args.foto_url,
            publicar=args.publicar,
            ciudad=args.ciudad,
            post_extraido=posts.get(imagen),
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
