import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { MatchWithPet } from '../api/types';
import { MisMatches } from './MisMatches';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return { ...actual, listarMatches: vi.fn() };
});

afterEach(() => {
  vi.resetAllMocks();
});

function renderConRouter() {
  return render(
    <MemoryRouter>
      <MisMatches />
    </MemoryRouter>,
  );
}

describe('MisMatches', () => {
  it('muestra el estado vacío con un enlace a Descubrir cuando no hay matches', async () => {
    vi.mocked(client.listarMatches).mockResolvedValue([]);

    renderConRouter();

    expect(await screen.findByText('Aún no tienes matches')).toBeInTheDocument();
    const enlace = screen.getByRole('link', { name: /ir a descubrir/i });
    expect(enlace).toHaveAttribute('href', '/descubrir');
  });

  it('lista los matches con su afinidad y estado cuando sí hay', async () => {
    const match: MatchWithPet = {
      id: 1,
      estado: 'solicitado',
      creado_en: '2026-01-01T00:00:00Z',
      pet: {
        id: 17,
        nombre: 'Canela',
        raza: 'Cocker mestizo',
        edad_meses: 42,
        fotos: [],
        estado: 'disponible',
      },
      afinidad: { score: 94, explicacion: '', incompatible: false },
    };
    vi.mocked(client.listarMatches).mockResolvedValue([match]);

    renderConRouter();

    expect(await screen.findByText('Canela')).toBeInTheDocument();
    expect(screen.getByText('94%')).toBeInTheDocument();
    expect(screen.getByText('● Esperando refugio')).toBeInTheDocument();
  });
});
