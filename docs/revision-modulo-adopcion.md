# Cómo revisar el módulo de adopción (AD-01 + AD-02) antes de aceptar el PR

> Para Javier (dueño del repo y único con acceso a Supabase/Vercel).
> Este documento existe porque el PR **no se puede mergear sin una acción manual tuya**, y porque hay dos hallazgos que conviene que veas con tus propios ojos.

---

## TL;DR — la única cosa que no puede salir mal

**Ejecuta `migrations/AD-01-pets.sql` en Supabase ANTES de mergear.** En producción está `SKIP_DB_CREATE_ALL=1`: la tabla `pets` no se crea sola, y el push a `main` despliega al instante. Si mergeas primero, `/api/pets` responde error en producción hasta que migres.

El resto de esta guía es para que puedas confiar en el diff sin leerlo entero.

---

## 1. Verificación automática (5 minutos, sin tocar nada)

```bash
git fetch origin && git checkout develop && git pull
bash init.sh
```

Debe imprimir **`Todo en verde.`** y salir 0, con **292 tests de API + 285 de web**. La línea base antes de este trabajo era 174 + 148.

Si quieres además el build de producción:

```bash
cd src/web && npm run build     # tsc -b + vite build, debe salir 0
```

### Si prefieres delegarlo

Pega esto en Claude Code, dentro del repo y en la rama `develop`:

```
Revisa el módulo de adopción (features AD-01 y AD-02) que está en develop sin mergear,
como revisor independiente y escéptico. No des nada por hecho: corre `bash init.sh` tú
mismo y cita la salida real.

Verifica:
1. Los 4 acceptance de AD-01 y los 4 de AD-02 en feature_list.json: para cada uno,
   encuéntrame el test concreto (archivo y nombre) que lo ejercita, y confírmame que pasa.
2. Que `migrations/AD-01-pets.sql` es puramente aditivo: sin DROP, sin TRUNCATE, sin ALTER
   sobre users/reports/organizaciones. Y que `tests/api/test_migracion_pets.py` compara de
   verdad ese SQL contra Pet.__table__ (rompe el .sql a propósito y confirma que el test
   se pone rojo; restaura el archivo después).
3. Que ninguna pantalla que escribe usa `getActiveUserId()` sin `hasActiveUser()`:
   `grep -rn "getActiveUserId" src/web/src`. El commit cc4de85 arregló 6 sitios; dime si
   queda alguno.
4. Que no entró ninguna dependencia nueva (diff de package.json, package-lock.json,
   requirements.txt, pyproject.toml) ni nada de WebSockets.
5. Que la rama origin/adopta-v1 y el tag adopta-v1.0.0 siguen en cde337f, intactos.

Dime qué te parece dudoso, no solo qué está bien. Si algo no te cuadra, prefiero saberlo.
```

---

## 2. Pruébalo en local (10 minutos)

```bash
bash dev.sh     # API :8000 + web :5173
```

Los datos son del seed (3 organizaciones, 8 mascotas). El usuario 1 es Ana Martínez y **es el autor de la organización 1**, lo cual importa para la prueba de seguridad del punto 3.

### El recorrido que vale la pena

| # | Qué | Dónde | Qué deberías ver |
|---|---|---|---|
| 1 | **Catálogo** | `/adoptar` | 7 mascotas con foto, edad legible ("4 meses", no "0 años"), tags y zona |
| 2 | **Filtro multivalor** | chips Perro **y** Gato | 7 resultados (5 perros + 2 gatos). Si solo salieran 2, el filtro estaría roto |
| 3 | **Ficha** | click en cualquiera | galería, historia, convivencia, checklist de salud con ✓/—, quién la publica, botón de WhatsApp |
| 4 | **Gate de cuenta** | `/adoptar/publicar` en incógnito | redirige a `/registro?volver=%2Fadoptar%2Fpublicar` |
| 5 | **Publicar como rescatista** | regístrate → `/adoptar/publicar` | la mascota aparece en `/adoptar` y la ficha te muestra a ti como contacto |
| 6 | **Panel de organización** | `/organizacion/1?tab=adopcion` como Ana | pestaña "En adopción", publicar, y cambiar estado a "adoptada" |
| 7 | **El puente** ⭐ | `/reporte/11` como Ana | "¿Nadie la reclamó? Puedes darla en adopción…" → el form llega **pre-llenado con las fotos del reporte** |
| 8 | **La guarda del puente** | intenta borrar el reporte 11 ya publicado | **409** en español, y el reporte conserva sus fotos |

El paso 7 es el corazón del módulo: alguien rescató un animal, nadie lo reclamó, y lo da en adopción sin volver a escribir nada. Fíjate en el copy — dice *"Seguimos buscando a la suya: el reporte no se borra"*.

---

## 3. Dos hallazgos que quiero que veas, no que te cuenten

### 3.1 Un bug de autoría que llevaba abierto desde la feature 09

Sin cuenta, `getActiveUserId()` devuelve `DEMO_USER_ID = 1`. Varias pantallas comparaban contra eso **sin comprobar `hasActiveUser()`**, así que **cualquier visitante anónimo era tratado como el usuario 1** y veía sus controles de escritura.

Reproducido en navegador antes de arreglarlo: con `localStorage` vacío, en `/organizacion/1` salían **"Editar información"** y **"Eliminar este lugar"**.

Para verlo tú mismo, en el commit anterior al fix:

```bash
git stash list && git checkout d407155~2   # commit previo a cc4de85
bash dev.sh
# navegador en incógnito → http://localhost:5173/organizacion/1
git checkout develop
```

**Alcance real en producción: probablemente nulo.** Las 27 organizaciones importadas pertenecen al usuario sistema **id 70**, no al 1. El riesgo existía solo para recursos cuyo autor fuera el usuario 1.

