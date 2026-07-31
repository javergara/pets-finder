# Panel del refugio (`/refugio`)

**Alcance:** backlog (`feature_list.json` → `09-shelter-panel`, `10-adoption-request-flow`). Fuente: `design/prototypes/HANDOFF.md` §5.10.

## Objetivo
El refugio publica mascotas y decide sobre la **solicitud de adopción** (no sobre el match — ADR 0002).

## Estructura
Cabecera: nombre del refugio, `N mascotas publicadas`, `Publicar mascota`. Cuatro métricas: interesados este mes, visitas agendadas, adopciones cerradas, apadrinamientos recaudados (COP). Tabla **Solicitudes por revisar**: adoptante · mascota · afinidad · estado · `Revisar`. Estados: `Cuestionario nuevo`, `Visita agendada`, `Sin responder · N días` (alerta `ochre` desde 2 días). Al abrir `Revisar`: cuestionario completo del adoptante, texto "Sobre mí", acciones `Agendar visita` / `Pedir más información` / `Descartar con motivo` (motivo obligatorio, no se muestra al adoptante en crudo).
