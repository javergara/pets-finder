# Investigación de producto — Reencuentro

> La investigación de la era Adopta (adopción de mascotas) vive en la rama `adopta-v1`.

## 1. Problema

El terremoto del Eje Cafetero (10 de agosto de 2026) separó a miles de mascotas de sus familias: animales que huyeron por el pánico, casas colapsadas, evacuaciones apresuradas. Los reportes están dispersos (grupos de WhatsApp, publicaciones sueltas, un mapa colaborativo de Google My Maps) sin estructura ni búsqueda. Quien encuentra una mascota no tiene forma sistemática de encontrar a su dueño, y viceversa.

## 2. Referentes reales

- **Mapa colaborativo del Eje Cafetero** (Google My Maps): marcadores georreferenciados con categorías por tipo de animal y códigos de color por estado. Validó la necesidad, pero sin estructura de datos ni contacto integrado.
- **Patitas a Salvo / mascotasporvenezuela.com** (terremotos de Venezuela, 2026): tres entradas ("Perdí a mi mascota" / "Encontré una mascota" / "Necesita atención"), búsqueda por zona, contacto directo. El modelo más cercano al nuestro.
- **PawBoost** (EE. UU.): "AMBER Alert para mascotas", alertas comunitarias por zona. Fuera de alcance del MVP (requiere base de usuarios), pero valida "reunido" como métrica central.
- **Love Lost (Petco)**: matching de fotos con AI. Estuvo fuera de alcance hasta la feature `24` (2026-08-13): hoy las coincidencias **suman** parecido visual sobre la heurística explicable de siempre (especie + zona + distancia + fecha), con modelos abiertos que corren fuera de la API y sin mandar las fotos a ningún tercero. Ver ADR 0012.

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

## 9. Benchmark: encontradogs.co (2026-08-13)

Evaluación de <https://www.encontradogs.co/> — competidor directo nacido del mismo terremoto ("Mascotas perdidas por el terremoto"), hecho por **Velttora**, que opera un ecosistema de emergencia: `encontrados.co` (personas desaparecidas) y "Help Network" (puntos de ayuda). Volumen observado: ~15 fichas (1 reunido), casi todo Cali/Palmira — nuestra zona Cali sola tiene >250 reportes activos tras la ingesta del Drive.

**Su modelo, distinto al nuestro en tres decisiones de fondo**:

1. **Ficha = mascota, no reporte**. Cada mascota tiene una ficha con atributos estructurados (especie/tamaño/color/raza/sexo/señas/dónde) y una **línea de tiempo de reportes** sobre ella (badge ENCONTRADA + fecha + fuente, "Último reporte: …"). Equivale a nuestro reporte + avistamientos (28), pero su tarjeta compone un **título automático con los atributos** cuando no hay nombre ("Perro mediano Blanco con manchas negras") — mucho más reconocible que nuestro genérico "Perro".
2. **Matching difuso como mecánica central, con score visible**. Dos caras del mismo motor: "**Busca a tu mascota**" (describes especie/color/señas/dónde en texto libre → te rankea los reportes más parecidos; su copy: "las señas particulares son lo que nadie más podría inventar — es lo que más pesa al comparar") y "**¿Es alguna de estas?**" en cada ficha con **porcentaje explícito** ("Se parece en un 57%") ordenando perdidos↔encontrados. Nuestras coincidencias (08) son deterministas (especie+zona+distancia+fecha) y sin score visible; ellos comparan también color/señas en texto libre.
3. **Contacto mediado, no directo**: teléfono y correo "**no se publican**" — quien ve la mascota deja un mensaje con su contacto y ellos lo reenvían al dueño. Verificación liviana por magic link al correo. Es lo opuesto a nuestro WhatsApp directo (ADR 0005): protege datos personales pero mete a un intermediario en el momento más urgente. Nuestro dato de contexto: el archivo comunitario del Drive publica teléfonos abiertamente — la norma cultural de la emergencia es el contacto directo.

**También tienen**: alertas por ficha ("Avísame si hay novedades" con correo — variante concreta de nuestra `22`), 1-3 fotos obligatorias al reportar, páginas `/ideas` y `/bug` para feedback, y un CTA para que albergues/fundaciones "publiquen en lote o integren su sistema" (nosotros ya lo hicimos con el crawler + Drive de Cali).

