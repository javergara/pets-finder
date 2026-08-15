import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation, useParams } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiError } from '../api/client';
import * as client from '../api/client';
import type { Mascota } from '../api/types';
import type { Organizacion } from '../api/types';
import type { Reporte } from '../api/types';
import * as imagen from '../lib/imagen';
import { setActiveUserId } from '../lib/session';
import { PublicarMascota } from './PublicarMascota';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return { ...actual, crearMascota: vi.fn(), subirFoto: vi.fn() };
});

// Los dos mocks del puente (AD-02 paso 8): con fotos heredadas de un reporte hay
// que ejercitar una subida de verdad, y el recorte real necesita medir el
// contenedor y cargar la imagen (imposible en jsdom). Mismos stubs que
// `FotoUpload.test.tsx`; en el resto de los tests de este archivo son inertes,
// porque el cropper solo se monta después de elegir un archivo.
vi.mock('../lib/imagen', () => ({ comprimirImagen: vi.fn(), recortarImagen: vi.fn() }));

vi.mock('react-easy-crop', async () => {
  const { createElement } = await import('react');
  return { default: () => createElement('div', null, 'cropper') };
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

// Camino puente (AD-02, A3): se llega con `?reporte=12` desde un encontrado
// propio que la persona tiene consigo. Todo lo que ya escribió en el reporte se
// precarga, y sus fotos —que ya están en Storage— se heredan sin volver a
// subirlas.
function renderPublicarDesdeReporte() {
  return render(
    <MemoryRouter initialEntries={['/adoptar/publicar?reporte=12']}>
      <Routes>
        <Route path="/adoptar/publicar" element={<PublicarMascota />} />
        <Route path="/adoptar/mascota/:id" element={<FichaStub />} />
        <Route path="/registro" element={<RegistroStub />} />
      </Routes>
    </MemoryRouter>,
  );
}

// Como `obtenerOrganizacion`: no está en la factory del mock (que no se toca) y
// se espía aquí.
function espiarReporte(overrides: Partial<Reporte> = {}) {
  return vi.spyOn(client, 'obtenerReporte').mockResolvedValue({
    id: 12,
    user_id: 7,
    tipo: 'encontrado',
    especie: 'gato',
    nombre_mascota: 'Michi',
    raza: 'criolla',
    color: 'carey',
    tamano: 'pequeño',
    descripcion: 'La encontré bajo unos escombros y la tengo en casa.',
    foto_url: '/media/uploads/reporte-a.jpg',
    fotos: ['/media/uploads/reporte-a.jpg', '/media/uploads/reporte-b.jpg'],
    zona: 'Manizales',
    ciudad_texto: null,
    barrio: 'Chipre',
    lat: 5.07,
    lng: -75.52,
    situacion: 'conmigo',
    fecha_evento: '2026-08-11',
    telefono_contacto: '3005554433',
    instagram: null,
    facebook: null,
    fuente: 'manual',
    crawl_metadata: null,
    idempotency_id: null,
    estado: 'activo',
    creado_en: '2026-08-12T08:00:00',
    resuelto_en: null,
    ...overrides,
  });
}

// Lo que el reporte no sabe (el reporte no pregunta sexo ni energía).
function completarLoQueFaltaDelReporte() {
  elegir('Sexo', 'Hembra');
  elegir('Energía', 'Energía media');
}

describe('PublicarMascota — desde un reporte encontrado (AD-02, A3)', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it('con ?reporte=12 precarga lo que ya está escrito en el reporte', async () => {
    setActiveUserId(7);
    espiarReporte();

    renderPublicarDesdeReporte();

    await waitFor(() => expect(screen.getByLabelText('Nombre')).toHaveValue('Michi'));
    expect(client.obtenerReporte).toHaveBeenCalledWith(12);
    expect(screen.getByLabelText('Historia')).toHaveValue(
      'La encontré bajo unos escombros y la tengo en casa.',
    );
    expect(screen.getByLabelText('Raza (opcional)')).toHaveValue('criolla');
    expect(screen.getByLabelText(/¿En qué zona/)).toHaveValue('Manizales');
    expect(screen.getByLabelText(/Barrio/)).toHaveValue('Chipre');
    expect(screen.getByLabelText(/Teléfono de contacto/)).toHaveValue('3005554433');
    // Especie y tamaño son los mismos catálogos en las dos tablas.
    expect(
      within(screen.getByRole('group', { name: 'Especie' })).getByRole('button', { name: 'Gato' }),
    ).toHaveAttribute('aria-pressed', 'true');
    expect(
      within(screen.getByRole('group', { name: 'Tamaño' })).getByRole('button', {
        name: 'Pequeña',
      }),
    ).toHaveAttribute('aria-pressed', 'true');
  });

  it('publica con report_id y con las fotos del reporte, sin volver a subirlas', async () => {
    setActiveUserId(7);
    espiarReporte();
    vi.mocked(client.crearMascota).mockResolvedValue(mascotaCreada({ id: 60, report_id: 12 }));

    renderPublicarDesdeReporte();
    await waitFor(() => expect(screen.getByLabelText('Nombre')).toHaveValue('Michi'));
    completarLoQueFaltaDelReporte();
    publicar();

    await waitFor(() => expect(client.crearMascota).toHaveBeenCalledTimes(1));
    expect(vi.mocked(client.crearMascota).mock.calls[0][0]).toMatchObject({
      report_id: 12,
      user_id: 7,
      rescatista_id: 7,
      // Las mismas URLs del reporte: ya viven en Storage, y el backend enlaza las
      // dos filas justamente para no duplicar archivos.
      fotos: ['/media/uploads/reporte-a.jpg', '/media/uploads/reporte-b.jpg'],
      zona: 'Manizales',
      lat: 5.07,
      lng: -75.52,
    });
    expect(client.subirFoto).not.toHaveBeenCalled();
    expect(await screen.findByText('ficha de la mascota 60')).toBeInTheDocument();
  });

  it('quitar una foto heredada la deja fuera del payload', async () => {
    setActiveUserId(7);
    espiarReporte();
    vi.mocked(client.crearMascota).mockResolvedValue(mascotaCreada({ id: 60, report_id: 12 }));

    renderPublicarDesdeReporte();
    await waitFor(() => expect(screen.getByLabelText('Nombre')).toHaveValue('Michi'));
    completarLoQueFaltaDelReporte();
    fireEvent.click(screen.getByRole('button', { name: 'Quitar la foto 1 del reporte' }));
    publicar();

    await waitFor(() => expect(client.crearMascota).toHaveBeenCalledTimes(1));
    expect(vi.mocked(client.crearMascota).mock.calls[0][0]).toMatchObject({
      fotos: ['/media/uploads/reporte-b.jpg'],
    });
  });

  it('con tres fotos heredadas ya no ofrece subir más', async () => {
    setActiveUserId(7);
    espiarReporte({
      fotos: ['/media/uploads/a.jpg', '/media/uploads/b.jpg', '/media/uploads/c.jpg'],
    });

    renderPublicarDesdeReporte();

    await waitFor(() => expect(screen.getByLabelText('Nombre')).toHaveValue('Michi'));
    // El tope de la ficha son 3: con el cupo lleno, el subidor no se monta.
    expect(screen.queryByLabelText('Foto de la mascota')).not.toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: 'Quitar la foto 3 del reporte' }),
    ).toBeInTheDocument();
  });

  it('con dos heredadas, la foto que se sube se suma a las del reporte', async () => {
    setActiveUserId(7);
    espiarReporte();
    vi.mocked(client.crearMascota).mockResolvedValue(mascotaCreada({ id: 60, report_id: 12 }));
    vi.mocked(client.subirFoto).mockResolvedValue({ foto_url: '/media/uploads/nueva.jpg' });
    vi.mocked(imagen.comprimirImagen).mockImplementation(async (archivo) => archivo);
    vi.mocked(imagen.recortarImagen).mockImplementation(async (archivo) => archivo);
    // jsdom no implementa object URLs.
    vi.stubGlobal('URL', {
      ...URL,
      createObjectURL: vi.fn(() => 'blob:preview-local'),
      revokeObjectURL: vi.fn(),
    });

    renderPublicarDesdeReporte();
    await waitFor(() => expect(screen.getByLabelText('Nombre')).toHaveValue('Michi'));
    completarLoQueFaltaDelReporte();
    // Con 2 heredadas queda cupo para 1, y con cupo 1 `FotoUpload` entra en modo
    // de foto única: solo avisa por `onFotoSubida`. Si el formulario escuchara
    // únicamente `onFotosSubidas`, esta foto se perdería en silencio.
    fireEvent.change(screen.getByLabelText('Foto de la mascota'), {
      target: { files: [new File(['bytes'], 'michi.jpg', { type: 'image/jpeg' })] },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Subir foto' }));
    await waitFor(() => expect(client.subirFoto).toHaveBeenCalledTimes(1));
    publicar();

    await waitFor(() => expect(client.crearMascota).toHaveBeenCalledTimes(1));
    expect(vi.mocked(client.crearMascota).mock.calls[0][0]).toMatchObject({
      fotos: [
        '/media/uploads/reporte-a.jpg',
        '/media/uploads/reporte-b.jpg',
        '/media/uploads/nueva.jpg',
      ],
    });
  });
});
