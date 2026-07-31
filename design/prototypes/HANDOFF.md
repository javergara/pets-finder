# Adopta — Especificación de diseño para implementación

**Producto:** plataforma de adopción de mascotas con descubrimiento tipo "swipe".
**Mercado:** Colombia (Bogotá primero). **Idioma:** español (es-CO). **Moneda:** COP.
**Estado:** prototipo de diseño. No hay backend real; todo lo descrito es el objetivo funcional.

Archivos de diseño en este proyecto:

| Archivo | Contenido |
|---|---|
| `Adopta Web App.dc.html` | Web app completa e interactiva (swipe funcional, 9 pantallas) |
| `Adopta Mobile.dc.html` | 10 pantallas móviles (402×874) en frame de iPhone |
| `Adopta Landing.dc.html` | Página de marketing pública |

---

## 1. Decisiones de producto ya tomadas

1. **El match no es mutuo.** Cuando el adoptante desliza a la derecha, el match se crea de inmediato: la mascota entra en "Mis matches", se abre un chat y el refugio recibe la solicitud con el cuestionario adjunto. El refugio no "acepta" para que exista el match; acepta o rechaza la **solicitud de adopción**, que es un paso posterior.
2. **El cuestionario de hogar es obligatorio** antes de ver el primer perfil. Es el freno ético del producto y la entrada del cálculo de afinidad.
3. **No se usa lenguaje de descarte.** Izquierda = "Ahora no", nunca "rechazar"/"nope". El copy aclara que la mascota sigue disponible para otros.
4. **La adopción no se cierra en la app.** Siempre hay visita presencial coordinada por chat. La app solo llega hasta "visita agendada".
5. **Sin costo ni comisión** para adoptantes y refugios. La monetización explorable es el apadrinamiento (donación recurrente), no la adopción.
6. **Tono institucional y calmado**, no lúdico. Nada de emoji, confeti ni gamificación de la adopción.

---

## 2. Roles

- **Adoptante** — descubre, hace match, chatea, apadrina.
- **Refugio / rescatista** (verificado) — publica mascotas, revisa solicitudes, agenda visitas, cierra adopciones, publica campañas de apadrinamiento.
- **Admin de plataforma** (fuera del alcance del prototipo) — verifica refugios, modera reportes.

---

## 3. Sistema visual

### Color

| Token | Hex | Uso |
|---|---|---|
| `bg` | `#F7F3EA` | fondo de página |
| `surface` | `#FFFDF8` | tarjetas, barras, campos |
| `surface-alt` | `#F3EDE0` | encabezados de tabla, avisos neutros |
| `ink` | `#1B1A17` | texto principal |
| `ink-soft` | `#3D3931` | párrafos largos |
| `muted` | `#6B665C` | texto secundario |
| `muted-2` | `#8A8172` | etiquetas mono, placeholders |
| `line` | `#E4DDCE` | bordes |
| `line-soft` | `#EFE9DC` | separadores internos |
| `forest` | `#1F4D3A` | acento primario, botones, activos |
| `forest-hover` | `#2E6E52` | hover del primario |
| `forest-tint` | `#E8EFE9` | fondos de acento (chips, cards de afinidad) |
| `forest-tint-line` | `#CFDFD3` | borde sobre `forest-tint` |
| `ochre` | `#B57C2E` | avisos, "ahora no", estados en espera |
| `danger` | `#9B3B2E` | acciones destructivas |

Sobre fondo verde (`forest`) el texto es `#F7F3EA`, el secundario `#C3D8CB`, las etiquetas mono `#A8C6B4` y los bordes `#4A8468`.

### Tipografía

- **Newsreader** (serif, 400/500) — titulares, nombres de mascota, cifras grandes. `letter-spacing: -0.015em` a `-0.025em` según el tamaño.
- **Work Sans** (400/500/600) — toda la interfaz y los párrafos.
- **IBM Plex Mono** (400/500) — etiquetas de sección en mayúsculas (`11px`, `letter-spacing: .06em`), badges numéricos, metadatos.

Escala usada: display 66/44/40/38 · título de pantalla 30/26 · subtítulo 20-24 · cuerpo 14.5-16 · secundario 12.5-13.5 · etiqueta mono 11-11.5. Mínimo absoluto en móvil: 12px, y ningún control táctil por debajo de 44px.

### Forma y profundidad

Radios: 8-11px controles · 14-16px tarjetas · 20-22px tarjeta de swipe y hojas inferiores · 9999px chips y avatares.
Bordes de 1px `line` en lugar de sombras. La única sombra del sistema es la de la tarjeta activa de swipe: `0 18px 40px -28px rgba(27,26,23,.5)`.
Espaciado en múltiplos de 4; gutter de página 22px en móvil, 32-56px en escritorio.

### Imágenes

