import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { Mascota } from '../api/types';
import { MascotaSwipeCard } from './MascotaSwipeCard';

// Las tres rutas de la tarjeta —botones, teclado y gesto— se prueban por
// separado porque son **equivalentes**, no alternativas: quien no puede
// arrastrar (teclado, lector de pantalla, motricidad reducida) tiene que poder
// hacer exactamente lo mismo. Si una se rompe, el deck deja fuera a alguien.
//
// ⚠️ Lo que jsdom hace de verdad aquí, medido en esta corrida (2026-08-15) y no
// asumido: `PointerEvent` **sí** existe y `fireEvent.pointerDown(el, {clientX})`
// **sí** transporta `clientX` y `pointerId`, así que los gestos se disparan con
// `fireEvent` normal, sin construir el evento a mano. Lo que **no** existe es
// `Element.setPointerCapture` (`typeof` da `undefined`), y por eso el componente
// lo llama con `?.`: sin la guarda, cada `pointerdown` lanza un `TypeError` que
// React reporta por consola (comprobado — la suite sigue en verde porque la
// llamada va después de guardar el inicio del arrastre, pero deja cuatro errores
// escupidos en cada corrida).
//
// El test de `adopta-v1` no ejercitaba el drag por otra razón, más simple: solo
// disparaba `pointerdown` sobre el corazón y nunca un `pointermove`/`pointerup`.
// Aquí el caso bajo umbral asevera además el `translateX(40px)` intermedio: sin
// eso pasaría igual con un `clientX` que llegara en 0 (dx=0 tampoco decide),
// es decir, por la razón equivocada.

const UMBRAL_PX = 110;

function mascota(overrides: Partial<Mascota> = {}): Mascota {
  return {
    id: 7,
    organizacion_id: 2,
    user_id: null,
    report_id: null,
    nombre: 'Canela',
    especie: 'perro',
    raza: 'Cocker mestiza',
    sexo: 'hembra',
    edad_meses: 5,
    tamano: 'mediano',
    energia: 'media',
    fotos: ['/media/seed/pet_7.jpg'],
    historia: 'Rescatada en Armenia tras el sismo.',
    tags: ['cariñosa', 'tranquila'],
    esterilizado: true,
    vacunas_al_dia: true,
    microchip: false,
    desparasitado: true,
    apto_ninos: true,
    apto_perros: true,
    apto_gatos: false,
    zona: 'Armenia',
    ciudad_texto: null,
    barrio: 'Providencia',
    lat: 4.53,
    lng: -75.68,
    telefono_contacto: null,
    estado: 'disponible',
    publicado_en: '2026-08-14T10:00:00',
    adoptado_en: null,
    publicador: {
      tipo: 'organizacion',
      id: 2,
      nombre: 'Fundación Patitas',
      telefono_contacto: '3001112233',
      zona: 'Armenia',
      ciudad_texto: null,
      barrio: 'Providencia',
      foto_url: null,
    },
    afinidad: {
      score: 94,
      explicacion: 'Buena combinación con tu hogar.',
      razones: [
        'Energía media, como buscas',
        'Tamaño adecuado para tu casa',
        'Le va bien con niños',
      ],
      incompatible: false,
    },
    es_favorito: false,
    ya_solicitada: false,
    distancia_km: null,
    ...overrides,
  };
}

/** Arrastra la tarjeta `pixeles` px desde el reposo y suelta. */
function arrastrar(tarjeta: HTMLElement, pixeles: number) {
  fireEvent.pointerDown(tarjeta, { clientX: 0, pointerId: 1 });
  fireEvent.pointerMove(tarjeta, { clientX: pixeles, pointerId: 1 });
  fireEvent.pointerUp(tarjeta, { clientX: pixeles, pointerId: 1 });
}

// --- Ruta 1: los botones -------------------------------------------------------

describe('MascotaSwipeCard — botones', () => {
  it('"Me interesa" y "Ahora no" son las dos direcciones del swipe', () => {
    const onSwipe = vi.fn();
    render(<MascotaSwipeCard mascota={mascota()} onSwipe={onSwipe} onAbrirFicha={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: 'Me interesa' }));
    fireEvent.click(screen.getByRole('button', { name: 'Ahora no' }));

    expect(onSwipe).toHaveBeenNthCalledWith(1, 'like');
    expect(onSwipe).toHaveBeenNthCalledWith(2, 'pass');
  });

  it('"Ver ficha" abre la ficha y no cuenta como swipe', () => {
    const onSwipe = vi.fn();
    const onAbrirFicha = vi.fn();
    render(<MascotaSwipeCard mascota={mascota()} onSwipe={onSwipe} onAbrirFicha={onAbrirFicha} />);

    fireEvent.click(screen.getByRole('button', { name: 'Ver ficha' }));

    expect(onAbrirFicha).toHaveBeenCalledOnce();
    expect(onSwipe).not.toHaveBeenCalled();
  });

  it('el copy nunca dice "rechazar": el match no es mutuo (ADR 0002)', () => {
    render(<MascotaSwipeCard mascota={mascota()} onSwipe={vi.fn()} onAbrirFicha={vi.fn()} />);

    expect(screen.queryByText(/rechaz/i)).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Ahora no' })).toBeInTheDocument();
  });
});

