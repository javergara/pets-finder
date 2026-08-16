"""El orden y el contenido de los rewrites de `vercel.json` (AD-08 paso 3).

Los rewrites por user-agent son lo único que hace que un rastreador de WhatsApp
llegue a `routers/paginas.py` en vez de recibir la SPA: sin ellos, los og tags
del paso 2 existen y **no los ve nadie**. Y son sensibles al orden — el catch-all
`/((?!api/).*)` casa con todo lo que no empiece por `api/`, así que cualquier
rewrite colocado detrás de él es código muerto que ningún test de Python ni de
web detectaría.

⚠️ **Límite explícito de este archivo**: verifica la **configuración**, no la
semántica de matching de Vercel. Que `:id` no cruce una `/` —y por tanto que
`/adoptar/mascota/7/editar` NO entre por este rewrite— es comportamiento de la
plataforma y no se puede probar leyendo el JSON. Eso se comprueba contra
producción, en AD-09, con un `curl` y el user-agent de un bot.
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

CATCH_ALL = "/((?!api/).*)"

# Las tres rutas que un bot tiene que poder alcanzar. Escritas a mano a
# propósito: si mañana alguien añade una página de bots y no la apunta aquí,
# este archivo no la protege y más vale que se note al leerlo.
FUENTES_DE_BOTS = (
    "/(cali|armenia|pereira|manizales|quibdo|bogota|medellin)",  # landings por zona (feature 46)
    "/reporte/:id",  # ficha de un reporte (feature 21)
    "/adoptar/mascota/:id",  # ficha de una mascota en adopción (AD-08)
)

# La lista de bots, escrita a mano y no derivada del JSON: es lo que convierte
# esto en un anti-drift. Quitar uno aquí o allá tiene que dar rojo.
# Googlebot NO está y no se añade de paso: cambiaría lo que Google indexa
# también de /reporte/:id, y esa es una decisión de SEO con su propio ADR.
BOTS = (
    "facebookexternalhit",
    "WhatsApp",
    "Twitterbot",
    "TelegramBot",
    "LinkedInBot",
    "Slackbot",
    "Discordbot",
)


def _rewrites() -> list[dict]:
    config = json.loads((REPO_ROOT / "vercel.json").read_text(encoding="utf-8"))
    return config["rewrites"]


def _por_fuente(fuente: str) -> dict:
    coincidencias = [r for r in _rewrites() if r["source"] == fuente]
    assert len(coincidencias) == 1, f"'{fuente}' aparece {len(coincidencias)} veces en vercel.json"
    return coincidencias[0]


def _bots_de(rewrite: dict) -> list[str]:
    """Saca la lista de user-agents de un valor con forma `.*(a|b|c).*`."""
    (condicion,) = rewrite["has"]
    valor = condicion["value"]
    assert valor.startswith(".*(") and valor.endswith(").*"), valor
    return valor[3:-3].split("|")


def test_la_ficha_de_adopcion_tiene_su_rewrite_de_bots():
    rewrite = _por_fuente("/adoptar/mascota/:id")

    assert rewrite["destination"] == "/api/index"


def test_el_bloque_de_bots_de_la_mascota_es_identico_al_del_reporte():
    """Comparación de objetos, no de un regex leído a ojo: los dos rewrites
    resuelven el mismo problema y una lista que se desincroniza deja media app
    sin vista previa, que es el fallo más fácil de no ver."""
    assert _por_fuente("/adoptar/mascota/:id")["has"] == _por_fuente("/reporte/:id")["has"]


def test_los_tres_rewrites_de_bots_escuchan_a_los_mismos_user_agents():
    for fuente in FUENTES_DE_BOTS:
        rewrite = _por_fuente(fuente)
        (condicion,) = rewrite["has"]
        assert condicion["type"] == "header"
        assert condicion["key"] == "user-agent"
        assert _bots_de(rewrite) == list(BOTS), f"la lista de bots de '{fuente}' cambió"


def test_ningun_rewrite_de_bots_queda_detras_del_catch_all():
    """El candado del paso: detrás del catch-all el rewrite existe, se lee bien
    y no se ejecuta nunca."""
    fuentes = [r["source"] for r in _rewrites()]
    indice_catch_all = fuentes.index(CATCH_ALL)

    for fuente in FUENTES_DE_BOTS:
        assert (
            fuentes.index(fuente) < indice_catch_all
        ), f"'{fuente}' está detrás del catch-all: los bots recibirían la SPA"


def test_el_catch_all_es_el_ultimo_rewrite():
    fuentes = [r["source"] for r in _rewrites()]

    assert fuentes[-1] == CATCH_ALL
    assert fuentes.count(CATCH_ALL) == 1
