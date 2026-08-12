# Convenciones de desarrollo — Reencuentro

## 1. Estructura de carpetas

```
src/api/reencuentro_api/
  models/      # entidades SQLAlchemy (1 archivo por entidad o grupo pequeño relacionado)
  schemas/     # Pydantic, contrato HTTP — nunca se exponen los modelos SQLAlchemy directo
  services/    # lógica de negocio pura (geo.py, ciudades.py, coincidencias.py), testeable sin FastAPI/DB
  routers/     # endpoints delgados: parsean input, llaman a services/, devuelven schemas
  main.py      # arma la app FastAPI, monta routers, CORS

src/web/src/
  screens/     # una pantalla por archivo (routing)
  components/  # componentes compartidos entre pantallas
  api/         # cliente HTTP tipado hacia src/api
  lib/         # utilidades sin estado de UI (mapa, ciudades, contacto, session)
```

Regla: si un archivo mezcla lógica de negocio con manejo de HTTP/DB, se está poniendo en el lugar equivocado — la lógica va a `services/`, no a `routers/` ni a componentes de React con `fetch` embebido y cálculo a la vez.

## 2. Nombres

- **Python:** `snake_case` para funciones/variables/módulos, `PascalCase` para clases (modelos, schemas Pydantic). Los schemas Pydantic de salida llevan sufijo `Out` (`PetOut`), los de entrada `In` (`SwipeIn`) cuando ambos existen para la misma entidad.
- **TypeScript/React:** `camelCase` para funciones/variables, `PascalCase` para componentes y tipos, un componente por archivo con el mismo nombre (`MatchCard.tsx` exporta `MatchCard`).
- **Rutas de API:** sustantivos en plural, en inglés (`/api/users`, `/api/reports`, `/api/uploads`) por consistencia con el resto del ecosistema HTTP; el **copy visible al usuario** siempre en español (es-CO), nunca se traduce la URL.
- **IDs de features/ADRs:** `NN-slug-en-espanol` para `feature_list.json`, `NNNN-slug-en-espanol` para ADRs (ya en uso en `docs/decisions/`).

## 3. Manejo de errores

- El backend responde con `HTTPException` de FastAPI y un cuerpo `{"detail": "mensaje en español"}` — el mensaje de error es copy de producto, no un stack trace ni un código interno.
- Nunca se atrapan excepciones genéricas (`except Exception`) para ocultar un bug; se atrapan solo los casos de negocio esperables (p. ej. `HomeProfile` inexistente al pedir afinidad → 404 con mensaje claro).
- En el frontend, todo `fetch` a la API pasa por el cliente de `src/web/src/api/` que normaliza errores a un tipo único (`ApiError`); las pantallas muestran mensajes de producto en español, nunca un mensaje técnico crudo.

## 4. Tests

- **Backend:** `pytest`. Los `services/` (geo, ciudades, coincidencias) tienen tests unitarios sin DB real; los `routers/` tienen tests de integración con una SQLite en memoria/temporal (fixture por test, nunca se comparte estado entre tests).
- **Frontend:** Vitest + Testing Library para lógica de componentes (p. ej. el pin por click en el mapa); no se persigue cobertura de UI pixel-perfect, sino comportamiento (qué se muestra, qué se llama en la API).
- Cada feature de `feature_list.json` con `acceptance` verificable debe tener al menos un test que la cubra directamente — el revisor no aprueba una feature cuyo `acceptance` no tiene test asociado.

## 5. Formato y lint

- **Python:** [`ruff`](https://docs.astral.sh/ruff/) para lint (incluye orden de imports) + `black` para formato. Config en `pyproject.toml` (raíz). Línea máxima 100. `target-version`/`target-version` de ambos apuntan a la versión real del intérprete disponible (3.10), no a una asumida de antemano.
- **TypeScript:** el scaffold de Vite (Fase 7) trajo [`oxlint`](https://oxc.rs/docs/guide/usage/linter.html) por defecto en vez de `eslint` — se mantiene esa elección (más rápido, cero config adicional) en vez de reemplazarlo por lo que este documento asumía originalmente. Formato con `prettier` (`.prettierrc.json`, raíz). Config de oxlint en `src/web/.oxlintrc.json`.
- Ningún archivo se commitea con lint en rojo; el hook de pre-commit (§7) lo impide.

## 6. Commits y ramas

- **Conventional Commits**: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`. Un commit por unidad lógica de trabajo (no se acumulan cambios de varias fases/features en un commit).
- Ramas: `main` (estable), `develop` (integración), `feat/<slug>` para una feature puntual si el trabajo lo amerita.
- El mensaje de commit explica el **por qué**, no repite el diff — igual que los ADRs.

## 7. Pre-commit

`.pre-commit-config.yaml` (raíz) corre `ruff`, `ruff-format` (o `black`, ver config) y `prettier` sobre los archivos modificados antes de cada commit. Se activa una vez con:

```bash
pip install pre-commit
pre-commit install
```

`init.sh` (Fase 5) verifica que el hook esté instalado y, si no, lo instala — así ningún colaborador (humano o agente) puede commitear código sin pasar por lint/formato, sin depender de que se acuerde de correrlo a mano.