// --- Ruta 2: el teclado --------------------------------------------------------

describe('MascotaSwipeCard — teclado', () => {
  it('las flechas y Enter hacen lo mismo que el gesto, sobre el role="group"', () => {
    const onSwipe = vi.fn();
    const onAbrirFicha = vi.fn();
    render(<MascotaSwipeCard mascota={mascota()} onSwipe={onSwipe} onAbrirFicha={onAbrirFicha} />);
    const tarjeta = screen.getByRole('group');

    fireEvent.keyDown(tarjeta, { key: 'ArrowRight' });
    fireEvent.keyDown(tarjeta, { key: 'ArrowLeft' });
    fireEvent.keyDown(tarjeta, { key: 'Enter' });

    expect(onSwipe).toHaveBeenNthCalledWith(1, 'like');
    expect(onSwipe).toHaveBeenNthCalledWith(2, 'pass');
    expect(onAbrirFicha).toHaveBeenCalledOnce();
  });

  it('la tarjeta es alcanzable con Tab y se anuncia con el nombre de la mascota', () => {
    render(<MascotaSwipeCard mascota={mascota()} onSwipe={vi.fn()} onAbrirFicha={vi.fn()} />);

    const tarjeta = screen.getByRole('group');
    expect(tarjeta).toHaveAttribute('tabindex', '0');
    expect(tarjeta).toHaveAccessibleName(/Canela/);
  });

  it('las teclas de la tarjeta no se disparan desde los botones de dentro', () => {
    const onSwipe = vi.fn();
    const onAbrirFicha = vi.fn();
    render(<MascotaSwipeCard mascota={mascota()} onSwipe={onSwipe} onAbrirFicha={onAbrirFicha} />);

    // Enter sobre "Me interesa" ya lo activa el navegador: sin el guard de
    // `target === currentTarget`, el mismo Enter subiría a la tarjeta y abriría
    // además la ficha (un swipe y una navegación con una sola tecla).
    fireEvent.keyDown(screen.getByRole('button', { name: 'Me interesa' }), { key: 'Enter' });

    expect(onAbrirFicha).not.toHaveBeenCalled();
    expect(onSwipe).not.toHaveBeenCalled();
  });
});

// --- Ruta 3: el gesto ----------------------------------------------------------

describe('MascotaSwipeCard — gesto', () => {
  it('arrastrar a la derecha más allá del umbral es "me interesa"', () => {
    const onSwipe = vi.fn();
    render(<MascotaSwipeCard mascota={mascota()} onSwipe={onSwipe} onAbrirFicha={vi.fn()} />);

    arrastrar(screen.getByRole('group'), 160);

    expect(onSwipe).toHaveBeenCalledExactlyOnceWith('like');
  });

  it('arrastrar a la izquierda más allá del umbral es "ahora no"', () => {
    const onSwipe = vi.fn();
    render(<MascotaSwipeCard mascota={mascota()} onSwipe={onSwipe} onAbrirFicha={vi.fn()} />);

    arrastrar(screen.getByRole('group'), -160);

    expect(onSwipe).toHaveBeenCalledExactlyOnceWith('pass');
  });

  it('un arrastre corto no decide nada y la tarjeta vuelve a su sitio', () => {
    const onSwipe = vi.fn();
    render(<MascotaSwipeCard mascota={mascota()} onSwipe={onSwipe} onAbrirFicha={vi.fn()} />);
    const tarjeta = screen.getByRole('group');

    fireEvent.pointerDown(tarjeta, { clientX: 0, pointerId: 1 });
    fireEvent.pointerMove(tarjeta, { clientX: 40, pointerId: 1 });

    // El estado intermedio se asevera a propósito: prueba que el `clientX` del
    // evento llegó de verdad. Sin esto, un `clientX` que llegara en 0 dejaría el
    // test verde por la razón equivocada (dx=0 tampoco llama a nadie).
    expect(tarjeta.style.transform).toContain('translateX(40px)');
    expect(40).toBeLessThan(UMBRAL_PX);

    fireEvent.pointerUp(tarjeta, { clientX: 40, pointerId: 1 });

    expect(onSwipe).not.toHaveBeenCalled();
    expect(tarjeta.style.transform).toContain('translateX(0px)');
  });

  it('si el navegador cancela el puntero, la tarjeta vuelve y NO decide nada', () => {
    const onSwipe = vi.fn();
    render(<MascotaSwipeCard mascota={mascota()} onSwipe={onSwipe} onAbrirFicha={vi.fn()} />);
    const tarjeta = screen.getByRole('group');

    fireEvent.pointerDown(tarjeta, { clientX: 0, pointerId: 1 });
    fireEvent.pointerMove(tarjeta, { clientX: 200, pointerId: 1 });
    fireEvent.pointerCancel(tarjeta, { clientX: 200, pointerId: 1 });

    // `adopta-v1` mandaba `pointercancel` al mismo `soltar` que `pointerup`, así
    // que un gesto que el navegador aborta (se lo lleva un scroll, entra una
    // llamada) contaba como decisión. Aquí no: el swipe saca la carta del deck y
    // no hay vuelta atrás, así que un gesto abortado se descarta entero.
    expect(onSwipe).not.toHaveBeenCalled();
    expect(tarjeta.style.transform).toContain('translateX(0px)');
  });
});

