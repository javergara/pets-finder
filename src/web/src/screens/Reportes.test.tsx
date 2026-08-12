import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { Reporte } from '../api/types';
import { Reportes } from './Reportes';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return { ...actual, listarReportes: vi.fn() };
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
    estado: 'activo',
    creado_en: '2026-08-12T08:00:00',
    resuelto_en: null,
    ...overrides,
  };
}

function renderReportes() {
  return render(
    <MemoryRouter>
      <Reportes />
    </MemoryRouter>,
  );
}

describe('Reportes', () => {
  it('muestra los reportes con tipo, especie, zona y fecha', async () => {
    vi.mocked(client.listarReportes).mockResolvedValue([
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
    ]);

    renderReportes();

    expect(await screen.findByText('Rocky')).toBeInTheDocument();
    expect(screen.getByText('Se perdió')).toBeInTheDocument();
    expect(screen.getByText('Encontrada')).toBeInTheDocument();
    // "Armenia"/"Pereira" también existen como opciones del filtro de zona:
    // la aserción se limita al pie de cada tarjeta.
    const tarjetaRocky = screen.getByRole('link', { name: /Rocky/ });
    expect(within(tarjetaRocky).getByText('Armenia')).toBeInTheDocument();
    expect(within(tarjetaRocky).getByText('10/08/2026')).toBeInTheDocument();
    const tarjetaGato = screen.getByRole('link', { name: /Gato/ });
    expect(within(tarjetaGato).getByText('Pereira')).toBeInTheDocument();
    // El encontrado sin nombre usa la especie como título.
    expect(screen.getByRole('heading', { name: 'Gato' })).toBeInTheDocument();
    // El listado inicial se pide sin filtros: orden y exclusión de reunidos los decide la API.
    expect(client.listarReportes).toHaveBeenCalledWith({});
  });

  it('cambiar un filtro re-consulta al backend con ese filtro', async () => {
    vi.mocked(client.listarReportes).mockResolvedValue([crearReporte()]);

    renderReportes();
    await screen.findByText('Rocky');

    fireEvent.change(screen.getByLabelText('Tipo'), { target: { value: 'perdido' } });
    await waitFor(() =>
      expect(client.listarReportes).toHaveBeenLastCalledWith({ tipo: 'perdido' }),
    );

    fireEvent.change(screen.getByLabelText('Zona'), { target: { value: 'Cali' } });
    await waitFor(() =>
      expect(client.listarReportes).toHaveBeenLastCalledWith({ tipo: 'perdido', zona: 'Cali' }),
    );
  });

  it('los filtros de características re-consultan, y la raza solo aparece con especie', async () => {
    vi.mocked(client.listarReportes).mockResolvedValue([crearReporte()]);

    renderReportes();
    await screen.findByText('Rocky');

    // Sin especie elegida no hay filtro de raza.
    expect(screen.queryByLabelText('Raza')).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Color'), { target: { value: 'Negro' } });
    await waitFor(() => expect(client.listarReportes).toHaveBeenLastCalledWith({ color: 'Negro' }));

    fireEvent.change(screen.getByLabelText('Tamaño'), { target: { value: 'grande' } });
    await waitFor(() =>
      expect(client.listarReportes).toHaveBeenLastCalledWith({ color: 'Negro', tamano: 'grande' }),
    );

    fireEvent.change(screen.getByLabelText('Especie'), { target: { value: 'perro' } });
    fireEvent.change(await screen.findByLabelText('Raza'), { target: { value: 'Labrador' } });
    await waitFor(() =>
      expect(client.listarReportes).toHaveBeenLastCalledWith({
        especie: 'perro',
        raza: 'Labrador',
        color: 'Negro',
        tamano: 'grande',
      }),
    );
  });

  it('cada tarjeta navega a /reporte/:id', async () => {
    vi.mocked(client.listarReportes).mockResolvedValue([crearReporte({ id: 7 })]);

    renderReportes();

    const tarjeta = await screen.findByRole('link', { name: /Rocky/ });
    expect(tarjeta).toHaveAttribute('href', '/reporte/7');
  });

  it('sin resultados muestra el estado vacío con una acción', async () => {
    vi.mocked(client.listarReportes).mockResolvedValue([]);

    renderReportes();

    expect(
      await screen.findByText('Ningún reporte coincide con estos filtros.'),
    ).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Crear el primer reporte' })).toHaveAttribute(
      'href',
      '/reportar/perdido',
    );
  });
});
