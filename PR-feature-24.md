# feat(coincidencias): parecido visual de las fotos (feature 24, ADR 0012)

> Reemplaza la descripción anterior del PR #5. Esta rama ya está **mergeada con `main`** (20+ commits) y no tiene conflictos.

## Por qué

Las coincidencias se ordenaban por `distancia_km + 0.5·|Δdías|` y la zona era filtro duro. Medido contra una réplica de los 260 reportes reales de producción:

- **234 de 260 reportes comparten exactamente el mismo pin** — el 78% viene del crawler, que ubica el reporte en el centro de la zona (ADR 0010 §8), así que la distancia entre ellos es 0.00 km.
- **El 89% de los 14.230 pares candidatos empata.** El peor caso es un reporte con **84 de sus 86 candidatos en el mismo puntaje exacto**, es decir orden arbitrario.

La heurística no estaba "un poco corta": para nueve de cada diez pares no podía ordenar nada. La foto era la única señal que quedaba.

## Qué hace

```
afinidad = cercania + BONO_VISUAL × bono
cercania = 1 / (1 + distancia_km + 0.5·|Δdías|)
bono     = max(0, similitud − 0.80) / 0.20
```

**El parecido solo suma, nunca resta.** El modelo tiene ~72% de top-1, así que un parecido bajo es *ausencia* de evidencia, no evidencia en contra; si restara, publicar una foto mala hundiría un reporte que hoy sale bien por cercanía.

De ahí sale la propiedad central: **sin vectores el orden es exactamente el anterior**, porque `cercania` es una transformación monótona del puntaje viejo. La degradación elegante es aritmética, no un `if` de emergencia. Verificado con un fuzz de 2000 escenarios aleatorios contra la implementación previa: *0 diferencias de orden, de conjunto y de distancias*.

La zona deja de ser filtro duro: un candidato de otra zona entra solo si su parecido llega al umbral.

## Cómo convive con lo que ya está en `main`

Esta rama se abrió antes de las features 35-46. Al mergear, **la 37 y la 24 resultaron complementarias** y se compusieron:

- **Feature 37 (razones visibles)** explica *por qué* coincide: "mismo perro", "a 0.6 km", "mismo color".
- **Feature 24 (esta)** añade el parecido de la foto, que es **la única razón capaz de traer un candidato de otra zona**.

Se muestran juntas, con el chip de la foto primero y con más peso visual.

**Un bug nació de juntarlas y está corregido**: `razones_coincidencia` emitía `"misma zona"` incondicionalmente — cierto mientras la zona era filtro duro, **falso** desde esta feature. Ahora distingue `misma zona (X)` de `otra zona (Y)`. Un chip de confianza que afirma algo falso es peor que no tenerlo.

Otras dos decisiones del merge:

- **`parecido` → `parecido_foto`.** La feature 38 ya usa `parecido` como entero 0-100 en la búsqueda por descripción. Dos campos con el mismo nombre y distinto significado son una trampa. ⚠️ **Cambio de contrato**: quien consuma `CoincidenciaOut` verá `parecido_foto`.
- **ADR 0011 → 0012.** El 0011 quedó tomado por las alertas por correo (feature 39). Se renumeró el nuestro tocando solo nuestras referencias.
- **`services/radar.py` (feature 43)** consumía `ordenar_coincidencias`, cuya firma pasó de 2 a 3 valores. Ajustado sin alterar su semántica: su puerta de calidad sigue siendo distancia+días.

## Arquitectura

El pipeline corre **fuera de la API** (`embeddings/`, mismo patrón que `crawler/`): torch no tiene wheels para el runtime serverless de Vercel ni cabría en su bundle. **La API no gana ni una dependencia** — el coseno de 384 dims es Python puro.

Dos etapas, y la primera no es un lujo: sin recortar al animal el vector describe el póster de "¡SE PERDIÓ!" y el chrome de los pantallazos de story, que es de lo que está llena la producción real.

| | sin recorte | con recorte |
|---|---|---|
| Falso positivo (perra dorada ↔ perro crema) | 0.885 | **0.461** |
| Verdadero positivo (la misma perra, 2 reportes) | 0.9999 | **0.997** |
| Base p99 (animales distintos, misma especie) | 0.790 | **0.770** |

Modelos Apache 2.0 corriendo en CPU local: **costo $0** y las fotos de gente real **no salen a ningún tercero** — la ventaja decisiva sobre una API de embeddings.

## Evidencia reproducible

`embeddings/ejemplos/calibracion.json` (251 fotos de producción) está commiteado y **atado por tests**: si alguien mueve un umbral, cambia el pipeline sin recalibrar, o el recorte deja de arreglar el falso positivo, la suite truena. Separación verificada:

```
base p99 0.776  <  medio 0.80  <  alto 0.90  <  p10 control positivo 0.937
```

