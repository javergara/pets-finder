"""La calibración commiteada como guarda de regresión.

`embeddings/ejemplos/calibracion.json` no es documentación decorativa: es la
evidencia del acceptance 2 de la feature 24. Estos tests la atan a las
constantes que la API usa de verdad, para que nadie mueva un umbral —o cambie
el modelo— sin volver a correr `python -m embeddings.calibrar`.

Offline: solo leen el JSON y las constantes. Ni red, ni torch, ni modelos.
"""

import json
from pathlib import Path

import pytest
from embeddings.modelo import PIPELINE

from reencuentro_api.services.coincidencias import UMBRAL_ALTO, UMBRAL_MEDIO

CALIBRACION = Path(__file__).resolve().parents[2] / "embeddings" / "ejemplos" / "calibracion.json"


@pytest.fixture(scope="module")
def calibracion() -> dict:
    if not CALIBRACION.is_file():
        pytest.fail(
            f"Falta {CALIBRACION.name}: es la evidencia de que el pipeline separa. "
            "Regenerar con `python -m embeddings.calibrar --salida <ruta>`."
        )
    return json.loads(CALIBRACION.read_text(encoding="utf-8"))


def test_la_calibracion_es_del_pipeline_vigente(calibracion):
    """Cambiar detector, embedder o umbral de recorte cambia el espacio vectorial:
    los umbrales calibrados para el pipeline viejo dejan de significar nada."""
    assert calibracion["pipeline"] == PIPELINE, (
        "La calibración es de otro pipeline. Volver a correr `embeddings.calibrar` "
        "antes de confiar en los umbrales."
    )


def test_los_umbrales_separan_el_ruido_de_la_senal(calibracion):
    """La regla de oro: por ENCIMA del p99 de los negativos (pares de animales
    distintos) y por DEBAJO del p10 del control positivo (la misma foto
    transformada). Si estas dos distribuciones se tocan, la feature no debe salir."""
    p99_negativos = max(v["p99"] for v in calibracion["linea_base_negativos"].values())
    p10_positivos = calibracion["control_positivo"]["p10"]

    assert p99_negativos < UMBRAL_MEDIO, (
        f"El umbral medio ({UMBRAL_MEDIO}) está dentro del ruido: el p99 de pares de "
        f"animales DISTINTOS es {p99_negativos}. Se marcarían coincidencias falsas."
    )
    assert UMBRAL_MEDIO < UMBRAL_ALTO < p10_positivos, (
        f"El umbral alto ({UMBRAL_ALTO}) está por encima del p10 del control positivo "
        f"({p10_positivos}): se perderían reencuentros reales."
    )


def test_la_cobertura_del_detector_es_razonable(calibracion):
    """Si el detector deja de encontrar animales, la feature se apaga sola en
    silencio: los reportes sin vector caen a la heurística de siempre."""
    cobertura = calibracion["vectores_obtenidos"] / calibracion["reportes_con_foto"]
    assert cobertura > 0.90, f"Solo {cobertura:.0%} de las fotos produjeron vector"


def _par(calibracion: dict, etiqueta: str) -> dict:
    for entrada in calibracion["pares_del_acceptance"]:
        if entrada["etiqueta"].startswith(etiqueta):
            if entrada.get("estado") == "ausente":
                pytest.skip(f"El par {entrada['par']} ya no existe en producción")
            return entrada
    pytest.fail(f"Falta el par '{etiqueta}' en la calibración")


def test_el_recorte_arregla_el_falso_positivo(calibracion):
    """Acceptance 2, caso negativo: sin recortar al animal el vector describe el
    póster y dos perros distintos daban 0.885. Es la razón de ser de la primera
    etapa del pipeline; si esto deja de cumplirse, el recorte dejó de servir."""
    par = _par(calibracion, "falso positivo")

    assert par["sin_recorte"] > UMBRAL_MEDIO, "el caso dejó de ser un falso positivo interesante"
    assert par["con_recorte"] < UMBRAL_MEDIO, (
        f"Sin recorte daba {par['sin_recorte']} y con recorte {par['con_recorte']}: "
        "dos perros distintos volverían a marcarse como coincidencia."
    )


def test_el_recorte_no_rompe_el_verdadero_positivo(calibracion):
    """Acceptance 2, caso positivo: la misma perra en dos reportes distintos debe
    seguir marcándose "alto" y NO confundirse con "es la misma imagen"."""
    from reencuentro_api.services.coincidencias import UMBRAL_MISMA_IMAGEN

    par = _par(calibracion, "verdadero positivo")

    assert par["con_recorte"] >= UMBRAL_ALTO, "el reencuentro real dejaría de marcarse como alto"
    assert par["con_recorte"] < UMBRAL_MISMA_IMAGEN, (
        f"{par['con_recorte']} cae en el rango de 'misma imagen' ({UMBRAL_MISMA_IMAGEN}): "
        "la guarda antifraude se tragaría un reencuentro real."
    )
