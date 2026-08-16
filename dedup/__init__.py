"""Dedup de reportes: sistema propio, aparte del crawler (ADR 0010).

Los duplicados no son un problema del crawler sino de la plataforma: la gente
publica dos veces, el mismo caso circula por varias páginas, y cada pipeline
de crawling puede re-importarlo. Este paquete es la fuente única de la lógica
de detección:

- `deteccion.py` — núcleo puro: candidatos por teléfono (identifica a la
  PERSONA, no al caso) discriminados por tipo/especie/nombre.
- `cli.py` — audita una instancia completa (`python -m dedup.cli`): agrupa en
  clusters, sugiere curación conservadora y emite el informe.
- El crawler importa de aquí su chequeo de publish; cualquier pipeline nueva
  puede hacer lo mismo.
"""
