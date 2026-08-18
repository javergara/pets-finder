import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { GaleriaFotos } from './GaleriaFotos';

const RELATIVA = '/media/uploads/a.jpg';
const ABSOLUTA = 'https://proyecto.supabase.co/storage/v1/object/public/fotos/b.jpg';

describe('GaleriaFotos', () => {
  it('sin fotos no renderiza nada', () => {
    const { container } = render(<GaleriaFotos fotos={[]} alt="Foto de Rocky" />);

    expect(container.firstChild).toBeNull();
  });

  it('con una sola foto muestra la grande con su alt y ninguna miniatura', () => {
    render(<GaleriaFotos fotos={[RELATIVA]} alt="Foto de Rocky" />);

    expect(screen.getByAltText('Foto de Rocky')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Ver foto/ })).not.toBeInTheDocument();
  });

  it('con varias fotos hay una miniatura por foto y el click cambia la grande', () => {
    render(<GaleriaFotos fotos={[RELATIVA, '/media/uploads/b.jpg']} alt="Foto de Rocky" />);

    expect(screen.getAllByRole('button', { name: /Ver foto/ })).toHaveLength(2);

    const grande = screen.getByAltText('Foto de Rocky');
    expect(grande.getAttribute('src')).toContain('/media/uploads/a.jpg');

    fireEvent.click(screen.getByRole('button', { name: 'Ver foto 2' }));
    expect(grande.getAttribute('src')).toContain('/media/uploads/b.jpg');
  });

  it('las rutas relativas pasan por mediaUrl y las del bucket van por /fotos', () => {
    render(<GaleriaFotos fotos={[RELATIVA, ABSOLUTA]} alt="Foto de Rocky" />);

    const grande = screen.getByAltText('Foto de Rocky');
    // En dev/test la base de la API es absoluta: la ruta relativa queda prefijada.
    expect(grande.getAttribute('src')).toMatch(/^https?:\/\/.+\/media\/uploads\/a\.jpg$/);

    // Feature 49: la foto del bucket se sirve por el proxy /fotos del dominio
    // (caché larga en vercel.json), no por la URL directa de Supabase.
    fireEvent.click(screen.getByRole('button', { name: 'Ver foto 2' }));
    expect(grande.getAttribute('src')).toBe('/fotos/b.jpg');
  });

  it('si el índice activo queda fuera del array tras un re-render, sigue mostrando una foto válida', () => {
    const { rerender } = render(
      <GaleriaFotos
        fotos={[RELATIVA, '/media/uploads/b.jpg', '/media/uploads/c.jpg']}
        alt="Foto"
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Ver foto 3' }));
    expect(screen.getByAltText('Foto').getAttribute('src')).toContain('/media/uploads/c.jpg');

    rerender(<GaleriaFotos fotos={[RELATIVA]} alt="Foto" />);

    // Clamp: no revienta y cae a la última foto disponible.
    expect(screen.getByAltText('Foto').getAttribute('src')).toContain('/media/uploads/a.jpg');
    expect(screen.queryByRole('button', { name: /Ver foto/ })).not.toBeInTheDocument();
  });
});