En el prototipo todas las fotos son placeholders: `repeating-linear-gradient(135deg, #EDE6D8 0 10px, #E4DBCA 10px 20px)` con una etiqueta mono `foto · <nombre>`. Al implementar, sustituir por la foto real manteniendo el mismo radio y proporción (4:3 en grillas, 3:4 en la tarjeta de swipe).

---

## 4. Arquitectura de información

**Web app (escritorio)** — barra lateral fija de 264px:
`Descubrir · Mis matches (contador) · Mensajes (punto de no leídos) · Apadrinar` — separador — `Mi perfil · Cuestionario de hogar · Ajustes` — separador — `Panel del refugio` (solo si la cuenta tiene rol refugio). Pie con avatar y ciudad del usuario.

**Móvil** — barra de pestañas inferior de 4: `Descubrir · Matches · Mensajes · Perfil`. Apadrinar y Ajustes cuelgan de Perfil. Filtros es una hoja inferior sobre Descubrir.

**Público (landing)** — nav: Cómo funciona · Para refugios · Apadrinar · Entrar a la app.

---

## 5. Pantallas

### 5.1 Cuestionario de hogar (`/cuestionario`)
Seis pasos, una pregunta por paso, barra de progreso y contador `Paso N de 6`. Bloquea `/descubrir` hasta completarse.

Preguntas: (1) tipo de vivienda y espacio exterior; (2) personas en casa y edades / si hay niños; (3) rutina diaria — horas fuera de casa; (4) otras mascotas actuales; (5) experiencia previa y presupuesto mensual estimado; (6) qué tipo de compañía busca (energía, tamaño, especie).

Cada paso: opciones como tarjetas radio de altura ≥56px, seleccionada con fondo `forest-tint` y borde `forest`. Debajo, un aviso en `surface-alt` recordando que la honestidad evita devoluciones. Pie con `Atrás` (secundario) y `Continuar` (primario, ancho flexible).

Editable después desde Mi perfil; al editarlo se recalculan todas las afinidades.

### 5.2 Descubrir (`/descubrir`)
Columna central con la baraja + carril derecho de filtros (escritorio) / hoja inferior (móvil).

**Baraja:** tres capas. Las dos de atrás son rectángulos vacíos con `translateY(11px) scale(.97)` y `translateY(22px) scale(.94)`. La de arriba es la tarjeta interactiva, 420×560 en escritorio y ancho completo menos 44px en móvil.

**Tarjeta:** foto (flex:1) con badges superiores izquierdos — `NN% afín` (fondo `forest`) y `N,N km` (fondo `surface`, borde) — y contador de fotos abajo a la derecha. Bloque inferior: nombre (Newsreader 25-27px) + `edad · raza` en `muted`; fila de chips de personalidad (máx. 3 visibles) en `forest-tint`; pie separado por línea con el nombre del refugio y el botón `Ver ficha`.

**Gestos:** arrastre con Pointer Events. `translateX(dx) rotate(dx/22)`. Umbral ±110px. Sellos "Me interesa" (verde, arriba a la derecha, `rotate(-8deg)`) y "Ahora no" (ocre, arriba a la izquierda, `rotate(8deg)`) con `opacity = clamp(|dx|/110)`. Al soltar sin superar el umbral, vuelve con `transform .28s cubic-bezier(.2,.8,.3,1)`. Teclado: `←`/`→` y `Enter` para abrir ficha; los botones inferiores (✕ 56px, `i` 46px, ♥ 56px) hacen lo mismo que el gesto y son la ruta accesible obligatoria.

**Filtros:** especie · tamaño · distancia (slider, por defecto 15 km) · edad · nivel de energía · convivencia (niños / perros / gatos, toggles). Chips multi-selección: activo = fondo `forest` texto claro; inactivo = `surface` con borde. Los filtros se aplican al instante y actualizan el contador `N perfiles cerca de ti`. Botón `Restablecer filtros`.

**Fin de baraja:** estado vacío que sugiere ampliar el radio o quitar filtros, y ofrece "Avísame cuando lleguen nuevos perfiles".

### 5.3 Ficha de mascota (`/mascota/:id`)
Escritorio: dos columnas (galería + historia + salud a la izquierda; tarjeta de acción pegajosa a la derecha). Móvil: hero de 330px con carrusel de puntos, contenido y barra de acción fija abajo (`✕` + `Me interesa adoptar`).

Bloques: galería (1 principal 4:3 + miniaturas), **Su historia** (texto real del refugio, no autogenerado), **Salud y cuidados** (esterilizado, vacunas, microchip, desparasitado), tarjeta de identidad (nombre, `edad · raza · distancia`), tarjeta de afinidad con el porcentaje y la explicación de por qué, chips de carácter, acciones, tarjeta del refugio (verificado, nº de adopciones, tiempo de respuesta) y una nota que ofrece apadrinar si no puede adoptar.

