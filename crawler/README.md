# Crawler de redes — Pet Finder Col

Proceso **independiente** de la app (ADR 0009), organizado en **pipelines de
crawling**: cada pipeline es una forma distinta de obtener publicaciones de
redes, y todas convergen en el mismo extractor (LlamaExtract) → publicador
(API pública con `fuente: "crawl"`). Este paquete implementa la primera:

- **Pipeline de pantallazos** (este CLI): recibe un pantallazo o una carpeta
  de pantallazos aportados a mano.
- Candidatas futuras (cada una con su decisión propia): bot que reciba
  forwards/DMs, APIs oficiales, scraping donde los ToS lo permitan.

No se despliega a Vercel; sus dependencias de terceros no tocan las de la
API. Corre desde el checkout del repo e importa el **contrato real** de la API
(`ReportIn` y las zonas): la validación es local, con los mismos mensajes del
backend, y no hay copias que se desincronicen.

## Instalación

```bash
.venv/bin/pip install -r crawler/requirements.txt
```

## Configuración (env vars)

| Variable | Qué es |
| --- | --- |
| `LLAMA_CLOUD_API_KEY` | Key de LlamaCloud para la extracción |
| `CRAWLER_USER_ID` | Id del usuario sistema dueño de los reportes crawleados |
| `PETFINDER_API_URL` | API destino. Default `http://127.0.0.1:8000` (local). Apuntar a producción SOLO con autorización explícita del dueño |

## Uso

```bash
# Un pantallazo (dry-run: extrae e imprime los payloads, no publica nada)
python -m crawler.cli captura.png --url-post https://www.instagram.com/p/ABC123/

# Una carpeta completa de pantallazos
python -m crawler.cli pantallazos/

# Publicar de verdad (contra PETFINDER_API_URL)
python -m crawler.cli pantallazos/ --publicar
```

- `--url-post` es la clave de dedup de un pantallazo único (con carpeta, cada
  imagen usa su sha256). Un post ya procesado no se re-extrae nunca (estado
  local en `crawler/estado/`, gitignored).
- La misma clave viaja como `idempotency_id` (`<clave>#<indice_mascota>`) en
  cada reporte: si una corrida muere a mitad de publicar, reintentar es
  seguro: el CLI reutiliza la extracción registrada (nunca vuelve al LLM, que
  no es determinista) y la API devuelve los reportes ya creados (200) en vez
  de duplicarlos.
- `--ciudad` es el fallback de zona cuando los posts no la dicen (quien
  recolecta pantallazos de un grupo local sabe de qué ciudad son).
- `--foto-url` adjunta una URL pública de foto al reporte (subirla antes con el
  endpoint de uploads o al bucket).
- Un pantallazo con N mascotas individualizables crea N reportes que comparten
  `url_post`, distinguidos por `crawl_metadata.indice_mascota`.

## Mapa del paquete

- `schema.py` — esquema de extracción (es también el prompt: las descripciones
  de los campos son las instrucciones del LLM).
- `extractor.py` — único módulo que habla con LlamaCloud (SDK v2 `llama-cloud`,
  extracción stateless: el esquema viaja en cada request; import perezoso).
- `publicador.py` — PostExtraido → `ReportIn` reales validados → POST a la API.
- `zonas.py` — ciudad extraída → zona + centro (zonas importadas de
  `services/ciudades.py`, fuente única).
- `dedup.py` — registro JSONL de posts procesados (extracción registrada ANTES
  de publicar; tolera líneas corruptas).
- `cli.py` — `python -m crawler.cli`, pantallazo único o carpeta.

Tests en `tests/crawler/` (corren con la suite normal, sin red y sin
`llama-cloud` instalado; el contrato se ejercita de verdad porque `convertir`
construye `ReportIn` reales).

## Ejemplo real

En [`ejemplos/dry-run-fotos-prod.json`](ejemplos/dry-run-fotos-prod.json) está
la salida completa de un dry-run sobre las 20 fotos reales de producción:
16 requests publicables (tipo y especie 16/16 contra las etiquetas humanas) y
5 excluidos con motivo. Detalle en [`ejemplos/README.md`](ejemplos/README.md).
