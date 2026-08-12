---
name: run-verification
description: Corre init.sh y los tests, y resume el resultado en docs/verification.md. Usar antes de aprobar cualquier feature y siempre en la Fase 8 del proyecto.
---

# run-verification

## Cuándo usar
El revisor lo usa antes de marcar cualquier feature como `done`. También se usa completo en la Fase 8 (cierre del MVP).

## Cómo

1. Corre `bash init.sh` desde la raíz del repo. Copia la salida real (no la resumas de memoria).
2. Si algo falla, identifica en qué sección (dependencias, feature_list, lint, tests) y no continúes hasta que se resuelva o quede explícitamente documentado como excepción aceptada por el usuario.
3. Actualiza `docs/verification.md` con: fecha, comando corrido, resultado (verde/rojo), y qué features quedaron cubiertas por qué tests.
4. Si es una verificación de feature puntual (no la Fase 8 completa), deja también el veredicto en `progress/current.md` para que el líder sepa si puede seguir con el siguiente paso.

## Qué no hacer
No marques nada como verificado si no corriste el comando en esta sesión — "debería pasar" no es un veredicto válido (ver `CHECKPOINTS.md`, sección "qué NO es un checkpoint válido").
