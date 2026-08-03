# Estado actual

**Fase activa:** post-MVP — cola de `feature_list.json`
**Feature en progreso:** ninguna. `07-adopter-profile` fue revisada por un agente revisor independiente (sesión fresca, 2026-08-03) y **APROBADA**: `status` pasó a `done` en `feature_list.json`. `06-filters` sigue `done` (commiteada en `c1f4149`). No queda ningún item `in_progress`.

## Veredicto de revisión — `07-adopter-profile` (APROBADA)

- `bash init.sh` corrido de verdad en esta sesión: verde de punta a punta — 55 tests de API (incluye `tests/api/test_users.py`, 5 tests nuevos) + 17 de frontend (incluye `MiPerfil.test.tsx`, 2 tests nuevos), `ruff`/`black`/oxlint/prettier limpios, `feature_list.json` válido.
- Acceptance 1 (`GET /api/users/{id}` devuelve perfil + HomeProfile + métricas): cubierto por `tests/api/test_users.py` — conteos exactos de `matches_activos`/`visitas_agendadas` contra un seed local con `Match` en los 5 estados de ADR 0002, caso con `HomeProfile`, caso sin `HomeProfile` (`home_profile: null`, status 200, no 404 — verificado explícitamente, no solo inferido), 404 en español para usuario inexistente, y `apadrinamientos == 0` explícito.
- Acceptance 2 ("Mi hogar" refleja HomeProfile): cubierto por `MiPerfil.test.tsx` — valores mockeados de `HomeProfile` visibles en el DOM, variante `home_profile: null` con placeholder sin romper.
- Convenciones (`docs/conventions.md`): estructura de carpetas respetada (`schemas/user.py`, `routers/users.py`, lógica de agregación en el router vía `func.count()`, sin negocio embebido en componentes React); `UserOut`/`UserMetricsOut`/`HomeProfileOut` siguen el sufijo `Out`; error 404 vía `HTTPException` con mensaje en español (`f"El usuario {user_id} no existe"`); sin `except Exception` genérico en ningún archivo tocado.
- Arquitectura §6 / ADR 0002: no se creó modelo `Sponsorship` — `apadrinamientos` es `0` fijo en `UserMetricsOut` con comentario explícito (`# Siempre 0: no existe tabla Sponsorship todavía (feature 12-sponsorship, backlog).`). La decisión de `home_profile: null` (200, no 404) en `GET /api/users/{id}` no contradice el ADR 0002 (que exige `HomeProfile` obligatorio solo en el flujo de afinidad de `GET /api/pets`, sin tocarlo) — está documentada palabra por palabra en el docstring del router, con las dos definiciones exactas de métricas reproducidas en el test. No se introdujo ningún endpoint de "aceptar match".
- `changes.md` tiene 3 entradas nuevas referenciando `07-adopter-profile` (pasos 1, 2-3, 4) con detalle técnico y estados de test.
- Ninguna otra feature quedó `in_progress` en simultáneo (confirmado en `feature_list.json` antes de tocarlo).
- Verificación manual en navegador real (hecha en esta sesión por otro agente, no repetida por mí): `/perfil` cargó con datos del usuario semilla `id=1` (Ana Martínez), métricas en 0, HomeProfile completo, bio — sin errores de consola. `/descubrir` con filtros funcionando. DB reseteada a estado limpio tras esa verificación.
- Único detalle menor, no bloqueante: el implementador no pudo hacer la verificación manual en navegador en su propia sesión (sin herramienta de automatización disponible); quedó cubierta por la verificación posterior de otro agente en esta misma sesión de revisión, ya referenciada arriba.

## Próximos pasos

Backlog completo, empezando por `08-onboarding-cuestionario` (cuestionario de hogar interactivo real, hoy sintético en el seed — nota: cuando se implemente, revisar si el criterio "home_profile: null, no 404" de `07-adopter-profile` sigue siendo el comportamiento correcto para un usuario recién registrado sin cuestionario completado, probablemente sí). Requiere retomar con más cuidado por el ADR de auth/onboarding (no hay auth real todavía, ver `docs/architecture.md` §6). Luego `09-shelter-panel`/`10-adoption-request-flow` (cerrar el ciclo de la solicitud de adopción). `11-chat` requiere reabrir el ADR 0001 de stack.

## Nota operativa
Si quedan servidores de `bash dev.sh` corriendo en segundo plano de una sesión anterior, deténlos (Ctrl+C o `pkill`) antes de correr `init.sh`/tests para evitar conflictos de puerto.
