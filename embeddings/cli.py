"""Worker de embeddings: calcula el vector visual de los reportes que no lo tienen.

Proceso independiente de la API (ADR 0012): el runtime serverless de Vercel no
puede cargar torch, así que esto corre desde el checkout — a mano hoy, por cron
después. Escribe directo a la DB (como `scripts/seed.py`) y NO por la API: no
hay auth real (ADR 0005 §4) y un endpoint abierto de escritura de embeddings
dejaría que cualquiera envenene el matching.

    python -m embeddings.cli                 # dry-run: dice qué haría
    python -m embeddings.cli --escribir      # calcula y guarda
    python -m embeddings.cli --reporte 66 --escribir
    python -m embeddings.cli --rehacer --escribir   # recalcula todo el pipeline

⚠️ Escribe en la base que diga DATABASE_URL. Apuntar a producción exige
autorización explícita del dueño. A diferencia de `scripts/seed.py`, este worker
NUNCA borra ni recrea nada: solo rellena dos columnas.
"""

from __future__ import annotations

import argparse
import logging
import sys

import requests

# El bootstrap de sys.path vive en __init__.py (mismo patrón que crawler/).
from reencuentro_api.media import MEDIA_DIR, prefijo_publico
from reencuentro_api.models import Report, SessionLocal, engine

from .modelo import PIPELINE, vector_de_foto

TIMEOUT_DESCARGA = 20
# El endpoint de uploads ya limita a 5 MB; este tope cubre lo que pueda haber
# entrado por otras vías y evita que una respuesta enorme tumbe la corrida.
MAX_BYTES_FOTO = 15 * 1024 * 1024


def leer_foto(foto_url: str) -> bytes | None:
    """Descarga (URL del bucket propio) o lee del disco (/media/... local).

    `foto_url` la fija quien crea el reporte y **cualquiera puede crear uno**
    (no hay auth real, ADR 0005 §4). Este worker corre desde la máquina del
    dueño o desde CI, así que una URL arbitraria lo convertiría en un SSRF
    contra su red interna, y una ruta local arbitraria en un lector de archivos
    de su disco. De ahí las dos restricciones de abajo.
    """
    if foto_url.startswith("http"):
        prefijo = prefijo_publico()
        if not prefijo or not foto_url.startswith(prefijo):
            print("    ! foto_url fuera del bucket propio — se ignora")
            return None
        try:
            # Sin redirects: si no, un 302 desde el bucket saltaría el filtro.
            respuesta = requests.get(
                foto_url, timeout=TIMEOUT_DESCARGA, stream=True, allow_redirects=False
            )
        except requests.RequestException as error:
            print(f"    ! red: {error}")
            return None
        if respuesta.status_code != 200:
            print(f"    ! HTTP {respuesta.status_code}")
            return None
        # Tope de tamaño: una respuesta enorme reventaría el proceso y con él
        # toda la corrida (el commit es único al final).
        contenido = respuesta.raw.read(MAX_BYTES_FOTO + 1, decode_content=True)
        if len(contenido) > MAX_BYTES_FOTO:
            print(f"    ! foto de más de {MAX_BYTES_FOTO // 1024 // 1024} MB — se ignora")
            return None
        return contenido

    if foto_url.startswith("/media/"):
        # `Path` deja que un componente absoluto descarte la base ("/media/C:/…")
        # y que ".." escale por encima, así que se resuelve y se comprueba.
        raiz = MEDIA_DIR.resolve()
        archivo = (raiz / foto_url[len("/media/") :]).resolve()
        if not archivo.is_relative_to(raiz):
            print(f"    ! ruta fuera de {raiz} — se ignora")
            return None
        if not archivo.is_file():
            print(f"    ! no existe en disco: {archivo}")
            return None
        return archivo.read_bytes()

    print(f"    ! ruta de foto no reconocida: {foto_url}")
    return None


def pendientes(session, rehacer: bool, reporte_id: int | None) -> list[Report]:
    """Reportes con foto cuyo vector falta o quedó de un pipeline viejo."""
    consulta = session.query(Report).filter(Report.foto_url.isnot(None))
    if reporte_id is not None:
        consulta = consulta.filter(Report.id == reporte_id)
    elif not rehacer:
        # `embedding_modelo != PIPELINE` es NULL (no true) cuando la columna es
        # NULL, así que una fila con vector pero sin pipeline —lo que dejaría un
        # backfill interrumpido a mitad— quedaría invisible para siempre.
        consulta = consulta.filter(
            (Report.embedding.is_(None))
            | (Report.embedding_modelo.is_(None))
            | (Report.embedding_modelo != PIPELINE)
        )
    return consulta.order_by(Report.id).all()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Calcula embeddings visuales de los reportes.")
    parser.add_argument(
        "--escribir", action="store_true", help="guarda en la DB (default: dry-run)"
    )
    parser.add_argument("--rehacer", action="store_true", help="recalcula aunque ya tengan vector")
    parser.add_argument("--reporte", type=int, default=None, help="procesa solo ese id")
    parser.add_argument("--limite", type=int, default=None, help="procesa como máximo N reportes")
    args = parser.parse_args(argv)

    # Sin esto los logger.info/warning de modelo.py se descartan y el operador
    # se come en silencio los ~10 s de carga de modelos y el motivo real de cada
    # foto sin vector (ilegible vs sin animal detectable).
    logging.basicConfig(level=logging.INFO, format="  %(message)s")

    print(f"DB: {engine.dialect.name} · {engine.url.host or engine.url.database}")
    print(f"Pipeline: {PIPELINE}")
    if not args.escribir:
        print("DRY-RUN — nada se guarda (usa --escribir para persistir)")

    session = SessionLocal()
    try:
        objetivo = pendientes(session, args.rehacer, args.reporte)
        if args.limite:
            objetivo = objetivo[: args.limite]
        print(f"{len(objetivo)} reportes por procesar\n")

        con_vector = sin_animal = sin_foto = 0
        for reporte in objetivo:
            print(f"  #{reporte.id} ({reporte.tipo}/{reporte.especie})", end=" ")
            contenido = leer_foto(reporte.foto_url)
            if contenido is None:
                sin_foto += 1
                continue

            vector = vector_de_foto(contenido)
            if vector is None:
                # El motivo exacto (ilegible vs sin animal) queda en el log de
                # `modelo.py`; para el operador ambos casos son lo mismo: ese
                # reporte se queda con coincidencias por cercanía nada más.
                print("→ sin vector (foto ilegible o sin animal detectable)")
                sin_animal += 1
                continue

            print(f"→ vector de {len(vector)} dims")
            con_vector += 1
            if args.escribir:
                reporte.embedding = vector
                reporte.embedding_modelo = PIPELINE

        if args.escribir:
            session.commit()
            print(f"\nGuardados {con_vector} vectores.")
        else:
            session.rollback()
            print(f"\n(dry-run) {con_vector} vectores calculados y descartados.")
        print(f"Sin vector: {sin_animal} · Foto no descargable: {sin_foto}")
    finally:
        session.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
