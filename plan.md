# Plan: bootstrap de "Adopta" (harness engineering + MVP)

## Contexto

El usuario pegó un prompt maestro muy detallado para construir, desde cero, una app de adopción de mascotas tipo Tinder ("PawMatch") siguiendo un sistema de *harness engineering* (divulgación progresiva, una feature a la vez, estado en disco, patrón líder-implementador-revisor, verificación ejecutable, memoria de procesos).

Sin embargo el directorio de trabajo (`/Users/javergara/javergara/projects/peptinder`) **no está vacío ni es un repo git**: ya contiene trabajo de diseño real, generado con la herramienta DesignSync en una sesión previa, para un producto llamado **"Adopta"**:

- `design/HANDOFF.md` — spec de diseño completa: mercado Colombia (es-CO, COP), 11 pantallas, sistema de color/tipografía, modelo de datos, fórmula de afinidad, decisiones de producto ya tomadas y explícitamente distintas de un Tinder genérico (**el match no es mutuo** — el swipe derecho crea el match de inmediato y notifica al refugio —, **cuestionario de hogar obligatorio** antes de navegar, **sin lenguaje de descarte**, **sin comisión** — monetización vía apadrinamiento).
- `design/Adopta Web App.dc.html`, `Adopta Mobile.dc.html`, `Adopta Landing.dc.html` — prototipos interactivos (swipe funcional) renderizados con el runtime DesignSync (`support.js`, `dc-runtime`).
- `design/ios-frame.jsx` — frame de dispositivo iOS reutilizable para los prototipos.
- `.claude/settings.local.json` — permisos residuales de **otro proyecto no relacionado** (una calculadora/tracker de dosificación de péptidos), sin relación con Adopta.

Esto entra en conflicto directo con partes del prompt genérico (nombre "PawMatch", UI bilingüe ES/EN, "matches con interés mutuo", stack sugerido con Supabase implícito para tiempo real). Se preguntó al usuario cómo resolver el conflicto. **Decisiones tomadas:**

1. **Fuente de verdad del producto = `design/HANDOFF.md` y los prototipos existentes.** El producto se llama **Adopta**, es **es-CO únicamente** (se elimina el requisito de i18n bilingüe), el match **no es mutuo**, el cuestionario de hogar es obligatorio, no hay comisión (se documenta apadrinamiento en el modelo de datos aunque quede fuera del MVP), y las 11 pantallas/modelo de datos/paleta ya definidos en HANDOFF.md se usan como base de `docs/product-research.md` y `design/`. El resto de la estructura de harness engineering del prompt (fases, archivos, agentes, skills, `feature_list.json`, etc.) se sigue tal cual.
2. **Stack de datos/backend del MVP = local, FastAPI + SQLAlchemy + SQLite** (el default del prompt maestro), documentado en un ADR que reconoce la recomendación de Supabase/Firebase de HANDOFF.md §10 y explica por qué no aplica al alcance actual (el MVP no incluye chat en tiempo real, que queda en backlog). Migrar a un BaaS queda como decisión futura si se aborda el chat.

Otras decisiones de ejecución (no requieren más confirmación):
- La carpeta física sigue llamándose `peptinder` (no se renombra el directorio); el nombre de producto "Adopta" se usa en README, `package.json`, `pyproject.toml`, docs y copy.
- `design/HANDOFF.md` y los 3 prototipos `.dc.html` + `ios-frame.jsx` + `support.js` se conservan tal cual y se mueven a `design/prototypes/` (destino ya previsto en la estructura objetivo). `design/design-system.md` y `design/screens/*.md` se **derivan/formalizan** a partir de HANDOFF.md (no se rediseña desde cero — ya está hecho el trabajo de diseño).
- `.claude/settings.local.json` (permisos de otro proyecto) se deja intacto pero se añade a `.gitignore` (es un archivo local, no versionable) y se crea un `.claude/settings.json` **nuevo y versionado** con los hooks/routing propios de Adopta. `.DS_Store` también se ignora.
- Al terminar, además de vivir en el plan de Claude Code, este plan se copia como `plan.md` en la raíz del repo (pedido explícito del usuario: "export the plan created as a plan.md"), y se referencia desde `AGENTS.md`.

## Alcance de esta sesión de planificación

El propio prompt del usuario ya especifica con gran detalle las 9 fases, la estructura de archivos, y los criterios de aceptación — no hace falta re-diseñar eso. Este plan documenta cómo se ejecutará **respetando ese prompt**, con las dos decisiones de arriba aplicadas, y sirve como referencia para que Claude Code se detenga fase por fase y pida validación, tal como pidió el usuario.

## Fases de ejecución (orden fijo, con checkpoint del usuario al final de cada una)

**Fase 1 — Bootstrap + Git**
`git init` en `peptinder/`, rama `main` + `develop`. `.gitignore` (incluye `.claude/settings.local.json`, `.DS_Store`, `node_modules/`, `.venv/`, `*.db`, `.env`, `dist/`, `data/app.db`, caches). `.env.example` sin secretos. Conventional Commits. Los archivos de diseño existentes se **mueven** (no se recrean) a `design/prototypes/`. Commit inicial de scaffolding + activos de diseño preexistentes.
→ Stop: mostrar árbol del repo, `feature_list.json` inicial y el primer commit.

