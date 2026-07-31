---
name: update-memory
description: Registra procesos importantes en memory/memory.md, cambios en changes.md, y progreso en progress/. Usar al final de cada paso no trivial, no solo al final de la sesión.
---

# update-memory

## Cuándo usar
Al terminar cualquier paso no trivial: una decisión de proceso tomada, un error resuelto de forma no obvia, una feature completada, o el cierre de una fase del proyecto.

## Cómo

- **`progress/current.md`** (se sobrescribe, es el estado *vivo*): qué se hizo en esta fase/paso, decisiones vigentes, próximo paso concreto. Debe poder leerse solo y entender dónde está el proyecto ahora mismo.
- **`progress/history.md`** (append-only, nunca se edita lo ya escrito): una entrada por fase/hito con fecha, qué se hizo y por qué fue relevante.
- **`memory/memory.md`** (append-only): solo lo que **no es obvio releyendo el código** — gotchas, decisiones de proceso y su razón, errores no triviales y cómo se resolvieron. No repitas aquí lo que ya está en un ADR o en `docs/conventions.md`.
- **`changes.md`** (append-only, granular): cambios técnicos con fecha y referencia a commit — para trazabilidad, no para contar una historia.
- **`CHANGELOG.md`**: solo cuando el cambio es relevante de cara a un release (formato Keep a Changelog), no para cada commit interno.

## Qué no hacer
No dejes una decisión importante solo en la respuesta de chat — si no está en uno de estos archivos, para efectos del proyecto no pasó (ver `AGENTS.md`, "regla dura de estado").
