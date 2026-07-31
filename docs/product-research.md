# Investigación de producto — Adopta

> Fuente primaria: `design/prototypes/HANDOFF.md` (spec de diseño ya elaborada en una sesión previa con DesignSync, incluidos prototipos interactivos). Este documento **formaliza** esas decisiones de producto para consumo del harness (feature list, arquitectura, tests), y añade el análisis complementario que pedía el prompt original (validación de pantallas, flujo de adopción real, encaje del scoring).

## 1. Producto y mercado

**Adopta** conecta adoptantes con mascotas en adopción de refugios/rescatistas verificados, usando un descubrimiento tipo swipe pero optimizado para **compatibilidad real de convivencia**, no para volumen de "matches". Mercado inicial: Colombia, Bogotá primero. Idioma único: es-CO. Moneda: COP.

Esto es una desviación deliberada de un Tinder-de-mascotas genérico: el objetivo de negocio no es maximizar "likes" sino minimizar devoluciones de mascotas por incompatibilidad de hogar, así que varias mecánicas típicas de dating apps se descartan a propósito (ver §3).

## 2. Roles

- **Adoptante** — completa un cuestionario de hogar, descubre mascotas, hace match, conversa con el refugio, opcionalmente apadrina.
- **Refugio / rescatista** (cuenta verificada) — publica mascotas, revisa solicitudes con el cuestionario adjunto, agenda visitas, cierra adopciones, publica campañas de apadrinamiento.
- **Admin de plataforma** — fuera de alcance del prototipo y del MVP; solo mencionado como rol futuro (verificación de refugios, moderación de reportes).

## 3. Decisiones de mecánica ya tomadas (y por qué se mantienen)

| Decisión | Qué significa | Por qué (no es solo estética) |
|---|---|---|
| **El match no es mutuo** | Deslizar a la derecha crea el match de inmediato: la mascota entra a "Mis matches", se abre chat, el refugio recibe la solicitud con el cuestionario. | El refugio no tiene poder de veto sobre el *match* — solo sobre la *solicitud de adopción*, un paso posterior. Modela correctamente que el "like" del adoptante es una manifestación de interés, no una promesa de adopción; evita fricción y confusión de "por qué no me hicieron match" que sí tiene sentido en dating pero no en adopción. |
| **Cuestionario de hogar obligatorio** antes de la primera ficha | Bloquea `/descubrir` hasta completarlo. | Es el freno ético del producto y el input obligatorio del cálculo de afinidad — sin datos de hogar no hay score, y sin score el descubrimiento pierde su propuesta de valor central. |
| **Sin lenguaje de descarte** | Izquierda = "Ahora no", nunca "rechazar"/"nope". | La mascota sigue disponible para otros; el copy no debe sugerir que el animal fue juzgado y descartado. |
| **La adopción no se cierra en la app** | El flujo llega hasta "visita agendada"; la entrega siempre es presencial y coordinada por chat. | Evita responsabilidad legal/operativa de gestionar entregas reales y refleja cómo funcionan los refugios reales (entrevista + visita previas). |
| **Sin comisión** | Gratis para adoptantes y refugios; monetización explorable vía apadrinamiento (donación recurrente). | Cobrar por adopción desalinea incentivos (presión a "cerrar" adopciones) y es contrario a cómo operan los refugios sin ánimo de lucro que serían los primeros usuarios reales. |
| **Tono institucional, no lúdico** | Sin emoji, confeti ni gamificación de la adopción. | La app maneja decisiones de bienestar animal; la gamificación de un "match" con una mascota reforzaría exactamente el comportamiento impulsivo que causa devoluciones. |

## 4. Flujo de adopción de extremo a extremo

```
Registro → Cuestionario de hogar (6 pasos, obligatorio)
   → Descubrir (swipe con afinidad visible)
      → like → Match inmediato (mascota a "Mis matches", chat abierto,
                refugio recibe solicitud + cuestionario)
         → Refugio revisa solicitud → agenda visita / pide más info / descarta con motivo
            → Visita agendada (fin del alcance de la app)
               → (fuera de la app) entrevista presencial, entrega, seguimiento
```

