# 0009 — Vista previa al compartir un reporte: og tags servidos solo a bots

- **Estado**: aceptada (2026-08-12)
- **Contexto**: la difusión por WhatsApp es el mecanismo #1 para encontrar mascotas (product-research §6-8), pero al compartir un link de `/reporte/:id` la vista previa salía genérica: la SPA sirve el mismo `index.html` para toda ruta y los rastreadores de WhatsApp/Facebook no ejecutan JavaScript.
- **Opciones evaluadas**:
  1. **SSR/prerender del frontend** (Next.js o prerender en build) — resuelve de raíz pero cambia el stack del frontend (ADR 0001/0007) por un solo caso de uso.
  2. **Función que inyecta meta tags en el index.html para todos** — doble fetch por visita humana (función + estáticos), latencia extra en la ruta más caliente.
  3. **Rewrite condicionado por user-agent solo para bots** (elegida): `vercel.json` manda `/reporte/:id` a la API **solo** cuando el user-agent es un rastreador conocido (`facebookexternalhit`, `WhatsApp`, `Twitterbot`, `TelegramBot`, `LinkedInBot`, `Slackbot`, `Discordbot`); la ruta FastAPI `GET /reporte/{id}` (routers/paginas.py) responde un HTML mínimo con og:title/description/image/url del reporte. Los humanos siguen recibiendo la SPA sin ningún costo extra.
- **Consecuencias**:
  - Cero impacto en la experiencia humana y cero dependencias nuevas; testeable con `TestClient` (el HTML es una respuesta más de la API).
  - La lista de bots es una regex mantenida a mano en `vercel.json` — un rastreador nuevo no listado verá la vista genérica (degradación aceptable, no rotura).
  - `SITE_URL` (env var, default `https://petfinder-col.com`) define las URLs absolutas de og:url/og:image.
  - El botón Compartir del detalle usa la Web Share API con fallback a copiar el link — sin SDKs de redes sociales.
