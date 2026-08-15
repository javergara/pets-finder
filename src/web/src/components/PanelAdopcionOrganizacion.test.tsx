import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { Mascota } from '../api/types';
import { esUsuarioActivo, setActiveUserId } from '../lib/session';
import { PanelAdopcionOrganizacion } from './PanelAdopcionOrganizacion';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return { ...actual, listarMascotas: vi.fn(), editarMascota: vi.fn() };
});

afterEach(() => {
  vi.resetAllMocks();
});

function mascota(overrides: Partial<Mascota> = {}): Mascota {
  return {
    id: 31,
    organizacion_id: 1,
    user_id: null,
    report_id: null,
    nombre: 'Nala',
    especie: 'perro',
    raza: null,
    sexo: 'hembra',
    edad_meses: 18,
    tamano: 'mediano',
    energia: 'media',
    fotos: [],
    historia: 'Rescatada tras el terremoto.',
    tags: [],
    esterilizado: false,
    vacunas_al_dia: false,
    microchip: false,
    desparasitado: false,
    apto_ninos: true,
    apto_perros: true,
    apto_gatos: true,
    zona: 'Armenia',
    ciudad_texto: null,
    barrio: null,
    lat: null,
    lng: null,
    telefono_contacto: '3001112233',
    estado: 'disponible',
    publicado_en: '2026-08-15T10:00:00',
    adoptado_en: null,
    publicador: null,
    afinidad: null,
    es_favorito: false,
    ya_solicitada: false,
    distancia_km: null,
    ...overrides,
  };
}

function renderPanel(esAutor: boolean) {
  return render(
    <MemoryRouter>
      <PanelAdopcionOrganizacion
        organizacionId={1}
        nombreOrganizacion="Fundación Huellitas"
        telefonoContacto="3001112233"
        zona="Armenia"
        esAutor={esAutor}
      />
    </MemoryRouter>,
  );
}

function resumen() {
  return within(screen.getByLabelText('Resumen de las mascotas del lugar'));
}