**Les falta lo que más usamos**: no hay mapa ni zonas (ubicación = texto libre "Caney (por surtifamiliar)"), no hay contacto inmediato, no hay red de apoyo propia (delegan a Help Network), varias fichas sin foto visible, y el feed no tiene filtros.

**Ideas aprovechables (candidatas a backlog, decisión del dueño)**:
- **Búsqueda por descripción** ("busca a tu mascota"): formulario del lado del dueño que rankea reportes por parecido. Se puede hacer **sin AI** con un score de atributos (especie exacta, color del catálogo, tamaño, zona, similitud de texto simple en señas) — sería la evolución natural de la 08 y un puente hacia la 24 (AI).
- **Score visible y explicable en coincidencias** ("coincide en especie, zona y color") — confianza sin cambiar el motor.
- **Título auto-compuesto en tarjetas sin nombre** ("Perro mediano café con blanco") — quick win puro de UI.
- **Alertas por reporte** (correo "avísame si hay novedades de este reporte") — recorta el alcance de la 22 a algo shippeable sin decidir aún el mecanismo por zona.

## 10. Benchmark: Patas en Cali (patitasencali.bolt.host, 2026-08-13)

Tablero comunitario caleño del mismo terremoto (generado con Bolt, sin backend propio visible). Sin cuentas, sin mapa, sin coincidencias, sin alertas ni og por aviso — pero con decisiones de producto que valen la pena:

**Su mecánica central son 4 flujos, no 2**: Perdí / Encontré / **"Necesito ayuda"** (urgencias: rescate, salud, comida) / **"Quiero ayudar"** (ofrezco servicios). Los dos últimos son un tablero de ayuda **entre personas**: "puedo recoger gatitos para hogar de paso", "ofrezco mi casa para animales perdidos", "tengo 2 sacos de comida". Nuestra red de apoyo (§7) solo modela *organizaciones con dirección física* — el particular que ofrece o necesita ayuda puntual no cabe en ella.

**Otras mecánicas observadas**: hasta 3 fotos por aviso con botón "Tomar foto" (cámara directa) además de galería; contacto multicanal opcional (WhatsApp + Instagram + Facebook por aviso); ubicación por comuna de Cali + barrio/referencia en texto; "¿Resuelto?" mediante un código que te dan al publicar (autoría sin cuentas — nosotros ya lo resolvemos con la cuenta liviana); checkbox "mostrar resueltos también"; campo libre de "Logística" ("no se deja agarrar"); y dos **avisos de seguridad** excelentes: al publicar ("este tablero es público, no compartas claves ni cuentas bancarias") y al coordinar encuentros ("nadie debe pedirte dinero; acuerda puntos visibles y ve acompañado; este tablero no verifica los avisos").

**Candidatas a adoptar (decisión del dueño)**:
1. **Tablero de ayuda entre personas** ("necesito ayuda" / "ofrezco ayuda") integrado en /ayudar junto al directorio de organizaciones — la brecha más real: es el tercer flujo de una emergencia y hoy no tiene dónde vivir en la app.
2. **Varias fotos por reporte** (hasta 3): flyer + fotos reales de la mascota (cambio de esquema).
3. **Avisos de seguridad** al publicar y al contactar — puro copy, quick win, y las estafas con recompensas son un riesgo real documentado.
4. **"Tomar foto" con cámara directa** en móvil (atributo `capture` del input) — trivial.
5. Instagram/Facebook opcionales como canales de contacto en reportes manuales (hoy solo teléfono; los crawleados ya enlazan su post).

## 11. Fase 2: la adopción vuelve (features `AD-01`…`AD-08`, 2026-08-16)

**Por qué ahora, y por qué no antes.** El pivot de agosto (ADR 0005) borró la adopción del alcance por una razón correcta: en la semana de un terremoto, lo urgente es reunir a una mascota con su familia, no colocarla en otra. Seis semanas después el dominio de emergencia está completo y desplegado, y aparece el caso que no tenía dónde vivir: **la mascota que nadie reclama**. Un "encontrado" que lleva meses activo no es un reencuentro pendiente, es un animal sin hogar — y el rescatista que lo tiene en casa se queda sin siguiente paso dentro de la app. La adopción es **el final del arco de la emergencia**, no un producto distinto: por eso vive en el mismo repo, con la misma cuenta liviana, las mismas zonas y el mismo contacto por WhatsApp.

