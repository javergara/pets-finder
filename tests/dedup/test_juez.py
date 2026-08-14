"""Juez LLM: construcción del mensaje y parseo del veredicto (sin red)."""

import json

from dedup import juez


def _rep(**extra):
    return {
        "tipo": "encontrado",
        "especie": "perro",
        "descripcion": "Perro dorado mediano.",
        **extra,
    }


def test_mensaje_lleva_senas_de_ambos_y_fotos_solo_si_existen():
    a = _rep(foto_url="https://x/a.jpg", color="Miel / dorado")
    b = _rep(descripcion="Perro café, asustado.")  # sin foto

    contenido = juez.construir_mensaje(a, b)

    assert contenido[0]["type"] == "text"
    assert "Miel / dorado" in contenido[0]["text"]
    assert "Perro café, asustado." in contenido[0]["text"]
    imagenes = [c for c in contenido if c["type"] == "image_url"]
    assert [i["image_url"]["url"] for i in imagenes] == ["https://x/a.jpg"]
    # Campos vacíos de los reportes no viajan (ruido para el modelo).
    assert '": null' not in contenido[0]["text"]


def test_juzgar_par_parsea_el_veredicto(monkeypatch):
    class Respuesta:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "mismo_caso": True,
                                    "confianza": 0.9,
                                    "razon": "misma mancha",
                                    "fusion": {
                                        "descripcion": "Señas combinadas.",
                                        "color": "Negro",
                                        "campo_inventado": "se descarta",
                                    },
                                }
                            )
                        }
                    }
                ]
            }

    capturado = {}

    def post_falso(url, headers=None, json=None, timeout=None):
        capturado["payload"] = json
        return Respuesta()

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(juez.requests, "post", post_falso)

    veredicto = juez.juzgar_par(_rep(), _rep())

    assert veredicto["mismo_caso"] is True
    assert veredicto["confianza"] == 0.9
    # La fusión llega filtrada a los campos editables; lo inventado se descarta.
    assert veredicto["fusion"] == {"descripcion": "Señas combinadas.", "color": "Negro"}
    assert capturado["payload"]["model"] == juez.MODELO_DEFAULT
    assert capturado["payload"]["response_format"] == {"type": "json_object"}


def test_modelo_configurable_por_entorno(monkeypatch):
    class Respuesta:
        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"message": {"content": '{"mismo_caso": false}'}}]}

    capturado = {}
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("DEDUP_JUEZ_MODELO", "otro-modelo")
    monkeypatch.setattr(
        juez.requests, "post", lambda url, **kw: capturado.update(kw) or Respuesta()
    )

    veredicto = juez.juzgar_par(_rep(), _rep())

    assert capturado["json"]["model"] == "otro-modelo"
    assert veredicto["mismo_caso"] is False
    assert veredicto["fusion"] is None
