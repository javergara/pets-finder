import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { ShelterProfile, Solicitud } from '../api/types';
import { PanelRefugio } from './PanelRefugio';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return { ...actual, obtenerRefugio: vi.fn(), listarSolicitudes: vi.fn() };
});

afterEach(() => {
  vi.resetAllMocks();
});

function renderConRouter() {
  return render(
    <MemoryRouter>
      <PanelRefugio />
    </MemoryRouter>,
  );
}

const PERFIL_BASE: ShelterProfile = {
  id: 1,
  nombre: 'Refugio Huellas de Bogotá',
  ciudad: 'Bogotá',
  verificado: true,
  tiempo_respuesta_horas: 12,
  logo_url: null,
  metricas: {
    mascotas_publicadas: 6,
    interesados_este_mes: 8,
    visitas_agendadas: 2,
    adopciones_cerradas: 15,
    apadrinamientos_recaudados_cop: 250000,
  },
};

const SOLICITUD_SIN_RESPONDER: Solicitud = {
  id: 1,
  estado: 'solicitado',
  creado_en: '2026-01-01T00:00:00Z',
  adoptante: { id: 3, nombre: 'Ana Martínez' },
  pet: { id: 17, nombre: 'Canela', raza: 'Cocker mestizo', fotos: [] },
  afinidad: { score: 82, explicacion: '', incompatible: false },
  etiqueta: 'Sin responder · 5 días',
};

const SOLICITUD_VISITA: Solicitud = {
  id: 2,
  estado: 'visita_agendada',
  creado_en: '2026-01-02T00:00:00Z',
  adoptante: { id: 4, nombre: 'Luis Gómez' },
  pet: { id: 18, nombre: 'Toby', raza: 'Labrador', fotos: [] },
  afinidad: { score: 91, explicacion: '', incompatible: false },
  etiqueta: 'Visita agendada',
};

describe('PanelRefugio', () => {
  it('muestra cabecera, 4 métricas y tabla de solicitudes con colores de etiqueta', async () => {
    vi.mocked(client.obtenerRefugio).mockResolvedValue(PERFIL_BASE);
    vi.mocked(client.listarSolicitudes).mockResolvedValue([
      SOLICITUD_SIN_RESPONDER,
      SOLICITUD_VISITA,
    ]);

    renderConRouter();

    expect(await screen.findByText('Refugio Huellas de Bogotá')).toBeInTheDocument();
    expect(screen.getByText('6 mascotas publicadas')).toBeInTheDocument();

    const publicarLink = screen.getByRole('link', { name: 'Publicar mascota' });
    expect(publicarLink).toHaveAttribute('href', '/refugio/publicar');

    expect(screen.getByText('8')).toBeInTheDocument();
    expect(screen.getByText('Interesados este mes')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('Visitas agendadas')).toBeInTheDocument();
    expect(screen.getByText('15')).toBeInTheDocument();
    expect(screen.getByText('Adopciones cerradas')).toBeInTheDocument();
    expect(screen.getByText('$250.000')).toBeInTheDocument();
    expect(screen.getByText('Apadrinamientos recaudados')).toBeInTheDocument();

    expect(screen.getByText('Ana Martínez')).toBeInTheDocument();
    expect(screen.getByText('Canela')).toBeInTheDocument();
    expect(screen.getByText('82%')).toBeInTheDocument();

    const etiquetaOchre = screen.getByText('Sin responder · 5 días');
    expect(etiquetaOchre).toHaveClass('text-ochre');

    const etiquetaForest = screen.getByText('Visita agendada');
    expect(etiquetaForest).toHaveClass('text-forest');

    const revisarLinks = screen.getAllByRole('link', { name: 'Revisar' });
    expect(revisarLinks).toHaveLength(2);
    expect(revisarLinks[0]).toHaveAttribute('href', '/refugio/solicitudes/1');
  });

  it('muestra un estado vacío razonable cuando no hay solicitudes', async () => {
    vi.mocked(client.obtenerRefugio).mockResolvedValue(PERFIL_BASE);
    vi.mocked(client.listarSolicitudes).mockResolvedValue([]);

    renderConRouter();

    expect(await screen.findByText('Refugio Huellas de Bogotá')).toBeInTheDocument();
    expect(
      screen.getByText('Todavía no llegan solicitudes de adopción para tus mascotas publicadas.'),
    ).toBeInTheDocument();
  });
});