describe('PanelAdopcionOrganizacion (AD-02, A1)', () => {
  it('pide solo las mascotas de esta organización, incluidas las que ya no están disponibles', async () => {
    vi.mocked(client.listarMascotas).mockResolvedValue([mascota()]);

    renderPanel(false);

    await screen.findByRole('heading', { name: 'Nala' });
    // `estado: 'todos'` es el punto: el panel del lugar también muestra las
    // adoptadas y las que están en proceso, que el catálogo público esconde.
    expect(client.listarMascotas).toHaveBeenCalledWith({ organizacionId: 1, estado: 'todos' });
  });

  it('el autor ve el CTA para publicar con la organización en la URL', async () => {
    vi.mocked(client.listarMascotas).mockResolvedValue([mascota()]);

    renderPanel(true);

    const cta = await screen.findByRole('link', { name: 'Publicar una mascota' });
    // Sin el `?organizacion=1` el formulario publicaría a nombre de la persona,
    // no del lugar: es el parámetro que cambia de camino entero.
    expect(cta).toHaveAttribute('href', '/adoptar/publicar?organizacion=1');
  });

  it('quien no es el autor ve las mascotas pero ninguna acción de escritura', async () => {
    vi.mocked(client.listarMascotas).mockResolvedValue([
      mascota(),
      mascota({ id: 32, nombre: 'Tomás', estado: 'adoptado' }),
    ]);

    renderPanel(false);

    expect(await screen.findByRole('heading', { name: 'Nala' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Tomás' })).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'Publicar una mascota' })).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Estado de Nala')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Estado de Tomás')).not.toBeInTheDocument();
  });

  it('cuenta disponibles, en proceso y adoptadas', async () => {
    vi.mocked(client.listarMascotas).mockResolvedValue([
      mascota(),
      mascota({ id: 32, nombre: 'Tomás', estado: 'en_proceso' }),
      mascota({ id: 33, nombre: 'Bonita', estado: 'adoptado' }),
      mascota({ id: 34, nombre: 'Pelusa', estado: 'adoptado' }),
    ]);

    renderPanel(false);

    await screen.findByRole('heading', { name: 'Nala' });
    expect(resumen().getByText('Disponibles').nextElementSibling).toHaveTextContent('1');
    expect(resumen().getByText('En proceso').nextElementSibling).toHaveTextContent('1');
    expect(resumen().getByText('Adoptadas').nextElementSibling).toHaveTextContent('2');
  });

  it('el autor cambia el estado y el panel refleja el nuevo', async () => {
    setActiveUserId(3);
    vi.mocked(client.listarMascotas).mockResolvedValue([mascota()]);
    vi.mocked(client.editarMascota).mockResolvedValue(mascota({ estado: 'adoptado' }));

    renderPanel(true);

    fireEvent.change(await screen.findByLabelText('Estado de Nala'), {
      target: { value: 'adoptado' },
    });

    await waitFor(() => expect(client.editarMascota).toHaveBeenCalledTimes(1));
    // `user_id` es quien pide el cambio: sin él el backend responde 403.
    expect(client.editarMascota).toHaveBeenCalledWith(31, { user_id: 3, estado: 'adoptado' });
    await waitFor(() =>
      expect(resumen().getByText('Adoptadas').nextElementSibling).toHaveTextContent('1'),
    );
    expect(resumen().getByText('Disponibles').nextElementSibling).toHaveTextContent('0');
    expect(screen.getByLabelText('Estado de Nala')).toHaveValue('adoptado');
  });

  it('un 403 al cambiar el estado se avisa sin tumbar el panel', async () => {
    setActiveUserId(3);
    vi.mocked(client.listarMascotas).mockResolvedValue([mascota()]);
    vi.mocked(client.editarMascota).mockRejectedValue(
      new client.ApiError('Solo quien publicó la mascota puede editarla'),
    );

    renderPanel(true);

    fireEvent.change(await screen.findByLabelText('Estado de Nala'), {
      target: { value: 'adoptado' },
    });

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Solo quien publicó la mascota puede editarla',
    );
    // El panel sigue en pie: la mascota, su selector y el resumen no desaparecen,
    // y el estado no se mueve porque el backend no lo aceptó.
    expect(screen.getByRole('heading', { name: 'Nala' })).toBeInTheDocument();
    expect(screen.getByLabelText('Estado de Nala')).toHaveValue('disponible');
    expect(resumen().getByText('Disponibles').nextElementSibling).toHaveTextContent('1');
  });

  it('sin mascotas muestra su propio texto, con CTA solo para el autor', async () => {
    vi.mocked(client.listarMascotas).mockResolvedValue([]);

    const { unmount } = renderPanel(false);

    expect(await screen.findByText(/todavía no tiene mascotas publicadas/i)).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'Publicar una mascota' })).not.toBeInTheDocument();
    unmount();

    renderPanel(true);

    expect(await screen.findByText(/todavía no tiene mascotas publicadas/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Publicar una mascota' })).toBeInTheDocument();
  });

  // Contrato de las pantallas de detalle desde el fix de esqueletos (81d45ee):
  // mientras carga hay `role="status"`, y si falla hay `role="alert"` — nunca un
  // esqueleto eterno.
  it('mientras carga muestra un esqueleto anunciado', () => {
    vi.mocked(client.listarMascotas).mockReturnValue(new Promise(() => {}));

    renderPanel(false);

    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  // AD-02, paso 9: el lugar corrige lo que publicó sin salir de su panel. La
  // ficha pública no ofrece esto para las mascotas de organización (no sabe quién
  // la registró), así que este enlace es el único camino de edición del lugar.
  it('el autor edita cada mascota desde su tarjeta', async () => {
    vi.mocked(client.listarMascotas).mockResolvedValue([
      mascota(),
      mascota({ id: 32, nombre: 'Tomás' }),
    ]);

    renderPanel(true);

    expect(await screen.findByRole('link', { name: 'Editar la ficha de Nala' })).toHaveAttribute(
      'href',
      '/adoptar/mascota/31/editar',
    );
    expect(screen.getByRole('link', { name: 'Editar la ficha de Tomás' })).toHaveAttribute(
      'href',
      '/adoptar/mascota/32/editar',
    );
  });

  it('quien no es el autor no ve el enlace de editar', async () => {
    vi.mocked(client.listarMascotas).mockResolvedValue([mascota()]);

    renderPanel(false);

    await screen.findByRole('heading', { name: 'Nala' });
    expect(screen.queryByRole('link', { name: /Editar/i })).not.toBeInTheDocument();
  });

  it('si la carga falla lo dice en español y sale del esqueleto', async () => {
    vi.mocked(client.listarMascotas).mockRejectedValue(new Error('offline'));

    renderPanel(false);

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'No pudimos cargar las mascotas en adopción de este lugar.',
    );
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  // Fix 2026-08-15 (bug de autoría sin cuenta). El panel recibe `esAutor` ya
  // calculado, así que el caso se ejercita con el mismo cálculo que hace
  // OrganizacionDetalle: `esUsuarioActivo(user_id del lugar)`. Antes esa cuenta
  // era `1 === getActiveUserId()`, que sin cuenta da `true` y abría el panel del
  // usuario demo a cualquier visitante.
  it('sin cuenta, el lugar del usuario demo no da ninguna acción de escritura', async () => {
    vi.mocked(client.listarMascotas).mockResolvedValue([mascota()]);

    renderPanel(esUsuarioActivo(1));

    expect(await screen.findByRole('heading', { name: 'Nala' })).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'Publicar una mascota' })).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Estado de Nala')).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /Editar/i })).not.toBeInTheDocument();
  });
});
