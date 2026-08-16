import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { Mascota } from '../api/types';
import { setActiveUserId } from '../lib/session';
import { MisFavoritas } from './MisFavoritas';

// La lista guardada (AD-07, paso 5). Lo que estos casos protegen, por gravedad:
//
// 1. **Sin cuenta no se pide la lista de nadie.** Esta pantalla no compara
//    autoría: *consulta* por el id activo, y sin cuenta `getActiveUserId()` cae
//    al `DEMO_USER_ID = 1`, que en producción es una persona real (Ana
//    Martínez). Un visitante anónimo vería SUS mascotas guardadas —un historial
//    de navegación con nombre propio— y al tocar un corazón se las borraría. Por
//    eso el gate se asevera sobre la API, no sobre lo que se pinta: el
//    `<Navigate>` se renderiza igual, pero los efectos corren después del
//    commit, así que un gate que viva solo en el render deja salir la petición.
// 2. **Quitar no puede navegar.** La tarjeta entera es un `<Link>` a la ficha y
//    el corazón vive dentro: sin los dos guards, quitar una favorita saca a la
//    persona de su propia lista (el candado del `preventDefault` está en
//    `MascotaCard.test.tsx`, que es donde vive el código; aquí se asevera el
//    efecto compuesto: la tarjeta se va y la ubicación no cambia).
// 3. **Un fallo de red se dice.** Sin `.catch` la pantalla se queda en el
//    esqueleto para siempre y parece colgada — el bug real que arregló `81d45ee`
//    en otras tres pantallas.

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return { ...actual, listarFavoritas: vi.fn(), desmarcarFavorita: vi.fn() };
});

function mascota(overrides: Partial<Mascota> = {}): Mascota {
  return {
    id: 7,
    organizacion_id: 2,
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
    historia: 'Rescatada del barrio Providencia.',
    tags: ['cariñosa'],
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
    publicador: null,
    afinidad: null,
    // Todo lo que llega aquí está guardado por definición: el corazón nace lleno.
    es_favorito: true,
    ya_solicitada: false,
    distancia_km: null,
    ...overrides,
  };
}

beforeEach(() => {
  vi.mocked(client.listarFavoritas).mockResolvedValue([
    mascota(),
    mascota({ id: 8, nombre: 'Copito', especie: 'gato' }),
  ]);
  vi.mocked(client.desmarcarFavorita).mockResolvedValue(undefined);
});

afterEach(() => {
  vi.resetAllMocks();
  localStorage.clear();
});

/** Imprime la ruta completa: el gate no basta con que redirija, tiene que llevar
 * el `?volver=` exacto para devolver aquí a quien acaba de registrarse. */
function RegistroStub() {
  const { pathname, search } = useLocation();
  return <p>{`registro ${pathname}${search}`}</p>;
}

/** La ubicación, aparte del stub de registro: quitar una favorita no puede
 * llevarse a la persona a la ficha de la mascota que acaba de quitar. */
function Ubicacion() {
  const { pathname } = useLocation();
  return <p>{`ubicación ${pathname}`}</p>;
}

