#!/usr/bin/env python3
"""Valida feature_list.json: usado por init.sh y por el hook de pre-commit.

Reglas:
- JSON parseable, con una lista "items".
- Cada item tiene id, title, description, status, depends_on.
- status es uno de: todo, in_progress, done.
- ids únicos.
- como máximo un item en status "in_progress".
- depends_on solo referencia ids que existen en la lista.
"""

import json
import sys

VALID_STATUS = {"todo", "in_progress", "done"}
REQUIRED_FIELDS = {"id", "title", "description", "status", "depends_on"}


def validate(path: str) -> list[str]:
    errors: list[str] = []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"no se pudo leer/parsear {path}: {exc}"]

    items = data.get("items")
    if not isinstance(items, list):
        return [f"{path} debe tener una clave 'items' de tipo lista"]

    ids = []
    for i, item in enumerate(items):
        missing = REQUIRED_FIELDS - item.keys()
        if missing:
            errors.append(f"item #{i} le faltan campos: {sorted(missing)}")
            continue
        ids.append(item["id"])
        if item["status"] not in VALID_STATUS:
            errors.append(f"item '{item['id']}': status inválido '{item['status']}'")

    duplicate_ids = {i for i in ids if ids.count(i) > 1}
    if duplicate_ids:
        errors.append(f"ids duplicados: {sorted(duplicate_ids)}")

    in_progress = [item["id"] for item in items if item.get("status") == "in_progress"]
    if len(in_progress) > 1:
        errors.append(f"más de un item in_progress (máximo 1): {in_progress}")

    known_ids = set(ids)
    for item in items:
        for dep in item.get("depends_on", []):
            if dep not in known_ids:
                errors.append(f"item '{item.get('id')}' depende de id inexistente: '{dep}'")

    return errors


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else "feature_list.json"
    errors = validate(path)
    if errors:
        for e in errors:
            print(f"  - {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
