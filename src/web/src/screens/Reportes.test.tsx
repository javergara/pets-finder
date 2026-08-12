import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { Reporte } from '../api/types';
import { Reportes } from './Reportes';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return { ...actual, listarReportesPaginado: vi.fn(), obtenerConteos: vi.fn() };
});

beforeEach(() => {
  vi.mocked(client.listarReportesPaginado).mockResolvedValue({ items: [], total: 0 });
  vi.mocked(client.obtenerConteos).mockResolvedValue({ perdidos: 0, encontrados: 0 });
});

afterEach(() => {
  vi.resetAllMocks();
});

function crearReporte(overrides: Partial<Reporte> = {}): Reporte {
  return {
    id: 1,
    user_id: 1,
    tipo: 'perdido',
    especie: 'perro',
    nombre_mascota: 'Rocky',
    raza: null,
    color: null,
    tamano: null,
    descripcion: 'Criollo color miel con collar rojo',
    foto_url: '/media/seed/report_1.jpg',
    zona: 'Armenia',
    ciudad_texto: null,
    barrio: 'La Castellana',
    lat: 4.54,
    lng: -75.68,
    situacion: null,
    fecha_evento: '2026-08-10',
    telefono_contacto: '3001234561',
    fuente: 'manual',
    crawl_metadata: null,
    idempotency_id: null,
    estado: 'activo',
    creado_en: '2026-08-12T08:00:00',
    resuelto_en: null,
    ...overrides,
  };
}

function renderReportes(entrada = '/reportes') {
  return render(
    <MemoryRouter initialEntries={[entrada]}>
      <Reportes />
    </MemoryRouter>,
  );
}

