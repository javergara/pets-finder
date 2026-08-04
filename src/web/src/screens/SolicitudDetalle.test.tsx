import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { SolicitudDetalle as SolicitudDetalleType } from '../api/types';
import { DEMO_SHELTER_ID } from '../lib/constants';
import { SolicitudDetalle } from './SolicitudDetalle';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return {
    ...actual,
    obtenerSolicitud: vi.fn(),
    agendarVisita: vi.fn(),
    pedirInformacion: vi.fn(),
    descartarSolicitud: vi.fn(),
  };
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

const SOLICITUD_BASE: SolicitudDetalleType = {
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

function solicitudConEstado(estado: string, etiqueta = SOLICITUD_BASE.etiqueta) {
  return { ...SOLICITUD_BASE, estado, etiqueta };
}

describe('SolicitudDetalle', () => {
  it('muestra el cuestionario completo y el "Sobre mí"', async () => {
    vi.mocked(client.obtenerSolicitud).mockResolvedValue(SOLICITUD_BASE);

    renderConRouter();

    expect(await screen.findByText('Ana Martínez')).toBeInTheDocument();
    expect(screen.getByText('82% afín')).toBeInTheDocument();
    expect(screen.getByText('Jardín')).toBeInTheDocument();
    expect(
      screen.getByText('Amo los animales y tengo experiencia con perros grandes.'),
    ).toBeInTheDocument();
  });

  it('tiene un enlace "Ver conversación" hacia el hilo del match', async () => {
    vi.mocked(client.obtenerSolicitud).mockResolvedValue(SOLICITUD_BASE);

    renderConRouter('1');

    const enlace = await screen.findByRole('link', { name: 'Ver conversación' });
    expect(enlace).toHaveAttribute('href', '/refugio/solicitudes/1/mensajes');
  });

  it('muestra copy de fallback cuando bio es null', async () => {
    vi.mocked(client.obtenerSolicitud).mockResolvedValue({ ...SOLICITUD_BASE, bio: null });

    renderConRouter();

    expect(
      await screen.findByText(
        'Todavía no escribió nada sobre sí. Esto lo ven los refugios al recibir su solicitud.',
      ),
    ).toBeInTheDocument();
  });

  it.each([
    { estado: 'solicitado', agendar: false, info: false, descartar: false },
    { estado: 'en_revision', agendar: false, info: true, descartar: false },
    { estado: 'visita_agendada', agendar: true, info: true, descartar: false },
  ])(
    'estado "%s": habilita/deshabilita los botones según la matriz de transiciones',
    async ({ estado, agendar, info, descartar }) => {
      vi.mocked(client.obtenerSolicitud).mockResolvedValue(solicitudConEstado(estado));

      renderConRouter();
      await screen.findByText('Ana Martínez');

      expect(screen.getByRole('button', { name: 'Agendar visita' })).toHaveProperty(
        'disabled',
        agendar,
      );
      expect(screen.getByRole('button', { name: 'Pedir más información' })).toHaveProperty(
        'disabled',
        info,
      );
      expect(screen.getByRole('button', { name: 'Descartar' })).toHaveProperty(
        'disabled',
        descartar,
      );
    },
  );

  it('estado "cerrado" (terminal): no muestra los 3 botones de acción, solo una nota informativa', async () => {
    vi.mocked(client.obtenerSolicitud).mockResolvedValue(
      solicitudConEstado('cerrado', 'Solicitud cerrada'),
    );

    renderConRouter();
    await screen.findByText('Ana Martínez');

    expect(screen.queryByRole('button', { name: 'Agendar visita' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Pedir más información' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Descartar' })).not.toBeInTheDocument();
    expect(screen.getByText('Solicitud cerrada')).toBeInTheDocument();
  });

  it('agendar visita: llama al cliente con los ids correctos y actualiza la pantalla con la respuesta', async () => {
    vi.mocked(client.obtenerSolicitud).mockResolvedValue(solicitudConEstado('solicitado'));
    vi.mocked(client.agendarVisita).mockResolvedValue(
      solicitudConEstado('visita_agendada', 'Visita agendada'),
    );

    renderConRouter('1');
    await screen.findByText('Ana Martínez');

    fireEvent.click(screen.getByRole('button', { name: 'Agendar visita' }));

    expect(await screen.findByText(/Visita agendada/)).toBeInTheDocument();
    expect(client.agendarVisita).toHaveBeenCalledWith(DEMO_SHELTER_ID, 1);
  });

  it('descartar: el formulario valida el texto vacío, y al confirmar llama al cliente con el motivo exacto', async () => {
    vi.mocked(client.obtenerSolicitud).mockResolvedValue(solicitudConEstado('solicitado'));
    vi.mocked(client.descartarSolicitud).mockResolvedValue(
      solicitudConEstado('cerrado', 'Solicitud cerrada'),
    );

    renderConRouter('1');
    await screen.findByText('Ana Martínez');

    fireEvent.click(screen.getByRole('button', { name: 'Descartar' }));

    const confirmar = screen.getByRole('button', { name: 'Confirmar descarte' });
    expect(confirmar).toBeDisabled();

    const textarea = screen.getByLabelText('Motivo del descarte');
    fireEvent.change(textarea, { target: { value: '   ' } });
    expect(confirmar).toBeDisabled();

    fireEvent.change(textarea, { target: { value: 'El adoptante no respondió las llamadas.' } });
    expect(confirmar).not.toBeDisabled();

    fireEvent.click(confirmar);

    expect(await screen.findByText('Solicitud cerrada')).toBeInTheDocument();
    expect(client.descartarSolicitud).toHaveBeenCalledWith(
      DEMO_SHELTER_ID,
      1,
      'El adoptante no respondió las llamadas.',
    );
  });

  it('muestra el mensaje de ApiError si una acción falla (ej. 409 por carrera)', async () => {
    vi.mocked(client.obtenerSolicitud).mockResolvedValue(solicitudConEstado('solicitado'));
    vi.mocked(client.agendarVisita).mockRejectedValue(
      new client.ApiError("No se puede 'agendar-visita' una solicitud en estado 'cerrado'"),
    );

    renderConRouter('1');
    await screen.findByText('Ana Martínez');

    fireEvent.click(screen.getByRole('button', { name: 'Agendar visita' }));

    expect(
      await screen.findByText("No se puede 'agendar-visita' una solicitud en estado 'cerrado'"),
    ).toBeInTheDocument();
  });
});
