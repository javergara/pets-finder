# Mensajes (`/mensajes`)

**Alcance:** backlog (`feature_list.json` → `11-chat`, requiere revisar ADR 0001 si se necesita realtime). Fuente: `design/prototypes/HANDOFF.md` §5.6.

## Objetivo
Chat adoptante↔refugio por match.

## Estructura
Escritorio: lista de conversaciones (320px) + hilo. Móvil: lista y hilo como pantallas separadas. Cabecera del hilo: avatar del refugio, nombre, `Conversación sobre <Mascota>`, atajo `Ver ficha`. Primer elemento: aviso de sistema explicando por qué se abrió la conversación. Burbujas propias en `forest` (radio `14 14 4 14`), del refugio en `surface` con borde (radio `14 14 14 4`), máx. 62%/76% de ancho (escritorio/móvil). Respuestas rápidas sugeridas cuando el refugio propone cita. Compositor: campo + `Enviar` (escritorio) o botón circular `↑` (móvil).
