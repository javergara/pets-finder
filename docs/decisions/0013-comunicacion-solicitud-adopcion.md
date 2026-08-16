# 0013 — Comunicación de una solicitud de adopción: WhatsApp directo

## Estado

Aceptada (2026-08-16). **Supera al ADR 0004** ("Chat: WebSockets nativos sobre
FastAPI, sin BaaS", era Adopta), que no se restaura a `main` y queda archivado
con la rama `adopta-v1`. Extiende al módulo de adopción la regla que el ADR 0005
§3 ya fijó para el dominio de emergencia: contacto directo por WhatsApp/teléfono,
sin chat interno.

## Contexto

AD-05 dejó la solicitud completa: quien publica la recibe, la mueve entre estados
y la cierra. Lo que falta es la conversación — el "hablemos" que hay entre pedir
una mascota y entregarla.

La era Adopta ya la había resuelto, y el ADR 0004 dejó escrita esa solución:
**WebSockets nativos de FastAPI con un `ConnectionManager` en memoria**, un dict
`match_id -> list[WebSocket]` a nivel de módulo. El propio ADR 0004 acotó su
validez con precisión — *"correcto y suficiente para un solo proceso `uvicorn`
sin `--workers`, que es como corre `dev.sh` hoy"*— y anotó la limitación de
escalado como deuda a reconsiderar.

Ese "hoy" ya no existe. **La app corre en Vercel como funciones serverless** (ADR
0007): cada request levanta una instancia efímera de `api/index.py`, no hay
proceso persistente entre requests, no hay memoria compartida entre invocaciones
y no hay conexión que sobreviva a la respuesta. Un `ConnectionManager` en memoria
allí no es "poco escalable": no funciona ni una vez. `chat.py` y `chat_manager.py`
de `adopta-v1` no se pueden portar, y la limitación que el ADR 0004 anotó como
futura ya se cumplió. Por eso se decide de nuevo, en vez de arrastrar el port.

## Opciones evaluadas

| Opción | Costo real | Veredicto |
|---|---|---|
| **(a) WhatsApp directo** con mensaje precargado por estado | Cero infraestructura: dos funciones puras de copy sobre el `urlWhatsApp` que ya existe. No hay tabla, ni dependencia, ni endpoint nuevo. El teléfono ya viaja en el contrato de AD-05 (el del publicador en `SolicitudOut.publicador`, el del adoptante en `SolicitudDetalleOut.telefono_contacto`). **La conversación no queda dentro del producto.** | **Elegida** |
| **(b) Supabase Realtime** sobre una tabla `mensajes` | Dependencia nueva en el navegador (`@supabase/supabase-js`) y por tanto **ADR extra**; la clave anon expuesta al cliente, con RLS por fila como única barrera —y este producto no tiene auth real (ADR 0005: sin contraseñas), así que la barrera no la hay—; una tabla que crear y migrar a mano en prod (`SKIP_DB_CREATE_ALL=1`); y un canal de mensajería que mantener, moderar y respaldar. | Descartada |
| **(c) Polling** sobre una tabla `mensajes` propia | Sin dependencias nuevas y sin WebSockets: funcionaría en serverless. Pero introduce **chat interno** —justo lo que el ADR 0005 §3 sacó del producto—, con latencia de segundos, y cada pestaña abierta gasta invocaciones serverless del free tier a razón de una cada pocos segundos, por una conversación que ocurre dos o tres veces por adopción. | Descartada |

Las tres funcionan técnicamente. Lo que decide no es la latencia: es que **(b) y
(c) construyen un canal de mensajería que el producto ya decidió no tener**.

## Decisión

**(a) WhatsApp directo, en las dos direcciones, con el mensaje precargado según
el estado de la solicitud.**

- `src/web/src/lib/contacto.ts` gana dos funciones puras de copy —adoptante →
  publicador y publicador → adoptante—, sobre el `urlWhatsApp` que ya usan los
  flujos de emergencia, la red de apoyo y la ficha de adopción. Mencionan la
  marca **Pet Finder Col** y la mascota concreta, como el resto de los mensajes
  precargados de la app.
- El texto cambia por estado porque el motivo de escribir cambia: presentarse en
  `solicitado`, preguntar cómo va en `en_revision`, confirmar la visita en
  `visita_agendada`, coordinar la entrega en `adoptado`.
- **No entra ninguna tabla, ningún endpoint y ninguna dependencia.** Un test de
  guardarraíl recorre `src/api/reencuentro_api/**/*.py` y falla si aparece
  `WebSocket`, `websockets` o `ConnectionManager`.

## Consecuencias

- **Ninguna dependencia de WebSockets ni de proceso persistente entra a
  producción.** La API sigue siendo un conjunto de funciones sin estado, que es
  lo único que el runtime de Vercel garantiza.
- **La conversación vive fuera de la app**, en el canal que las dos partes ya
  tienen abierto y saben usar. Es el mismo trato que el producto hace desde el
  pivot: cero fricción de adopción a cambio de cero control del canal.
- **El estado de la solicitud (AD-05) es el único registro interno del avance.**
  Lo que se acordó por WhatsApp no se ve en la app; lo que sí se ve es en qué
  punto está: solicitada, en revisión, visita agendada, adoptada, cerrada. Por
  eso mover el estado deja de ser un trámite y pasa a ser la memoria del proceso.
- **Se pierde el historial dentro del producto**: no hay forma de auditar una
  conversación, ni de retomarla desde otro dispositivo, ni de moderarla. Se
  acepta a cambio de que la comunicación funcione de verdad en el stack real —un
  chat interno que no se puede desplegar no protege a nadie—.
- El teléfono es el punto único de contacto, así que su ausencia es una carencia
  visible: sin `telefono_contacto` la pantalla dice que no lo dejaron, en vez de
  pintar un botón que no lleva a ninguna parte. Ya es el criterio de
  `MascotaDetalle`.
- Si algún día hace falta un canal interno —moderación, denuncia, verificación—,
  este ADR se revisa entero: la opción (c) es el punto de partida, no la (b),
  porque no añade dependencia ni expone claves.
