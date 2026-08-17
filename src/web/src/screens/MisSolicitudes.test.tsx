import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { EstadoSolicitud, Solicitud } from '../api/types';
import { ETIQUETA_ESTADO_SOLICITUD } from '../lib/adopcion';
import { setActiveUserId } from '../lib/session';
import { MisSolicitudes } from './MisSolicitudes';

// Las dos mitades de una solicitud en una sola pantalla (AD-05, paso 6): lo que
// pediste y lo que te pidieron.
//
// Lo que estos casos protegen, por orden de gravedad:
//
// 1. **Sin cuenta no se leen las solicitudes de nadie.** `getActiveUserId()` cae
//    al `DEMO_USER_ID = 1`, que en producción es una persona real: sin el gate,
//    un visitante anónimo vería las solicitudes de esa persona —con el mensaje y
//    el teléfono de quien las envió— sin haberse registrado. Es el bug de
//    autoría del fix `cc4de85`, y aquí son datos personales de terceros.
// 2. **Las dos listas se piden con el filtro correcto**: `adoptante_id` para las
//    que envió y `publicador_id` para las que recibió. Cruzarlos mostraría las
//    solicitudes ajenas en la sección propia.
// 3. **El estado se lee de un vistazo** y el enlace lleva al detalle correcto:
//    sin el id exacto, la fila no sirve para decidir nada.

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return { ...actual, listarSolicitudes: vi.fn() };
});

afterEach(() => {
  vi.resetAllMocks();
  localStorage.clear();
});

function solicitud(overrides: Partial<Solicitud> = {}): Solicitud {
  return {
    id: 12,
    estado: 'solicitado',
    etiqueta: 'Sin responder · 5 días',
    creado_en: '2026-08-14T10:00:00',
    actualizado_en: null,
    pet: {
      id: 7,
      nombre: 'Canela',
      especie: 'perro',
      raza: 'Cocker mestiza',
      edad_meses: 18,
      fotos: ['/media/seed/pet_7.jpg'],
      estado: 'disponible',
    },
    publicador: {
      tipo: 'organizacion',
      id: 2,
      nombre: 'Fundación Huellitas',
      telefono_contacto: '3001112233',
      zona: 'Armenia',
      ciudad_texto: null,
      barrio: null,
      foto_url: null,
    },
    adoptante: { id: 7, nombre: 'Ana Martínez' },
    afinidad: null,
    acciones_disponibles: [],
    ...overrides,
  };
}

/** Una solicitud por estado persistido, para ver los cinco badges a la vez. */
function unaPorEstado(): Solicitud[] {
  const estados = Object.keys(ETIQUETA_ESTADO_SOLICITUD) as EstadoSolicitud[];
  return estados.map((estado, i) =>
    solicitud({ id: 100 + i, estado, pet: { ...solicitud().pet, id: 200 + i } }),
  );
}

// Stub que imprime la ruta completa: sin cuenta la pantalla no solo tiene que
// redirigir, tiene que llevar el `?volver=` para regresar aquí tras registrarse.
function RegistroStub() {
  const { pathname, search } = useLocation();
  return <p>{`registro ${pathname}${search}`}</p>;
}

function renderMisSolicitudes() {
  return render(
    <MemoryRouter initialEntries={['/adoptar/mis-solicitudes']}>
      <Routes>
        <Route path="/adoptar/mis-solicitudes" element={<MisSolicitudes />} />
        <Route path="/registro" element={<RegistroStub />} />
      </Routes>
    </MemoryRouter>,
  );
}

/** Las dos llamadas del montaje, resueltas por filtro y no por orden: la
 * pantalla las lanza juntas y el orden de resolución no es parte del contrato. */
function responder(enviadas: Solicitud[], recibidas: Solicitud[]) {
  vi.mocked(client.listarSolicitudes).mockImplementation((filtro) =>
    Promise.resolve(filtro.adoptanteId !== undefined ? enviadas : recibidas),
  );
}

