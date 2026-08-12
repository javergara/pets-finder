import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { Reporte } from '../api/types';
import { ZONAS } from '../lib/ciudades';
import { ReporteDetalle } from './ReporteDetalle';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return { ...actual, obtenerReporte: vi.fn() };
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

  it('el mini-mapa muestra el pin en la posición del reporte', async () => {
    vi.mocked(client.obtenerReporte).mockResolvedValue(crearReporte());

    renderDetalle();

    const pin = await screen.findByRole('button', {
      name: 'Ubicación del reporte de Rocky',
    });
    // El centro del bounding box de Armenia no cae en el centro exacto del
    // lienzo (el bounding box no es simétrico respecto al centro declarado),
    // pero la posición interpolada debe estar dentro del lienzo.
    const left = parseFloat(pin.style.left);
    const top = parseFloat(pin.style.top);
    expect(left).toBeGreaterThan(0);
    expect(left).toBeLessThan(100);
    expect(top).toBeGreaterThan(0);
    expect(top).toBeLessThan(100);
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
});
