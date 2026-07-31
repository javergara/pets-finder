# Estado actual

**Fase activa:** 6 — Diseño formalizado en design/ (completa, pendiente checkpoint del usuario)
**Feature en progreso:** ninguna

## Hecho en esta fase
- `design/design-system.md`: tokens de color/tipografía/forma/profundidad, imágenes, estados, accesibilidad y el gesto de swipe como referencia de implementación — formalizado a partir de `design/prototypes/HANDOFF.md` §3/§9, sin rediseñar nada. Se deja explícito que no hay modo oscuro diseñado (no se inventa uno).
- `design/screens/*.md`: las 11 pantallas de HANDOFF.md, cada una marcada con su `feature_list.json` correspondiente:
  - Detalle completo (alcance MVP): `descubrir.md`, `mascota-detalle.md`, `match-modal.md`, `mis-matches.md`.
  - Detalle breve (post-MVP/backlog, referencian directamente a HANDOFF.md): `cuestionario.md`, `mensajes.md`, `apadrinar.md`, `mi-perfil.md`, `ajustes.md`, `panel-refugio.md`, `landing-publica.md`.
- Los prototipos interactivos ya existentes en `design/prototypes/` quedan como la referencia navegable — no se recrearon.

## Decisiones vigentes (ver plan.md)
- Producto = **Adopta**, es-CO únicamente. Stack: React+Vite+TS+Tailwind / FastAPI+SQLAlchemy / SQLite local (ADR 0001). Match no mutuo (ADR 0002); afinidad al vuelo (ADR 0003).

## Próximo paso
Checkpoint de Fase 6 con el usuario. Luego Fase 7: implementar el MVP (esquema SQLite, seed, API FastAPI, deck de swipe React, ficha, matches, score de afinidad) — la fase más larga, activa la primera feature (`01-foundations-data`) en `feature_list.json`.
