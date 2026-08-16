# 0012 — Coincidencias asistidas por parecido visual de las fotos

## Estado

Aceptado (2026-08-13). **Reemplaza la regla "coincidencias sin AI"** del ADR
0005 §4 y de `docs/product-research.md` §2 — igual que el ADR 0008 reemplazó la
parte de mapa del 0005 §5. La heurística explicable **no se retira**: sigue
siendo la base, y el parecido visual solo se suma encima.

## Contexto

Las coincidencias eran tipo opuesto + misma especie + **misma zona**, ordenadas
por `distancia_km + 0.5 × |Δdías|`. Dos límites reales:

1. **No miran la foto**, que es el identificador principal de una mascota para
   un humano (`product-research.md` §4).
2. **La zona es un filtro duro**: la mascota que apareció en la ciudad vecina no
   aparece nunca, y es un caso frecuente y doloroso.

Con 260 reportes reales en producción (251 con foto) el problema es agudo, y
medirlo contra una réplica de los datos reales dio el argumento definitivo:

- **234 de los 260 reportes comparten exactamente el mismo pin.** El 78% viene
  del crawler (ADR 0010 §8: sin coordenadas en el post, el pin cae en el centro
  de la zona), así que la distancia entre ellos es 0.00 km.
- Resultado: de los 14.230 pares candidatos activos, **el 89% empata** con otro
  bajo la heurística vieja. El peor caso es un reporte con **84 de sus 86
  candidatos en el mismo puntaje exacto** — o sea, orden arbitrario.

La heurística no está "un poco corta": para nueve de cada diez pares **no puede
ordenar nada**. La foto es la única señal que queda.

La feature `24-ai-matching-fotos` exigía explícitamente ADR con
proveedor/costo/privacidad y **mejora demostrable sobre casos de prueba
definidos antes de implementar**.

## Opciones evaluadas

| Opción | Veredicto |
|---|---|
| **DINOv2-small afinado para animales** (`AvitoTech/DINO-v2-small-for-animal-identification`) | **Elegida.** Apache 2.0, 384 dims, 22.1M params, entrenado con 1.9M fotos de 695k animales únicos. ROC AUC 0.985 reportado |
| MegaDescriptor (BVRA) | Descartada: **cc-by-nc-4.0** (no comercial) y 1.9 GB la variante grande |
| CLIP genérico / MobileCLIP | Descartada como principal: buena para "perro dorado con collar rojo", débil para **identidad individual** |
| API de inferencia (Hugging Face) | Descartada: free tier ~100K créditos/mes, insuficiente; además mandaría las fotos de los usuarios a un tercero |
| Embedding en el navegador (transformers.js) | Descartada: obliga a un modelo genérico y a ~43 MB de descarga en datos móviles, en plena emergencia |
| Vector DB (Qdrant/Chroma) o pgvector | Descartadas **por ahora**: ver §Almacenamiento |

## Decisión

### 1. Pipeline de dos etapas, fuera de la API

`embeddings/` es un proceso independiente (mismo patrón que `crawler/`, ADR
0010): la API corre serverless en Vercel con CPython 3.14 y torch no tiene
wheels cp314 ni cabe en el bundle. Corre a mano hoy, por cron después.

1. **Recorte al animal** — `hustvl/yolos-tiny` (26 MB, Apache 2.0, clases COCO).
2. **Embedding** — el modelo de Avito, token CLS normalizado, 384 dims.

**El recorte no es un lujo, es el hallazgo central de la calibración.** En
producción abundan los pósters diseñados ("¡SE PERDIÓ!" con banda roja y
tipografía) y los pantallazos de story con chrome del teléfono: sin recortar,
el vector describe la maqueta y no la mascota.

El efecto del recorte, medido sobre las fotos reales:

| | sin recorte | con recorte |
|---|---|---|
| Base (animales distintos, misma especie) | media 0.258 · p99 0.790 | media 0.197 · p99 0.770 |
| Falso positivo (perra dorada ↔ perro crema) | 0.885 | **0.461** |
| Verdadero positivo (la misma perra, archivos distintos) | 1.000 | **0.997** |

