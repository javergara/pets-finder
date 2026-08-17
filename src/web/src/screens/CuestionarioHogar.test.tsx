import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { PerfilHogar } from '../api/types';
import { setActiveUserId } from '../lib/session';
import { CuestionarioHogar } from './CuestionarioHogar';

// Cuestionario de hogar (AD-04, paso 4): el wizard de 6 pasos de `/adoptar/mi-hogar`.
//
// Lo que protegen estos casos, por orden de gravedad:
//
// 1. **Es una escritura, así que sin cuenta no se entra.** `getActiveUserId()`
//    cae al `DEMO_USER_ID = 1`: sin el gate, un visitante anónimo
//    **sobrescribiría el cuestionario de una persona real** y le cambiaría el
//    deck. Por eso el gate va antes de leer ningún id, y el caso asevera además
//    que no se pide ningún perfil.
// 2. **El presupuesto es opcional de verdad.** `adopta-v1` arrancaba con
//    `300000` puesto: quien no tocara el campo mandaba un dato que nunca dio, y
//    la afinidad lo usaba como si fuera suyo.
// 3. **No se guarda a medias**: "Continuar" no avanza hasta que el paso está
//    contestado, y un error del backend se muestra sin navegar a ningún lado.

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return { ...actual, obtenerPerfilHogar: vi.fn(), guardarPerfilHogar: vi.fn() };
});

const obtenerPerfilHogar = vi.mocked(client.obtenerPerfilHogar);
const guardarPerfilHogar = vi.mocked(client.guardarPerfilHogar);

function Ubicacion() {
  const location = useLocation();
  return <span data-testid="ubicacion">{`${location.pathname}${location.search}`}</span>;
}

function montar() {
  return render(
    <MemoryRouter initialEntries={['/adoptar/mi-hogar']}>
      <Ubicacion />
      <Routes>
        <Route path="/adoptar/mi-hogar" element={<CuestionarioHogar />} />
        <Route path="/adoptar/descubrir" element={<p>Deck de descubrimiento</p>} />
        <Route path="/registro" element={<p>Formulario de registro</p>} />
      </Routes>
    </MemoryRouter>,
  );
}

// Sin `user_id`: `HomeProfileOut` no lo devuelve (quien recibe la respuesta es
// siempre su dueño). Tenerlo aquí hacía que el fixture describiera un cuerpo que
// el backend nunca manda, y como el test mockea el `fetch`, nadie lo notaba.
const PERFIL_GUARDADO: PerfilHogar = {
  vivienda: 'casa',
  espacio_exterior: 'patio',
  personas_en_casa: 4,
  tiene_ninos: true,
  tiene_otros_perros: false,
  tiene_otros_gatos: true,
  horas_fuera_dia: 5,
  experiencia_previa: 'mucha',
  presupuesto_mensual_cop: 250000,
  preferencia_especies: ['gato'],
  preferencia_tamanos: ['pequeño'],
  preferencia_energia: 'baja',
};

/** Contesta el paso visible y pulsa "Continuar"/"Terminar". */
function responderPaso(paso: number) {
  const grupo = (nombre: string) => screen.getByRole('group', { name: nombre });

  switch (paso) {
    case 1:
      fireEvent.click(screen.getByRole('button', { name: 'Apartamento' }));
      fireEvent.click(screen.getByRole('button', { name: 'Sin espacio exterior' }));
      break;
    case 2:
      fireEvent.change(screen.getByLabelText(/cuántas personas/i), { target: { value: '2' } });
      fireEvent.click(within(grupo('¿Hay niños en casa?')).getByRole('button', { name: 'No' }));
      break;
    case 3:
      fireEvent.change(screen.getByLabelText(/horas pasas fuera/i), { target: { value: '9' } });
      break;
    case 4:
      fireEvent.click(
        within(grupo('¿Viven otros perros en casa?')).getByRole('button', { name: 'No' }),
      );
      fireEvent.click(
        within(grupo('¿Viven otros gatos en casa?')).getByRole('button', { name: 'No' }),
      );
      break;
    case 5:
      fireEvent.click(screen.getByRole('button', { name: 'Algo de experiencia' }));
      break;
    case 6:
      fireEvent.click(
        within(grupo('¿Qué especies te interesan?')).getByRole('button', { name: 'Perro' }),
      );
      fireEvent.click(
        within(grupo('¿Qué tamaños prefieres?')).getByRole('button', { name: 'Mediana' }),
      );
      fireEvent.click(
        within(grupo('¿Qué nivel de energía prefieres?')).getByRole('button', {
          name: 'Energía media',
        }),
      );
      break;
  }
}

async function recorrerLosSeisPasos() {
  for (let paso = 1; paso <= 6; paso += 1) {
    responderPaso(paso);
    fireEvent.click(screen.getByRole('button', { name: paso === 6 ? 'Terminar' : 'Continuar' }));
  }
}