Impacto medido sobre la réplica: **43 reportes cambian su candidato #1**, y **40 pares marcados de 14.230** (0.28% — selectivo, no ruido).

## Seguridad

Sin auth real (ADR 0005 §4), bastaba **bajar la foto pública de un reporte perdido y volver a subirla** —lo que le da una URL nueva— para clavar un "encontrado" falso en el primer puesto desde cualquier punto del país: el "tengo a tu perro, mándame un giro". La guarda compara **vectores**, no URLs.

Techo conocido: quien recorte o recomprima la foto ajena vuelve a pasar. La respuesta a eso es moderación (feature 23), no un umbral más agresivo que empezaría a descartar reencuentros reales.

También cerrados en el worker: SSRF (`foto_url` la fija cualquiera y el worker corre en la máquina del dueño), path traversal con rutas absolutas, bomba de descompresión, y `foto_url` sin `max_length` que producía un 500 en Postgres.

## ⚠️ ANTES DE MERGEAR — migración obligatoria

```sql
ALTER TABLE reports ADD COLUMN embedding JSON;
ALTER TABLE reports ADD COLUMN embedding_modelo VARCHAR(80);
```

**Sin esto se cae la app entera, no solo las coincidencias**: el modelo declara las columnas, así que toda consulta de reportes las pide. Comprobado contra una copia sin ellas — `/api/reports`, `/api/reports/{id}` y `/coincidencias` responden **500**.

`create_all()` **no** las crea (solo crea tablas que faltan, nunca añade columnas) — comprobado también, así que da igual el valor de `SKIP_DB_CREATE_ALL`.

El ALTER es aditivo, nullable, O(1) en Postgres 11+, sin downtime, y **se puede correr antes del deploy sin ningún riesgo**: el código viejo ignora las columnas. El orden inverso es el que rompe.

Después del deploy: backfill con `python -m embeddings.cli --escribir` (por lotes con `--limite`, porque hoy hace un solo commit al final). No es urgente: un reporte sin vector se comporta exactamente como antes — verificado.

## Rollback

Las columnas son aditivas y nullable: revertir el código deja la app funcionando igual que hoy, con las columnas ahí sin usar. **No hay pérdida de datos posible** — el worker solo rellena dos columnas, nunca borra ni modifica nada más.

## Qué más entra (y por qué está aquí)

- `defer(embedding)` en el listado: el vector es el 93% del peso de la fila y ese endpoint no lo usa. Sin esto, cada carga del mapa arrastraría ~1 MB de vectores desde Postgres hasta la función para tirarlos.
- Filtros de `/coincidencias` bajados a SQL: mediana **30 → 16 ms** con 110 reportes más.
- Accesibilidad: el chip "medio" tenía contraste 3.06:1 a 11px (falla AA).
- **`init.sh` corría `pytest tests/api`**, así que `tests/crawler` nunca se ejecutó ahí desde que existe.
- **`dev.sh` asumía `.venv/bin/activate`** y no arrancaba en Windows; ahora detecta el intérprete y respeta `DATABASE_URL`.

## Verificación

**228 tests de Python + 148 de web**, ruff y ruff-format limpios, build de producción limpio. La suite corre sin torch, sin red y sin descargar modelos (comprobado con un plugin que revienta ante cualquier import de torch o conexión no-loopback).

Auditoría del merge: se revisó **línea por línea cada eliminación respecto a `main`**. Apareció una pérdida real —la resolución del `CHANGELOG.md` se había comido las secciones `[2.4.0]` y `[2.3.0]` enteras— y se reconstruyó desde la versión de `main`. `changes.md` y `progress/current.md` conservan todos los encabezados de `main`.

`bash init.sh` no queda verde en Windows por tres motivos de entorno reproducibles sobre archivos que este PR no toca: `python3` es el alias del Microsoft Store, `black` se niega por el bug de CPython 3.12.5, e `init.sh:47` asume `.venv/bin/activate`.

## Cómo probarlo sin tocar producción

Se construye una réplica local desde el API público y se apunta `DATABASE_URL` ahí:

```bash
DATABASE_URL="sqlite:///<ruta>/replica-prod.db" bash dev.sh
```

En `/reporte/66` ("Sasha", gata calicó perdida en Cali) aparece **#78 de primera con "foto muy parecida"**, por encima de un candidato a 0.82 km mientras #78 está a 5.02 km.

## Decisiones abiertas

- **Los umbrales están calibrados sobre Cali.** Cuando entren más ciudades hay que recalibrar: ~1% de los pares cruzados supera 0.80 por azar.
- **`feature_list.json` trae la 24 en `done`.** Confirmar si se acepta o vuelve a `in_progress` hasta que esté desplegada y verificada en navegador.
- **Sasha (#66 ↔ #78) merece revisión humana ya**, independientemente de este PR: hay una familia y una gata reales detrás.