El "descarte con motivo" por parte del refugio es privado (el motivo no se muestra al adoptante en crudo) para evitar fricción, pero permite que la app registre por qué una solicitud no avanzó — dato valioso para mejorar el score de afinidad a futuro.

## 5. Compatibilidad adoptante↔mascota

Se calcula al vuelo entre `HomeProfile` y `Pet`, no se persiste como columna (cambia si cualquiera de los dos cambia). Ponderación (ver detalle de reglas en `docs/decisions/`):

- Energía de la mascota vs. horas fuera y rutina — 30%
- Tamaño vs. tipo de vivienda y espacio exterior — 20%
- Convivencia declarada (niños / otros perros / gatos) — 20%
- Preferencia declarada de especie y tamaño — 15%
- Experiencia previa y presupuesto vs. necesidades de cuidado — 15%

**Reglas duras** (no son parte del score, son un filtro previo): si la mascota no es apta con niños y el hogar declara niños, o no es apta con gatos y el hogar declara gato, la pareja se marca **incompatible** y no entra en la baraja de descubrimiento (queda visible solo por búsqueda directa, con aviso).

El score siempre se acompaña de una frase explicativa ("energía media que encaja con tus 6-8 horas fuera"); nunca se muestra un número sin justificación — esto es un requisito de producto, no solo de copy, porque el score es lo que hace confiable la mecánica de swipe (sin esto sería indistinguible de un Tinder genérico).

Orden de la baraja: afinidad descendente, con inserción periódica (cada 4-5 tarjetas) de mascotas difíciles de ubicar (senior, con condición médica, >90 días publicada) — evita que el algoritmo de afinidad esconda sistemáticamente a los animales que más necesitan visibilidad.

## 6. Pantallas — validación de cobertura

`HANDOFF.md` ya especifica 11 pantallas con wireframe, componentes y estados vacío/carga/error. Se validan como completas para el alcance del producto (adoptante + refugio + público):

1. Cuestionario de hogar (`/cuestionario`)
2. Descubrir / baraja de swipe (`/descubrir`)
3. Ficha de mascota (`/mascota/:id`)
4. Modal/pantalla de match
5. Mis matches (`/matches`)
6. Mensajes (`/mensajes`)
7. Apadrinar (`/apadrinar`)
8. Mi perfil (`/perfil`)
9. Ajustes (`/ajustes`)
10. Panel del refugio (`/refugio`)
11. Landing pública

No se identifican pantallas faltantes para el alcance definido. Explícitamente fuera de alcance (§11 de HANDOFF.md, confirmado aquí): pasarela de pagos real, verificación de identidad, contrato de adopción digital, transporte, seguimiento post-adopción, moderación/reportes, app nativa. Éstas implican integraciones de terceros o procesos legales que no aportan al objetivo del MVP (demostrar la mecánica de descubrimiento con afinidad real).

## 7. Alcance del MVP vs. backlog

El MVP (Fase 7 del proyecto) cubre **solo** la porción de este flujo que no depende de autenticación real, chat en tiempo real, ni integraciones externas: fundaciones de datos, deck de swipe con afinidad, ficha de mascota, matches (creación no-mutua al hacer like) y el cálculo de score. El cuestionario de hogar se resuelve en el MVP con `HomeProfile` sintético por adoptante semilla (no hay registro ni UI de cuestionario interactivo todavía) — el gate y el formulario de 6 pasos quedan en backlog como "Onboarding". Mensajería, panel de refugio, apadrinamiento y landing pública quedan en backlog completo. Detalle y criterios de aceptación en `feature_list.json`.

## 8. Modelo de datos (referencia)

Ver `feature_list.json` y `docs/architecture.md` para el detalle técnico; el modelo conceptual (`User`, `HomeProfile`, `Shelter`, `Pet`, `Swipe`, `Match`, `Thread`, `Message`, `Sponsorship`) es el definido en `design/prototypes/HANDOFF.md` §6, sin cambios — ya está pensado correctamente para soportar match no-mutuo (tabla `Swipe` separada de `Match`) y afinidad calculada al vuelo (no persistida).
