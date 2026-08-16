import { render, screen } from '@testing-library/react';
// Segundo import del mismo módulo a propósito: la línea de arriba es de AD-01 y
// este archivo solo admite adiciones (es la red de seguridad de la ficha).
import { fireEvent, waitFor } from '@testing-library/react';
// Tercer import del mismo módulo, misma regla de adiciones: `act` solo lo usa el
// bloque de favoritos (AD-07) y solo para vaciar la cola de microtasks antes de
// aseverar que algo NO pasó.
import { act } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
// Segundo import del mismo módulo, por el mismo motivo que el de arriba: la
// línea anterior es de AD-01 y `useLocation` lo necesita solo el bloque de
// favoritos (AD-07), para imprimir la ruta completa del registro.
import { useLocation } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { Mascota, Publicador } from '../api/types';
import { setActiveUserId } from '../lib/session';
import { MascotaDetalle } from './MascotaDetalle';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return { ...actual, obtenerMascota: vi.fn() };
});

afterEach(() => {
  vi.resetAllMocks();
});

function publicadorOrganizacion(overrides: Partial<Publicador> = {}): Publicador {
  return {
    tipo: 'organizacion',
    id: 3,
    nombre: 'Fundación Huellitas',
    telefono_contacto: '3001112233',
    zona: 'Armenia',
    ciudad_texto: null,
    barrio: 'Centro',
    foto_url: null,
    ...overrides,
  };
}

function publicadorRescatista(overrides: Partial<Publicador> = {}): Publicador {
  return {
    tipo: 'rescatista',
    // ⚠️ Es un id de `users`, no de `organizaciones`: el mismo número existe en
    // las dos tablas y apuntan a cosas distintas.
    id: 3,
    nombre: 'Ana Martínez',
    telefono_contacto: '3009998877',
    zona: 'Pereira',
    ciudad_texto: null,
    barrio: null,
    foto_url: null,
    ...overrides,
  };
}

function mascota(overrides: Partial<Mascota> = {}): Mascota {
  return {
    id: 7,
    organizacion_id: 3,
    user_id: null,
    report_id: null,
    nombre: 'Nala',
    especie: 'perro',
    raza: 'Criolla',
    sexo: 'hembra',
    edad_meses: 18,
    tamano: 'mediano',
    energia: 'media',
    fotos: ['/media/seed/pet_7.jpg'],
    historia: 'La rescataron del barrio Providencia después del sismo.',
    tags: ['cariñosa', 'buena con niños'],
    esterilizado: true,
    vacunas_al_dia: true,
    microchip: true,
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
    publicador: publicadorOrganizacion(),
    afinidad: null,
    es_favorito: false,
    ya_solicitada: false,
    distancia_km: null,
    ...overrides,
  };
}

