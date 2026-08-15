import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import type { Mascota } from '../api/types';
import { MascotaCard } from './MascotaCard';

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
    historia: 'Rescatada del barrio Providencia, duerme donde le pongan una cobija.',
    tags: ['cariñosa', 'buena con niños'],
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

function renderCard(datos: Mascota) {
  return render(
    <MemoryRouter>
      <MascotaCard mascota={datos} />
    </MemoryRouter>,
  );
}

describe('MascotaCard', () => {
  it('muestra el nombre, la edad legible y los tags', () => {
    renderCard(mascota());

    expect(screen.getByRole('heading', { name: 'Nala' })).toBeInTheDocument();
    // 18 meses se dicen "1 año" (edadLegible trunca), nunca "2 años" ni "0 años".
    expect(screen.getByText(/1 año/)).toBeInTheDocument();
    expect(screen.getByText('cariñosa')).toBeInTheDocument();
    expect(screen.getByText('buena con niños')).toBeInTheDocument();
  });

  it('muestra la raza y la zona', () => {
    renderCard(mascota());

    expect(screen.getByText(/Criolla/)).toBeInTheDocument();
    expect(screen.getByText('Armenia')).toBeInTheDocument();
  });

  it('no rompe la tarjeta con muchos tags: muestra como mucho tres', () => {
    renderCard(mascota({ tags: ['uno', 'dos', 'tres', 'cuatro', 'cinco'] }));

    expect(screen.getByText('tres')).toBeInTheDocument();
    expect(screen.queryByText('cuatro')).not.toBeInTheDocument();
    expect(screen.queryByText('cinco')).not.toBeInTheDocument();
  });

  it('la foto carga en diferido y su alt menciona el nombre', () => {
    renderCard(mascota());

    const foto = screen.getByRole('img');
    expect(foto).toHaveAttribute('loading', 'lazy');
    expect(foto.getAttribute('alt')).toContain('Nala');
    // La ruta relativa pasa por mediaUrl (en test la base de la API es absoluta).
    expect(foto.getAttribute('src')).toContain('/media/seed/pet_7.jpg');
  });

  it('toda la tarjeta es un link a la ficha de la mascota', () => {
    renderCard(mascota({ id: 42 }));

    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('href', '/adoptar/mascota/42');
    expect(link).toHaveTextContent('Nala');
  });

  it.each([
    ['disponible' as const, 'En adopción'],
    ['en_proceso' as const, 'En proceso'],
    ['adoptado' as const, 'Adoptada 💚'],
  ])('el badge de estado %s dice "%s"', (estado, copy) => {
    renderCard(mascota({ estado }));

    expect(screen.getByText(copy)).toBeInTheDocument();
  });

  it('sin afinidad no muestra el porcentaje (en AD-01 siempre es null)', () => {
    renderCard(mascota());

    expect(screen.queryByText(/% afín/)).not.toBeInTheDocument();
  });

  it('con afinidad muestra el score', () => {
    renderCard(
      mascota({
        afinidad: {
          score: 88,
          explicacion: 'Encaja con tu hogar',
          razones: [],
          incompatible: false,
        },
      }),
    );

    expect(screen.getByText('88% afín')).toBeInTheDocument();
  });

  it('una mascota sin fotos se sigue viendo entera', () => {
    renderCard(mascota({ fotos: [] }));

    expect(screen.queryByRole('img')).not.toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Nala' })).toBeInTheDocument();
    expect(screen.getByRole('link')).toHaveAttribute('href', '/adoptar/mascota/7');
  });
});