**Lo que sí obliga eso**: la emergencia no cede el primer plano. Los dos CTAs de la landing siguen siendo "Perdí a mi mascota" y "Encontré una mascota"; "Adoptar" entra como enlace **terciario** en la landing (hermano del de "Centros de ayuda", sin borde) y como **8.º** enlace de la nav, detrás de los caminos de emergencia. No es una preferencia estética: hay tests que fijan el orden y la ausencia de borde, para que un cambio de copy no convierta la adopción en el tercer CTA sin que salte nada. Tampoco se metió la métrica de adopciones en la franja verde de la landing: ese número significa **reencuentros**, y mezclar dos métricas en una sola franja las vuelve ilegibles.

### Qué se recortó del backlog original, y por qué

- **Apadrinamiento** (`Sponsorship` de la era Adopta). Era la mitad de `AD-07` en el backlog fuente y **no se implementó**. La razón es de producto, no de esfuerzo: **la app no tiene pasarela de pagos ni va a tenerla**, así que "apadrinar" se reduciría a una fila en la base de datos más un botón de WhatsApp — exactamente lo que `Organizacion.como_donar` (texto libre: Nequi, cuenta, link) **ya cubre** desde la red de apoyo, y con más información útil para quien quiere ayudar. Un compromiso registrado que nadie puede cobrar ni verificar es una promesa que la app no puede sostener. Si algún día hay pasarela, el apadrinamiento se rediseña con ADR propio, no se resucita el port.
- **Chat interno** (ADR 0004 de la era Adopta: WebSockets nativos de FastAPI). **Reemplazado por WhatsApp directo, ADR 0013.** El motivo es técnico y es duro: el `ConnectionManager` de aquel ADR es un dict a nivel de módulo, en memoria, y la app corre hoy como **funciones serverless en Vercel** (ADR 0007) — cada request levanta una instancia efímera, no hay proceso persistente, no hay memoria compartida entre invocaciones y ninguna conexión sobrevive a la respuesta. Ahí ese diseño no es "poco escalable": no funciona ni una vez. El propio ADR 0004 había acotado su validez a "un solo proceso `uvicorn` sin `--workers`, que es como corre `dev.sh` hoy", y ese "hoy" se acabó. Además coincide con la decisión de producto que el ADR 0005 §3 ya había tomado para la emergencia: contacto directo, sin chat. Una app de emergencia que obliga a volver a ella para leer un mensaje pierde a la gente; WhatsApp ya está abierto en el teléfono de todo el mundo.

### Backlog: mascotas en la búsqueda por descripción (fuera de alcance a propósito)

La búsqueda por descripción de la **feature 38** (`services/busqueda.py`: el dueño describe a su mascota y la app rankea reportes por parecido explicable, sin AI) **solo mira `reports`**. Sería natural que también encontrara mascotas de `pets` — alguien que busca "perro mediano café" quizá esté a un paso de adoptar a uno igual.

**No se hizo, y la razón es que media integración es peor que ninguna.** Los campos no casan, y se puede comprobar uno por uno: el endpoint **exige** `tipo=perdido|encontrado`, que en `Pet` no significa nada; puntúa `color` con el segundo peso más alto y **`Pet` no tiene columna `color`** (`grep -c color models/pet.py` → 0); busca las "señas" dentro de `descripcion`/`nombre_mascota`/`raza`/`barrio`, cuyo equivalente en `Pet` sería `historia`/`nombre`/`raza`/`barrio` — un mapeo que hay que **decidir**, no adivinar; y la `zona` de un reporte es "dónde se perdió o se vio", mientras la de una mascota es "dónde está disponible". Mezclarlas sin resolver eso daría un porcentaje que **parece** explicable y no lo es, justo lo contrario de lo que la feature 38 promete. Encima el resultado tiene dos destinos distintos: un reporte lleva a "contacta a quien la vio", una mascota a "pide adoptarla". Hacerlo bien exige decidir el peso relativo entre los dos mundos, qué hacer con los campos que no casan y cómo se presenta una lista mezclada — eso es una feature con su plan, y probablemente su ADR. Queda anotado aquí para que se retome como decisión, no como parche.
