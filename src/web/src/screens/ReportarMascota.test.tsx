import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { Reporte } from '../api/types';
import { ZONAS } from '../lib/ciudades';
import { setActiveUserId } from '../lib/session';
import { ReportarMascota } from './ReportarMascota';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return { ...actual, crearReporte: vi.fn(), subirFoto: vi.fn() };
});

beforeEach(() => {
  // El gate de registro mira localStorage: con esto el usuario "existe".
  setActiveUserId(1);
});

afterEach(() => {
  vi.resetAllMocks();
  localStorage.clear();
});

function crearReporteRespuesta(overrides: Partial<Reporte> = {}): Reporte {
  return {
    id: 99,
    user_id: 1,
    tipo: 'perdido',
    especie: 'perro',
    nombre_mascota: 'Rocky',
    raza: null,
    color: null,
    tamano: null,
    descripcion: 'Criollo color miel',
    foto_url: null,
    zona: 'Armenia',
    ciudad_texto: null,
    barrio: null,
    lat: 4.534,
    lng: -75.681,
    situacion: null,
    fecha_evento: '2026-08-10',
    telefono_contacto: '3001234567',
    estado: 'activo',
    creado_en: '2026-08-12T08:00:00',
    resuelto_en: null,
    ...overrides,
  };
}

