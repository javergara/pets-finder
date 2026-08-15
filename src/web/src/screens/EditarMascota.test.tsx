import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation, useParams } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { Mascota, MascotaUpdate, Publicador } from '../api/types';
import { setActiveUserId } from '../lib/session';
import { EditarMascota } from './EditarMascota';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return { ...actual, obtenerMascota: vi.fn(), editarMascota: vi.fn(), subirFoto: vi.fn() };
});

afterEach(() => {
  vi.resetAllMocks();
});

function publicadorRescatista(overrides: Partial<Publicador> = {}): Publicador {
  return {
    tipo: 'rescatista',
    id: 7,
    nombre: 'Ana Martínez',
    telefono_contacto: '3001234567',
    zona: 'Armenia',
    ciudad_texto: null,
    barrio: null,
    foto_url: null,
    ...overrides,
  };
}

function mascota(overrides: Partial<Mascota> = {}): Mascota {
  return {
    id: 31,
    organizacion_id: null,
    user_id: 7,
    report_id: null,
    nombre: 'Nala',
    especie: 'perro',
    raza: 'Criolla',
    sexo: 'hembra',
    edad_meses: 18,
    tamano: 'mediano',
    energia: 'media',
    fotos: ['/media/uploads/nala-1.jpg'],
    historia: 'Rescatada tras el terremoto.',
    tags: ['cariñosa', 'tranquila'],
    esterilizado: true,
    vacunas_al_dia: false,
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
    telefono_contacto: '3001234567',
    estado: 'disponible',
    publicado_en: '2026-08-15T10:00:00',
    adoptado_en: null,
    publicador: publicadorRescatista(),
    afinidad: null,
    es_favorito: false,
    ya_solicitada: false,
    distancia_km: null,
    ...overrides,
  };
}

function FichaStub() {
  const { id } = useParams<{ id: string }>();
  return <p>{`ficha de la mascota ${id}`}</p>;
}

// Imprime la ruta completa: el gate no solo tiene que redirigir, tiene que
// llevar el `?volver=` que devuelve aquí después de registrarse.
function RegistroStub() {
  const { pathname, search } = useLocation();
  return <p>{`registro ${pathname}${search}`}</p>;
}

function renderEditar() {
  return render(
    <MemoryRouter initialEntries={['/adoptar/mascota/31/editar']}>
      <Routes>
        <Route path="/adoptar/mascota/:id/editar" element={<EditarMascota />} />
        <Route path="/adoptar/mascota/:id" element={<FichaStub />} />
        <Route path="/adoptar" element={<p>catálogo stub</p>} />
        <Route path="/registro" element={<RegistroStub />} />
      </Routes>
    </MemoryRouter>,
  );
}

// Los datos con los que se llamó a `editarMascota` (segundo argumento).
function datosGuardados(): MascotaUpdate {
  return vi.mocked(client.editarMascota).mock.calls[0][1];
}

