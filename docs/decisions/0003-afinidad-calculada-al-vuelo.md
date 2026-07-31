# 0003 — La afinidad se calcula al vuelo, no se persiste

## Estado
Aceptado.

## Contexto
El score de compatibilidad (`feature_list.json` → `05-affinity-score`) depende de dos entidades mutables: `HomeProfile` (puede editarse, y HANDOFF.md §5.1 exige que al editarlo "se recalculan todas las afinidades") y `Pet` (sus atributos de cuidado pueden actualizarse por el refugio). Persistir un score calculado en el momento del match crearía un problema de invalidación de caché: cada edición de cualquiera de las dos entidades tendría que disparar un recálculo masivo de todos los pares afectados.

## Decisión
El score de afinidad se calcula en el momento de cada request (`services/affinity.py`, función pura `HomeProfile × Pet → (score: int, explicación: str)`), tanto para ordenar el deck de descubrimiento como para mostrarlo en la ficha de mascota y en matches. No existe una columna `affinity_score` en ninguna tabla.

## Consecuencias
- Editar un `HomeProfile` o un `Pet` refleja el nuevo score inmediatamente en cualquier vista, sin job de recálculo ni caché que invalidar.
- El costo de calcular en cada request es aceptable para el volumen de datos de un MVP (decenas de mascotas); si el catálogo creciera a un tamaño donde esto sea un cuello de botella real, se reconsiderará (p. ej. cachear por `(home_profile_id, pet_id)` con invalidación por versión), pero no se optimiza preventivamente ahora.
- La función de scoring debe ser pura (sin I/O) precisamente para que sea barata de invocar repetidamente y fácil de testear de forma aislada (ver criterios de aceptación de `05-affinity-score`).
