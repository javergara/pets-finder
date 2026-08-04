import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { MascotaNecesitaApoyo, Sponsorship } from '../api/types';
import { Apadrinar } from './Apadrinar';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return {
    ...actual,
    listarNecesitanApoyo: vi.fn(),
    crearApadrinamiento: vi.fn(),
  };
});

afterEach(() => {
  vi.resetAllMocks();
});

function renderConRouter() {
  return render(
    <MemoryRouter>
      <Apadrinar />
    </MemoryRouter>,
  );
}

const MASCOTAS: MascotaNecesitaApoyo[] = [
  {
    id: 1,
    nombre: 'Rocky',
    fotos: ['/media/rocky.jpg'],
    historia: 'Rocky lleva un año esperando un hogar.',
    monto_recaudado_cop: 60000,
    porcentaje_cubierto: 30,
  },
  {
    id: 2,
    nombre: 'Mishi',
    fotos: [],
    historia: 'Mishi es una gata senior muy cariñosa.',
    monto_recaudado_cop: 180000,
    porcentaje_cubierto: 90,
  },
];

const SPONSORSHIP_CREADO: Sponsorship = {
  id: 5,
  pet: { id: 1, nombre: 'Rocky', fotos: ['/media/rocky.jpg'] },
  monto_cop: 70000,
  periodicidad: 'mensual',
  activo: true,
  iniciado_en: '2026-08-03T00:00:00Z',
  novedad: null,
};

describe('Apadrinar', () => {
  it('renderiza los tres niveles de donación y el selector de periodicidad', async () => {
    vi.mocked(client.listarNecesitanApoyo).mockResolvedValue(MASCOTAS);

    renderConRouter();

    expect(screen.getByText('$30.000')).toBeInTheDocument();
    expect(screen.getByText('$70.000')).toBeInTheDocument();
    expect(screen.getByText('Monto libre')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Mensual/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Pago único/ })).toBeInTheDocument();

    await screen.findByText('Rocky');
  });

  it('seleccionar "Monto libre" habilita el input y, vacío, deshabilita el botón Apadrinar', async () => {
    vi.mocked(client.listarNecesitanApoyo).mockResolvedValue(MASCOTAS);

    renderConRouter();
    await screen.findByText('Rocky');

    expect(screen.queryByLabelText(/Cuánto quieres aportar/)).not.toBeInTheDocument();

    fireEvent.click(screen.getByText('Monto libre'));

    const input = screen.getByLabelText(/Cuánto quieres aportar/);
    expect(input).toBeInTheDocument();

    const botones = screen.getAllByRole('button', { name: 'Apadrinar' });
    expect(botones[0]).toBeDisabled();

    fireEvent.change(input, { target: { value: '50000' } });
    expect(botones[0]).not.toBeDisabled();

    fireEvent.change(input, { target: { value: '' } });
    expect(botones[0]).toBeDisabled();
  });

  it('selecciona el nivel $70.000 y apadrina con la periodicidad mensual por defecto', async () => {
    vi.mocked(client.listarNecesitanApoyo).mockResolvedValue(MASCOTAS);
    vi.mocked(client.crearApadrinamiento).mockResolvedValue(SPONSORSHIP_CREADO);

    renderConRouter();
    await screen.findByText('Rocky');

    fireEvent.click(screen.getByText('$70.000'));
    const botones = screen.getAllByRole('button', { name: 'Apadrinar' });
    fireEvent.click(botones[0]);

    await screen.findByText(/¡Gracias por apadrinar a Rocky!/);

    expect(client.crearApadrinamiento).toHaveBeenCalledWith({
      user_id: expect.any(Number),
      pet_id: 1,
      monto_cop: 70000,
      periodicidad: 'mensual',
    });
  });

  it('la lista "Necesitan apoyo ahora" renderiza barra de progreso y porcentaje por mascota', async () => {
    vi.mocked(client.listarNecesitanApoyo).mockResolvedValue(MASCOTAS);

    renderConRouter();

    expect(await screen.findByText(/30% cubierto/)).toBeInTheDocument();
    expect(screen.getByText(/90% cubierto/)).toBeInTheDocument();
    expect(screen.getByText('Rocky')).toBeInTheDocument();
    expect(screen.getByText('Mishi')).toBeInTheDocument();
  });

  it('si el backend rechaza el apadrinamiento, muestra el mensaje de error', async () => {
    vi.mocked(client.listarNecesitanApoyo).mockResolvedValue(MASCOTAS);
    vi.mocked(client.crearApadrinamiento).mockRejectedValue(
      new client.ApiError('El usuario 1 no existe'),
    );

    renderConRouter();
    await screen.findByText('Rocky');

    const botones = screen.getAllByRole('button', { name: 'Apadrinar' });
    fireEvent.click(botones[0]);

    await screen.findByText('El usuario 1 no existe');
  });
});
