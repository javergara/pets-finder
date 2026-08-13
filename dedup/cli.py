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

from .deteccion import clusters_duplicados, pares_fusionables, plan_curacion
from .juez import juzgar_par


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
        "--juez",
        action="store_true",
        help="Anota los pares ambiguos con el veredicto de un modelo (requiere OPENAI_API_KEY)",
    )
    parser.add_argument(
        "--fusionar",
        action="store_true",
        help="Aplica la fusión del juez en pares crawl propios (requiere --juez y CRAWLER_USER_ID)",
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

    por_id = {r["id"]: r for r in reportes}

    if args.juez:
        if not os.environ.get("OPENAI_API_KEY"):
            print("--juez requiere OPENAI_API_KEY en el entorno", file=sys.stderr)
            return 2
        for c in plan:
            for s in c["sobrantes"]:
                if not s["accion"].startswith("revisión"):
                    continue
                try:
                    s["juez"] = juzgar_par(por_id[c["canonico"]], por_id[s["id"]])
                except Exception as exc:  # noqa: BLE001 — un par fallido no tumba el informe
                    s["juez"] = {"error": str(exc)}
                    print(f"  juez #{c['canonico']}↔#{s['id']}: ERROR — {exc}", file=sys.stderr)
                    continue
                v = s["juez"]
                veredicto = "MISMO caso" if v["mismo_caso"] else "casos distintos"
                print(
                    f"  juez #{c['canonico']}↔#{s['id']}: {veredicto} "
                    f"(confianza {v['confianza']:.2f}) — {v['razon']}"
                )

    if args.json:
        with open(args.json, "w") as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)
        print(f"informe completo en {args.json}")

    if args.fusionar:
        if not args.juez or user_id_crawler is None:
            print("--fusionar requiere --juez y CRAWLER_USER_ID", file=sys.stderr)
            return 2
        respaldo_fusion = []
        for par in pares_fusionables(plan, por_id, user_id_crawler):
            respaldo_fusion.append(por_id[par["sobrante"]])
            with open(args.respaldo, "w") as f:
                json.dump(respaldo_fusion, f, indent=2, ensure_ascii=False)
            r = requests.put(
                f"{api_url}/api/reports/{par['canonico']}",
                json={"user_id": user_id_crawler, **par["fusion"]},
                timeout=30,
            )
            r.raise_for_status()
            r = requests.delete(
                f"{api_url}/api/reports/{par['sobrante']}",
                params={"user_id": user_id_crawler},
                timeout=30,
            )
            r.raise_for_status()
            print(
                f"fusionado #{par['sobrante']} → #{par['canonico']} "
                f"(señas combinadas aplicadas; respaldo en {args.respaldo})"
            )

    if not args.aplicar:
        return 0

    if user_id_crawler is None:
        print("--aplicar requiere CRAWLER_USER_ID en el entorno", file=sys.stderr)
        return 2
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