function renderReportar(tipo: 'perdido' | 'encontrado') {
  return render(
    <MemoryRouter initialEntries={[`/reportar/${tipo}`]}>
      <Routes>
        <Route path="/reportar/perdido" element={<ReportarMascota tipo="perdido" />} />
        <Route path="/reportar/encontrado" element={<ReportarMascota tipo="encontrado" />} />
        <Route path="/registro" element={<div>Registro stub</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('ReportarMascota — campos condicionales', () => {
  it('en "perdido" muestra el nombre de la mascota y no la situación', () => {
    renderReportar('perdido');

    expect(screen.getByLabelText('Nombre de tu mascota (opcional)')).toBeInTheDocument();
    expect(screen.queryByLabelText('¿Dónde está ahora?')).not.toBeInTheDocument();
  });

  it('ofrece raza/color/tamaño predefinidos, y la raza desaparece con especie "otro"', () => {
    renderReportar('perdido');

    // Con perro (default): las tres características, con opciones predefinidas.
    expect(screen.getByLabelText('Raza')).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Labrador' })).toBeInTheDocument();
    expect(screen.getByLabelText('Color')).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Miel / dorado' })).toBeInTheDocument();
    expect(screen.getByLabelText('Tamaño')).toBeInTheDocument();

    // Con gato: cambian las razas.
    fireEvent.change(screen.getByLabelText('¿Qué animal es?'), { target: { value: 'gato' } });
    expect(screen.getByRole('option', { name: 'Siamés' })).toBeInTheDocument();
    expect(screen.queryByRole('option', { name: 'Labrador' })).not.toBeInTheDocument();

    // Con "otro" no hay raza; color y tamaño siguen.
    fireEvent.change(screen.getByLabelText('¿Qué animal es?'), { target: { value: 'otro' } });
    expect(screen.queryByLabelText('Raza')).not.toBeInTheDocument();
    expect(screen.getByLabelText('Color')).toBeInTheDocument();
  });

  it('en "encontrado" muestra la situación y no el nombre', () => {
    renderReportar('encontrado');

    expect(screen.getByLabelText('¿Dónde está ahora?')).toBeInTheDocument();
    expect(screen.queryByLabelText('Nombre de tu mascota (opcional)')).not.toBeInTheDocument();
  });
});

describe('ReportarMascota — gate de registro', () => {
  it('sin usuario registrado redirige a /registro?volver=', () => {
    localStorage.clear();

    renderReportar('perdido');

    expect(screen.getByText('Registro stub')).toBeInTheDocument();
  });
});

describe('ReportarMascota — envío', () => {
  function llenarMinimo() {
    fireEvent.change(screen.getByLabelText('Descripción y señas'), {
      target: { value: 'Criollo color miel con collar rojo' },
    });
    fireEvent.change(screen.getByLabelText('Teléfono de contacto (WhatsApp)'), {
      target: { value: '3001234567' },
    });
  }

  it('publica un reporte perdido con el pin (por defecto, el centro de la zona)', async () => {
    // El click sobre el mapa real (Leaflet) entrega lat/lng directas y no corre
    // en jsdom (guard MODE==='test' en MapaLienzo) — se verifica manualmente en
    // navegador (acceptance 5 de la feature 14). Aquí se cubre el contrato: el
    // payload lleva las coords del pin, que arranca en el centro declarado de la
    // zona elegida (lib/ciudades.ts).
    vi.mocked(client.crearReporte).mockResolvedValue(crearReporteRespuesta());

    renderReportar('perdido');
    llenarMinimo();
    fireEvent.click(screen.getByRole('button', { name: 'Publicar reporte de perdida' }));

    await screen.findByText('Reporte publicado');

    const caja = ZONAS.Armenia;
    expect(client.crearReporte).toHaveBeenCalledWith(
      expect.objectContaining({
        user_id: 1,
        tipo: 'perdido',
        zona: 'Armenia',
        lat: caja.centroLat,
        lng: caja.centroLng,
      }),
    );
    // Sin situacion en un perdido (el backend lo rechazaría con 422).
    expect(vi.mocked(client.crearReporte).mock.calls[0][0].situacion).toBeUndefined();
  });

  it('las características elegidas van en el payload; sin elegir, no se envían', async () => {
    vi.mocked(client.crearReporte).mockResolvedValue(crearReporteRespuesta());

    renderReportar('perdido');
    llenarMinimo();
    fireEvent.change(screen.getByLabelText('Raza'), { target: { value: 'Labrador' } });
    fireEvent.change(screen.getByLabelText('Color'), { target: { value: 'Negro' } });
    fireEvent.change(screen.getByLabelText('Tamaño'), { target: { value: 'grande' } });
    fireEvent.click(screen.getByRole('button', { name: 'Publicar reporte de perdida' }));

    await screen.findByText('Reporte publicado');

    const payload = vi.mocked(client.crearReporte).mock.calls[0][0];
    expect(payload.raza).toBe('Labrador');
    expect(payload.color).toBe('Negro');
    expect(payload.tamano).toBe('grande');
  });

  it('publica un encontrado con situacion y sin nombre_mascota', async () => {
    vi.mocked(client.crearReporte).mockResolvedValue(
      crearReporteRespuesta({ tipo: 'encontrado', situacion: 'conmigo', nombre_mascota: null }),
    );

    renderReportar('encontrado');
    llenarMinimo();
    fireEvent.click(screen.getByRole('button', { name: 'Publicar reporte de encontrada' }));

    await screen.findByText('Reporte publicado');

    const payload = vi.mocked(client.crearReporte).mock.calls[0][0];
    expect(payload.situacion).toBe('conmigo');
    expect(payload.nombre_mascota).toBeUndefined();
  });

  it('con zona "Otro" exige la ciudad en texto antes de enviar', async () => {
    renderReportar('perdido');
    llenarMinimo();
    fireEvent.change(screen.getByLabelText('¿En qué zona?'), { target: { value: 'Otro' } });
    fireEvent.click(screen.getByRole('button', { name: 'Publicar reporte de perdida' }));

    await screen.findByText('Cuéntanos en qué ciudad o municipio estás.');
    expect(client.crearReporte).not.toHaveBeenCalled();
  });

  it('muestra el mensaje del backend si la publicación falla', async () => {
    vi.mocked(client.crearReporte).mockRejectedValue(
      new client.ApiError('El teléfono de contacto es obligatorio'),
    );

    renderReportar('perdido');
    llenarMinimo();
    fireEvent.click(screen.getByRole('button', { name: 'Publicar reporte de perdida' }));

    await screen.findByText('El teléfono de contacto es obligatorio');
  });
});
