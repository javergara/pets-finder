"""Crawler de redes sociales para Pet Finder Col (ADR 0009).

Paquete INDEPENDIENTE en ejecución (no se despliega a Vercel ni lo importa la
API) pero que corre desde el checkout del repo e importa el CONTRATO de la API
como fuente de verdad: ReportIn (validación local idéntica al backend, mismos
mensajes) y las zonas de services/ciudades.py (cero copias que se
desincronicen). Sus dependencias de terceros sí viven aparte
(crawler/requirements.txt).

Pipelines de crawling: cada una obtiene publicaciones a su manera (la primera:
pantallazos) y todas convergen en extractor (LlamaExtract) → publicador (POST
/api/reports público con fuente "crawl").
"""

import sys
from pathlib import Path

# El contrato de la API se importa desde el checkout (ver docstring).
_RAIZ_REPO = Path(__file__).resolve().parents[1]
_API = str(_RAIZ_REPO / "src" / "api")
if _API not in sys.path:
    sys.path.insert(0, _API)
