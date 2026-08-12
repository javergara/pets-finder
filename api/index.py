"""Entry point de Vercel: expone la app FastAPI completa como función serverless.

Vercel detecta la variable `app` (ASGI) en api/index.py y enruta hacia ella todo
lo que el rewrite de vercel.json le mande (los paths originales /api/* y /health
llegan intactos a FastAPI — el rewrite solo elige la función, no reescribe la URL
que ve el framework). El paquete real vive en src/api/, fuera del directorio api/
de Vercel, por eso el sys.path.

Requiere las env vars del proyecto Vercel (docs/deploy.md): DATABASE_URL
(Supabase Postgres), SUPABASE_URL, SUPABASE_SERVICE_KEY y SUPABASE_BUCKET —
sin filesystem persistente, la API es 100% sin estado (ADR 0006/0007).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "api"))

from reencuentro_api.main import app  # noqa: E402, F401