function renderFicha() {
  return render(
    <MemoryRouter initialEntries={['/adoptar/mascota/7']}>
      <Routes>
        <Route path="/adoptar/mascota/:id" element={<MascotaDetalle />} />
        <Route path="/adoptar" element={<div>Catálogo stub</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('MascotaDetalle', () => {
  it('muestra el nombre, la historia y la ficha de datos', async () => {
    vi.mocked(client.obtenerMascota).mockResolvedValue(mascota());

    renderFicha();

    expect(await screen.findByRole('heading', { name: 'Nala' })).toBeInTheDocument();
    // ⚠️ Única línea de este bloque tocada por AD-07, y su premisa caducó de
    // verdad: la ficha ahora pide la mascota con `adoptante_id` (es lo que llena
    // `es_favorito` y pinta el corazón). Sin cuenta ese segundo argumento va
    // `undefined` —nunca el `DEMO_USER_ID = 1`—, y aseverarlo por nombre es más
    // fuerte que la aridad de antes: el test cae si algún día se cuela el id
    // inventado. Mismo ajuste que hizo AD-07 paso 4 en `CatalogoAdopcion`.
    expect(client.obtenerMascota).toHaveBeenCalledWith(7, undefined);
    expect(
      screen.getByText('La rescataron del barrio Providencia después del sismo.'),
    ).toBeInTheDocument();
    expect(screen.getByText('Criolla')).toBeInTheDocument();
    expect(screen.getByText('Hembra')).toBeInTheDocument();
    expect(screen.getByText('Mediana')).toBeInTheDocument();
    expect(screen.getByText('Energía media')).toBeInTheDocument();
    // edadLegible(18) trunca a "1 año" (nunca "2 años") y el tramo lo dice el chip.
    expect(screen.getByText('1 año')).toBeInTheDocument();
    expect(screen.getByText('Joven')).toBeInTheDocument();
    expect(screen.getByText('cariñosa')).toBeInTheDocument();
  });

  it('con varias fotos usa la galería con miniaturas', async () => {
    vi.mocked(client.obtenerMascota).mockResolvedValue(
      mascota({ fotos: ['/media/seed/pet_7.jpg', '/media/seed/pet_7b.jpg'] }),
    );

    renderFicha();

    await screen.findByRole('heading', { name: 'Nala' });
    expect(screen.getByRole('button', { name: 'Ver foto 1' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Ver foto 2' })).toBeInTheDocument();
    expect(screen.getByAltText('Foto de Nala, en adopción')).toBeInTheDocument();
  });

  it('con una sola foto no hay miniaturas', async () => {
    vi.mocked(client.obtenerMascota).mockResolvedValue(mascota());

    renderFicha();

    await screen.findByRole('heading', { name: 'Nala' });
    expect(screen.queryByRole('button', { name: /Ver foto/ })).not.toBeInTheDocument();
    expect(screen.getByAltText('Foto de Nala, en adopción')).toBeInTheDocument();
  });

  // Acceptance A3, literal: esterilizado / vacunas al día / microchip /
  // desparasitado. Los dos extremos, porque un checklist que siempre dice ✓ no
  // informa nada.
  const SALUD = ['Esterilización', 'Vacunas al día', 'Microchip', 'Desparasitación'];

  it('el checklist de salud marca ✓ lo que está confirmado', async () => {
    vi.mocked(client.obtenerMascota).mockResolvedValue(
      mascota({ esterilizado: true, vacunas_al_dia: true, microchip: true, desparasitado: true }),
    );

    renderFicha();

    await screen.findByRole('heading', { name: 'Nala' });
    for (const dato of SALUD) {
      expect(screen.getByText(`✓ ${dato}`)).toBeInTheDocument();
    }
  });

  it('el checklist de salud marca — lo que no está confirmado', async () => {
    vi.mocked(client.obtenerMascota).mockResolvedValue(
      mascota({
        esterilizado: false,
        vacunas_al_dia: false,
        microchip: false,
        desparasitado: false,
      }),
    );

    renderFicha();

    await screen.findByRole('heading', { name: 'Nala' });
    for (const dato of SALUD) {
      expect(screen.getByText(`— ${dato}`)).toBeInTheDocument();
    }
  });

  it('si publica una organización, su nombre lleva a su perfil', async () => {
    vi.mocked(client.obtenerMascota).mockResolvedValue(mascota());

    renderFicha();

    await screen.findByRole('heading', { name: 'Nala' });
    expect(screen.getByRole('link', { name: 'Fundación Huellitas' })).toHaveAttribute(
      'href',
      '/organizacion/3',
    );
  });

  it('si publica un rescatista, su nombre NO enlaza a ningún perfil de organización', async () => {
    vi.mocked(client.obtenerMascota).mockResolvedValue(
      mascota({
        organizacion_id: null,
        user_id: 3,
        telefono_contacto: '3009998877',
        publicador: publicadorRescatista(),
      }),
    );

    renderFicha();

    await screen.findByRole('heading', { name: 'Nala' });
    expect(screen.getByText('Ana Martínez')).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'Ana Martínez' })).not.toBeInTheDocument();
    // El id 3 de un rescatista es de `users`: /organizacion/3 sería otra entidad.
    const enlacesAOrganizacion = screen
      .getAllByRole('link')
      .filter((a) => (a.getAttribute('href') ?? '').startsWith('/organizacion'));
    expect(enlacesAOrganizacion).toHaveLength(0);
  });

  it('el botón de WhatsApp lleva al teléfono del publicador con el mensaje precargado', async () => {
    vi.mocked(client.obtenerMascota).mockResolvedValue(mascota());

    renderFicha();

    await screen.findByRole('heading', { name: 'Nala' });
    const whatsapp = screen.getByRole('link', { name: 'Escribir por WhatsApp' });
    expect(whatsapp).toHaveAttribute('href', expect.stringContaining('wa.me'));
    const href = whatsapp.getAttribute('href') ?? '';
    expect(href.startsWith('https://wa.me/573001112233?text=')).toBe(true);
    expect(decodeURIComponent(href.split('?text=')[1])).toBe(
      'Hola, vi a Nala en Pet Finder Col y me interesa adoptarla. ¿Sigue disponible?',
    );
  });

  it('sin teléfono de contacto no se pinta el botón de WhatsApp', async () => {
    vi.mocked(client.obtenerMascota).mockResolvedValue(
      mascota({ publicador: publicadorOrganizacion({ telefono_contacto: null }) }),
    );

    renderFicha();

    await screen.findByRole('heading', { name: 'Nala' });
    expect(screen.queryByRole('link', { name: 'Escribir por WhatsApp' })).not.toBeInTheDocument();
    expect(screen.getByText(/no dejó un teléfono/i)).toBeInTheDocument();
  });

  it('incluye el aviso de seguridad antes de coordinar un encuentro', async () => {
    vi.mocked(client.obtenerMascota).mockResolvedValue(mascota());

    renderFicha();

    await screen.findByRole('heading', { name: 'Nala' });
    expect(screen.getByText(/Pet Finder Col no verifica los reportes/)).toBeInTheDocument();
  });

  it('si la mascota no existe muestra el mensaje del backend y la salida al catálogo, sin esqueleto', async () => {
    vi.mocked(client.obtenerMascota).mockRejectedValue(
      new client.ApiError('La mascota 7 no existe'),
    );

    renderFicha();

    expect(await screen.findByRole('alert')).toHaveTextContent('La mascota 7 no existe');
    expect(screen.getByRole('link', { name: /Ver las mascotas en adopción/i })).toHaveAttribute(
      'href',
      '/adoptar',
    );
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  it('un fallo de red también sale del esqueleto, con copy en español', async () => {
    vi.mocked(client.obtenerMascota).mockRejectedValue(new Error('offline'));

    renderFicha();

    expect(await screen.findByRole('alert')).toHaveTextContent(
      /No pudimos cargar esta mascota. Revisa tu conexión e intenta de nuevo./,
    );
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });
});

// AD-02, paso 9. Bloque aparte para no tocar una línea del de arriba: los casos
// de AD-01 son la garantía de que la ficha pública no cambió de comportamiento.
//
// `eliminarMascota` se espía con `vi.spyOn` en vez de añadirla a la factory del
// `vi.mock` de arriba, que habría sido una línea modificada (sobre un módulo
// mockeado con factory el spy funciona igual, verificado en el paso 7).
describe('MascotaDetalle — acciones de quien la publicó (AD-02)', () => {
  function mascotaDeRescatista(idRescatista: number, overrides: Partial<Mascota> = {}): Mascota {
    return mascota({
      organizacion_id: null,
      user_id: idRescatista,
      telefono_contacto: '3009998877',
      publicador: publicadorRescatista({ id: idRescatista }),
      ...overrides,
    });
  }

  it('el rescatista que la publicó ve editar y despublicar', async () => {
    setActiveUserId(3);
    vi.mocked(client.obtenerMascota).mockResolvedValue(mascotaDeRescatista(3));

    renderFicha();

    await screen.findByRole('heading', { name: 'Nala' });
    expect(screen.getByRole('link', { name: /Editar/i })).toHaveAttribute(
      'href',
      '/adoptar/mascota/7/editar',
    );
    expect(screen.getByRole('button', { name: /Despublicar/i })).toBeInTheDocument();
  });

  it('otro usuario con cuenta no ve ninguna de las dos', async () => {
    setActiveUserId(9);
    vi.mocked(client.obtenerMascota).mockResolvedValue(mascotaDeRescatista(3));

    renderFicha();

    await screen.findByRole('heading', { name: 'Nala' });
    expect(screen.queryByRole('link', { name: /Editar/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Despublicar/i })).not.toBeInTheDocument();
  });

  // ⚠️ El riesgo del módulo: `getActiveUserId()` cae al usuario demo (id 1) sin
  // cuenta. Sin `hasActiveUser()`, un visitante vería editar y despublicar sobre
  // las mascotas del usuario 1 — que en producción es una persona real.
  it('sin cuenta no las ve, aunque la mascota sea del usuario demo', async () => {
    vi.mocked(client.obtenerMascota).mockResolvedValue(mascotaDeRescatista(1));

    renderFicha();

    await screen.findByRole('heading', { name: 'Nala' });
    expect(screen.queryByRole('link', { name: /Editar/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Despublicar/i })).not.toBeInTheDocument();
  });

  // La ficha no sabe quién registró la organización (el publicador trae el id del
  // LUGAR, no el de su autor): adivinarlo enseñando las acciones a quien tenga
  // ese mismo id en `users` sería un leak. El lugar se gestiona desde su panel.
  it('una mascota de organización no muestra esas acciones ni a su autor', async () => {
    setActiveUserId(3);
    vi.mocked(client.obtenerMascota).mockResolvedValue(mascota());

    renderFicha();

    await screen.findByRole('heading', { name: 'Nala' });
    expect(screen.queryByRole('link', { name: /Editar/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Despublicar/i })).not.toBeInTheDocument();
  });

  it('despublicar pide confirmación en la página y luego borra y vuelve al catálogo', async () => {
    setActiveUserId(3);
    vi.mocked(client.obtenerMascota).mockResolvedValue(mascotaDeRescatista(3));
    const eliminar = vi.spyOn(client, 'eliminarMascota').mockResolvedValue(undefined);

    renderFicha();

    await screen.findByRole('heading', { name: 'Nala' });
    fireEvent.click(screen.getByRole('button', { name: /Despublicar/i }));
    // Primer paso: pregunta, y todavía no ha borrado nada.
    expect(screen.getByText(/no se puede deshacer/i)).toBeInTheDocument();
    expect(eliminar).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: 'Sí, despublicar' }));

    await waitFor(() => expect(eliminar).toHaveBeenCalledWith(7, 3));
    expect(await screen.findByText('Catálogo stub')).toBeInTheDocument();
  });

  it('un fallo al despublicar se avisa en español y la ficha sigue en pie', async () => {
    setActiveUserId(3);
    vi.mocked(client.obtenerMascota).mockResolvedValue(mascotaDeRescatista(3));
    vi.spyOn(client, 'eliminarMascota').mockRejectedValue(
      new client.ApiError('Solo quien publicó la mascota puede despublicarla'),
    );

    renderFicha();

    await screen.findByRole('heading', { name: 'Nala' });
    fireEvent.click(screen.getByRole('button', { name: /Despublicar/i }));
    fireEvent.click(screen.getByRole('button', { name: 'Sí, despublicar' }));

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Solo quien publicó la mascota puede despublicarla',
    );
    expect(screen.getByRole('heading', { name: 'Nala' })).toBeInTheDocument();
  });
});

// AD-07, paso 7. Tercer bloque aparte, por la misma razón que el de AD-02: los
// casos de arriba son la red de seguridad de la ficha pública y no cambian.
//
// Lo que estos casos protegen, por gravedad:
//
// 1. **`adoptante_id` solo con cuenta.** Es lo que llena `es_favorito`, así que
//    la tentación es mandarlo siempre; pero `getActiveUserId()` cae al
//    `DEMO_USER_ID = 1`, una persona real en producción, y un visitante anónimo
//    vería el corazón lleno con lo que ELLA guardó — y al tocarlo se lo borraría.
// 2. **Guardar es la única escritura que esta ficha admite de quien no publicó.**
//    Sin cuenta el corazón se pinta igual (esconderlo ocultaría que los
//    favoritos existen) pero lleva al registro con el `?volver=` de ESTA ficha,
//    que es a donde hay que volver para terminar el gesto.
describe('MascotaDetalle — corazón de favoritos (AD-07)', () => {
  function RegistroStub() {
    const { pathname, search } = useLocation();
    return <p>{`registro ${pathname}${search}`}</p>;
  }

  /** Como `renderFicha`, más la ruta del registro: el gate sin cuenta navega y
   * hay que poder leer la URL completa a la que llegó. */
  function renderFichaConRegistro() {
    return render(
      <MemoryRouter initialEntries={['/adoptar/mascota/7']}>
        <Routes>
          <Route path="/adoptar/mascota/:id" element={<MascotaDetalle />} />
          <Route path="/adoptar" element={<div>Catálogo stub</div>} />
          <Route path="/registro" element={<RegistroStub />} />
        </Routes>
      </MemoryRouter>,
    );
  }

  it('con cuenta pide la ficha con el id de quien mira', async () => {
    setActiveUserId(7);
    vi.mocked(client.obtenerMascota).mockResolvedValue(mascota());

    renderFicha();

    await screen.findByRole('heading', { name: 'Nala' });
    expect(client.obtenerMascota).toHaveBeenCalledWith(7, 7);
  });

  it('sin cuenta NO manda adoptante_id (el fallback es una persona real)', async () => {
    vi.mocked(client.obtenerMascota).mockResolvedValue(mascota());

    renderFicha();

    await screen.findByRole('heading', { name: 'Nala' });
    expect(client.obtenerMascota).toHaveBeenCalledWith(7, undefined);
  });

  it('el corazón nace lleno si la mascota ya está guardada', async () => {
    setActiveUserId(7);
    vi.mocked(client.obtenerMascota).mockResolvedValue(mascota({ es_favorito: true }));

    renderFichaConRegistro();

    expect(await screen.findByRole('button', { name: 'Quitar de favoritos' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Guardar en favoritos' })).not.toBeInTheDocument();
  });

  it('con cuenta, guardar llama a la API y el corazón queda lleno sin re-consultar la ficha', async () => {
    setActiveUserId(7);
    vi.mocked(client.obtenerMascota).mockResolvedValue(mascota());
    const marcar = vi
      .spyOn(client, 'marcarFavorita')
      .mockResolvedValue(mascota({ es_favorito: true }));
    const desmarcar = vi.spyOn(client, 'desmarcarFavorita').mockResolvedValue(undefined);

    renderFichaConRegistro();
    await screen.findByRole('heading', { name: 'Nala' });

    fireEvent.click(screen.getByRole('button', { name: 'Guardar en favoritos' }));

    expect(marcar).toHaveBeenCalledWith(7, 7);
    expect(desmarcar).not.toHaveBeenCalled();
    // Optimista: el corazón cambia sin esperar la respuesta y la ficha NO se
    // vuelve a pedir (recargarla entera por un corazón haría parpadear la foto).
    await waitFor(() =>
      expect(screen.getByRole('button', { name: 'Quitar de favoritos' })).toBeInTheDocument(),
    );
    expect(client.obtenerMascota).toHaveBeenCalledTimes(1);
  });

  it('con cuenta, tocar una ya guardada la quita', async () => {
    setActiveUserId(7);
    vi.mocked(client.obtenerMascota).mockResolvedValue(mascota({ es_favorito: true }));
    const marcar = vi.spyOn(client, 'marcarFavorita').mockResolvedValue(mascota());
    const desmarcar = vi.spyOn(client, 'desmarcarFavorita').mockResolvedValue(undefined);

    renderFichaConRegistro();
    await screen.findByRole('heading', { name: 'Nala' });

    fireEvent.click(screen.getByRole('button', { name: 'Quitar de favoritos' }));

    expect(desmarcar).toHaveBeenCalledWith(7, 7);
    expect(marcar).not.toHaveBeenCalled();
    await waitFor(() =>
      expect(screen.getByRole('button', { name: 'Guardar en favoritos' })).toBeInTheDocument(),
    );
  });

  it('sin cuenta el corazón se pinta igual, pero lleva al registro sin llamar a la API', async () => {
    vi.mocked(client.obtenerMascota).mockResolvedValue(mascota());
    const marcar = vi.spyOn(client, 'marcarFavorita').mockResolvedValue(mascota());
    const desmarcar = vi.spyOn(client, 'desmarcarFavorita').mockResolvedValue(undefined);

    renderFichaConRegistro();
    await screen.findByRole('heading', { name: 'Nala' });

    fireEvent.click(screen.getByRole('button', { name: 'Guardar en favoritos' }));

    // El orden importa: lo grave no es dejar de navegar, es escribir. Sin el
    // gate, esta llamada saldría con el `DEMO_USER_ID = 1` y guardaría la
    // mascota en la lista de una persona real.
    expect(marcar).not.toHaveBeenCalled();
    expect(desmarcar).not.toHaveBeenCalled();
    // El `?volver=` lleva ESTA ficha, con su id: quien se registra para guardar
    // vuelve a la mascota que estaba mirando, no al catálogo.
    expect(
      await screen.findByText('registro /registro?volver=%2Fadoptar%2Fmascota%2F7'),
    ).toBeInTheDocument();
  });

  it('si la API falla, la ficha no muestra error ni deshace el corazón', async () => {
    setActiveUserId(7);
    vi.mocked(client.obtenerMascota).mockResolvedValue(mascota());
    vi.spyOn(client, 'marcarFavorita').mockRejectedValue(new client.ApiError('offline'));

    renderFichaConRegistro();
    await screen.findByRole('heading', { name: 'Nala' });

    fireEvent.click(screen.getByRole('button', { name: 'Guardar en favoritos' }));

    // ⚠️ El flush explícito NO es ceremonia: este caso asevera que **no pasa
    // nada** cuando la promesa se rechaza, y el corazón ya está lleno por el
    // optimista desde el clic. Sin vaciar antes la cola de microtasks dentro de
    // `act`, las dos aserciones de abajo pasan por llegar temprano —comprobado:
    // con `waitFor` a secas, la mutación que revierte el corazón en el `.catch`
    // SOBREVIVE— (`memory/memory.md`, 2026-08-16).
    await act(async () => {});

    expect(screen.getByRole('button', { name: 'Quitar de favoritos' })).toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });
});