### 5.4 Match (modal / pantalla completa en móvil)
Se dispara al deslizar a la derecha o pulsar `Me interesa adoptar`. Escritorio: modal de 420px sobre `rgba(27,26,23,.42)`, animación `popIn .24s cubic-bezier(.2,.8,.3,1)`. Móvil: pantalla completa en `forest`.
Contenido: etiqueta mono `Nuevo match`, foto circular, titular `Te interesa <Nombre>`, explicación de que se envió el perfil y el cuestionario al refugio con su tiempo de respuesta, y dos acciones: `Escribir al refugio` (primaria) y `Seguir viendo perfiles`.

### 5.5 Mis matches (`/matches`)
Filtros de estado: Todos · Esperando refugio · Visita agendada. Escritorio: grilla `minmax(228px,1fr)`. Móvil: lista horizontal con miniatura 76px.
Cada tarjeta: foto, badge de afinidad, nombre, `edad · raza`, punto de estado (`forest` = visita agendada, `ochre` = esperando/en revisión) con su texto, y `Abrir conversación`.
Estado vacío con enlace a Descubrir.

### 5.6 Mensajes (`/mensajes`)
Escritorio: lista de conversaciones de 320px + hilo. Móvil: lista y hilo como pantallas separadas.
Cabecera del hilo: avatar del refugio, nombre, `Conversación sobre <Mascota>`, atajo `Ver ficha`.
Primer elemento del hilo: aviso del sistema explicando por qué se abrió la conversación y recordando la visita previa a la entrega.
Burbujas: propias en `forest` con texto claro y radio `14 14 4 14`; del refugio en `surface` con borde y radio `14 14 14 4`; máx. 62% de ancho en escritorio, 76% en móvil.
Respuestas rápidas sugeridas (`Sí, agendar` / `Proponer otra hora`) cuando el refugio propone una cita.
Compositor: campo + botón `Enviar` (escritorio) o botón circular `↑` (móvil).

### 5.7 Apadrinar (`/apadrinar`)
Tres niveles: $30.000 (alimento), $70.000 (alimento + veterinario, destacado) y monto libre; todos mensuales, con opción de pago único.
Lista "Necesitan apoyo ahora": foto, nombre, necesidad concreta, barra de progreso `forest` sobre `#EFE9DC` y `NN% cubierto`, botón `Apadrinar`.
Tras apadrinar: novedad mensual con foto en el perfil del padrino.

### 5.8 Mi perfil (`/perfil`)
Cabecera con avatar 82px, nombre, `ciudad · barrio · miembro desde`, insignias (`Identidad verificada`, `Cuestionario completo`) y `Editar`.
Tres métricas: matches activos, visitas agendadas, apadrinamientos.
Tarjeta **Mi hogar**: resumen en dos columnas de las respuestas del cuestionario (vivienda, espacio exterior, personas, niños, otras mascotas, horas fuera). Tarjeta **Sobre mí** con texto libre que el refugio ve al recibir la solicitud.

### 5.9 Ajustes (`/ajustes`)
Grupos con etiqueta mono en mayúsculas y tarjeta de filas separadas por `line-soft`:
- **Cuenta** — correo, teléfono (enmascarado), ciudad.
- **Notificaciones** — nuevos perfiles cerca (máx. uno al día), respuestas del refugio (push y correo), campañas de donación (resumen mensual).
- **Privacidad** — mostrar el barrio al refugio solo tras el match; descargar mis datos.
- Acciones: cerrar sesión; eliminar cuenta (`danger`).

### 5.10 Panel del refugio (`/refugio`)
Cabecera con nombre del refugio, `N mascotas publicadas` y botón `Publicar mascota`.
Cuatro métricas: interesados este mes, visitas agendadas, adopciones cerradas, apadrinamientos recaudados (COP).
Tabla **Solicitudes por revisar**: adoptante · mascota · afinidad · estado · `Revisar`. Estados: `Cuestionario nuevo`, `Visita agendada`, `Sin responder · N días` (alerta en `ochre` a partir de 2 días).
Al abrir `Revisar`: cuestionario completo del adoptante, su texto "Sobre mí", y acciones `Agendar visita` / `Pedir más información` / `Descartar con motivo` (el motivo es obligatorio y no se muestra al adoptante en crudo).

### 5.11 Landing pública
Hero con propuesta de valor y baraja de tarjetas inclinadas; tres cifras de credibilidad. `Cómo funciona` en cuatro pasos. Sección argumentativa sobre por qué el cuestionario va primero. Franja verde de apadrinamiento. Sección para refugios con vista previa del panel. Pie.

---

## 6. Modelo de datos (mínimo)