// --- Captura del puntero: por qué NO se hace al presionar ----------------------
//
// ⚠️ Bug real, encontrado en el recorrido manual de AD-03 con Chrome 151 (no en
// jsdom, que ni implementa `setPointerCapture`): capturando el puntero en el
// `pointerdown` —como hacía `adopta-v1`— el navegador redirige el `pointerup` **y
// el `click`** al elemento que capturó. Medido por CDP sobre el deck real: al
// pulsar "Me interesa" el `click` llegaba al `role="group"` y NUNCA al botón, así
// que los tres botones de la tarjeta estaban MUERTOS con ratón y con dedo —
// funcionaban solo el teclado y el gesto, justo las dos rutas que no usa la
// mayoría. Por eso la captura se pide en el primer `pointermove` que supera
// `INICIO_ARRASTRE_PX`: un click nunca captura nada.

describe('MascotaSwipeCard — captura del puntero', () => {
  const capturar = vi.fn();

  beforeEach(() => {
    capturar.mockClear();
    // jsdom no trae `setPointerCapture`; se define para poder aseverar CUÁNDO se
    // llama, que es lo único que distingue el bug del arreglo.
    (Element.prototype as unknown as Record<string, unknown>).setPointerCapture = capturar;
  });

  afterEach(() => {
    delete (Element.prototype as unknown as Record<string, unknown>).setPointerCapture;
  });

  it('presionar sin mover NO captura el puntero: el click tiene que llegar al botón', () => {
    render(<MascotaSwipeCard mascota={mascota()} onSwipe={vi.fn()} onAbrirFicha={vi.fn()} />);

    fireEvent.pointerDown(screen.getByRole('group'), { clientX: 0, pointerId: 1 });

    expect(capturar).not.toHaveBeenCalled();
  });

  it('en cuanto el gesto es un arrastre de verdad, captura una sola vez', () => {
    render(<MascotaSwipeCard mascota={mascota()} onSwipe={vi.fn()} onAbrirFicha={vi.fn()} />);
    const tarjeta = screen.getByRole('group');

    fireEvent.pointerDown(tarjeta, { clientX: 0, pointerId: 9 });
    fireEvent.pointerMove(tarjeta, { clientX: 4, pointerId: 9 });
    // Cuatro píxeles es el temblor de un click, no un arrastre.
    expect(capturar).not.toHaveBeenCalled();

    fireEvent.pointerMove(tarjeta, { clientX: 60, pointerId: 9 });
    fireEvent.pointerMove(tarjeta, { clientX: 90, pointerId: 9 });

    // Una sola vez y con el id del puntero: capturar en cada `pointermove`
    // dispararía `gotpointercapture` decenas de veces por gesto.
    expect(capturar).toHaveBeenCalledExactlyOnceWith(9);
  });
});

// --- Favorita (prop opcional) --------------------------------------------------

