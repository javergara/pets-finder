import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { Mascota } from '../api/types';
import { FILTROS_ADOPCION_DEFAULT } from '../lib/adopcion';
import { CatalogoAdopcion } from './CatalogoAdopcion';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return {
    ...actual,
    listarMascotas: vi.fn(),
    obtenerAdopcionesResumen: vi.fn(),
  };
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
    es_favorito: false,
    ya_solicitada: false,
    distancia_km: null,
    ...overrides,
  };
}

beforeEach(() => {
  vi.mocked(client.listarMascotas).mockResolvedValue([
    mascota(),
    mascota({ id: 8, nombre: 'Copito', especie: 'gato', tamano: 'pequeño' }),
  ]);
  vi.mocked(client.obtenerAdopcionesResumen).mockResolvedValue({ total: 0, recientes: [] });
});

afterEach(() => {
  vi.resetAllMocks();
});

function renderCatalogo() {
  return render(
    <MemoryRouter initialEntries={['/adoptar']}>
      <CatalogoAdopcion />
    </MemoryRouter>,
  );
}

describe('CatalogoAdopcion', () => {
  it('al montar pide el catálogo con los filtros por defecto y pinta las tarjetas', async () => {
    renderCatalogo();

    expect(client.listarMascotas).toHaveBeenCalledWith(FILTROS_ADOPCION_DEFAULT);
    expect(await screen.findByRole('heading', { name: 'Nala' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Copito' })).toBeInTheDocument();
  });

  it('el chip "Perro" filtra por especie y queda marcado como presionado', async () => {
    renderCatalogo();
    await screen.findByRole('heading', { name: 'Nala' });

    const chipPerro = screen.getByRole('button', { name: 'Perro' });
    expect(chipPerro).toHaveAttribute('aria-pressed', 'false');

    fireEvent.click(chipPerro);

    await waitFor(() => expect(client.listarMascotas).toHaveBeenCalledTimes(2));
    expect(client.listarMascotas).toHaveBeenLastCalledWith({
      ...FILTROS_ADOPCION_DEFAULT,
      especie: ['perro'],
    });
    expect(screen.getByRole('button', { name: 'Perro' })).toHaveAttribute('aria-pressed', 'true');
  });

  it('un segundo chip de la misma familia acumula en vez de reemplazar', async () => {
    renderCatalogo();
    await screen.findByRole('heading', { name: 'Nala' });

    fireEvent.click(screen.getByRole('button', { name: 'Perro' }));
    await waitFor(() => expect(client.listarMascotas).toHaveBeenCalledTimes(2));
    fireEvent.click(screen.getByRole('button', { name: 'Gato' }));

    await waitFor(() => expect(client.listarMascotas).toHaveBeenCalledTimes(3));
    expect(client.listarMascotas).toHaveBeenLastCalledWith({
      ...FILTROS_ADOPCION_DEFAULT,
      especie: ['perro', 'gato'],
    });
    expect(screen.getByRole('button', { name: 'Perro' })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByRole('button', { name: 'Gato' })).toHaveAttribute('aria-pressed', 'true');
  });

  it('la zona es un control de valor único', async () => {
    renderCatalogo();
    await screen.findByRole('heading', { name: 'Nala' });

    fireEvent.change(screen.getByLabelText('Zona'), { target: { value: 'Cali' } });

    await waitFor(() => expect(client.listarMascotas).toHaveBeenCalledTimes(2));
    expect(client.listarMascotas).toHaveBeenLastCalledWith({
      ...FILTROS_ADOPCION_DEFAULT,
      zona: 'Cali',
    });
  });

  it('"Limpiar filtros" vuelve a los valores por defecto', async () => {
    renderCatalogo();
    await screen.findByRole('heading', { name: 'Nala' });

    fireEvent.click(screen.getByRole('button', { name: 'Perro' }));
    await waitFor(() => expect(client.listarMascotas).toHaveBeenCalledTimes(2));

    fireEvent.click(screen.getByRole('button', { name: 'Limpiar filtros' }));

    await waitFor(() => expect(client.listarMascotas).toHaveBeenCalledTimes(3));
    expect(client.listarMascotas).toHaveBeenLastCalledWith(FILTROS_ADOPCION_DEFAULT);
    expect(screen.getByRole('button', { name: 'Perro' })).toHaveAttribute('aria-pressed', 'false');
  });

  it('sin resultados muestra un estado vacío con su CTA, no el esqueleto de carga', async () => {
    vi.mocked(client.listarMascotas).mockResolvedValue([]);

    renderCatalogo();

    expect(await screen.findByText(/Todavía no hay mascotas/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /centros de ayuda/i })).toBeInTheDocument();
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  it('el CTA del estado vacío lleva a publicar una mascota, no a los centros de ayuda (AD-02)', async () => {
    vi.mocked(client.listarMascotas).mockResolvedValue([]);

    renderCatalogo();

    expect(
      await screen.findByRole('link', { name: 'Publicar una mascota en adopción' }),
    ).toHaveAttribute('href', '/adoptar/publicar');
  });

  it('el header ofrece siempre la entrada a publicar (AD-02)', async () => {
    renderCatalogo();
    await screen.findByRole('heading', { name: 'Nala' });

    expect(screen.getByRole('link', { name: 'Dar en adopción' })).toHaveAttribute(
      'href',
      '/adoptar/publicar',
    );
  });

  it('si la API falla muestra un mensaje en español y quita el esqueleto', async () => {
    vi.mocked(client.listarMascotas).mockRejectedValue(new Error('offline'));

    renderCatalogo();

    expect(await screen.findByRole('alert')).toHaveTextContent(
      /No pudimos cargar las mascotas en adopción/i,
    );
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  it('la franja de adopciones logradas aparece cuando hay al menos una', async () => {
    vi.mocked(client.obtenerAdopcionesResumen).mockResolvedValue({
      total: 3,
      recientes: [
        {
          id: 4,
          nombre: 'Pelusa',
          especie: 'gato',
          raza: null,
          edad_meses: 24,
          fotos: ['/media/seed/pet_4.jpg'],
          estado: 'adoptado',
        },
      ],
    });

    renderCatalogo();

    expect(await screen.findByText('3')).toBeInTheDocument();
    expect(screen.getByText(/adopciones logradas/i)).toBeInTheDocument();
  });

  it('sin adopciones todavía, la franja no se muestra (nunca un cero triste)', async () => {
    renderCatalogo();
    await screen.findByRole('heading', { name: 'Nala' });

    expect(screen.queryByText(/adopciones logradas/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/adopción lograda/i)).not.toBeInTheDocument();
  });

  // Este caso reemplaza al que aseveraba que NO había chips de edad. Su premisa
  // ("el backend los ignora") dejó de ser cierta en el paso 5 de AD-03, cuando
  // `GET /api/pets` empezó a traducir `edad_categoria` a SQL: mantenerlo sería
  // fijar por test una limitación que ya no existe.
  it('el chip "Cachorra" filtra por tramo de edad y queda marcado como presionado', async () => {
    renderCatalogo();
    await screen.findByRole('heading', { name: 'Nala' });

    const chipCachorra = screen.getByRole('button', { name: 'Cachorra' });
    expect(chipCachorra).toHaveAttribute('aria-pressed', 'false');

    fireEvent.click(chipCachorra);

    await waitFor(() => expect(client.listarMascotas).toHaveBeenCalledTimes(2));
    expect(client.listarMascotas).toHaveBeenLastCalledWith({
      ...FILTROS_ADOPCION_DEFAULT,
      edad: ['cachorro'],
    });
    expect(screen.getByRole('button', { name: 'Cachorra' })).toHaveAttribute(
      'aria-pressed',
      'true',
    );
  });
});
