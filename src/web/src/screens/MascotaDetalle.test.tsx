import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { Mascota, Publicador } from '../api/types';
import { MascotaDetalle } from './MascotaDetalle';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return { ...actual, obtenerMascota: vi.fn() };
});

afterEach(() => {
  vi.resetAllMocks();
});

function publicadorOrganizacion(overrides: Partial<Publicador> = {}): Publicador {
  return {
    tipo: 'organizacion',
    id: 3,
    nombre: 'Fundación Huellitas',
    telefono_contacto: '3001112233',
    zona: 'Armenia',
    ciudad_texto: null,
    barrio: 'Centro',
    foto_url: null,
    ...overrides,
  };
}

function publicadorRescatista(overrides: Partial<Publicador> = {}): Publicador {
  return {
    tipo: 'rescatista',
    // ⚠️ Es un id de `users`, no de `organizaciones`: el mismo número existe en
    // las dos tablas y apuntan a cosas distintas.
    id: 3,
    nombre: 'Ana Martínez',
    telefono_contacto: '3009998877',
    zona: 'Pereira',
    ciudad_texto: null,
    barrio: null,
    foto_url: null,
    ...overrides,
  };
}

function mascota(overrides: Partial<Mascota> = {}): Mascota {
  return {
    id: 7,
    organizacion_id: 3,
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
    historia: 'La rescataron del barrio Providencia después del sismo.',
    tags: ['cariñosa', 'buena con niños'],
    esterilizado: true,
    vacunas_al_dia: true,
    microchip: true,
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
    publicador: publicadorOrganizacion(),
    afinidad: null,
    es_favorito: false,
    ya_solicitada: false,
    distancia_km: null,
    ...overrides,
  };
}

