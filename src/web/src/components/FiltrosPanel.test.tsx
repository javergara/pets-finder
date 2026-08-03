import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { FILTROS_DEFAULT } from '../api/types';
import { FiltrosPanel } from './FiltrosPanel';

describe('FiltrosPanel', () => {
  it('se renderiza con los filtros por defecto', () => {
    render(<FiltrosPanel filtros={FILTROS_DEFAULT} onChange={vi.fn()} onReset={vi.fn()} />);

    expect(screen.getByText('Perro')).toBeInTheDocument();
    expect(screen.getByText('Distancia: 15 km')).toBeInTheDocument();
    expect(screen.getByText('Restablecer filtros')).toBeInTheDocument();
  });

  it('clic en un chip de especie agrega ese valor al arreglo', () => {
    const onChange = vi.fn();
    render(<FiltrosPanel filtros={FILTROS_DEFAULT} onChange={onChange} onReset={vi.fn()} />);

    fireEvent.click(screen.getByText('Perro'));

    expect(onChange).toHaveBeenCalledWith({ ...FILTROS_DEFAULT, especie: ['perro'] });
  });

  it('clic de nuevo en el mismo chip lo quita del arreglo', () => {
    const onChange = vi.fn();
    const filtrosConPerro = { ...FILTROS_DEFAULT, especie: ['perro'] };
    render(<FiltrosPanel filtros={filtrosConPerro} onChange={onChange} onReset={vi.fn()} />);

    fireEvent.click(screen.getByText('Perro'));

    expect(onChange).toHaveBeenCalledWith({ ...FILTROS_DEFAULT, especie: [] });
  });

  it('clic en un toggle de convivencia invierte ese booleano', () => {
    const onChange = vi.fn();
    render(<FiltrosPanel filtros={FILTROS_DEFAULT} onChange={onChange} onReset={vi.fn()} />);

    fireEvent.click(screen.getByText('Apta con niños'));

    expect(onChange).toHaveBeenCalledWith({ ...FILTROS_DEFAULT, aptoNinos: true });
  });

  it('clic en "Restablecer filtros" dispara onReset', () => {
    const onReset = vi.fn();
    render(<FiltrosPanel filtros={FILTROS_DEFAULT} onChange={vi.fn()} onReset={onReset} />);

    fireEvent.click(screen.getByText('Restablecer filtros'));

    expect(onReset).toHaveBeenCalledOnce();
  });
});