describe('MisSolicitudes', () => {
  it('pide las que envió y las que recibió con el id de quien mira', async () => {
    setActiveUserId(7);
    responder([solicitud()], []);

    renderMisSolicitudes();

    await screen.findByText('Canela');
    expect(client.listarSolicitudes).toHaveBeenCalledWith({ adoptanteId: 7 });
    expect(client.listarSolicitudes).toHaveBeenCalledWith({ publicadorId: 7 });
    expect(client.listarSolicitudes).toHaveBeenCalledTimes(2);
  });

  it('separa las que envió de las que recibió', async () => {
    setActiveUserId(7);
    responder(
      [solicitud()],
      [
        solicitud({
          id: 13,
          adoptante: { id: 9, nombre: 'Carlos Ruiz' },
          pet: { ...solicitud().pet, id: 8, nombre: 'Rocky' },
        }),
      ],
    );

    renderMisSolicitudes();

    // Quien envió ve de quién es la mascota; quien recibió, quién se la pidió.
    expect(await screen.findByText(/Publicada por Fundación Huellitas/)).toBeInTheDocument();
    expect(screen.getByText(/Carlos Ruiz/)).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Las que enviaste' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Las que recibiste' })).toBeInTheDocument();
  });

  // El badge es el respaldo estable de `lib/adopcion.ts`; la `etiqueta` del
  // backend ("Sin responder · 5 días") depende de los días y llega calculada.
  it('cada estado se ve con su copy y su color, y ninguno usa el rojo de emergencia', async () => {
    setActiveUserId(7);
    responder(unaPorEstado(), []);

    renderMisSolicitudes();

    await screen.findByText('Esperando respuesta');
    for (const badge of Object.values(ETIQUETA_ESTADO_SOLICITUD)) {
      expect(screen.getByText(badge.texto)).toHaveClass(badge.color);
    }
    // `danger` está reservado en toda la app a "perdido": una solicitud cerrada
    // no es una emergencia.
    expect(document.body.innerHTML).not.toContain('danger');
  });

  it('cada fila lleva al detalle de esa solicitud', async () => {
    setActiveUserId(7);
    responder([solicitud({ id: 42 })], []);

    renderMisSolicitudes();

    expect(await screen.findByRole('link', { name: /Canela/ })).toHaveAttribute(
      'href',
      '/adoptar/solicitud/42',
    );
  });

  it('sin solicitudes cada sección ofrece su propia salida', async () => {
    setActiveUserId(7);
    responder([], []);

    renderMisSolicitudes();

    expect(await screen.findByText(/Todavía no has pedido ninguna mascota/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Ver mascotas en adopción' })).toHaveAttribute(
      'href',
      '/adoptar',
    );
    expect(screen.getByText(/Nadie te ha pedido todavía/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Publicar una mascota' })).toHaveAttribute(
      'href',
      '/adoptar/publicar',
    );
  });

  it('mientras carga muestra un esqueleto anunciado, no una pantalla vacía', () => {
    setActiveUserId(7);
    vi.mocked(client.listarSolicitudes).mockReturnValue(new Promise(() => {}));

    renderMisSolicitudes();

    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('si la API falla lo dice en español y sale del esqueleto', async () => {
    setActiveUserId(7);
    // El backend responde en español: es copy de producto, se muestra tal cual.
    vi.mocked(client.listarSolicitudes).mockRejectedValue(
      new client.ApiError('Solo puedes ver tus propias solicitudes'),
    );

    renderMisSolicitudes();

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Solo puedes ver tus propias solicitudes',
    );
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });
});

// El gate de cuenta, aparte porque es el caso de seguridad: esta pantalla no
// compara autoría, *consulta* por el id activo. Sin cuenta ese id es el usuario
// demo (1), una persona real en producción, y la respuesta trae sus solicitudes
// con el nombre de quien se las envió. Mismo patrón que `MisReportes`.
describe('MisSolicitudes sin cuenta', () => {
  it('redirige al registro con el volver, sin pedir solicitudes de nadie', async () => {
    responder([solicitud()], []);

    renderMisSolicitudes();

    expect(
      await screen.findByText('registro /registro?volver=%2Fadoptar%2Fmis-solicitudes'),
    ).toBeInTheDocument();
    expect(client.listarSolicitudes).not.toHaveBeenCalled();
    expect(screen.queryByText('Canela')).not.toBeInTheDocument();
  });
});