Se descartó la hipótesis de que el modelo puntuara "pantallazo-idad":
crawl-crawl 0.253 ≈ manual-manual 0.266.

**Calibración vigente** — `embeddings/ejemplos/calibracion.json`, 251 fotos de
producción, regenerable con `python -m embeddings.calibrar`:

| | n | media | p95 | p99 |
|---|---|---|---|---|
| Base negativos (gato) | 5.453 | 0.184 | 0.569 | **0.776** |
| Base negativos (perro) | 9.577 | 0.224 | 0.584 | **0.770** |
| Control positivo (misma foto transformada) | 100 | 0.963 | — | p10 **0.937** |

De ahí salen los umbrales: **0.776 < 0.80 (medio) < 0.90 (alto) < 0.937**. La
regla para el futuro es esa — por encima del p99 de la base y por debajo del p10
del control positivo. Cobertura del detector: 244/251 fotos.

Limitación conocida y aceptada: el `min` del control positivo es 0.05. En un
puñado de casos el detector elige otro sujeto en la imagen transformada (fotos
con varios animales, o recortes que dejan al animal fuera). Falla hacia el lado
seguro — es una coincidencia que no se muestra, no una falsa.

### 2. El worker escribe directo a la base, no por la API

No hay auth real (ADR 0005 §4). Un endpoint abierto de escritura de embeddings
dejaría que cualquiera envenene el matching. El worker es herramienta del dueño,
como `scripts/seed.py`, y **nunca borra ni recrea nada**: solo rellena dos
columnas.

### 3. Almacenamiento: columna JSON, no vector DB

`Report.embedding` (JSON, portable — nativo en Postgres, TEXT en SQLite, mismo
patrón que `crawl_metadata`) y `Report.embedding_modelo`.

El tope real del free tier de Supabase Storage (1 GB) son ~300-500 fotos: un
escaneo completo de 384 dims en Python puro sobre decenas de candidatos son
microsegundos. Traer pgvector obligaría a ramificar por dialecto y mantener un
camino distinto en dev/tests, a cambio de nada medible. **Umbral de revisión:
~10k reportes** — ahí pgvector (gratis en Supabase) es el paso natural y solo
cambia el tipo de la columna.

`embedding_modelo` versiona el pipeline **completo**: vectores de pipelines
distintos no son comparables y la comparación exige que ambos lados coincidan.
Durante un backfill los reportes sin recalcular simplemente no se comparan, en
vez de mezclar dos espacios vectoriales en silencio.

### 4. El parecido solo suma, nunca resta

```
cercania = 1 / (1 + distancia_km + PESO_DIAS × |Δdías|)          → (0, 1]
bono     = max(0, similitud − UMBRAL_MEDIO) / (1 − UMBRAL_MEDIO)
afinidad = cercania + BONO_VISUAL × bono                          (BONO_VISUAL = 2.0)
```

El modelo tiene ~72% de top-1: **un parecido bajo no es evidencia de que sean
mascotas distintas, solo ausencia de evidencia**. Si restara, publicar una foto
mala hundiría un reporte que hoy sale bien por cercanía.

De ahí dos propiedades que los tests fijan:

- **Sin embeddings el orden es exactamente el de antes de este ADR**, porque
  `cercania` es una transformación monótona decreciente del puntaje viejo. La
  degradación elegante que exige el acceptance es aritmética, no un `if`.
- Un parecido "alto" (≥0.90) gana contra la cercanía sola — el caso de la
  ciudad vecina.

La **zona deja de ser filtro duro**: un candidato de otra zona entra solo si su
parecido llega a `UMBRAL_MEDIO`.

### 5. Bandas, nunca porcentajes

`alto ≥ 0.90`, `medio ≥ 0.80`, y por debajo no se dice nada. Umbrales
calibrados contra los datos reales (base al p99 = 0.770); marcan 6 de 1608
pares tipo-opuesto.

Un "87%" se leería como probabilidad y **una certeza falsa hace que alguien
entregue una mascota a quien no es**. Es el mismo criterio de tono del ADR 0005
y del propio código, que ya decía que su puntaje "no es una probabilidad".

