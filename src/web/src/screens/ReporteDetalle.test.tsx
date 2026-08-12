import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { Reporte } from '../api/types';
import { ZONAS } from '../lib/ciudades';
import { ReporteDetalle } from './ReporteDetalle';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return {
    ...actual,
    obtenerReporte: vi.fn(),
    listarCoincidencias: vi.fn(),
    marcarReunido: vi.fn(),
  };
});

beforeEach(() => {
  // La mayoría de los casos no ejercita coincidencias: lista vacía por defecto.
  vi.mocked(client.listarCoincidencias).mockResolvedValue([]);
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
    descripcion: 'Criollo color miel con collar rojo',
    foto_url: '/media/seed/report_1.jpg',
    zona: 'Armenia',
    ciudad_texto: null,
    barrio: 'La Castellana',
    lat: ZONAS.Armenia.centroLat,
    lng: ZONAS.Armenia.centroLng,
    situacion: null,
    fecha_evento: '2026-08-10',
    telefono_contacto: '3001234561',
    estado: 'activo',
    creado_en: '2026-08-12T08:00:00',
    resuelto_en: null,
    ...overrides,
  };
}

function renderDetalle(id = 1) {
  return render(
    <MemoryRouter initialEntries={[`/reporte/${id}`]}>
      <Routes>
        <Route path="/reporte/:id" element={<ReporteDetalle />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('ReporteDetalle', () => {
  it('muestra los datos del reporte y los hrefs exactos de WhatsApp y llamada', async () => {
    vi.mocked(client.obtenerReporte).mockResolvedValue(crearReporte());

    renderDetalle();

    expect(await screen.findByRole('heading', { name: 'Rocky' })).toBeInTheDocument();
    expect(screen.getByText('Criollo color miel con collar rojo')).toBeInTheDocument();

    const whatsapp = screen.getByRole('link', { name: 'Contactar por WhatsApp' });
    const href = whatsapp.getAttribute('href') ?? '';
    expect(href.startsWith('https://wa.me/573001234561?text=')).toBe(true);
    // El mensaje precargado menciona el reporte y la app.
    const texto = decodeURIComponent(href.split('?text=')[1]);
    expect(texto).toContain('Rocky');
    expect(texto).toContain('Reencuentro');

    expect(screen.getByRole('link', { name: 'Llamar' })).toHaveAttribute(
      'href',
      'tel:+573001234561',
    );
  });

  it('el mini-mapa incluye el pin del reporte con su color por tipo', async () => {
    // Los tiles y la posición real los pinta Leaflet en el navegador (no corre
    // en jsdom); el contrato testeable es el equivalente accesible del pin.
    vi.mocked(client.obtenerReporte).mockResolvedValue(crearReporte());

    renderDetalle();

    const pin = await screen.findByRole('button', {
      name: 'Ubicación del reporte de Rocky',
    });
    expect(pin.className).toContain('bg-danger');
  });

  it('un encontrado usa la especie como título, el badge forest y su situación', async () => {
    vi.mocked(client.obtenerReporte).mockResolvedValue(
      crearReporte({
        tipo: 'encontrado',
        nombre_mascota: null,
        especie: 'gato',
        situacion: 'conmigo',
      }),
    );

    renderDetalle();

    expect(await screen.findByRole('heading', { name: 'Gato' })).toBeInTheDocument();
    expect(screen.getByText('Encontrada')).toBeInTheDocument();
    expect(screen.getByText('La tiene resguardada quien la reportó')).toBeInTheDocument();
  });

  it('muestra las posibles coincidencias con su distancia y link al detalle', async () => {
    vi.mocked(client.obtenerReporte).mockResolvedValue(crearReporte());
    vi.mocked(client.listarCoincidencias).mockResolvedValue([
      {
        ...crearReporte({
          id: 2,
          tipo: 'encontrado',
          nombre_mascota: null,
          situacion: 'conmigo',
          descripcion: 'Perro color miel resguardado',
        }),
        distancia_km: 0.6,
      },
    ]);

    renderDetalle();

    expect(await screen.findByText('Posibles coincidencias')).toBeInTheDocument();
    expect(screen.getByText('a 0.6 km')).toBeInTheDocument();
    const links = screen.getAllByRole('link');
    expect(links.some((l) => l.getAttribute('href') === '/reporte/2')).toBe(true);
  });

  it('sin coincidencias no muestra la sección', async () => {
    vi.mocked(client.obtenerReporte).mockResolvedValue(crearReporte());

    renderDetalle();

    await screen.findByRole('heading', { name: 'Rocky' });
    expect(screen.queryByText('Posibles coincidencias')).not.toBeInTheDocument();
  });

  it('un reporte reunido celebra el reencuentro y no muestra botones de contacto', async () => {
    vi.mocked(client.obtenerReporte).mockResolvedValue(
      crearReporte({ estado: 'reunido', resuelto_en: '2026-08-12T15:00:00' }),
    );

    renderDetalle();

    expect(
      await screen.findByText('Esta mascota ya se reencontró con su familia. 💚'),
    ).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'Contactar por WhatsApp' })).not.toBeInTheDocument();
  });

  it('el botón de marcar reunida solo aparece para el autor, y al usarlo celebra', async () => {
    // Sin nada en localStorage getActiveUserId() cae a DEMO_USER_ID=1 == user_id del reporte.
    vi.mocked(client.obtenerReporte).mockResolvedValue(crearReporte({ user_id: 1 }));
    vi.mocked(client.marcarReunido).mockResolvedValue(
      crearReporte({ estado: 'reunido', resuelto_en: '2026-08-12T15:00:00' }),
    );

    renderDetalle();

    const boton = await screen.findByRole('button', { name: 'Marcar como reunida' });
    boton.click();

    expect(
      await screen.findByText('Esta mascota ya se reencontró con su familia. 💚'),
    ).toBeInTheDocument();
    expect(client.marcarReunido).toHaveBeenCalledWith(1, 1);
  });

  it('el botón de marcar reunida NO aparece para quien no es el autor', async () => {
    vi.mocked(client.obtenerReporte).mockResolvedValue(crearReporte({ user_id: 2 }));

    renderDetalle();

    await screen.findByRole('heading', { name: 'Rocky' });
    expect(screen.queryByRole('button', { name: 'Marcar como reunida' })).not.toBeInTheDocument();
  });
});
