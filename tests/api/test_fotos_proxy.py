"""El proxy /fotos/{nombre} (feature 49): caché de edge sin tocar el bucket.

Lo que se fija aquí es el contrato con el CDN de Vercel: la respuesta DEBE traer
`s-maxage` (sin él, el edge no cachea y cada vista vuelve a gastar egress del
bucket — que es exactamente el problema que originó la feature) y el contenido
debe salir intacto, con su content-type.
"""

from reencuentro_api.routers import fotos


def _configurar_supabase(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://abc123.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "service-key-de-prueba")


class _Respuesta:
    def __init__(self, status_code=200, content=b"", headers=None):
        self.status_code = status_code
        self.content = content
        self.headers = headers or {}


def test_sirve_la_foto_del_bucket_con_cache_de_edge(client, monkeypatch):
    _configurar_supabase(monkeypatch)
    pedidas = []

    def fake_get(url, timeout=None):
        pedidas.append(url)
        return _Respuesta(200, b"bytes-de-la-foto", {"content-type": "image/webp"})

    monkeypatch.setattr(fotos.http, "get", fake_get)

    r = client.get("/fotos/abc123.webp")

    assert r.status_code == 200
    assert r.content == b"bytes-de-la-foto"
    assert r.headers["content-type"] == "image/webp"
    # El contrato con el edge: sin s-maxage no hay caché y el proxy no sirve de nada.
    assert "s-maxage=31536000" in r.headers["cache-control"]
    assert "immutable" in r.headers["cache-control"]
    # Pidió exactamente ese objeto del bucket público.
    assert pedidas == ["https://abc123.supabase.co/storage/v1/object/public/fotos/abc123.webp"]


def test_head_responde_los_mismos_headers_sin_body(client, monkeypatch):
    """Algunos rastreadores hacen HEAD antes de descargar la og:image; sin la
    ruta registrada FastAPI respondía 405 (curl -I lo delató en prod)."""
    _configurar_supabase(monkeypatch)
    monkeypatch.setattr(
        fotos.http,
        "get",
        lambda url, timeout=None: _Respuesta(200, b"bytes", {"content-type": "image/jpeg"}),
    )

    r = client.head("/fotos/abc123.jpg")

    assert r.status_code == 200
    assert "s-maxage=31536000" in r.headers["cache-control"]
    assert r.content == b""


def test_foto_inexistente_en_el_bucket_es_404(client, monkeypatch):
    _configurar_supabase(monkeypatch)
    monkeypatch.setattr(fotos.http, "get", lambda url, timeout=None: _Respuesta(400))

    r = client.get("/fotos/no-existe.jpg")

    assert r.status_code == 404


def test_sin_supabase_configurado_es_404(client, monkeypatch):
    """En dev/tests las fotos viven bajo /media/… y mediaUrl nunca produce
    /fotos/…: si algo llega aquí sin bucket configurado, 404 honesto."""
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_KEY", raising=False)

    r = client.get("/fotos/x.jpg")

    assert r.status_code == 404
