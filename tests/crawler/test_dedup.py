from pathlib import Path

from crawler.dedup import (
    clave_de,
    marcar_publicado,
    obtener,
    registrar_extraccion,
    registrar_invalido,
)


def test_clave_prefiere_url_y_cae_en_hash(tmp_path):
    imagen = tmp_path / "captura.png"
    imagen.write_bytes(b"pixeles")

    assert clave_de("https://instagram.com/p/ABC/", imagen) == "https://instagram.com/p/ABC/"
    clave_hash = clave_de(None, imagen)
    assert clave_hash.startswith("sha256:")
    # Determinista: el mismo archivo produce la misma clave.
    assert clave_de("  ", imagen) == clave_hash


def test_extraccion_se_registra_antes_de_publicar(tmp_path):
    """El ciclo retry-safe: extraído-sin-publicar conserva los payloads para
    reutilizarlos, y publicar deja los ids en la misma clave."""
    registro = tmp_path / "procesados.jsonl"
    payloads = [{"descripcion": "perrita negra"}, {"descripcion": "perro dorado"}]

    assert obtener("clave-1", registro) is None

    registrar_extraccion("clave-1", payloads, registro)
    entrada = obtener("clave-1", registro)
    assert entrada is not None
    assert entrada["payloads"] == payloads
    assert entrada["reporte_ids"] is None  # extraído pero aún no publicado

    marcar_publicado("clave-1", [10, 11], registro)
    entrada = obtener("clave-1", registro)
    assert entrada is not None
    assert entrada["reporte_ids"] == [10, 11]
    assert entrada["payloads"] == payloads  # se conservan para auditoría
    assert obtener("clave-2", registro) is None


def test_extraccion_invalida_queda_registrada_con_motivo(tmp_path):
    """No se re-paga el LLM por una extracción que el contrato rechazó."""
    registro = tmp_path / "procesados.jsonl"
    registrar_invalido("clave-x", "sin camino de contacto", registro)
    entrada = obtener("clave-x", registro)
    assert entrada is not None
    assert entrada["motivo"] == "sin camino de contacto"
    assert entrada["reporte_ids"] is None


def test_linea_corrupta_no_tumba_el_registro(tmp_path):
    """Un crash a mitad de escritura deja una línea truncada: se ignora, no
    brickea todas las corridas futuras."""
    registro = tmp_path / "procesados.jsonl"
    registrar_extraccion("clave-1", [{"descripcion": "x"}], registro)
    with registro.open("a") as f:
        f.write('{"clave": "https://insta')  # línea truncada, sin salto final

    assert obtener("clave-1", registro) is not None
    assert obtener("clave-rota", registro) is None


def test_registro_por_defecto_esta_gitignored():
    """El estado local nunca debe viajar en un PR."""
    from crawler.dedup import RUTA_REGISTRO

    repo_root = Path(__file__).resolve().parents[2]
    gitignore = (repo_root / ".gitignore").read_text()
    assert "crawler/estado/" in gitignore
    assert RUTA_REGISTRO.parent.name == "estado"