describe('Reportes', () => {
  it('muestra los reportes con tipo, especie, zona y fecha', async () => {
    vi.mocked(client.listarReportesPaginado).mockResolvedValue({
      items: [
        crearReporte(),
        crearReporte({
          id: 2,
          tipo: 'encontrado',
          especie: 'gato',
          nombre_mascota: null,
          situacion: 'conmigo',
          zona: 'Pereira',
          fecha_evento: '2026-08-11',
        }),
      ],
      total: 2,
    });

    renderReportes();

    expect(await screen.findByText('Rocky')).toBeInTheDocument();
    expect(screen.getByText('Se perdió')).toBeInTheDocument();
    expect(screen.getByText('Encontrada')).toBeInTheDocument();
    // "Armenia"/"Pereira" también existen como opciones del filtro de zona:
    // la aserción se limita al pie de cada tarjeta.
    const tarjetaRocky = screen.getByRole('link', { name: /Rocky/ });
    expect(within(tarjetaRocky).getByText('Armenia')).toBeInTheDocument();
    // El pie une fecha del evento + recencia (feature 34): "10/08/2026 · hace …".
    expect(within(tarjetaRocky).getByText(/10\/08\/2026 · hace/)).toBeInTheDocument();
    const tarjetaGato = screen.getByRole('link', { name: /Gato/ });
    expect(within(tarjetaGato).getByText('Pereira')).toBeInTheDocument();
    // El encontrado sin nombre usa la especie como título.
    expect(screen.getByRole('heading', { name: 'Gato' })).toBeInTheDocument();
    // El listado inicial se pide sin filtros: orden y exclusión de reunidos los decide la API.
    expect(client.listarReportesPaginado).toHaveBeenCalledWith({}, 12, 0);
  });

  it('cambiar un filtro re-consulta al backend con ese filtro', async () => {
    vi.mocked(client.listarReportesPaginado).mockResolvedValue({
      items: [crearReporte()],
      total: 1,
    });

    renderReportes();
    await screen.findByText('Rocky');

    fireEvent.change(screen.getByLabelText('Tipo'), { target: { value: 'perdido' } });
    await waitFor(() =>
      expect(client.listarReportesPaginado).toHaveBeenLastCalledWith({ tipo: 'perdido' }, 12, 0),
    );

    fireEvent.change(screen.getByLabelText('Zona'), { target: { value: 'Cali' } });
    await waitFor(() =>
      expect(client.listarReportesPaginado).toHaveBeenLastCalledWith(
        { tipo: 'perdido', zona: 'Cali' },
        12,
        0,
      ),
    );
  });

  it('los filtros de características re-consultan, y la raza solo aparece con especie', async () => {
    vi.mocked(client.listarReportesPaginado).mockResolvedValue({
      items: [crearReporte()],
      total: 1,
    });

    renderReportes();
    await screen.findByText('Rocky');

    // Sin especie elegida no hay filtro de raza.
    expect(screen.queryByLabelText('Raza')).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Color'), { target: { value: 'Negro' } });
    await waitFor(() =>
      expect(client.listarReportesPaginado).toHaveBeenLastCalledWith({ color: 'Negro' }, 12, 0),
    );

    fireEvent.change(screen.getByLabelText('Tamaño'), { target: { value: 'grande' } });
    await waitFor(() =>
      expect(client.listarReportesPaginado).toHaveBeenLastCalledWith(
        { color: 'Negro', tamano: 'grande' },
        12,
        0,
      ),
    );

    fireEvent.change(screen.getByLabelText('Especie'), { target: { value: 'perro' } });
    fireEvent.change(await screen.findByLabelText('Raza'), { target: { value: 'Labrador' } });
    await waitFor(() =>
      expect(client.listarReportesPaginado).toHaveBeenLastCalledWith(
        { especie: 'perro', raza: 'Labrador', color: 'Negro', tamano: 'grande' },
        12,
        0,
      ),
    );
  });

  it('cada tarjeta navega a /reporte/:id', async () => {
    vi.mocked(client.listarReportesPaginado).mockResolvedValue({
      items: [crearReporte({ id: 7 })],
      total: 1,
    });

    renderReportes();

    const tarjeta = await screen.findByRole('link', { name: /Rocky/ });
    expect(tarjeta).toHaveAttribute('href', '/reporte/7');
  });

  it('sin resultados muestra el estado vacío con una acción', async () => {
    vi.mocked(client.listarReportesPaginado).mockResolvedValue({ items: [], total: 0 });

    renderReportes();

    expect(
      await screen.findByText('Ningún reporte coincide con estos filtros.'),
    ).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Crear el primer reporte' })).toHaveAttribute(
      'href',
      '/reportar/perdido',
    );
  });

  it('muestra los conteos por tipo del backend en el resumen y en el filtro', async () => {
    vi.mocked(client.obtenerConteos).mockResolvedValue({ perdidos: 12, encontrados: 5 });
    vi.mocked(client.listarReportesPaginado).mockResolvedValue({
      items: [crearReporte()],
      total: 1,
    });

    renderReportes();

    expect(await screen.findByText('12 perdidas')).toBeInTheDocument();
    expect(screen.getByText('5 encontradas')).toBeInTheDocument();
    expect(screen.getByText(/1 con estos filtros/)).toBeInTheDocument();
    expect((screen.getByRole('option', { name: 'Perdidas (12)' }) as HTMLOptionElement).value).toBe(
      'perdido',
    );
  });

  it('el filtro de estado pide los reunidos y las tarjetas celebran', async () => {
    vi.mocked(client.listarReportesPaginado).mockResolvedValue({
      items: [crearReporte({ estado: 'reunido', resuelto_en: '2026-08-12T10:00:00' })],
      total: 1,
    });

    renderReportes();
    fireEvent.change(screen.getByLabelText('Estado'), { target: { value: 'reunido' } });

    await waitFor(() =>
      expect(client.listarReportesPaginado).toHaveBeenLastCalledWith({ estado: 'reunido' }, 12, 0),
    );
    expect(await screen.findByText('Reunida 💚')).toBeInTheDocument();
  });

  it('llegar con ?estado=reunido (link de la landing) arranca en reunidos', async () => {
    vi.mocked(client.listarReportesPaginado).mockResolvedValue({ items: [], total: 0 });

    renderReportes('/reportes?estado=reunido');

    await waitFor(() =>
      expect(client.listarReportesPaginado).toHaveBeenCalledWith({ estado: 'reunido' }, 12, 0),
    );
    expect((screen.getByLabelText('Estado') as HTMLSelectElement).value).toBe('reunido');
  });

  it('escribir en Buscar re-consulta con q y conserva los filtros', async () => {
    vi.mocked(client.listarReportesPaginado).mockResolvedValue({
      items: [crearReporte()],
      total: 1,
    });

    renderReportes();
    await screen.findByText('Rocky');

    fireEvent.change(screen.getByLabelText('Tipo'), { target: { value: 'perdido' } });
    fireEvent.change(screen.getByLabelText('Buscar'), { target: { value: 'collar rojo' } });

    await waitFor(() =>
      expect(client.listarReportesPaginado).toHaveBeenLastCalledWith(
        { tipo: 'perdido', q: 'collar rojo' },
        12,
        0,
      ),
    );
  });

  it('Cargar más pide la página siguiente con offset y acumula sin perder filtros', async () => {
    const pagina1 = Array.from({ length: 12 }, (_, i) => crearReporte({ id: i + 1 }));
    vi.mocked(client.listarReportesPaginado).mockResolvedValue({ items: pagina1, total: 15 });

    renderReportes();
    const boton = await screen.findByRole('button', { name: 'Cargar más (3 restantes)' });

    vi.mocked(client.listarReportesPaginado).mockResolvedValue({
      items: [crearReporte({ id: 13, nombre_mascota: 'Extra' })],
      total: 15,
    });
    fireEvent.click(boton);

    expect(await screen.findByText('Extra')).toBeInTheDocument();
    expect(client.listarReportesPaginado).toHaveBeenLastCalledWith({}, 12, 12);
    // Los 12 de la primera página siguen renderizados (acumula, no reemplaza).
    expect(screen.getAllByText('Rocky').length).toBe(12);
  });
});
