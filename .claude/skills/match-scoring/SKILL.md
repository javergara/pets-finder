---
name: match-scoring
description: Implementa o modifica el cálculo de compatibilidad adoptante↔mascota (src/api/adopta_api/services/affinity.py). Usar para la feature 05-affinity-score y cualquier ajuste posterior a la fórmula.
---

# match-scoring

## Cuándo usar
Al implementar `05-affinity-score`, o si cambia la ponderación/reglas duras documentadas en `docs/product-research.md` §5 y `docs/decisions/0003-afinidad-calculada-al-vuelo.md`.

## Cómo

1. La función vive en `src/api/adopta_api/services/affinity.py`, es **pura** (sin I/O, sin acceso a DB dentro de la función — recibe `HomeProfile` y `Pet` ya cargados) — ver ADR 0003 sobre por qué no se persiste el score.
2. Ponderación (no la reinventes, está fijada en `docs/product-research.md` §5):
   - Energía de la mascota vs. horas fuera y rutina — 30%
   - Tamaño vs. tipo de vivienda y espacio exterior — 20%
   - Convivencia declarada (niños / otros perros / gatos) — 20%
   - Preferencia declarada de especie y tamaño — 15%
   - Experiencia previa y presupuesto vs. necesidades de cuidado — 15%
3. Reglas duras (se evalúan **antes** del score, no como parte del promedio ponderado): si la mascota no es apta con niños y el hogar declara niños, o no es apta con gatos y el hogar declara gato → marcar la pareja como `incompatible` en vez de devolver un score bajo.
4. La función siempre devuelve `(score: int, explicación: str)` — nunca un número solo. La explicación es determinista dado el input (no generada por LLM en el MVP).
5. Tests obligatorios (ver `feature_list.json` → `05-affinity-score` → `acceptance`): un caso de alta afinidad, uno de baja afinidad, y uno donde se activa una regla dura.

## Dónde se usa el resultado
Deck de descubrimiento (orden + badge), ficha de mascota, y listado de matches — la misma función, no tres implementaciones distintas.
