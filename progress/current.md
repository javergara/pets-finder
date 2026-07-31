# Estado actual

**Fase activa:** 5 — Sistema de harness engineering (completa, pendiente checkpoint del usuario)
**Feature en progreso:** ninguna

## Hecho en esta fase
- `AGENTS.md`: mapa de divulgación progresiva, flujo líder→implementador→revisor, tabla de routing tarea→agente/skill→archivos.
- `CHECKPOINTS.md`: checkpoint global, por feature y por fase del proyecto; qué NO es un checkpoint válido.
- `init.sh` + `scripts/validate_feature_list.py`: **probado de verdad**, corre en verde antes de que exista código de producto (omite con aviso claro lo que aún no aplica, solo falla en validaciones reales). Se encontró y corrigió un tag inexistente en `.pre-commit-config.yaml` (`mirrors-prettier` `v3.3.3` no existe → `v3.1.0`).
- `requirements-dev.txt` (ruff, black, pytest, pre-commit) — instalado en `.venv/` local.
- `memory/memory.md`, `changes.md`, `CHANGELOG.md` (Keep a Changelog).
- `.claude/agents/{leader,implementer,reviewer,researcher,designer}.md`.
- `.claude/skills/{seed-data,db-migrations,run-verification,update-memory,match-scoring}/SKILL.md`.
- `.claude/settings.json` + `.claude/hooks/{post-edit-format,validate-feature-list}.sh` — **probados de verdad**: el hook de validación bloquea (exit 2) un `feature_list.json` con >1 `in_progress` usando una copia descartable en el scratchpad, y deja pasar (exit 0) uno válido.

## Decisiones vigentes (ver plan.md)
- Producto = **Adopta**, es-CO únicamente. Stack: React+Vite+TS+Tailwind / FastAPI+SQLAlchemy / SQLite local (ADR 0001). Match no mutuo (ADR 0002); afinidad al vuelo (ADR 0003).

## Próximo paso
Checkpoint de Fase 5 con el usuario. Luego Fase 6: formalizar `design/design-system.md` y `design/screens/*.md` a partir de `design/prototypes/HANDOFF.md`.
