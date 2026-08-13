
## 2026-08-12 — Incidente de deploy: Vercel dejó de auto-desplegar main (resuelto manualmente)

- Tras el merge del stack del crawler, DOS pushes a main (aea5fb7, 1dadda8) no crearon NINGÚN deployment (ni Production ni Canceled), mientras los previews de ramas sí se creaban. Diagnóstico vía dashboard con el navegador: sin errores de build — los deployments simplemente no se crearon.
- Solución: Deployments → "…" → Create Deployment → main → Deploy to Production (el trigger manual respondió 200 y quedó Ready). Verificado: bundle DUPVExON servido con el detalle crawleado, health 200, columnas nuevas activas.
- Si se repite: revisar los webhook deliveries de la GitHub App de Vercel, o usar el mismo Create Deployment del dashboard. Este mismo commit sirve de prueba de si el auto-deploy se recuperó.
