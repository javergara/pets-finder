"""Auditoría de duplicados de una instancia completa de Pet Finder Col.

    python -m dedup.cli                     # informe contra PETFINDER_API_URL
    python -m dedup.cli --json informe.json # además guarda el informe completo
    python -m dedup.cli --aplicar           # elimina las copias crawl propias

Sin --aplicar es solo lectura. --aplicar borra ÚNICAMENTE los sobrantes
'casi seguro' que sean copias crawl del usuario del crawler (CRAWLER_USER_ID):
lo único que sus herramientas de autor pueden eliminar. Los duplicados
manuales siempre quedan en 'revisión humana' — un caso real borrado por error
es una mascota que nadie busca.
"""

import argparse
import json
import os
import sys

import requests

from .deteccion import clusters_duplicados, plan_curacion


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Detecta duplicados en los reportes publicados")
    parser.add_argument("--json", type=str, default=None, help="Ruta para el informe JSON completo")
    parser.add_argument(
        "--respaldo",
        type=str,
        default="respaldo_dedup.json",
        help="Archivo donde se respalda el JSON completo de cada reporte antes de borrarlo",
    )
    parser.add_argument(
        "--aplicar",
        action="store_true",
        help="Elimina las copias crawl propias marcadas 'casi seguro' (requiere CRAWLER_USER_ID)",
    )
    args = parser.parse_args(argv)

    api_url = os.environ.get("PETFINDER_API_URL", "http://127.0.0.1:8000").rstrip("/")
    user_id_crawler = (
        int(os.environ["CRAWLER_USER_ID"]) if os.environ.get("CRAWLER_USER_ID") else None
    )

    respuesta = requests.get(f"{api_url}/api/reports", params={"estado": "todos"}, timeout=30)
    respuesta.raise_for_status()
    reportes = respuesta.json()

    clusters = clusters_duplicados(reportes)
    plan = plan_curacion(clusters, user_id_crawler)

    eliminables = [s for c in plan for s in c["sobrantes"] if s["accion"].startswith("eliminable")]
    revision = [s for c in plan for s in c["sobrantes"] if s["accion"].startswith("revisión")]

    print(f"{len(reportes)} reportes en {api_url} → {len(plan)} clusters de posibles duplicados")
    for c in plan:
        etiqueta = c["nombre"] or f"{c['especie']} sin nombre"
        ids = ", ".join(f"#{s['id']}" for s in c["sobrantes"])
        print(
            f"  [{c['nivel']:11}] {etiqueta:15} ({c['tipo']}, tel …{c['telefono'][-4:]}) "
            f"canónico #{c['canonico']} · sobrantes: {ids}"
        )
    print(
        f"\nresumen: {len(eliminables)} eliminables (copias crawl propias) · "
        f"{len(revision)} para revisión humana"
    )

    if args.json:
        with open(args.json, "w") as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)
        print(f"informe completo en {args.json}")

    if not args.aplicar:
        return 0

    if user_id_crawler is None:
        print("--aplicar requiere CRAWLER_USER_ID en el entorno", file=sys.stderr)
        return 2
    por_id = {r["id"]: r for r in reportes}
    respaldo = []
    borrados = 0
    for sobrante in eliminables:
        # Un duplicado con avistamientos lleva pistas colgadas: no se borra.
        avs = requests.get(f"{api_url}/api/reports/{sobrante['id']}/avistamientos", timeout=30)
        if avs.ok and avs.json():
            print(f"#{sobrante['id']} omitido: tiene {len(avs.json())} avistamiento(s)")
            continue
        respaldo.append(por_id[sobrante["id"]])
        with open(args.respaldo, "w") as f:
            json.dump(respaldo, f, indent=2, ensure_ascii=False)
        r = requests.delete(
            f"{api_url}/api/reports/{sobrante['id']}",
            params={"user_id": user_id_crawler},
            timeout=30,
        )
        r.raise_for_status()
        borrados += 1
        print(f"eliminado #{sobrante['id']} (copia crawl duplicada; respaldo en {args.respaldo})")
    print(f"curación aplicada: {borrados} copias eliminadas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
