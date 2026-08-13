# 0011 — Alertas por reporte: email vía Resend detrás de env vars

- **Estado**: aceptada (2026-08-13)
- **Contexto**: la feature 39 ("avísame si hay novedades" de un reporte, benchmark encontradogs en product-research §9) necesita enviar correos — el primer canal saliente del proyecto. La feature 22 (alertas por zona) sigue pendiente de decisión; esta es su recorte mínimo shippeable: suscripción por reporte, sin cuenta, con baja en un click.
- **Opciones evaluadas**:
  1. **SMTP directo** (Gmail u otro): frágil en serverless (conexiones lentas, reputación de IP), credenciales de una cuenta personal en producción.
  2. **WhatsApp Business API**: el canal natural del proyecto, pero requiere aprobación de Meta, número dedicado y costos — desproporcionado hoy.
  3. **Resend por API HTTP** (elegida): un POST con `requests` (ya en las dependencias por Supabase Storage), free tier de 100 correos/día y 3.000/mes, remitente verificable con el dominio propio. Mismo patrón operativo que Supabase: la clave vive en env vars de Vercel, nunca en el repo.
- **Decisión**: `services/notificaciones.py` envía vía `https://api.resend.com/emails` con `RESEND_API_KEY` y `RESEND_FROM` (default `onboarding@resend.dev`, el remitente de pruebas de Resend). **Sin `RESEND_API_KEY` el envío es un no-op con log** — la app funciona igual y los endpoints que disparan avisos (avistamiento nuevo, reencuentro) jamás fallan por el proveedor (best-effort con log). La baja es `GET /api/suscripciones/baja/{token}`: el token aleatorio es la autorización (quien tiene el link recibió el email).
- **Consecuencias**:
  - El dueño debe crear la cuenta de Resend, verificar el dominio `petfinder-col.com` (2 registros DNS en GoDaddy) y poner las 2 env vars en Vercel para que los correos salgan de verdad; mientras tanto las suscripciones se guardan y no se pierde nada.
  - El envío es síncrono dentro del request (pocos suscriptores por reporte); si el volumen crece, mover a una cola es el siguiente paso y merece revisar este ADR.
  - Los correos de terceros nunca se exponen por la API (SuscripcionOut no incluye email ni token).
