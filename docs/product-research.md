# Investigación de producto — Reencuentro

> La investigación de la era Adopta (adopción de mascotas) vive en la rama `adopta-v1`.

## 1. Problema

El terremoto del Eje Cafetero (10 de agosto de 2026) separó a miles de mascotas de sus familias: animales que huyeron por el pánico, casas colapsadas, evacuaciones apresuradas. Los reportes están dispersos (grupos de WhatsApp, publicaciones sueltas, un mapa colaborativo de Google My Maps) sin estructura ni búsqueda. Quien encuentra una mascota no tiene forma sistemática de encontrar a su dueño, y viceversa.

## 2. Referentes reales

- **Mapa colaborativo del Eje Cafetero** (Google My Maps): marcadores georreferenciados con categorías por tipo de animal y códigos de color por estado. Validó la necesidad, pero sin estructura de datos ni contacto integrado.
- **Patitas a Salvo / mascotasporvenezuela.com** (terremotos de Venezuela, 2026): tres entradas ("Perdí a mi mascota" / "Encontré una mascota" / "Necesita atención"), búsqueda por zona, contacto directo. El modelo más cercano al nuestro.
- **PawBoost** (EE. UU.): "AMBER Alert para mascotas", alertas comunitarias por zona. Fuera de alcance del MVP (requiere base de usuarios), pero valida "reunido" como métrica central.
- **Love Lost (Petco)**: matching de fotos con AI. Fuera de alcance — nuestras coincidencias son por especie + zona + distancia + fecha, sin AI.

## 3. Roles

- **Dueño**: perdió su mascota. Reporta con foto, señas, dónde se perdió y su teléfono. Revisa coincidencias con reportes de encontradas.
- **Rescatista**: encontró una mascota (la tiene consigo o la vio). Reporta con foto, dónde, y su teléfono.
- No hay rol de administrador en el MVP; no hay moderación de reportes.

## 4. Decisiones de mecánica (y por qué)

| Decisión | Por qué |
|---|---|
| Dos CTAs gigantes en la landing: "Perdí" / "Encontré" | En emergencia, el usuario decide en 2 segundos qué camino es el suyo. Patrón de Patitas a Salvo. |
| Registro mínimo reutilizado (nombre + email, sin contraseña) | Cada paso extra cuesta reportes; pero ligar reportes a un usuario permite editarlos y marcarlos reunidos después. |
| Contacto directo WhatsApp/tel, sin chat interno | Es el canal que todo el mundo ya tiene abierto en Colombia. Cero fricción, cero infraestructura. |
| Foto obligatoria en el reporte | La foto es el identificador principal de una mascota para un humano. |
| Pin en el mapa propio (click) + zona | Coordenadas exactas sin depender de servicios de mapas externos. |
| Coincidencias por especie + zona + distancia + fecha | Simple, explicable y útil; sin AI ni servicios externos. |
| Estado "reunido" con contador público | La métrica de esperanza: motiva a reportar y a compartir. Los reunidos salen del listado/mapa activos. |
| Sin lenguaje de descarte ni de fracaso | Herencia de producto de la era Adopta: el tono importa. "Reunido", nunca "cerrado sin éxito". |

## 5. Flujo principal

1. Landing → "Perdí a mi mascota" (o "Encontré una").
2. Si no está registrado → registro liviano → vuelve al formulario (`?volver=`).
3. Formulario: foto, especie, señas, zona + pin en el mapa, fecha, teléfono. Campos condicionales: `nombre_mascota` (perdido), `situacion` conmigo/vista (encontrado).
4. El reporte aparece en el listado (filtros tipo/especie/zona) y en el mapa (color por tipo).
5. En el detalle de un reporte: contacto directo + posibles coincidencias del tipo opuesto.
6. Cuando la mascota vuelve a casa: el autor la marca "reunida" → sale de las vistas activas y alimenta el contador de reencuentros de la landing.

## 6. Benchmark post-lanzamiento: Reúne Mascotas (2026-08-12)

Evaluación de <https://reunemascotas.brannd.com.co/> — app hermana del **mismo terremoto** (pedida por el usuario como fuente de features). Es más simple que Pet Finder Col: reporte sin cuenta (solo nombre + WhatsApp), una foto comprimida, raza/color como texto libre, mapa "por zonas" clickeable sin pins reales, sin coincidencias, sin características filtrables, sin eliminar/editar.

**Lo que ya cubrimos igual o mejor**: compresión de fotos, contacto por WhatsApp, filtros por especie/estado/zona, mapa (el nuestro con pins reales Leaflet), coincidencias, contador de reunidos, características predefinidas.

**Lo que vale la pena adoptar** (entró al backlog):
- **Cobertura de Medellín** (y Palmira) como zona propia — ellos la tienen, nosotros la mandamos a "Otro" (`26-zona-medellin`).
- **Vista pública "Solo reunidos"** — navegar las historias de esperanza, no solo el contador (`27-vista-reencuentros`).
- Su formulario ultra liviano confirma la decisión del registro mínimo: no adoptamos "reportar sin cuenta" porque perderíamos marcar-reunido y eliminar (ligados a autoría), pero refuerza mantener el registro en 3 campos.

Además del benchmark, entraron mejoras realistas de lo ya construido: avistamientos de terceros (`28`, patrón PawBoost/Love Lost), edición completa del reporte (`29`), búsqueda + paginación (`30`) y pin por geolocalización (`31`).

## 7. El tercer actor: la ayuda organizada (features 32-33, 2026-08-12)

Además de dueños↔rescatistas, una emergencia tiene un tercer actor: **quien organiza la ayuda** (centros de acopio, fundaciones, tiendas, veterinarias). La sección unificada **/ayudar** los pone en un solo mapa/directorio con contacto directo por WhatsApp (coherente con §3: sin chat interno, sin pagos en la app — "Cómo donar" es texto informativo). La mecánica de **necesidades** ("50 kg de comida" → "Quiero ayudar" → "Cubierta 💚") replica la métrica de esperanza de los reencuentros: pedidos concretos y accionables en vez de "ayuden por favor", y celebración visible cuando la ayuda llega. Publica cualquiera con la cuenta liviana; la moderación queda en el backlog (23).

## 8. Benchmark: Encuentra tu Peludo (2026-08-12)

Evaluación de <https://encuentratupeludo.vercel.app/> (también post-terremoto, también en Vercel). Su feed muestra contadores reales por tipo — **204 perdidos / 25 vistos / 9 rescatados** — un dato de mercado en sí mismo: la demanda es abrumadoramente de dueños buscando.

**Lo que ya cubrimos igual o mejor**: publicación rápida (ellos sin cuenta — nosotros mantenemos la cuenta liviana porque sostiene marcar-reunido/editar/eliminar, ADR 0005), una foto ≤4MB (nosotros ≤5MB con compresión en el navegador), WhatsApp directo, filtros por ciudad/especie/estado, su página /ayuda por ciudad (nuestra red de apoyo tiene mapa, necesidades accionables y "cómo donar" — más completa), y su tipo "Visto" (nuestro `situacion: vista` + los avistamientos georreferenciados sobre reportes perdidos).

**Lo que vale la pena adoptar**:
- **Contadores visibles por tipo** en el feed (su "Perdidos 204" da urgencia y prueba social; nosotros no mostramos números en el listado) → feature `34`.
- **Recencia** ("hace 2 horas") en tarjetas — en emergencia, lo reciente vale más que la fecha absoluta → feature `34`.
- **Compartir por reporte**: ellos lo tienen por tarjeta; refuerza la prioridad de nuestra `21-compartir-reporte` (ya en backlog).
