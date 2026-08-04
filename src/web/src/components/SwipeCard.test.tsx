import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { Pet } from '../api/types';
import { SwipeCard } from './SwipeCard';

const pet: Pet = {
  id: 1,
  shelter_id: 1,
  nombre: 'Canela',
  especie: 'perro',
  raza: 'Cocker mestizo',
  sexo: 'hembra',
  edad_meses: 42,
  tamano: 'mediano',
  energia: 'media',
  fotos: [],
  historia: '',
  tags: ['equilibrada'],
  esterilizado: true,
  vacunas_al_dia: true,
  microchip: true,
  desparasitado: true,
  apto_ninos: true,
  apto_perros: true,
  apto_gatos: true,
  estado: 'disponible',
  publicado_en: '2026-01-01T00:00:00Z',
  shelter: null,
  afinidad: { score: 94, explicacion: 'Buena combinación.', incompatible: false },
  es_favorito: false,
  lat: null,
  lng: null,
  distancia_km: null,
};

describe('SwipeCard', () => {
  it('muestra el nombre, la afinidad y los datos de la mascota', () => {
    render(
      <SwipeCard pet={pet} onSwipe={vi.fn()} onOpenDetail={vi.fn()} onToggleFavorito={vi.fn()} />,
    );

    expect(screen.getByText('Canela')).toBeInTheDocument();
    expect(screen.getByText('94% afín')).toBeInTheDocument();
  });

  it('abre la ficha al pulsar "Ver ficha"', () => {
    const onOpenDetail = vi.fn();
    render(
      <SwipeCard
        pet={pet}
        onSwipe={vi.fn()}
        onOpenDetail={onOpenDetail}
        onToggleFavorito={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByText('Ver ficha'));

    expect(onOpenDetail).toHaveBeenCalledOnce();
  });

  it('el teclado es una ruta equivalente al gesto (flechas y Enter)', () => {
    const onSwipe = vi.fn();
    const onOpenDetail = vi.fn();
    render(
      <SwipeCard
        pet={pet}
        onSwipe={onSwipe}
        onOpenDetail={onOpenDetail}
        onToggleFavorito={vi.fn()}
      />,
    );
    const tarjeta = screen.getByRole('group');

    fireEvent.keyDown(tarjeta, { key: 'ArrowRight' });
    fireEvent.keyDown(tarjeta, { key: 'ArrowLeft' });
    fireEvent.keyDown(tarjeta, { key: 'Enter' });

    expect(onSwipe).toHaveBeenNthCalledWith(1, 'like');
    expect(onSwipe).toHaveBeenNthCalledWith(2, 'pass');
    expect(onOpenDetail).toHaveBeenCalledOnce();
  });

  it('muestra el corazón vacío cuando la mascota no es favorita, con aria-label de guardar', () => {
    render(
      <SwipeCard pet={pet} onSwipe={vi.fn()} onOpenDetail={vi.fn()} onToggleFavorito={vi.fn()} />,
    );

    expect(screen.getByLabelText('Guardar en favoritos')).toHaveTextContent('♡');
  });

  it('muestra el corazón lleno cuando la mascota ya es favorita, con aria-label de quitar', () => {
    render(
      <SwipeCard
        pet={{ ...pet, es_favorito: true }}
        onSwipe={vi.fn()}
        onOpenDetail={vi.fn()}
        onToggleFavorito={vi.fn()}
      />,
    );

    expect(screen.getByLabelText('Quitar de favoritos')).toHaveTextContent('♥');
  });

  it('pulsar el botón de favorito llama a onToggleFavorito y no dispara el gesto de swipe', () => {
    const onSwipe = vi.fn();
    const onToggleFavorito = vi.fn();
    render(
      <SwipeCard
        pet={pet}
        onSwipe={onSwipe}
        onOpenDetail={vi.fn()}
        onToggleFavorito={onToggleFavorito}
      />,
    );
    const boton = screen.getByLabelText('Guardar en favoritos');

    fireEvent.pointerDown(boton, { clientX: 100, pointerId: 1 });
    fireEvent.click(boton);

    expect(onToggleFavorito).toHaveBeenCalledOnce();
    expect(onSwipe).not.toHaveBeenCalled();
  });
});