**Fase 2 — Investigación de producto**
`docs/product-research.md` se redacta **a partir de** `design/HANDOFF.md` (roles, decisiones de producto ya tomadas, modelo de datos, fórmula de afinidad, casos límite) más un análisis complementario de features de industria (adopción real: proceso de solicitud, rol de refugios, compatibilidad). `feature_list.json` traduce esto a alcance, con el orden del §5 del prompt adaptado a las entidades de Adopta (`User`/`HomeProfile`/`Shelter`/`Pet`/`Swipe`/`Match`) y dejando explícito qué queda en backlog (chat en tiempo real, apadrinamiento, panel de refugio completo, landing).

**Fase 3 — Arquitectura**
`docs/architecture.md` + ADRs en `docs/decisions/`, incluyendo el ADR de stack (React+Vite+TS+Tailwind / FastAPI+SQLAlchemy / SQLite local, con la nota sobre por qué no Supabase todavía) y un ADR sobre el modelo de match no-mutuo y el cuestionario obligatorio como reglas de negocio del backend (no solo de UI).

**Fase 4 — Convenciones**
`docs/conventions.md` (estilo, nombres, estructura, tests, lint/format: `ruff`/`black`, `eslint`/`prettier`, pre-commit).

**Fase 5 — Harness engineering**
`AGENTS.md`, `CHECKPOINTS.md`, `init.sh`, `progress/`, `memory/memory.md`, `changes.md`, `CHANGELOG.md`, `.claude/agents/{leader,implementer,reviewer,researcher,designer}.md`, `.claude/skills/{seed-data,db-migrations,run-verification,update-memory,match-scoring}/SKILL.md`, `.claude/settings.json` (hooks de lint/test post-edit + validación de `feature_list.json` con máx. 1 `in_progress`).

**Fase 6 — Diseño**
`design/design-system.md` y `design/screens/*.md` **formalizan** el contenido ya presente en `HANDOFF.md` (tokens de color/tipografía, las 11 pantallas con estados vacío/carga/error, comportamiento del gesto de swipe) en el formato objetivo del repo; los prototipos navegables ya existentes en `design/prototypes/` quedan como la referencia interactiva (se documentan, no se recrean).

**Fase 7 — MVP local**
Implementación del alcance de la Fase 2: esquema SQLite, seed determinista (`scripts/seed.py`) de mascotas/refugios/adoptantes con `HomeProfile` sintético, descarga de fotos con *fallback* offline a placeholders locales (créditos en `data/seed/CREDITS.md`), API FastAPI, deck de swipe en React (gestos como en el prototipo `.dc.html`, sin lenguaje de descarte: "Ahora no" / "Me interesa"), ficha de mascota, matches (no mutuo — al deslizar a la derecha se crea el match de inmediato) y score de afinidad con la ponderación de HANDOFF.md §7. Un solo comando para levantar API + web.

**Fase 8 — Verificación**
`bash init.sh` en verde (deps, seed, lint, tests, validación de `feature_list.json`). Evidencia en `docs/verification.md`. Prueba manual del deck de swipe en navegador antes de dar el MVP por bueno.

**Fase 9 — Cierre**
`CLAUDE.md` con cómo retomar el proyecto, mapa del repo, comandos exactos. Actualización final de `CHANGELOG.md`, `changes.md`, `progress/history.md`, `memory/memory.md`. Copia de este plan como `plan.md` en la raíz. Commit final limpio.

## Archivos/decisiones clave a tener presentes durante la ejecución

- Producto = **Adopta**, no PawMatch; es-CO únicamente, sin i18n bilingüe.
- Match no mutuo; cuestionario de hogar obligatorio (para el MVP puede resolverse con `HomeProfile` sintético por adoptante semilla, dejando el flujo interactivo de onboarding en backlog — se decide con precisión en la Fase 2).
- Sin lenguaje de descarte en copy ("Ahora no", nunca "rechazar").
- Stack: React+Vite+TS+Tailwind / FastAPI+SQLAlchemy / SQLite local — documentado vía ADR, no Supabase/Firebase por ahora.
- Reutilizar `design/HANDOFF.md` y los `.dc.html` existentes en vez de rediseñar desde cero.
- `.claude/settings.local.json` existente (de otro proyecto) se ignora vía `.gitignore`, no se borra ni se reutiliza.
- Detenerse al final de cada una de las 9 fases para validación del usuario, tal como pidió explícitamente.

## Verificación end-to-end

- `bash init.sh` debe terminar en verde (instala deps, corre seed, lint, tests, valida `feature_list.json`).
- Levantar API + web con el comando único documentado en `CLAUDE.md` y probar en navegador: cargar el deck, deslizar una mascota a la derecha, confirmar que aparece en Matches con su score de afinidad, abrir su ficha.
- Tests automatizados cubriendo: persistencia SQLite del seed, cálculo de score de afinidad (casos límite de HANDOFF.md §7, incluidas las reglas duras de incompatibilidad), y los endpoints principales (listar mascotas, registrar swipe, listar matches).