function renderFicha() {
  return render(
    <MemoryRouter initialEntries={['/adoptar/mascota/7']}>
      <Routes>
        <Route path="/adoptar/mascota/:id" element={<MascotaDetalle />} />
        <Route path="/adoptar" element={<div>Catálogo stub</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('MascotaDetalle', () => {
  it('muestra el nombre, la historia y la ficha de datos', async () => {
    vi.mocked(client.obtenerMascota).mockResolvedValue(mascota());

    renderFicha();

    expect(await screen.findByRole('heading', { name: 'Nala' })).toBeInTheDocument();
    expect(client.obtenerMascota).toHaveBeenCalledWith(7);
    expect(
      screen.getByText('La rescataron del barrio Providencia después del sismo.'),
    ).toBeInTheDocument();
    expect(screen.getByText('Criolla')).toBeInTheDocument();
    expect(screen.getByText('Hembra')).toBeInTheDocument();
    expect(screen.getByText('Mediana')).toBeInTheDocument();
    expect(screen.getByText('Energía media')).toBeInTheDocument();
    // edadLegible(18) trunca a "1 año" (nunca "2 años") y el tramo lo dice el chip.
    expect(screen.getByText('1 año')).toBeInTheDocument();
    expect(screen.getByText('Joven')).toBeInTheDocument();
    expect(screen.getByText('cariñosa')).toBeInTheDocument();
  });

  it('con varias fotos usa la galería con miniaturas', async () => {
    vi.mocked(client.obtenerMascota).mockResolvedValue(
      mascota({ fotos: ['/media/seed/pet_7.jpg', '/media/seed/pet_7b.jpg'] }),
    );

    renderFicha();

    await screen.findByRole('heading', { name: 'Nala' });
    expect(screen.getByRole('button', { name: 'Ver foto 1' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Ver foto 2' })).toBeInTheDocument();
    expect(screen.getByAltText('Foto de Nala, en adopción')).toBeInTheDocument();
  });

  it('con una sola foto no hay miniaturas', async () => {
    vi.mocked(client.obtenerMascota).mockResolvedValue(mascota());

    renderFicha();

    await screen.findByRole('heading', { name: 'Nala' });
    expect(screen.queryByRole('button', { name: /Ver foto/ })).not.toBeInTheDocument();
    expect(screen.getByAltText('Foto de Nala, en adopción')).toBeInTheDocument();
  });

  // Acceptance A3, literal: esterilizado / vacunas al día / microchip /
  // desparasitado. Los dos extremos, porque un checklist que siempre dice ✓ no
  // informa nada.
  const SALUD = ['Esterilización', 'Vacunas al día', 'Microchip', 'Desparasitación'];

  it('el checklist de salud marca ✓ lo que está confirmado', async () => {
    vi.mocked(client.obtenerMascota).mockResolvedValue(
      mascota({ esterilizado: true, vacunas_al_dia: true, microchip: true, desparasitado: true }),
    );

    renderFicha();

    await screen.findByRole('heading', { name: 'Nala' });
    for (const dato of SALUD) {
      expect(screen.getByText(`✓ ${dato}`)).toBeInTheDocument();
    }
  });

  it('el checklist de salud marca — lo que no está confirmado', async () => {
    vi.mocked(client.obtenerMascota).mockResolvedValue(
      mascota({
        esterilizado: false,
        vacunas_al_dia: false,
        microchip: false,
        desparasitado: false,
      }),
    );

    renderFicha();

    await screen.findByRole('heading', { name: 'Nala' });
    for (const dato of SALUD) {
      expect(screen.getByText(`— ${dato}`)).toBeInTheDocument();
    }
  });

  it('si publica una organización, su nombre lleva a su perfil', async () => {
    vi.mocked(client.obtenerMascota).mockResolvedValue(mascota());

    renderFicha();

    await screen.findByRole('heading', { name: 'Nala' });
    expect(screen.getByRole('link', { name: 'Fundación Huellitas' })).toHaveAttribute(
      'href',
      '/organizacion/3',
    );
  });

  it('si publica un rescatista, su nombre NO enlaza a ningún perfil de organización', async () => {
    vi.mocked(client.obtenerMascota).mockResolvedValue(
      mascota({
        organizacion_id: null,
        user_id: 3,
        telefono_contacto: '3009998877',
        publicador: publicadorRescatista(),
      }),
    );

    renderFicha();

    await screen.findByRole('heading', { name: 'Nala' });
    expect(screen.getByText('Ana Martínez')).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'Ana Martínez' })).not.toBeInTheDocument();
    // El id 3 de un rescatista es de `users`: /organizacion/3 sería otra entidad.
    const enlacesAOrganizacion = screen
      .getAllByRole('link')
      .filter((a) => (a.getAttribute('href') ?? '').startsWith('/organizacion'));
    expect(enlacesAOrganizacion).toHaveLength(0);
  });

  it('el botón de WhatsApp lleva al teléfono del publicador con el mensaje precargado', async () => {
    vi.mocked(client.obtenerMascota).mockResolvedValue(mascota());

    renderFicha();

    await screen.findByRole('heading', { name: 'Nala' });
    const whatsapp = screen.getByRole('link', { name: 'Escribir por WhatsApp' });
    expect(whatsapp).toHaveAttribute('href', expect.stringContaining('wa.me'));
    const href = whatsapp.getAttribute('href') ?? '';
    expect(href.startsWith('https://wa.me/573001112233?text=')).toBe(true);
    expect(decodeURIComponent(href.split('?text=')[1])).toBe(
      'Hola, vi a Nala en Pet Finder Col y me interesa adoptarla. ¿Sigue disponible?',
    );
  });

  it('sin teléfono de contacto no se pinta el botón de WhatsApp', async () => {
    vi.mocked(client.obtenerMascota).mockResolvedValue(
      mascota({ publicador: publicadorOrganizacion({ telefono_contacto: null }) }),
    );

    renderFicha();

    await screen.findByRole('heading', { name: 'Nala' });
    expect(screen.queryByRole('link', { name: 'Escribir por WhatsApp' })).not.toBeInTheDocument();
    expect(screen.getByText(/no dejó un teléfono/i)).toBeInTheDocument();
  });

  it('incluye el aviso de seguridad antes de coordinar un encuentro', async () => {
    vi.mocked(client.obtenerMascota).mockResolvedValue(mascota());

    renderFicha();

    await screen.findByRole('heading', { name: 'Nala' });
    expect(screen.getByText(/Pet Finder Col no verifica los reportes/)).toBeInTheDocument();
  });

  it('si la mascota no existe muestra el mensaje del backend y la salida al catálogo, sin esqueleto', async () => {
    vi.mocked(client.obtenerMascota).mockRejectedValue(
      new client.ApiError('La mascota 7 no existe'),
    );

    renderFicha();

    expect(await screen.findByRole('alert')).toHaveTextContent('La mascota 7 no existe');
    expect(screen.getByRole('link', { name: /Ver las mascotas en adopción/i })).toHaveAttribute(
      'href',
      '/adoptar',
    );
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  it('un fallo de red también sale del esqueleto, con copy en español', async () => {
    vi.mocked(client.obtenerMascota).mockRejectedValue(new Error('offline'));

    renderFicha();

    expect(await screen.findByRole('alert')).toHaveTextContent(
      /No pudimos cargar esta mascota. Revisa tu conexión e intenta de nuevo./,
    );
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });
});
