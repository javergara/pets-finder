# Worker de parecido visual — Pet Finder Col

Proceso **independiente** de la app (ADR 0012): calcula el vector visual de la
foto de cada reporte y lo guarda en `reports.embedding`, para que las
coincidencias se ordenen también por lo que se ve y no solo por cercanía.

No se despliega a Vercel: el runtime serverless no puede cargar torch. Corre
desde el checkout, hoy a mano y por cron más adelante — igual que `crawler/`.

## Instalación

```bash
.venv/Scripts/pip install -r embeddings/requirements.txt   # Windows
.venv/bin/pip install -r embeddings/requirements.txt       # Linux/macOS
```

Sus dependencias **jamás** van en `src/api/requirements.txt`: la API no las
necesita (el coseno es Python puro) y no caben en la función serverless.

## Configuración

| Variable | Qué es |
| --- | --- |
| `DATABASE_URL` | Base donde escribir. Sin ella, la SQLite local. Apuntar a producción **solo con autorización explícita del dueño** |
| `SUPABASE_URL` | Host del bucket. **Obligatoria para procesar fotos remotas**: el worker solo descarga URLs que empiecen por el prefijo público de ESE bucket |
| `SUPABASE_BUCKET` | Nombre del bucket (default `fotos`) |

`foto_url` la fija quien crea el reporte, y cualquiera puede crear uno (no hay
auth real, ADR 0005 §4). Como este worker corre en la máquina del dueño o en
CI, aceptar cualquier URL lo convertiría en un SSRF contra su red interna: por
eso solo descarga del bucket propio, sin seguir redirects y con tope de tamaño,
y por eso las rutas `/media/...` se resuelven y se comprueba que no escapen del
directorio. **No necesita la `service_role` key**: solo lee fotos públicas.

## Uso

```bash
python -m embeddings.cli                        # dry-run: dice qué haría
python -m embeddings.cli --escribir             # calcula y guarda
python -m embeddings.cli --reporte 66 --escribir
python -m embeddings.cli --rehacer --escribir   # recalcula todo (cambió el pipeline)
```

Por defecto solo procesa los reportes cuyo vector falta o quedó de un pipeline
viejo, así que re-correrlo es barato e idempotente. **Nunca borra ni recrea
nada** (a diferencia de `scripts/seed.py`): solo rellena dos columnas.

Salvedad conocida: las fotos que no producen vector (rotas, o sin animal
detectable) quedan en `NULL` y por tanto **se reintentan en cada corrida** —
descarga y dos modelos cada vez. Con un puñado de casos no molesta; si algún día
son muchos, la salida es un centinela que marque "intentado y falló" en vez de
dejar la columna vacía.

## Cómo funciona (y por qué el recorte importa)

1. **Recorte al animal** — `hustvl/yolos-tiny` (26 MB, Apache 2.0, clases COCO).
2. **Embedding** — `AvitoTech/DINO-v2-small-for-animal-identification`
   (Apache 2.0, 384 dims), DINOv2-small afinado para identidad individual de
   perros y gatos.

El paso 1 no es un lujo. En producción abundan los pósters diseñados
("¡SE PERDIÓ!" con banda roja y tipografía) y los pantallazos de story con
chrome del teléfono: sin recortar, el vector describe la maqueta. Medido sobre
las 140 fotos reales de producción:

| | sin recorte | con recorte |
| --- | --- | --- |
| Base (animales distintos, misma especie) | media 0.258 · p99 0.790 | media 0.197 · p99 0.770 |
| Falso positivo (perra dorada ↔ perro crema) | 0.885 | **0.461** |
| Verdadero positivo (la misma perra, 2 fotos) | 1.000 | **0.997** |

Cobertura del detector: 244/251 fotos de producción. Las que no traen animal
detectable (o tienen la foto rota — producción tiene al menos una truncada) se
quedan sin vector y sus coincidencias salen por cercanía, exactamente como antes.

Los números vigentes y reproducibles están en
[`ejemplos/calibracion.json`](ejemplos/README.md).

## Cuando cambie el modelo

`PIPELINE` en `modelo.py` versiona **las dos etapas juntas**. Vectores de
pipelines distintos no son comparables, y la comparación exige que ambos lados
coincidan — así que cambiar detector, embedder, umbral de detección o margen de
recorte obliga a subir la versión y correr `--rehacer --escribir`. Mientras el
backfill corre, los reportes sin recalcular simplemente no se comparan
visualmente: nunca hay una mezcla silenciosa de espacios vectoriales.

## Mapa del paquete

- `modelo.py` — único módulo que habla con torch/transformers (imports
  perezosos: el repo se puede importar sin estas dependencias).
- `cli.py` — `python -m embeddings.cli`, dry-run por defecto.

Tests en `tests/embeddings/` (corren con la suite normal, sin red, sin torch y
sin descargar modelos: el embebedor se inyecta falso).
