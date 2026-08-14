import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import { PublicarAvisoAyuda } from './PublicarAvisoAyuda';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return { ...actual, crearAvisoAyuda: vi.fn() };
});

beforeEach(() => {
  localStorage.setItem('reencuentro_active_user_id', '5');
});

afterEach(() => {
  localStorage.clear();
  vi.resetAllMocks();
});

function renderPublicar(query = '?tipo=ofrezco') {
  return render(
    <MemoryRouter initialEntries={[`/ayudar/publicar-aviso${query}`]}>
      <Routes>
        <Route path="/ayudar/publicar-aviso" element={<PublicarAvisoAyuda />} />
        <Route path="/registro" element={<p>pantalla de registro</p>} />
        <Route path="/ayudar" element={<p>pantalla de ayudar</p>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('PublicarAvisoAyuda', () => {
  it('publica un aviso de ofrezco con zona y categoría, y navega a la Comunidad', async () => {
    vi.mocked(client.crearAvisoAyuda).mockResolvedValue({} as never);

    renderPublicar('?tipo=ofrezco');

    fireEvent.change(screen.getByLabelText('Categoría'), { target: { value: 'transporte' } });
    fireEvent.change(screen.getByLabelText('Título breve'), {
      target: { value: 'Puedo transportar animales' },
    });
    fireEvent.change(screen.getByLabelText('Descripción'), {
      target: { value: 'Tengo carro y tiempo los fines de semana.' },
    });
    fireEvent.change(screen.getByLabelText('Zona'), { target: { value: 'Cali' } });
    fireEvent.change(screen.getByLabelText('Teléfono de contacto (WhatsApp)'), {
      target: { value: '3001234567' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Publicar aviso' }));

    await waitFor(() =>
      expect(client.crearAvisoAyuda).toHaveBeenCalledWith({
        user_id: 5,
        tipo: 'ofrezco',
        categoria: 'transporte',
        titulo: 'Puedo transportar animales',
        descripcion: 'Tengo carro y tiempo los fines de semana.',
        zona: 'Cali',
        telefono_contacto: '3001234567',
      }),
    );
    expect(await screen.findByText('pantalla de ayudar')).toBeInTheDocument();
  });

  it('muestra el aviso de espacio público (feature 40) y valida campos', () => {
    renderPublicar('?tipo=pido');

    expect(screen.getByText(/espacio público/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Publicar aviso' }));
    expect(
      screen.getByText('Completa el título, la descripción, la zona y tu teléfono.'),
    ).toBeInTheDocument();
    expect(client.crearAvisoAyuda).not.toHaveBeenCalled();
  });

  it('sin cuenta redirige al registro con volver', () => {
    localStorage.clear();

    renderPublicar();

    expect(screen.getByText('pantalla de registro')).toBeInTheDocument();
  });
});
