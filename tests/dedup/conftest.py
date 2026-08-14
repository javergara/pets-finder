import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
# El paquete crawler/ vive en la raíz; reencuentro_api se necesita para el test
# de contrato (los payloads del crawler deben pasar el ReportIn real de la API).
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src" / "api"))