describe('EditarMascota (AD-02, A1 y A2)', () => {
  it('precarga los valores que la mascota ya tiene publicados', async () => {
    setActiveUserId(7);
    vi.mocked(client.obtenerMascota).mockResolvedValue(mascota());

    renderEditar();

    expect(await screen.findByLabelText('Nombre')).toHaveValue('Nala');
    expect(client.obtenerMascota).toHaveBeenCalledWith(31);
    expect(screen.getByLabelText(/Raza/)).toHaveValue('Criolla');
    expect(screen.getByLabelText(/Edad/)).toHaveValue(18);
    expect(screen.getByLabelText('Historia')).toHaveValue('Rescatada tras el terremoto.');
    expect(screen.getByLabelText(/Etiquetas/)).toHaveValue('cariñosa, tranquila');
    expect(screen.getByLabelText(/Barrio/)).toHaveValue('Providencia');
    expect(screen.getByLabelText(/Teléfono/)).toHaveValue('3001234567');
    // Los catálogos cerrados también llegan marcados, no en blanco.
    const especie = within(screen.getByRole('group', { name: 'Especie' }));
    expect(especie.getByRole('button', { name: 'Perro' })).toHaveAttribute('aria-pressed', 'true');
    const tamano = within(screen.getByRole('group', { name: 'Tamaño' }));
    expect(tamano.getByRole('button', { name: 'Mediana' })).toHaveAttribute('aria-pressed', 'true');
    // Y los siete sí/no, cada uno con la respuesta guardada (no el default).
    const gatos = within(screen.getByRole('group', { name: '¿Convive bien con gatos?' }));
    expect(gatos.getByRole('button', { name: 'No' })).toHaveAttribute('aria-pressed', 'true');
    const esterilizada = within(screen.getByRole('group', { name: '¿Está esterilizada?' }));
    expect(esterilizada.getByRole('button', { name: 'Sí' })).toHaveAttribute(
      'aria-pressed',
      'true',
    );
  });

  it('guardar manda user_id con los campos editados y vuelve a la ficha', async () => {
    setActiveUserId(7);
    vi.mocked(client.obtenerMascota).mockResolvedValue(mascota());
    vi.mocked(client.editarMascota).mockResolvedValue(mascota({ nombre: 'Nala Bonita' }));

    renderEditar();

    fireEvent.change(await screen.findByLabelText('Nombre'), { target: { value: 'Nala Bonita' } });
    fireEvent.change(screen.getByLabelText('Historia'), {
      target: { value: 'Ya está lista para una familia.' },
    });
    fireEvent.click(
      within(screen.getByRole('group', { name: '¿Tiene las vacunas al día?' })).getByRole(
        'button',
        {
          name: 'Sí',
        },
      ),
    );
    fireEvent.click(screen.getByRole('button', { name: 'Guardar cambios' }));

    await waitFor(() => expect(client.editarMascota).toHaveBeenCalledTimes(1));
    expect(vi.mocked(client.editarMascota).mock.calls[0][0]).toBe(31);
    // `user_id` es quien pide el cambio: sin él el backend responde 403.
    expect(datosGuardados()).toMatchObject({
      user_id: 7,
      nombre: 'Nala Bonita',
      historia: 'Ya está lista para una familia.',
      vacunas_al_dia: true,
      fotos: ['/media/uploads/nala-1.jpg'],
      tags: ['cariñosa', 'tranquila'],
    });
    expect(await screen.findByText('ficha de la mascota 31')).toBeInTheDocument();
  });

  it('no hay campo de zona ni de ciudad, y lo explica en vez de callarlo', async () => {
    setActiveUserId(7);
    vi.mocked(client.obtenerMascota).mockResolvedValue(mascota());
    vi.mocked(client.editarMascota).mockResolvedValue(mascota());

    renderEditar();

    await screen.findByLabelText('Nombre');
    // `MascotaUpdate` (espejo de `PetUpdate`) no los declara: mudar de zona
    // cambiaría el encuadre en el mapa, así que se despublica y se republica.
    expect(screen.queryByLabelText(/zona/i)).toBeNull();
    expect(screen.queryByLabelText(/ciudad/i)).toBeNull();
    expect(screen.getByText(/despublícala y publícala de nuevo/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Guardar cambios' }));

    await waitFor(() => expect(client.editarMascota).toHaveBeenCalledTimes(1));
    const datos = datosGuardados();
    expect('zona' in datos).toBe(false);
    expect('ciudad_texto' in datos).toBe(false);
  });

  it('quitar una de las fotos actuales la saca del guardado', async () => {
    setActiveUserId(7);
    vi.mocked(client.obtenerMascota).mockResolvedValue(
      mascota({ fotos: ['/media/uploads/nala-1.jpg', '/media/uploads/nala-2.jpg'] }),
    );
    vi.mocked(client.editarMascota).mockResolvedValue(mascota());

    renderEditar();

    fireEvent.click(await screen.findByRole('button', { name: /Quitar la foto 1/ }));
    fireEvent.click(screen.getByRole('button', { name: 'Guardar cambios' }));

    await waitFor(() => expect(client.editarMascota).toHaveBeenCalledTimes(1));
    // La lista completa, nunca una mutación parcial: así la guarda el backend.
    expect(datosGuardados().fotos).toEqual(['/media/uploads/nala-2.jpg']);
  });

  it('si la mascota no existe muestra el mensaje del backend, sin esqueleto eterno', async () => {
    setActiveUserId(7);
    vi.mocked(client.obtenerMascota).mockRejectedValue(
      new client.ApiError('La mascota 31 no existe'),
    );

    renderEditar();

    expect(await screen.findByRole('alert')).toHaveTextContent('La mascota 31 no existe');
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Nombre')).toBeNull();
    expect(screen.getByRole('link', { name: /Ver las mascotas en adopción/i })).toHaveAttribute(
      'href',
      '/adoptar',
    );
  });

  it('mientras carga anuncia el esqueleto', () => {
    setActiveUserId(7);
    vi.mocked(client.obtenerMascota).mockReturnValue(new Promise(() => {}));

    renderEditar();

    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('un 403 del backend se muestra en español y la pantalla sigue en pie', async () => {
    setActiveUserId(9);
    vi.mocked(client.obtenerMascota).mockResolvedValue(mascota());
    vi.mocked(client.editarMascota).mockRejectedValue(
      new client.ApiError('Solo quien publicó la mascota puede editarla'),
    );

    renderEditar();

    fireEvent.click(await screen.findByRole('button', { name: 'Guardar cambios' }));

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Solo quien publicó la mascota puede editarla',
    );
    expect(screen.getByLabelText('Nombre')).toHaveValue('Nala');
    expect(screen.queryByText('ficha de la mascota 31')).toBeNull();
  });

  // Mismo riesgo que en la ficha: `getActiveUserId()` cae al usuario demo (id 1)
  // sin cuenta, así que una pantalla que ESCRIBE tiene que cerrarse antes de leer
  // ningún id — si no, un visitante edita las mascotas de una persona real.
  it('sin cuenta manda al registro, sin formulario y sin pedir la mascota', async () => {
    vi.mocked(client.obtenerMascota).mockResolvedValue(mascota());

    renderEditar();

    expect(
      await screen.findByText('registro /registro?volver=%2Fadoptar%2Fmascota%2F31%2Feditar'),
    ).toBeInTheDocument();
    expect(screen.queryByLabelText('Nombre')).toBeNull();
    expect(client.obtenerMascota).not.toHaveBeenCalled();
  });
});
