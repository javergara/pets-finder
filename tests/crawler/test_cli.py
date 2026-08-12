from crawler.cli import listar_imagenes


def test_carpeta_lista_solo_imagenes_en_orden(tmp_path):
    (tmp_path / "b.png").write_bytes(b"b")
    (tmp_path / "a.jpg").write_bytes(b"a")
    (tmp_path / "notas.txt").write_text("no soy imagen")
    (tmp_path / "c.JPEG").write_bytes(b"c")

    assert [p.name for p in listar_imagenes(tmp_path)] == ["a.jpg", "b.png", "c.JPEG"]


def test_archivo_unico_se_devuelve_tal_cual(tmp_path):
    imagen = tmp_path / "captura.png"
    imagen.write_bytes(b"pixeles")
    assert listar_imagenes(imagen) == [imagen]
