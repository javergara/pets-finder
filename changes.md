# changes.md — bitácora interna de cambios (append-only)

Cambios importantes con fecha y referencia a commit. Granular y técnico — el `CHANGELOG.md` es la versión curada para release.

## 2026-07-31

- Bootstrap del repo: git init, `.gitignore`, `.env.example`, README, diseño preexistente movido a `design/prototypes/`. (`87e5117`)
- `docs/product-research.md` + `feature_list.json` poblado con 15 features (5 MVP, 2 post-MVP, 8 backlog). (`09701b2`)
- `docs/architecture.md` + ADRs 0001 (stack), 0002 (match no-mutuo), 0003 (afinidad al vuelo). (`8ddf946`)
- `docs/conventions.md` + config de ruff/black/prettier + `.pre-commit-config.yaml`. (`30518da`)
- Sistema de harness engineering: `AGENTS.md`, `CHECKPOINTS.md`, `init.sh` + `scripts/validate_feature_list.py`, `memory/memory.md`, `.claude/agents/*`, `.claude/skills/*`, `.claude/settings.json`. (pendiente de commit — Fase 5)
