import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { SolicitudDetalle as SolicitudDetalleType } from '../api/types';
import { SolicitudDetalle } from './SolicitudDetalle';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return { ...actual, obtenerSolicitud: vi.fn() };
});

afterEach(() => {
  vi.resetAllMocks();
});

function renderConRouter(matchId = '1') {
  return render(
    <MemoryRouter initialEntries={[`/refugio/solicitudes/${matchId}`]}>
      <Routes>
        <Route path="/refugio/solicitudes/:matchId" element={<SolicitudDetalle />} />
      </Routes>
    </MemoryRouter>,
  );
}

const SOLICITUD_DETALLE: SolicitudDetalleType = {
  id: 1,
  estado: 'solicitado',
  creado_en: '2026-01-01T00:00:00Z',
  adoptante: { id: 3, nombre: 'Ana Martínez' },
  pet: { id: 17, nombre: 'Canela', raza: 'Cocker mestizo', fotos: [] },
  afinidad: { score: 82, explicacion: '', incompatible: false },
  etiqueta: 'Cuestionario nuevo',
  bio: 'Amo los animales y tengo experiencia con perros grandes.',
  home_profile: {
    vivienda: 'casa',
    espacio_exterior: 'jardin',
    personas_en_casa: 3,
    tiene_ninos: true,
    tiene_otros_perros: false,
    tiene_otros_gatos: true,
    horas_fuera_dia: 6,
    experiencia_previa: 'mucha',
    presupuesto_mensual_cop: 300000,
    preferencia_especies: ['perro'],
    preferencia_tamanos: ['grande'],
    preferencia_energia: 'media',
  },
};

describe('SolicitudDetalle', () => {
  it('muestra el cuestionario completo y el "Sobre mí", sin botones de acción ausentes', async () => {
    vi.mocked(client.obtenerSolicitud).mockResolvedValue(SOLICITUD_DETALLE);

    renderConRouter();

    expect(await screen.findByText('Ana Martínez')).toBeInTheDocument();
    expect(screen.getByText('82% afín')).toBeInTheDocument();

    // Cuestionario completo (HogarResumen)
    expect(screen.getByText('Jardín')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getAllByText('Sí')).toHaveLength(2); // tiene_ninos + tiene_otros_gatos
    expect(screen.getByText('6h')).toBeInTheDocument();

    // Sobre mí
    expect(
      screen.getByText('Amo los animales y tengo experiencia con perros grandes.'),
    ).toBeInTheDocument();

    // Los tres botones de acción NO deben existir todavía (feature 10-adoption-request-flow):
    // ninguno de los tres nombres aparece como botón o enlace accionable.
    expect(screen.queryByRole('button', { name: /agendar visita/i })).not.toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: /pedir más información/i }),
    ).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /descartar/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /agendar visita/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /pedir más información/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /descartar/i })).not.toBeInTheDocument();

    // Nota de "próxima entrega" explícita, mencionando las tres acciones ausentes por nombre.
    const nota = screen.getByText(
      'Agendar visita, pedir más información y descartar con motivo estarán disponibles en una próxima entrega.',
    );
    expect(nota).toBeInTheDocument();
  });

  it('muestra copy de fallback cuando bio es null', async () => {
    vi.mocked(client.obtenerSolicitud).mockResolvedValue({ ...SOLICITUD_DETALLE, bio: null });

    renderConRouter();

    expect(
      await screen.findByText(
        'Todavía no escribió nada sobre sí. Esto lo ven los refugios al recibir su solicitud.',
      ),
    ).toBeInTheDocument();
  });
});