```
User        id, nombre, email, teléfono, ciudad, barrio, avatar, bio,
            rol ('adoptante'|'refugio'), verificado, creadoEn
HomeProfile userId, vivienda, espacioExterior, personas, niños,
            otrasMascotas[], horasFuera, experiencia, presupuestoMensual,
            preferencias{especie[], tamaño[], energía}, completadoEn
Shelter     id, nombre, ciudad, verificado, adopcionesCerradas,
            tiempoRespuestaHoras, logo
Pet         id, shelterId, nombre, especie, raza, sexo, edadMeses, tamaño,
            energía, fotos[], historia, tags[],
            salud{esterilizado, vacunas, microchip, desparasitado},
            aptoNiños, aptoPerros, aptoGatos, ubicación{lat,lng},
            estado ('disponible'|'en_proceso'|'adoptado'), publicadoEn
Swipe       userId, petId, dirección ('like'|'pass'), creadoEn
Match       id, userId, petId, shelterId,
            estado ('solicitado'|'en_revision'|'visita_agendada'|'adoptado'|'cerrado'),
            afinidad, creadoEn
Thread      id, matchId, participantes[], últimoMensajeEn
Message     id, threadId, autorId|'sistema', texto, adjuntos[], leídoEn
Sponsorship id, userId, petId, montoCOP, periodicidad, activo, iniciadoEn
```

## 7. Cálculo de afinidad

Porcentaje entero 0-100, calculado al vuelo entre `HomeProfile` y `Pet`. Ponderación sugerida para el prototipo:

- Energía de la mascota vs. horas fuera y rutina — 30%
- Tamaño vs. tipo de vivienda y espacio exterior — 20%
- Convivencia (niños / otros perros / gatos declarados) — 20%
- Preferencia declarada de especie y tamaño — 15%
- Experiencia previa y presupuesto vs. necesidades de cuidado — 15%

Reglas duras: si la mascota no es apta con niños y hay niños en casa, o no es apta con gatos y hay gato en casa, se marca **incompatible** y no entra en la baraja (visible solo por búsqueda directa, con aviso).
El porcentaje siempre se acompaña de una frase que lo explique ("energía media que encaja con tus 6-8 horas fuera"), nunca aparece solo.
Ordenamiento de la baraja: afinidad descendente, con inserción periódica de mascotas difíciles de ubicar (senior, con condición médica, >90 días publicadas) cada 4-5 tarjetas.

## 8. Estados y casos límite

- Cuestionario incompleto → `/descubrir` redirige al paso pendiente.
- Sin resultados con los filtros actuales → estado vacío con acciones para ampliar radio o limpiar filtros.
- Fin de la baraja → estado vacío con aviso opt-in de nuevos perfiles.
- Mascota adoptada mientras estaba en tus matches → la tarjeta pasa a estado `adoptado` con mensaje del sistema en el hilo; no se borra.
- Refugio sin responder en 3 días → aviso al adoptante de que puede seguir explorando; nunca se culpa al refugio.
- Sin matches / sin mensajes / sin apadrinamientos → estados vacíos propios, todos con una acción concreta.
- Carga: esqueletos con los mismos radios y el gradiente de placeholder, sin spinners.
- Errores de red en el swipe: se encolan localmente y se reintentan; el gesto nunca se bloquea.

## 9. Accesibilidad

- Toda acción de gesto tiene un botón equivalente y navegación por teclado (`←` `→` `Enter` `Esc`).
- Contraste mínimo AA: `forest` sobre `bg` y `ink` sobre `surface` cumplen; no usar `muted-2` para texto menor de 11px sobre fondos con textura.
- Placeholders de foto con `alt` descriptivo real al conectar imágenes.
- `prefers-reduced-motion`: desactivar `popIn` del match y la rotación de la tarjeta; el swipe pasa a transición de opacidad.
- Objetivos táctiles ≥44px; los chips de filtro en móvil miden 38-42px de alto con 44px de área efectiva.

## 10. Recomendación técnica y orden de construcción

React + TypeScript, Vite, Tailwind (mapear la tabla de color de §3 a tokens), React Router, Zustand o TanStack Query para estado remoto, Framer Motion para el swipe (o Pointer Events crudos como en el prototipo, que ya es suficiente), Supabase o Firebase para auth/DB/storage/realtime del chat. Mobile: responsive web (PWA) primero; el diseño móvil de este proyecto es esa misma web app a 402px.

Orden sugerido: (1) auth y cuestionario; (2) modelo de datos y seed de mascotas; (3) baraja de swipe con afinidad; (4) ficha y match; (5) matches y chat en tiempo real; (6) panel del refugio y publicación de mascotas; (7) apadrinamiento; (8) ajustes, notificaciones y estados vacíos; (9) landing.

## 11. Fuera del alcance de este prototipo

Pasarela de pagos real, verificación de identidad, contrato de adopción digital, transporte, seguimiento post-adopción, moderación y reportes, y la app nativa. Todos están previstos en el modelo pero no diseñados.
