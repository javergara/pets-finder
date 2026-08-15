import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation, useParams } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiError } from '../api/client';
import * as client from '../api/client';
import type { Mascota } from '../api/types';
import type { Organizacion } from '../api/types';
import { setActiveUserId } from '../lib/session';
import { PublicarMascota } from './PublicarMascota';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return { ...actual, crearMascota: vi.fn(), subirFoto: vi.fn() };
});

// `setup.ts` limpia localStorage tras CADA test, así que la cuenta activa se
// declara dentro del cuerpo del test que la necesita (y el test del gate
// simplemente no la declara).
afterEach(() => {
  vi.resetAllMocks();
});

function mascotaCreada(overrides: Partial<Mascota> = {}): Mascota {
  return {
    id: 31,
    organizacion_id: null,
    user_id: 7,
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
    telefono_contacto: '3001234567',
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

// Stub que imprime la ruta completa: el gate no solo tiene que redirigir, tiene
// que llevar el `?volver=` correcto para volver aquí después de registrarse.
function RegistroStub() {
  const { pathname, search } = useLocation();
  return <p>{`registro ${pathname}${search}`}</p>;
}

function FichaStub() {
  const { id } = useParams<{ id: string }>();
  return <p>{`ficha de la mascota ${id}`}</p>;
}

function renderPublicar() {
  return render(
    <MemoryRouter initialEntries={['/adoptar/publicar']}>
      <Routes>
        <Route path="/adoptar/publicar" element={<PublicarMascota />} />
        <Route path="/adoptar/mascota/:id" element={<FichaStub />} />
        <Route path="/registro" element={<RegistroStub />} />
      </Routes>
    </MemoryRouter>,
  );
}

// Camino organización (AD-02, A1): el mismo formulario con `?organizacion=7`.
// Al publicar se vuelve al lugar, no a la ficha, así que el stub imprime la ruta
// completa para poder aseverar el `?tab=adopcion`.
function OrganizacionStub() {
  const { pathname, search } = useLocation();
  return <p>{`organizacion ${pathname}${search}`}</p>;
}

function renderPublicarParaOrganizacion() {
  return render(
    <MemoryRouter initialEntries={['/adoptar/publicar?organizacion=7']}>
      <Routes>
        <Route path="/adoptar/publicar" element={<PublicarMascota />} />
        <Route path="/adoptar/mascota/:id" element={<FichaStub />} />
        <Route path="/organizacion/:id" element={<OrganizacionStub />} />
        <Route path="/registro" element={<RegistroStub />} />
      </Routes>
    </MemoryRouter>,
  );
}

// `obtenerOrganizacion` no está en la factory del mock de arriba (que no se toca):
// se espía aquí, que sobre un módulo mockeado con factory funciona igual.
function espiarOrganizacion(overrides: Partial<Organizacion> = {}) {
  return vi.spyOn(client, 'obtenerOrganizacion').mockResolvedValue({
    id: 7,
    user_id: 7,
    tipo: 'fundacion',
    nombre: 'Fundación Huellitas',
    descripcion: 'Rescatamos mascotas afectadas por el sismo.',
    zona: 'Pereira',
    ciudad_texto: null,
    barrio: 'Centro',
    direccion: 'Cra 14 #10-25',
    lat: 4.81,
    lng: -75.69,
    telefono_contacto: '3009998877',
    horario: null,
    como_donar: null,
    foto_url: null,
    estado: 'activo',
    creado_en: '2026-08-12T10:00:00',
    necesidades_pendientes: 0,
    ...overrides,
  });
}

function elegir(grupo: string, opcion: string) {
  fireEvent.click(
    within(screen.getByRole('group', { name: grupo })).getByRole('button', { name: opcion }),
  );
}

type Overrides = { telefono?: string; zona?: string };

function llenarFormulario({ telefono = '3001234567', zona = 'Armenia' }: Overrides = {}) {
  fireEvent.change(screen.getByLabelText('Nombre'), { target: { value: 'Nala' } });
  elegir('Especie', 'Perro');
  elegir('Sexo', 'Hembra');
  elegir('Tamaño', 'Mediana');
  elegir('Energía', 'Energía media');
  fireEvent.change(screen.getByLabelText('Edad (en meses)'), { target: { value: '18' } });
  fireEvent.change(screen.getByLabelText('Historia'), {
    target: { value: 'Rescatada tras el terremoto.' },
  });
  fireEvent.change(screen.getByLabelText(/Etiquetas/), {
    target: { value: 'cariñosa, tranquila' },
  });
  fireEvent.change(screen.getByLabelText(/¿En qué zona/), { target: { value: zona } });
  fireEvent.change(screen.getByLabelText(/Teléfono de contacto/), { target: { value: telefono } });
}

// Lo mismo, sin zona ni teléfono: en el camino de organización los precarga el
// lugar y escribirlos a mano taparía justo lo que hay que comprobar.
function llenarBasicos() {
  fireEvent.change(screen.getByLabelText('Nombre'), { target: { value: 'Nala' } });
  elegir('Especie', 'Perro');
  elegir('Sexo', 'Hembra');
  elegir('Tamaño', 'Mediana');
  elegir('Energía', 'Energía media');
  fireEvent.change(screen.getByLabelText('Historia'), {
    target: { value: 'Rescatada tras el terremoto.' },
  });
}

function publicar() {
  fireEvent.click(screen.getByRole('button', { name: 'Publicar en adopción' }));
}

describe('PublicarMascota — rescatista individual (AD-02, A2)', () => {
  it('sin cuenta redirige al registro con volver y no llama a la API', () => {
    renderPublicar();

    // El `?volver=` va codificado: si se rompe, el registro no sabe adónde devolver.
    expect(screen.getByText('registro /registro?volver=%2Fadoptar%2Fpublicar')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Publicar en adopción' })).not.toBeInTheDocument();
    // Lo importante del gate: `getActiveUserId()` cae al usuario demo (id 1)
    // cuando no hay cuenta, así que sin esto un visitante publicaría mascotas a
    // nombre de una persona real en producción.
    expect(client.crearMascota).not.toHaveBeenCalled();
  });

  it('con cuenta publica como rescatista y navega a la ficha', async () => {
    setActiveUserId(7);
    vi.mocked(client.crearMascota).mockResolvedValue(mascotaCreada({ id: 31 }));

    renderPublicar();
    llenarFormulario();
    publicar();

    await waitFor(() => expect(client.crearMascota).toHaveBeenCalledTimes(1));
    const datos = vi.mocked(client.crearMascota).mock.calls[0][0];
    expect(datos).toMatchObject({
      user_id: 7,
      rescatista_id: 7,
      nombre: 'Nala',
      especie: 'perro',
      sexo: 'hembra',
      tamano: 'mediano',
      energia: 'media',
      edad_meses: 18,
      historia: 'Rescatada tras el terremoto.',
      tags: ['cariñosa', 'tranquila'],
      zona: 'Armenia',
      telefono_contacto: '3001234567',
    });
    // El camino de organización es otro (paso 7): mandar los dos publicadores da 422.
    expect('organizacion_id' in datos).toBe(false);
    expect(await screen.findByText('ficha de la mascota 31')).toBeInTheDocument();
  });

  it('manda los flags de salud y convivencia que se marcaron', async () => {
    setActiveUserId(7);
    vi.mocked(client.crearMascota).mockResolvedValue(mascotaCreada());

    renderPublicar();
    llenarFormulario();
    elegir('¿Está esterilizada?', 'Sí');
    elegir('¿Convive bien con gatos?', 'No');
    publicar();

    await waitFor(() => expect(client.crearMascota).toHaveBeenCalledTimes(1));
    expect(vi.mocked(client.crearMascota).mock.calls[0][0]).toMatchObject({
      esterilizado: true,
      vacunas_al_dia: false,
      apto_ninos: true,
      apto_perros: true,
      apto_gatos: false,
    });
  });

  it('sin teléfono avisa en español y no llama a la API', () => {
    setActiveUserId(7);

    renderPublicar();
    llenarFormulario({ telefono: '' });
    publicar();

    expect(screen.getByRole('alert')).toHaveTextContent(/teléfono/i);
    expect(client.crearMascota).not.toHaveBeenCalled();
  });

  it('con zona "Otro" y sin ciudad avisa y no llama a la API', () => {
    setActiveUserId(7);

    renderPublicar();
    llenarFormulario({ zona: 'Otro' });
    publicar();

    expect(screen.getByRole('alert')).toHaveTextContent(/ciudad/i);
    expect(client.crearMascota).not.toHaveBeenCalled();
  });

  it('con zona "Otro" y ciudad sí publica, mandando ciudad_texto', async () => {
    setActiveUserId(7);
    vi.mocked(client.crearMascota).mockResolvedValue(mascotaCreada());

    renderPublicar();
    llenarFormulario({ zona: 'Otro' });
    fireEvent.change(screen.getByLabelText(/¿En qué ciudad/), { target: { value: 'Popayán' } });
    publicar();

    await waitFor(() => expect(client.crearMascota).toHaveBeenCalledTimes(1));
    expect(vi.mocked(client.crearMascota).mock.calls[0][0]).toMatchObject({
      zona: 'Otro',
      ciudad_texto: 'Popayán',
    });
  });

  it('un error del backend se muestra tal cual en un bloque de alerta', async () => {
    setActiveUserId(7);
    vi.mocked(client.crearMascota).mockRejectedValue(
      new ApiError('Solo quien registró la organización puede publicar mascotas en adopción'),
    );

    renderPublicar();
    llenarFormulario();
    publicar();

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Solo quien registró la organización puede publicar mascotas en adopción',
    );
  });

  it('muestra el aviso de espacio público antes de publicar', () => {
    setActiveUserId(7);

    renderPublicar();

    expect(screen.getByText(/espacio público/)).toBeInTheDocument();
  });
});

describe('PublicarMascota — a nombre de una organización (AD-02, A1)', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('con ?organizacion=7 precarga zona y teléfono del lugar', async () => {
    setActiveUserId(7);
    espiarOrganizacion();

    renderPublicarParaOrganizacion();

    // Publicar desde el lugar no debería obligar a reescribir su zona ni su
    // teléfono: el 90% de las veces la mascota está donde está la fundación.
    await waitFor(() => expect(screen.getByLabelText(/¿En qué zona/)).toHaveValue('Pereira'));
    expect(screen.getByLabelText(/Teléfono de contacto/)).toHaveValue('3009998877');
    expect(client.obtenerOrganizacion).toHaveBeenCalledWith(7);
    expect(screen.getByText(/Fundación Huellitas/)).toBeInTheDocument();
  });

  it('publica con organizacion_id, sin rescatista_id, y vuelve al lugar en la pestaña de adopción', async () => {
    setActiveUserId(7);
    espiarOrganizacion();
    vi.mocked(client.crearMascota).mockResolvedValue(
      mascotaCreada({ id: 44, organizacion_id: 7, user_id: null }),
    );

    renderPublicarParaOrganizacion();
    await waitFor(() => expect(screen.getByLabelText(/¿En qué zona/)).toHaveValue('Pereira'));
    llenarBasicos();
    publicar();

    await waitFor(() => expect(client.crearMascota).toHaveBeenCalledTimes(1));
    const datos = vi.mocked(client.crearMascota).mock.calls[0][0];
    expect(datos).toMatchObject({
      user_id: 7,
      organizacion_id: 7,
      nombre: 'Nala',
      zona: 'Pereira',
      telefono_contacto: '3009998877',
    });
    // El publicador es exclusivo: mandar los dos es un 422 del backend, y
    // `user_id` (quien hace el request) no es el dueño en este camino.
    expect('rescatista_id' in datos).toBe(false);
    expect(
      await screen.findByText('organizacion /organizacion/7?tab=adopcion'),
    ).toBeInTheDocument();
  });

  it('en una organización ajena el 403 del backend se lee en español y el formulario sigue ahí', async () => {
    setActiveUserId(9);
    espiarOrganizacion();
    vi.mocked(client.crearMascota).mockRejectedValue(
      new ApiError('Solo quien registró la organización puede publicar mascotas en adopción'),
    );

    renderPublicarParaOrganizacion();
    await waitFor(() => expect(screen.getByLabelText(/¿En qué zona/)).toHaveValue('Pereira'));
    llenarBasicos();
    publicar();

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Solo quien registró la organización puede publicar mascotas en adopción',
    );
    expect(screen.getByRole('button', { name: 'Publicar en adopción' })).toBeInTheDocument();
  });

  it('sin cuenta el gate sigue mandando al registro, con la organización en el volver', () => {
    espiarOrganizacion();

    renderPublicarParaOrganizacion();

    expect(
      screen.getByText('registro /registro?volver=%2Fadoptar%2Fpublicar%3Forganizacion%3D7'),
    ).toBeInTheDocument();
    expect(client.crearMascota).not.toHaveBeenCalled();
  });
});
