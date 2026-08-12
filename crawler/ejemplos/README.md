# Ejemplos — corridas reales de la pipeline

## `dry-run-fotos-prod.json`

Salida real de un dry-run (2026-08-12) sobre las 20 fotos de los reportes de
producción de petfinder-col.com — varias son pantallazos genuinos de redes que
la comunidad subió tras el sismo. Es exactamente lo que el crawler enviaría al
`POST /api/reports` (nada fue enviado):

- **16 requests publicables** — contra las etiquetas humanas de los reportes de
  prod: tipo 16/16, especie 16/16, nombres correctos donde eran legibles, y el
  caso multi-mascota real ("Iru y Nala") separado en 2 reportes con
  `idempotency_id` `#0`/`#1`.
- **5 no publicables con motivo explícito** — 3 fotos sin texto de publicación
  (detectadas por `es_publicacion`: sin texto, los datos serían adivinados) y
  2 sin ningún camino de contacto (rechazadas por el propio `ReportIn` de la
  API, con su mensaje).

Generado con `python -m crawler.cli <carpeta> --ciudad Cali` (tier
`agentic_plus` de LlamaExtract). Los teléfonos y cuentas que aparecen ya son
públicos: vienen de los pantallazos que los mismos usuarios publicaron en la
plataforma.