describe('MascotaSwipeCard — favorita', () => {
  it('sin la prop no se pinta el corazón: no hay botón que no guarde nada', () => {
    render(<MascotaSwipeCard mascota={mascota()} onSwipe={vi.fn()} onAbrirFicha={vi.fn()} />);

    expect(screen.queryByLabelText('Guardar en favoritos')).not.toBeInTheDocument();
  });

  it('con la prop, el corazón guarda y NO arrastra la tarjeta (stopPropagation)', () => {
    const onSwipe = vi.fn();
    const onAlternarFavorita = vi.fn();
    render(
      <MascotaSwipeCard
        mascota={mascota()}
        onSwipe={onSwipe}
        onAbrirFicha={vi.fn()}
        onAlternarFavorita={onAlternarFavorita}
      />,
    );
    const corazon = screen.getByLabelText('Guardar en favoritos');
    const tarjeta = screen.getByRole('group');

    // El gesto empieza SOBRE el corazón: sin `stopPropagation` en su
    // `pointerdown`, la tarjeta registraría el arrastre y quien solo quería
    // guardar la mascota se la llevaría del deck de un dedazo.
    fireEvent.pointerDown(corazon, { clientX: 0, pointerId: 1 });
    fireEvent.pointerMove(tarjeta, { clientX: 160, pointerId: 1 });
    fireEvent.pointerUp(tarjeta, { clientX: 160, pointerId: 1 });
    fireEvent.click(corazon);

    expect(onAlternarFavorita).toHaveBeenCalledOnce();
    expect(onSwipe).not.toHaveBeenCalled();
  });

  it('el corazón lleno anuncia quitar, no guardar', () => {
    render(
      <MascotaSwipeCard
        mascota={mascota({ es_favorito: true })}
        onSwipe={vi.fn()}
        onAbrirFicha={vi.fn()}
        onAlternarFavorita={vi.fn()}
      />,
    );

    expect(screen.getByLabelText('Quitar de favoritos')).toBeInTheDocument();
  });
});

// --- Afinidad explicable (acceptance A3) ---------------------------------------

describe('MascotaSwipeCard — afinidad', () => {
  it('muestra el porcentaje y al menos dos razones legibles', () => {
    render(<MascotaSwipeCard mascota={mascota()} onSwipe={vi.fn()} onAbrirFicha={vi.fn()} />);

    expect(screen.getByText('94% afín')).toBeInTheDocument();
    const razones = screen.getAllByRole('listitem');
    expect(razones.length).toBeGreaterThanOrEqual(2);
    expect(razones[0]).toHaveTextContent('Energía media, como buscas');
    expect(razones[1]).toHaveTextContent('Tamaño adecuado para tu casa');
  });

  it('sin afinidad no inventa ni porcentaje ni razones, y la tarjeta sigue usable', () => {
    const onSwipe = vi.fn();
    render(
      <MascotaSwipeCard
        mascota={mascota({ afinidad: null })}
        onSwipe={onSwipe}
        onAbrirFicha={vi.fn()}
      />,
    );

    // Es el camino mayoritario: quien no completó el cuestionario de hogar
    // recibe el deck con `afinidad: null` en todas las tarjetas.
    expect(screen.queryByText(/% afín/)).not.toBeInTheDocument();
    expect(screen.queryAllByRole('listitem')).toHaveLength(0);
    expect(screen.getByRole('heading', { name: 'Canela' })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Me interesa' }));
    expect(onSwipe).toHaveBeenCalledExactlyOnceWith('like');
  });
});

// --- Datos de la tarjeta -------------------------------------------------------

describe('MascotaSwipeCard — ficha resumida', () => {
  it('la edad va por edadLegible: un cachorro de 5 meses no es "0 años"', () => {
    render(<MascotaSwipeCard mascota={mascota()} onSwipe={vi.fn()} onAbrirFicha={vi.fn()} />);

    // `Math.round(edad_meses / 12)` del original renderizaba "0 años" aquí.
    expect(screen.getByText(/5 meses/)).toBeInTheDocument();
    expect(screen.queryByText(/0 años/)).not.toBeInTheDocument();
  });

  it('nombra a quien la publicó y la zona donde está', () => {
    render(<MascotaSwipeCard mascota={mascota()} onSwipe={vi.fn()} onAbrirFicha={vi.fn()} />);

    expect(screen.getByText('Fundación Patitas')).toBeInTheDocument();
    expect(screen.getByText('Armenia')).toBeInTheDocument();
  });

  it('sin foto la tarjeta no se rompe y sigue teniendo sus tres acciones', () => {
    render(
      <MascotaSwipeCard
        mascota={mascota({ fotos: [], publicador: null })}
        onSwipe={vi.fn()}
        onAbrirFicha={vi.fn()}
      />,
    );

    expect(screen.getByText(/Sin foto todavía/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Me interesa' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Ahora no' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Ver ficha' })).toBeInTheDocument();
  });
});
