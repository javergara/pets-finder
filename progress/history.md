# Historial (append-only)

## 2026-07-31 — Fase 1: Bootstrap + Git
- Se encontró que el directorio de trabajo no estaba vacío: contenía diseño preexistente para "Adopta" (generado con DesignSync) en vez de partir de cero como sugería el prompt genérico original ("PawMatch"). Se acordó con el usuario usar ese diseño como fuente de verdad del producto y mantener FastAPI+SQLite local (no Supabase) para el MVP. Detalle completo en `plan.md`.
- `git init` con identidad local (sin tocar `~/.gitconfig`, autorizado explícitamente por el usuario).
- Diseño existente movido de `design/*` a `design/prototypes/*` sin modificar contenido.
- Creados: `.gitignore`, `.env.example`, `README.md`, `feature_list.json` (esqueleto vacío), estructura de carpetas del repo.
