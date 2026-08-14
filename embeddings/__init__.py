"""Worker de parecido visual entre reportes (ADR 0012).

Paquete INDEPENDIENTE en ejecución (no se despliega a Vercel ni lo importa la
API) pero que corre desde el checkout e importa los modelos y las rutas de media
de la API como fuente de verdad. Sus dependencias de terceros viven aparte
(embeddings/requirements.txt): torch no tiene wheels para el runtime serverless
de Vercel ni cabría en su bundle.

Calcula el vector de la foto de cada reporte y lo guarda en `reports.embedding`,
para que `services/coincidencias.py` ordene también por lo que se ve.
"""

import sys
from pathlib import Path

# Los modelos de la API se importan desde el checkout (ver docstring).
_RAIZ_REPO = Path(__file__).resolve().parents[1]
_API = str(_RAIZ_REPO / "src" / "api")
if _API not in sys.path:
    sys.path.insert(0, _API)