beforeEach(() => {
  setActiveUserId(7);
  obtenerPerfilHogar.mockResolvedValue(null);
  guardarPerfilHogar.mockResolvedValue({ ...PERFIL_GUARDADO });
});

afterEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
});

describe('CuestionarioHogar', () => {
  it('sin cuenta manda al registro y no pide el perfil de nadie', () => {
    localStorage.clear();

    montar();

    expect(screen.getByTestId('ubicacion').textContent).toBe(
      '/registro?volver=%2Fadoptar%2Fmi-hogar',
    );
    // El gate va ANTES de leer ningún id: si se leyera `getActiveUserId()`
    // primero, esta llamada iría con el `DEMO_USER_ID = 1`, que es una persona
    // real, y el siguiente "Terminar" sobrescribiría su cuestionario.
    expect(obtenerPerfilHogar).not.toHaveBeenCalled();
  });

  it('arranca en el paso 1 de 6, sin "Atrás" y con "Continuar" deshabilitado', async () => {
    montar();

    expect(await screen.findByText('Paso 1 de 6')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Atrás' })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Continuar' })).toBeDisabled();
  });

  it('habilita "Continuar" solo cuando el paso está contestado entero', async () => {
    montar();
    await screen.findByText('Paso 1 de 6');

    fireEvent.click(screen.getByRole('button', { name: 'Apartamento' }));
    expect(screen.getByRole('button', { name: 'Continuar' })).toBeDisabled();

    fireEvent.click(screen.getByRole('button', { name: 'Sin espacio exterior' }));
    expect(screen.getByRole('button', { name: 'Continuar' })).toBeEnabled();

    fireEvent.click(screen.getByRole('button', { name: 'Continuar' }));
    expect(screen.getByText('Paso 2 de 6')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Atrás' })).toBeInTheDocument();
  });

  it('recorre los seis pasos y guarda el payload exacto, con el presupuesto en null', async () => {
    montar();
    await screen.findByText('Paso 1 de 6');

    await recorrerLosSeisPasos();

    await waitFor(() => expect(guardarPerfilHogar).toHaveBeenCalledTimes(1));
    expect(guardarPerfilHogar).toHaveBeenCalledWith(7, {
      user_id: 7,
      vivienda: 'apartamento',
      espacio_exterior: 'ninguno',
      personas_en_casa: 2,
      tiene_ninos: false,
      tiene_otros_perros: false,
      tiene_otros_gatos: false,
      horas_fuera_dia: 9,
      experiencia_previa: 'algo',
      // Nadie tocó el campo: se manda vacío, no el `300000` por defecto de
      // `adopta-v1`, que metía en la afinidad un dato que la persona no dio.
      presupuesto_mensual_cop: null,
      preferencia_especies: ['perro'],
      preferencia_tamanos: ['mediano'],
      preferencia_energia: 'media',
    });
    await waitFor(() =>
      expect(screen.getByTestId('ubicacion').textContent).toBe('/adoptar/descubrir'),
    );
  });

  it('ofrece las tres especies, incluida "Otro animal"', async () => {
    montar();
    await screen.findByText('Paso 1 de 6');
    for (let paso = 1; paso <= 5; paso += 1) {
      responderPaso(paso);
      fireEvent.click(screen.getByRole('button', { name: 'Continuar' }));
    }

    const especies = within(screen.getByRole('group', { name: '¿Qué especies te interesan?' }));
    // Excluirla condenaría a cero de afinidad a toda mascota que no sea perro ni
    // gato, y el catálogo tiene la especie "otro" desde AD-01.
    expect(especies.getByRole('button', { name: 'Otro animal' })).toBeInTheDocument();
    expect(especies.getByRole('button', { name: 'Perro' })).toBeInTheDocument();
    expect(especies.getByRole('button', { name: 'Gato' })).toBeInTheDocument();
  });

  it('precarga el cuestionario ya contestado para reeditarlo', async () => {
    obtenerPerfilHogar.mockResolvedValue({ ...PERFIL_GUARDADO });

    montar();

    await waitFor(() =>
      expect(screen.getByRole('button', { name: 'Casa' })).toHaveAttribute('aria-pressed', 'true'),
    );
    expect(screen.getByRole('button', { name: 'Patio' })).toHaveAttribute('aria-pressed', 'true');
    expect(obtenerPerfilHogar).toHaveBeenCalledWith(7, 7);
  });

  it('muestra el error del backend y no navega', async () => {
    guardarPerfilHogar.mockRejectedValue(new client.ApiError('No pudimos guardar tu hogar'));
    montar();
    await screen.findByText('Paso 1 de 6');

    await recorrerLosSeisPasos();

    expect(await screen.findByRole('alert')).toHaveTextContent('No pudimos guardar tu hogar');
    expect(screen.getByTestId('ubicacion').textContent).toBe('/adoptar/mi-hogar');
  });
});
