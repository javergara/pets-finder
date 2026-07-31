# Ficha de mascota (`/mascota/:id`)

**Alcance:** MVP (`feature_list.json` → `03-pet-profile`). Fuente: `design/prototypes/HANDOFF.md` §5.3.

## Objetivo
Dar toda la información necesaria para decidir, con el score de afinidad siempre explicado.

## Estructura
- Escritorio: dos columnas — galería + historia + salud a la izquierda, tarjeta de acción pegajosa a la derecha.
- Móvil: hero de 330px con carrusel de puntos, contenido debajo, barra de acción fija abajo (`✕` + `Me interesa adoptar`).

## Componentes
- **Galería:** 1 foto principal (4:3) + miniaturas.
- **Su historia:** texto real del refugio (no autogenerado).
- **Salud y cuidados:** esterilizado, vacunas, microchip, desparasitado.
- **Tarjeta de identidad:** nombre, `edad · raza · distancia`.
- **Tarjeta de afinidad:** porcentaje + explicación de por qué (nunca el número solo — ver `docs/decisions/0003-afinidad-calculada-al-vuelo.md`).
- **Chips de carácter.**
- **Tarjeta del refugio:** verificado, nº de adopciones, tiempo de respuesta.
- **Nota de apadrinamiento** (backlog `12-sponsorship`): "si no puedes adoptar, puedes apadrinar".

## Estados
- **Carga:** esqueleto con el radio de la galería (14-16px) y gradiente de placeholder.
- **Mascota ya adoptada mientras estaba en tus matches:** pasa a estado `adoptado`, no se borra la ficha (ver `design/prototypes/HANDOFF.md` §8).