**Por qué sobrevivió 30 features y tres revisores**: había **14 tests verdes protegiéndolo**. Usaban fixtures con `user_id: 1` y nunca llamaban a `setActiveUserId`, así que aserraban literalmente *"sin cuenta se ven los controles del usuario 1"*. El fix (`cc4de85`) tuvo que tocarlos para declarar explícitamente la cuenta que asumían por accidente: **7 líneas eliminadas en total**, todas imports ampliados o comentarios que enunciaban la premisa del bug. **Cero aserciones borradas o debilitadas** — puedes auditarlo con:

```bash
git show cc4de85 --stat
git diff cc4de85~1 cc4de85 -- src/web/src/screens/*.test.tsx | grep '^-' | grep -v '^---'
```

### 3.2 La deuda de fondo, que NO está arreglada

El fix tapa la interfaz. **El backend sigue aceptando la escritura cuando el `user_id` que manda el cliente coincide con el del autor**, y nada impide llamar al endpoint a mano desde la consola. Con el gate bien puesto no queda hueco práctico por la UI, pero **la autoría real sigue siendo una promesa del frontend en toda la app**.

Es consecuencia directa del "registro mínimo sin contraseña" (ADR 0005) — una decisión de producto consciente, no un descuido. Merece **su propio ADR** (token firmado, magic link, o aceptar el riesgo por escrito), no un parche dentro de una feature de adopción. Queda anotado en `progress/current.md`.

---

## 4. Lo que tienes que hacer tú para poder mergear

### Paso 1 — Ejecutar la migración

En tu terminal, para copiar el SQL:

```bash
pbcopy < migrations/AD-01-pets.sql
```

Supabase → proyecto de producción → **SQL Editor** → **New query** → pegar → **Run**.
*(Si el proyecto aparece pausado, dale a "Restore"/"Resume" primero: el plan gratuito lo pausa tras una semana sin actividad.)*

Respuesta esperada: `Success. No rows returned`.

### Paso 2 — Verificar que el CHECK llegó

```sql
select conname from pg_constraint where conrelid = 'public.pets'::regclass;
```

Debe listar **`ck_pets_publicador_exclusivo`**. Es lo que garantiza que una mascota cuelgue de una organización **o** de un rescatista, nunca de ambos ni de ninguno. Si falta, dev y producción divergen en silencio.

### Paso 3 — Mergear y comprobar el deploy

Ya con la tabla creada, acepta el PR. Después:

```bash
curl -s https://petfinder-col.com/health                 # {"status":"ok"}
curl -s https://petfinder-col.com/api/pets | head        # JSON, no error
curl -s https://petfinder-col.com/api/pets/adopciones    # {"total":0,"recientes":[]}
```

⚠️ **Verifica que el deployment existió de verdad.** El auto-deploy de `main` ya falló en silencio una vez (documentado en `memory/memory.md`, 2026-08-12): los pushes no creaban deployments y se resolvió reconectando la GitHub App en Settings → Git.

---

## 5. Sobre el SQL, si te da respeto darle a Run

`migrations/AD-01-pets.sql` **crea una tabla nueva y nada más**:

- Cero `DROP`, cero `DELETE`, cero `ALTER` sobre `users`, `reports` u `organizaciones` — solo las referencia por clave foránea.
- **No puede modificar ni borrar una fila existente.** Tus 204 reportes importados no se tocan.
- Lleva `create table if not exists`, así que es idempotente: re-ejecutarlo no rompe nada.
- Termina con `enable row level security`, como el resto de las tablas.
- El peor fallo realista es que la sentencia dé error (permisos) y no quede nada creado.

Y no es una transcripción a mano del modelo: **`tests/api/test_migracion_pets.py` compara ese `.sql` contra `Pet.__table__` columna a columna**, verifica que el `CHECK` y el `RLS` viajan, y prohíbe `drop`/`truncate`. Se comprobó que el test falla de verdad rompiendo el SQL de cuatro formas distintas.

---

## 6. Qué NO entra en este PR

- **AD-03 a AD-09** del backlog (`feature_list_adopcion.json`): deck de swipe, perfil de hogar, solicitudes, favoritos, integración transversal. Siguen en `todo`.
- **Enlace en la nav y en la landing**: `/adoptar` existe pero no está enlazado desde la navegación principal. Es deliberado — va en AD-08, para decidir con calma cuánto protagonismo quitarle a los dos caminos de emergencia. Hoy se llega por URL directa o desde el puente de un reporte.
- **Nada de chat**: el chat por WebSockets de la era Adopta es incompatible con el serverless de Vercel. La decisión (WhatsApp directo) se documentará en el ADR 0012 durante AD-06.
- **Apadrinamiento**: recortado por decisión de producto. `Organizacion.como_donar` ya cubre la intención.

---

## 7. Deuda conocida que queda anotada

| Qué | Dónde | Gravedad |
|---|---|---|
| La UI es la única barrera de autoría (ADR 0005) | `progress/current.md` | Merece ADR propio |
| 6 pantallas de listado sin `.catch`: un fallo de red las deja mudas | `progress/current.md` | Baja, cosmética |
| Bundle > 500 kB pre-gzip | aviso de Vite | Preexistente desde la feature 44 |
| Prettier de `node_modules` ≠ el de `.pre-commit-config.yaml` | mete ruido en diffs ajenos | Un `chore:` de una línea |
| Las mascotas nacen sin `lat`/`lng` (el form no pide pin) | por diseño | El filtro por distancia nacerá muerto en AD-03 |

---

**Si algo de esto no te cuadra, dilo antes de mergear.** El PR no tiene prisa; la base de datos de producción sí tiene 204 reportes reales.
