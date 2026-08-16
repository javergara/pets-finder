"""Guardarraíl del ADR 0013: ninguna pieza de chat en tiempo real entra a la API.

La era Adopta resolvió la comunicación de una solicitud con **WebSockets nativos
de FastAPI y un `ConnectionManager` en memoria** (ADR 0004): un dict
`match_id -> list[WebSocket]` a nivel de módulo, correcto para un solo proceso
`uvicorn`. En producción la API es una función serverless (ADR 0007): cada
request levanta una instancia efímera, no hay proceso persistente entre
requests ni memoria compartida entre invocaciones. Ese manager no es "poco
escalable" ahí: no funciona ni una vez.

Por eso el ADR 0013 elige WhatsApp directo y **supera al 0004**, y por eso este
archivo existe. El riesgo real no es que alguien decida volver a los WebSockets
—eso pasaría por un ADR—: es que alguien porte por inercia `chat.py` o
`chat_manager.py` desde `origin/adopta-v1` mientras trae el resto del módulo, y
que la app pase los tests en local (donde sí hay un `uvicorn` persistente) y
falle solo en producción.

Un test de contenido de archivos es raro, y es a propósito: no hay ninguna
llamada que hacer para comprobar la ausencia de algo. La alternativa —confiar en
que el ADR se lea— ya falló una vez en este repo.
"""

from pathlib import Path

import reencuentro_api

#: Las tres huellas de la solución del ADR 0004. `WebSocket` cubre el tipo y el
#: decorador (`@router.websocket`, que en minúsculas cae en `websockets`);
#: `ConnectionManager` cubre el registro en memoria, que es la pieza que el
#: serverless hace imposible aunque el transporte fuera otro.
PROHIBIDAS = ("WebSocket", "websockets", "ConnectionManager")

RAIZ_API = Path(reencuentro_api.__file__).parent

ARCHIVOS = sorted(RAIZ_API.rglob("*.py"))


def test_hay_archivos_que_revisar():
    """Si el `rglob` deja de encontrar el paquete, el guardarraíl pasaría vacío.

    Un test que recorre archivos y no encuentra ninguno es verde y no comprueba
    nada: este caso es el que impide que el de abajo se vuelva decorativo si
    algún día cambia el layout del paquete.
    """
    assert len(ARCHIVOS) > 20
    assert (RAIZ_API / "main.py") in ARCHIVOS


def test_ninguna_dependencia_de_websockets():
    """Ni WebSockets ni estado en memoria entre requests, en ningún módulo de la API.

    Un solo caso para toda la API, y no uno parametrizado por archivo: no son 50
    comportamientos distintos sino una propiedad del paquete entero, y así el
    fallo llega con **todos** los sitios que hay que arreglar, no solo con el
    primero que ordenó el `rglob`.
    """
    hallazgos = {
        str(archivo.relative_to(RAIZ_API.parent)): [
            huella for huella in PROHIBIDAS if huella in archivo.read_text(encoding="utf-8")
        ]
        for archivo in ARCHIVOS
    }
    culpables = {ruta: huellas for ruta, huellas in hallazgos.items() if huellas}

    assert not culpables, (
        f"{culpables}: el ADR 0013 dejó fuera el chat en tiempo real porque el "
        "ConnectionManager en memoria del ADR 0004 no sobrevive al serverless de "
        "Vercel. Si hace falta un canal interno, se revisa el ADR primero."
    )


def test_las_dependencias_de_la_api_no_traen_un_cliente_de_realtime():
    """La otra puerta del ADR 0013: la opción (b) entraba por `requirements.txt`.

    Supabase Realtime se descartó por producto (clave anon en el navegador sin
    auth real detrás, tabla de mensajes que migrar, ADR extra). Aquí se fija que
    la API no arrastre su SDK ni un cliente de websockets propio: `uvicorn` ya
    trae `websockets` como dependencia transitiva, así que el candado va sobre lo
    que el repo declara, no sobre lo que el entorno instala.
    """
    requirements = (RAIZ_API.parent / "requirements.txt").read_text(encoding="utf-8").lower()

    assert "supabase" not in requirements
    assert "websocket" not in requirements