### 6. Guarda contra "la misma imagen", que además es una defensa antifraude

Si dos reportes son en realidad la misma imagen, su similitud **no cuenta como
evidencia**. Se detecta por vector (`similitud >= 0.9999`), no por URL, y cubre
dos casos:

- El crawler saca N mascotas de un mismo pantallazo (ADR 0010 §6): ahí un coseno
  de 1.0 dice "es la misma imagen", no "es la misma mascota". En la calibración,
  los 6 pares con coseno exacto 1.000 eran todos de ese origen.
- **Fraude.** Sin auth real, cualquiera puede bajar la foto pública de un reporte
  perdido, volver a subirla —lo que le da una URL nueva, así que comparar URLs no
  sirve— y publicar un "encontrado" que quedaría clavado en el primer puesto con
  parecido máximo desde cualquier punto del país. Es el "tengo a tu perro,
  mándame un giro" y esta feature lo habilitaría sin la guarda.

Techo conocido y aceptado: quien recorte o recomprima la foto ajena baja del
umbral y vuelve a pasar. Contra eso la respuesta es **moderación (feature 23)**,
no un umbral más agresivo que empezaría a descartar reencuentros reales — el
verdadero positivo medido fue 0.997.

Se evaluó y **se descartó** limitar además el salto entre zonas por distancia:
la zona la elige quien publica, así que un estafador simplemente declara la zona
de la víctima. Sería fricción para casos legítimos (una mascota transportada
lejos) sin costo real para el atacante.

### 7. Impacto medido sobre datos reales

Verificado contra una réplica local de los 260 reportes de producción (prod
nunca se tocó: los datos salieron del API público):

- **43 reportes cambian su candidato #1.**
- **40 pares marcados de 14.230** (0.28%): 4 en "alto", 36 en "medio". Selectivo,
  no ruido.
- **0 candidatos nuevos de otra zona**, porque hoy toda la producción está en
  Cali. La apertura de zona es capacidad instalada, no beneficio actual — y hay
  que revisar el umbral cuando entren más ciudades, porque ~1% de los pares
  cruzados superaría 0.80 por azar.
- **0 regresiones**: los 16 reportes sin vector conservan exactamente el orden
  histórico.
- Latencia del endpoint tras bajar los filtros a SQL: mediana **16 ms** con 260
  reportes (era 30 ms con 150 trayendo la tabla entera).

## Consecuencias

- **Costo: $0 real.** Ambos modelos son Apache 2.0 y corren en CPU en la máquina
  del dueño (o en un runner de GitHub Actions: el repo es público). Sin API de
  terceros, sin tarjetas — coherente con los ADRs 0007 y 0008.
- **Privacidad: las fotos no salen a ningún tercero.** Es la ventaja decisiva de
  la inferencia propia sobre una API de embeddings: las fotos de mascotas de
  gente real se procesan localmente contra pesos descargados una vez. Los
  vectores no se exponen en la API (`ReportOut` enumera sus campos).
- **La API no gana ni una dependencia**: el coseno es Python puro.
- **Migración de producción ANTES de mergear a `main`** (regla dura del repo):

  ```sql
  ALTER TABLE reports ADD COLUMN embedding JSON;
  ALTER TABLE reports ADD COLUMN embedding_modelo VARCHAR(80);
  ```

  Aditiva y retrocompatible: los reportes existentes quedan en NULL y sus
  coincidencias siguen saliendo por cercanía. ⚠️ Con `SKIP_DB_CREATE_ALL=1` en
  producción las columnas **no se crean solas** en el deploy.
- **Los umbrales son calibración, no verdad revelada**: salieron de 140 fotos de
  un momento concreto. Revisarlos cuando el volumen crezca, y volver a correr la
  calibración si se cambia cualquiera de los dos modelos.
- **Sigue sin haber moderación**: un parecido alto es una pista para que dos
  personas se contacten por WhatsApp, no una verificación de propiedad. La
  feature 23 del backlog es el lugar para atacar el abuso.
