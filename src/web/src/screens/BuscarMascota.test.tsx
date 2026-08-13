import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { Reporte } from '../api/types';
import { BuscarMascota } from './BuscarMascota';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return { ...actual, buscarParecidos: vi.fn() };
});

afterEach(() => {
  vi.resetAllMocks();
});

function crearResultado(overrides: Partial<Reporte> = {}) {
  return {
    id: 5,
    user_id: 1,
    tipo: 'encontrado' as const,
    especie: 'perro' as const,
    nombre_mascota: null,
    raza: null,
    color: 'Negro',
    tamano: 'mediano' as const,
    descripcion: 'Perro con collar rojo',
    foto_url: null,
    zona: 'Cali',
    ciudad_texto: null,
    barrio: null,
    lat: 3.45,
    lng: -76.53,
    situacion: 'conmigo' as const,
    fecha_evento: '2026-08-10',
    telefono_contacto: '3001234567',
    fuente: 'manual' as const,
    crawl_metadata: null,
    idempotency_id: null,
    estado: 'activo' as const,
    creado_en: new Date().toISOString(),
    resuelto_en: null,
    ...overrides,
    parecido: 85,
    razones: ['misma zona (Cali)', 'mismo color (negro)'],
  };
}

function renderBuscar() {
  return render(
    <MemoryRouter initialEntries={['/buscar']}>
      <BuscarMascota />
    </MemoryRouter>,
  );
}

describe('BuscarMascota', () => {
  it('por defecto busca entre las encontradas con los criterios elegidos', async () => {
    vi.mocked(client.buscarParecidos).mockResolvedValue([crearResultado()]);

    renderBuscar();
    fireEvent.change(screen.getByLabelText('Color'), { target: { value: 'Negro' } });
    fireEvent.change(screen.getByLabelText('Zona'), { target: { value: 'Cali' } });
    fireEvent.change(screen.getByLabelText(/Señas particulares/), {
      target: { value: 'collar rojo' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Buscar/ }));

    expect(client.buscarParecidos).toHaveBeenCalledWith({
      tipo: 'encontrado',
      especie: 'perro',
      zona: 'Cali',
      color: 'Negro',
      tamano: undefined,
      senas: 'collar rojo',
    });
    // El resultado se muestra con su parecido y razones.
    expect(await screen.findByText('Se parece en un 85%')).toBeInTheDocument();
    expect(screen.getByText('misma zona (Cali)')).toBeInTheDocument();
    // Y la tarjeta navega al detalle.
    const links = screen.getAllByRole('link');
    expect(links.some((l) => l.getAttribute('href') === '/reporte/5')).toBe(true);
  });

  it('en modo "Encontré una" busca entre las perdidas', async () => {
    vi.mocked(client.buscarParecidos).mockResolvedValue([]);

    renderBuscar();
    fireEvent.click(screen.getByRole('button', { name: 'Encontré una' }));
    fireEvent.click(screen.getByRole('button', { name: /Buscar/ }));

    expect(client.buscarParecidos).toHaveBeenCalledWith(
      expect.objectContaining({ tipo: 'perdido' }),
    );
    expect(await screen.findByText('Ningún reporte de esa especie por ahora')).toBeInTheDocument();
  });
});
