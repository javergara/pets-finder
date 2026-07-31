# Cuestionario de hogar (`/cuestionario`)

**Alcance:** backlog (`feature_list.json` → `08-onboarding-cuestionario`). En el MVP, el `HomeProfile` es sintético (seed) y esta pantalla no se construye todavía. Fuente: `design/prototypes/HANDOFF.md` §5.1.

## Objetivo
Crear el `HomeProfile` real (bloquea `/descubrir` hasta completarse) — es el freno ético del producto y el input de la afinidad.

## Estructura
Seis pasos, una pregunta por paso, barra de progreso + `Paso N de 6`:
1. Vivienda y espacio exterior. 2. Personas/niños en casa. 3. Rutina — horas fuera. 4. Otras mascotas actuales. 5. Experiencia previa y presupuesto mensual. 6. Tipo de compañía buscada (energía, tamaño, especie).

Cada paso: tarjetas radio ≥56px de alto, seleccionada = `forest-tint` + borde `forest`; aviso en `surface-alt` sobre la honestidad para evitar devoluciones; pie con `Atrás`/`Continuar`.

## Notas de implementación futura
Editable después desde Mi perfil; al editarlo se recalculan todas las afinidades (consistente con ADR 0003 — no hay caché que invalidar, se recalcula solo).