function renderMisFavoritas() {
  return render(
    <MemoryRouter initialEntries={['/adoptar/mis-favoritas']}>
      <Ubicacion />
      <Routes>
        <Route path="/adoptar/mis-favoritas" element={<MisFavoritas />} />
        <Route path="/registro" element={<RegistroStub />} />
        <Route path="/adoptar/mascota/:id" element={<p>ficha</p>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('MisFavoritas', () => {
  it('pide la lista con el id de quien mira y pinta una tarjeta por mascota', async () => {
    setActiveUserId(7);

    renderMisFavoritas();

    expect(await screen.findByRole('heading', { name: 'Nala' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Copito' })).toBeInTheDocument();
    expect(client.listarFavoritas).toHaveBeenCalledWith(7);
    expect(client.listarFavoritas).toHaveBeenCalledTimes(1);
  });

  it('reusa la tarjeta del catálogo: cada una lleva a su ficha y trae el corazón lleno', async () => {
    setActiveUserId(7);

    renderMisFavoritas();

    // El link envolvente y el `aria-label` de "guardada" son de `MascotaCard`:
    // si esta pantalla se hiciera una rejilla propia, este caso se cae.
    expect(await screen.findByRole('link', { name: /Nala/ })).toHaveAttribute(
      'href',
      '/adoptar/mascota/7',
    );
    expect(screen.getAllByRole('button', { name: 'Quitar de favoritos' })).toHaveLength(2);
    expect(screen.queryByRole('button', { name: 'Guardar en favoritos' })).not.toBeInTheDocument();
  });

  it('mientras carga muestra un esqueleto anunciado, no una pantalla vacía', () => {
    setActiveUserId(7);
    vi.mocked(client.listarFavoritas).mockReturnValue(new Promise(() => {}));

    renderMisFavoritas();

    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('sin favoritas todavía, invita al deck en vez de dejar un hueco', async () => {
    setActiveUserId(7);
    vi.mocked(client.listarFavoritas).mockResolvedValue([]);

    renderMisFavoritas();

    expect(await screen.findByText(/Todavía no has guardado ninguna mascota/i)).toBeInTheDocument();
    // Al deck y no al catálogo: quien llega aquí y no tiene nada guardado no
    // necesita otra rejilla igual, necesita empezar a elegir.
    expect(screen.getByRole('link', { name: 'Descubrir mascotas' })).toHaveAttribute(
      'href',
      '/adoptar/descubrir',
    );
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  it('si la API falla lo dice en español y sale del esqueleto', async () => {
    setActiveUserId(7);
    // Sin el `.catch` de la carga, el esqueleto se queda para siempre y la
    // pantalla parece colgada (bug real de este repo, arreglado en `81d45ee`).
    vi.mocked(client.listarFavoritas).mockRejectedValue(new Error('offline'));

    renderMisFavoritas();

    expect(await screen.findByRole('alert')).toHaveTextContent(
      /No pudimos cargar tus mascotas guardadas/i,
    );
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  it('el backend habla en español: su mensaje se muestra tal cual', async () => {
    setActiveUserId(7);
    vi.mocked(client.listarFavoritas).mockRejectedValue(
      new client.ApiError('Solo puedes ver tus propios favoritos'),
    );

    renderMisFavoritas();

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Solo puedes ver tus propios favoritos',
    );
  });

  it('el corazón lleno quita la mascota: la tarjeta desaparece y no se navega', async () => {
    setActiveUserId(7);
    renderMisFavoritas();
    await screen.findByRole('heading', { name: 'Nala' });

    const noCancelado = fireEvent.click(
      screen.getAllByRole('button', { name: 'Quitar de favoritos' })[0],
    );

    expect(client.desmarcarFavorita).toHaveBeenCalledWith(7, 7);
    // La tarjeta se va de la lista al instante: en ESTA pantalla dejarla con el
    // corazón vacío sería una mascota que ya no pertenece a la lista que se
    // está mirando.
    expect(screen.queryByRole('heading', { name: 'Nala' })).not.toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Copito' })).toBeInTheDocument();
    // Dos aserciones, dos navegaciones distintas (`memory/memory.md`,
    // 2026-08-16): la ubicación cubre la del router, y el retorno `false` de
    // `fireEvent.click` es la ÚNICA señal en jsdom de que el `preventDefault`
    // frenó la navegación nativa del `<a href>` —una recarga entera en un
    // navegador real, que jsdom no simula.
    expect(screen.getByText('ubicación /adoptar/mis-favoritas')).toBeInTheDocument();
    expect(noCancelado).toBe(false);
  });

  it('si quitar falla, la tarjeta NO reaparece ni se pinta un error', async () => {
    setActiveUserId(7);
    vi.mocked(client.desmarcarFavorita).mockRejectedValue(new Error('offline'));
    renderMisFavoritas();
    await screen.findByRole('heading', { name: 'Nala' });

    fireEvent.click(screen.getAllByRole('button', { name: 'Quitar de favoritos' })[0]);

    // Reponer lo que alguien acaba de quitar es peor que perder el registro:
    // volvería a aparecer sola una mascota que la persona decidió sacar.
    //
    // ⚠️ El `waitFor` no es decorativo: la rechazada se resuelve en un
    // microtask y React no vuelca ese `setState` hasta el siguiente `act`. Sin
    // esta espera, una pantalla que SÍ repone la tarjeta pasaría este test
    // igual, porque la aserción correría antes del re-render (comprobado con la
    // mutación: `await Promise.resolve()` no bastaba).
    await waitFor(() => expect(screen.getByRole('heading', { name: 'Copito' })).toBeVisible());
    expect(screen.queryByRole('heading', { name: 'Nala' })).not.toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('quitar la última deja el estado vacío, no una rejilla en blanco', async () => {
    setActiveUserId(7);
    vi.mocked(client.listarFavoritas).mockResolvedValue([mascota()]);
    renderMisFavoritas();
    await screen.findByRole('heading', { name: 'Nala' });

    fireEvent.click(screen.getByRole('button', { name: 'Quitar de favoritos' }));

    expect(await screen.findByText(/Todavía no has guardado ninguna mascota/i)).toBeInTheDocument();
  });
});

// El gate de cuenta, aparte porque es el caso de seguridad de la pantalla.
describe('MisFavoritas sin cuenta', () => {
  it('redirige al registro con el volver, sin pedir los favoritos de nadie', async () => {
    renderMisFavoritas();

    expect(
      await screen.findByText('registro /registro?volver=%2Fadoptar%2Fmis-favoritas'),
    ).toBeInTheDocument();
    // Lo grave no es lo que se pinta: es que la petición salga con el
    // `DEMO_USER_ID = 1` y le enseñe a un anónimo los favoritos de una persona
    // real. Por eso el `if (!conCuenta) return` tiene que estar DENTRO del
    // efecto, no solo en el render.
    expect(client.listarFavoritas).not.toHaveBeenCalled();
    expect(screen.queryByRole('heading', { name: 'Nala' })).not.toBeInTheDocument();
  });
});
