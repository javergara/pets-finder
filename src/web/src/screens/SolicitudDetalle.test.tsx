import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { SolicitudDetalle as SolicitudDetalleTipo } from '../api/types';
import { mensajeAdopcionAdoptante, mensajeAdopcionPublicador, urlWhatsApp } from '../lib/contacto';
import { setActiveUserId } from '../lib/session';
import { SolicitudDetalle } from './SolicitudDetalle';

// El detalle de una solicitud de adopción (AD-05, paso 7). Lo que estos casos
// protegen, por orden de gravedad:
//
// 1. **Los botones los manda el backend.** `acciones_disponibles` llega
//    calculada para quien pregunta, y la pantalla solo la traduce a copy. En
//    `adopta-v1` esta misma pantalla reimplementaba `TRANSICIONES_VALIDAS` con
//    arrays de estados; las dos fuentes de verdad se separan a la primera
//    corrección del backend y la UI empieza a pintar botones que responden 409.
//    Por eso el caso decisivo es `['aprobar']` sobre estado `solicitado`: una
//    pantalla que recalcule la matriz pintaría los CUATRO botones, porque desde
//    `solicitado` todos son válidos.
// 2. **Sin cuenta no se abre.** El endpoint exige `solicitante_id` y
//    `getActiveUserId()` cae al `DEMO_USER_ID = 1` sin cuenta: un visitante
//    anónimo leería el mensaje, el teléfono y el cuestionario de hogar de la
//    persona que le escribió al usuario 1.
// 3. **El motivo del descarte no vuelve nunca.** Es la nota interna de quien
//    publica (ADR 0002) y no existe en ningún tipo del cliente: el caso lo
//    comprueba sobre el texto renderizado, que es donde se vería el descuido.

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return {
    ...actual,
    obtenerSolicitud: vi.fn(),
    agendarVisita: vi.fn(),
    pedirInformacion: vi.fn(),
    aprobarSolicitud: vi.fn(),
    descartarSolicitud: vi.fn(),
  };
});

afterEach(() => {
  vi.resetAllMocks();
  localStorage.clear();
});

const SOLICITUD_ID = 42;
const USUARIO = 7;
/** El id de quien pidió la mascota en el detalle de abajo: mirando con este
 * usuario la pantalla es la del adoptante, no la de quien publicó. */
const ADOPTANTE = 9;

function detalle(overrides: Partial<SolicitudDetalleTipo> = {}): SolicitudDetalleTipo {
  return {
    id: SOLICITUD_ID,
    estado: 'solicitado',
    etiqueta: 'Sin responder · 5 días',
    creado_en: '2026-08-10T10:00:00',
    actualizado_en: null,
    pet: {
      id: 8,
      nombre: 'Canela',
      especie: 'perro',
      raza: 'Cocker mestiza',
      edad_meses: 18,
      fotos: ['/media/seed/pet_8.jpg'],
      estado: 'disponible',
    },
    publicador: {
      tipo: 'organizacion',
      id: 2,
      nombre: 'Fundación Huellitas',
      telefono_contacto: '3001112233',
      zona: 'Armenia',
      ciudad_texto: null,
      barrio: null,
      foto_url: null,
    },
    adoptante: { id: 9, nombre: 'Carlos Ruiz' },
    afinidad: {
      score: 88,
      explicacion: 'Encaja muy bien con este hogar',
      razones: ['Tiene patio para una perra de energía alta', 'Pasa 4 horas fuera al día'],
      incompatible: false,
    },
    acciones_disponibles: [],
    bio: 'Vivo con mi familia y siempre tuvimos perros.',
    mensaje: 'Me encantaría darle un hogar a Canela.',
    telefono_contacto: '3009998877',
    home_profile: {
      vivienda: 'casa',
      espacio_exterior: 'patio',
      personas_en_casa: 3,
      tiene_ninos: true,
      tiene_otros_perros: false,
      tiene_otros_gatos: false,
      horas_fuera_dia: 4,
      experiencia_previa: 'mucha',
      presupuesto_mensual_cop: 250000,
      preferencia_especies: ['perro'],
      preferencia_tamanos: ['mediano'],
      preferencia_energia: 'alta',
    },
    ...overrides,
  };
}

/** Stub que imprime la ruta completa: sin cuenta la pantalla no solo tiene que
 * redirigir, tiene que llevar el `?volver=` de ESTA solicitud. */
function RegistroStub() {
  const { pathname, search } = useLocation();
  return <p>{`registro ${pathname}${search}`}</p>;
}

function renderDetalle() {
  return render(
    <MemoryRouter initialEntries={[`/adoptar/solicitud/${SOLICITUD_ID}`]}>
      <Routes>
        <Route path="/adoptar/solicitud/:id" element={<SolicitudDetalle />} />
        <Route path="/registro" element={<RegistroStub />} />
      </Routes>
    </MemoryRouter>,
  );
}

/** Los botones de acción, y solo ellos: la región tiene nombre accesible propio
 * para que "← Volver" y los enlaces de la ficha no cuenten como acciones. */
function botonesDeAccion(): string[] {
  const region = screen.queryByRole('region', { name: /qué quieres hacer/i });
  if (!region) return [];
  return within(region)
    .getAllByRole('button')
    .map((boton) => boton.textContent ?? '');
}

/** `usuario` decide qué lado de la solicitud se está mirando: por defecto el
 * publicador (el `USUARIO` que no es `adoptante.id`), y con `ADOPTANTE` el que
 * pidió la mascota. Es el mismo dato con el que la pantalla elige a quién se le
 * escribe por WhatsApp. */
async function montarCon(solicitud: SolicitudDetalleTipo, usuario: number = USUARIO) {
  setActiveUserId(usuario);
  vi.mocked(client.obtenerSolicitud).mockResolvedValue(solicitud);
  renderDetalle();
  await screen.findByRole('heading', { name: /Canela/ });
}

describe('SolicitudDetalle — los botones los manda el backend', () => {
  it('pinta exactamente las acciones que llegan en acciones_disponibles', async () => {
    await montarCon(detalle({ acciones_disponibles: ['agendar-visita', 'descartar'] }));

    expect(botonesDeAccion()).toEqual(['Agendar visita', 'Descartar solicitud']);
    expect(screen.queryByRole('button', { name: 'Confirmar adopción' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Pedir más información' })).not.toBeInTheDocument();
  });

  // EL CASO DECISIVO. El estado es `solicitado`, desde el que la matriz del
  // backend permite las cuatro acciones, pero `acciones_disponibles` trae una
  // sola: es el escenario real de una solicitud que el backend ya limitó (o de
  // una matriz que cambió). Una pantalla que decida con `solicitud.estado`
  // pintaría los cuatro botones y este caso la delata.
  it('con una sola acción disponible no pinta las otras tres, aunque el estado las permitiría', async () => {
    await montarCon(detalle({ estado: 'solicitado', acciones_disponibles: ['aprobar'] }));

    expect(botonesDeAccion()).toEqual(['Confirmar adopción']);
    expect(screen.getByText('Esperando respuesta')).toBeInTheDocument();
  });

  // Es lo que recibe SIEMPRE el adoptante (el match no es mutuo, ADR 0002) y
  // también quien publica cuando la solicitud ya está en un estado terminal.
  it('sin acciones disponibles no hay ningún botón de acción', async () => {
    await montarCon(detalle({ estado: 'adoptado', acciones_disponibles: [] }));

    expect(botonesDeAccion()).toEqual([]);
    expect(screen.queryByRole('region', { name: /qué quieres hacer/i })).not.toBeInTheDocument();
  });
});

describe('SolicitudDetalle — ejecutar una acción', () => {
  const CASOS = [
    { boton: 'Agendar visita', llamada: () => client.agendarVisita },
    { boton: 'Pedir más información', llamada: () => client.pedirInformacion },
    { boton: 'Confirmar adopción', llamada: () => client.aprobarSolicitud },
  ] as const;

  it.each(CASOS)('"$boton" llama a su función del cliente con (id, usuario)', async (caso) => {
    const fn = caso.llamada();
    vi.mocked(fn).mockResolvedValue(detalle({ estado: 'visita_agendada' }));
    await montarCon(
      detalle({
        acciones_disponibles: ['agendar-visita', 'pedir-informacion', 'aprobar', 'descartar'],
      }),
    );

    fireEvent.click(screen.getByRole('button', { name: caso.boton }));

    await waitFor(() => expect(fn).toHaveBeenCalledWith(SOLICITUD_ID, USUARIO));
    expect(fn).toHaveBeenCalledTimes(1);
  });

  // La respuesta de la acción es el detalle YA actualizado (incluida
  // `acciones_disponibles` recalculada), así que la pantalla no necesita un GET
  // detrás de cada botón: se repinta con lo que devolvió la acción.
  it('repinta la solicitud con lo que devuelve la acción, sin volver a pedirla', async () => {
    vi.mocked(client.agendarVisita).mockResolvedValue(
      detalle({ estado: 'visita_agendada', acciones_disponibles: ['aprobar'] }),
    );
    await montarCon(detalle({ acciones_disponibles: ['agendar-visita'] }));

    fireEvent.click(screen.getByRole('button', { name: 'Agendar visita' }));

    expect(await screen.findByText('Visita agendada')).toBeInTheDocument();
    expect(botonesDeAccion()).toEqual(['Confirmar adopción']);
    expect(client.obtenerSolicitud).toHaveBeenCalledTimes(1);
  });

  it('descartar exige un motivo: vacío y en blanco dejan el confirmar apagado', async () => {
    await montarCon(detalle({ acciones_disponibles: ['descartar'] }));

    fireEvent.click(screen.getByRole('button', { name: 'Descartar solicitud' }));

    const confirmar = screen.getByRole('button', { name: 'Confirmar descarte' });
    expect(confirmar).toBeDisabled();

    fireEvent.change(screen.getByLabelText(/motivo/i), { target: { value: '   ' } });
    expect(confirmar).toBeDisabled();

    fireEvent.change(screen.getByLabelText(/motivo/i), { target: { value: 'Ya adoptó otra' } });
    expect(confirmar).toBeEnabled();
    expect(client.descartarSolicitud).not.toHaveBeenCalled();
  });

  it('el motivo viaja recortado al descartar', async () => {
    vi.mocked(client.descartarSolicitud).mockResolvedValue(detalle({ estado: 'cerrado' }));
    await montarCon(detalle({ acciones_disponibles: ['descartar'] }));

    fireEvent.click(screen.getByRole('button', { name: 'Descartar solicitud' }));
    fireEvent.change(screen.getByLabelText(/motivo/i), {
      target: { value: '  Ya adoptó otra mascota  ' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Confirmar descarte' }));

    await waitFor(() =>
      expect(client.descartarSolicitud).toHaveBeenCalledWith(
        SOLICITUD_ID,
        USUARIO,
        'Ya adoptó otra mascota',
      ),
    );
  });

  // Los dos errores reales de esta pantalla llegan como `ApiError` con el texto
  // del backend, que ya es copy de producto en español: un 409 (pestaña vieja,
  // la solicitud avanzó por otro lado) y un 403 (no es quien publicó).
  const ERRORES = [
    'Ya no puedes agendar una visita: esta solicitud ya terminó con la adopción confirmada. Actualiza la página para verla como está ahora.',
    'Solo quien publicó la mascota puede gestionar esta solicitud',
  ];

  it.each(ERRORES)('muestra "%s" y deja volver a intentarlo', async (mensaje) => {
    vi.mocked(client.agendarVisita).mockRejectedValue(new client.ApiError(mensaje));
    await montarCon(detalle({ acciones_disponibles: ['agendar-visita'] }));

    fireEvent.click(screen.getByRole('button', { name: 'Agendar visita' }));

    expect(await screen.findByRole('alert')).toHaveTextContent(mensaje);
    // El botón se rehabilita: si la acción falló por un 409 el publicador
    // necesita poder intentar la que sí quedó válida sin recargar la página.
    expect(screen.getByRole('button', { name: 'Agendar visita' })).toBeEnabled();
  });

  it('mientras la acción va en camino el botón queda apagado', async () => {
    vi.mocked(client.aprobarSolicitud).mockReturnValue(new Promise(() => {}));
    await montarCon(detalle({ acciones_disponibles: ['aprobar'] }));

    fireEvent.click(screen.getByRole('button', { name: 'Confirmar adopción' }));

    await waitFor(() =>
      expect(screen.getByRole('button', { name: 'Confirmar adopción' })).toBeDisabled(),
    );
  });
});

describe('SolicitudDetalle — con qué se decide', () => {
  it('muestra la afinidad, el cuestionario de hogar, el mensaje y el teléfono', async () => {
    await montarCon(detalle());

    expect(screen.getByText('88% afín')).toBeInTheDocument();
    expect(screen.getByText(/Tiene patio para una perra de energía alta/)).toBeInTheDocument();
    expect(screen.getByText('Casa')).toBeInTheDocument();
    expect(screen.getByText('Patio')).toBeInTheDocument();
    expect(screen.getByText('Mucha experiencia')).toBeInTheDocument();
    expect(screen.getByText(/Me encantaría darle un hogar a Canela/)).toBeInTheDocument();
    // `urlTelefono` normaliza a E.164 (el 57 de Colombia), igual que en el resto
    // de la app: el número se lee tal cual lo dejaron, pero se marca completo.
    expect(screen.getByRole('link', { name: /3009998877/ })).toHaveAttribute(
      'href',
      'tel:+573009998877',
    );
  });

  // Desde AD-04 el cuestionario es OPCIONAL: en `adopta-v1` esto era un 404 y la
  // fila desaparecía del panel sin ningún error visible.
  it('sin cuestionario de hogar no se rompe: lo dice y sigue mostrando el resto', async () => {
    await montarCon(detalle({ home_profile: null, afinidad: null }));

    expect(screen.getByText(/Todavía no completó el cuestionario de hogar/i)).toBeInTheDocument();
    expect(screen.queryByText(/% afín/)).not.toBeInTheDocument();
    expect(screen.getByText(/Me encantaría darle un hogar a Canela/)).toBeInTheDocument();
  });

  // El motivo con el que se cierra una solicitud es la nota interna de quien
  // publica: se guarda, pero no vuelve en ninguna respuesta y quien no se quedó
  // con la mascota no tiene por qué leerlo (ADR 0002).
  it('una solicitud descartada no enseña ningún motivo', async () => {
    await montarCon(detalle({ estado: 'cerrado', acciones_disponibles: [] }));

    expect(screen.getByText('Solicitud cerrada')).toBeInTheDocument();
    expect(document.body.textContent ?? '').not.toMatch(/motivo/i);
  });

  it('si la solicitud no se puede cargar lo dice en español y ofrece la salida', async () => {
    setActiveUserId(USUARIO);
    vi.mocked(client.obtenerSolicitud).mockRejectedValue(
      new client.ApiError('Solo puedes ver tus propias solicitudes'),
    );

    renderDetalle();

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Solo puedes ver tus propias solicitudes',
    );
    expect(screen.getByRole('link', { name: 'Ver mis solicitudes' })).toHaveAttribute(
      'href',
      '/adoptar/mis-solicitudes',
    );
  });
});

// La comunicación de la solicitud (AD-06, ADR 0013): no hay chat interno, así
// que este botón es el único puente entre las dos personas. Lo que se comprueba
// es que apunta a la persona correcta —el teléfono del otro lado, nunca el
// propio— y con el mensaje del estado en el que está la solicitud.
describe('SolicitudDetalle — hablar por WhatsApp', () => {
  it('quien publicó le escribe a quien pidió la mascota, con el mensaje del estado', async () => {
    await montarCon(detalle({ estado: 'visita_agendada' }));

    const enlace = screen.getByRole('link', { name: /whatsapp/i });
    // El teléfono que dejó el adoptante al pedirla, no el del publicador.
    expect(enlace).toHaveAttribute(
      'href',
      urlWhatsApp(
        '3009998877',
        mensajeAdopcionPublicador('visita_agendada', 'Canela', 'Carlos Ruiz'),
      ),
    );
    expect(enlace).toHaveAttribute('href', expect.stringContaining('wa.me'));
    expect(screen.getByText(/Antes de coordinar un encuentro/i)).toBeInTheDocument();
  });

  it('quien pidió la mascota le escribe a quien la publicó, con el mensaje del estado', async () => {
    await montarCon(detalle({ estado: 'solicitado' }), ADOPTANTE);

    const enlace = screen.getByRole('link', { name: /whatsapp/i });
    // El teléfono del publicador (`publicador.telefono_contacto`), que es el
    // otro lado desde aquí.
    expect(enlace).toHaveAttribute(
      'href',
      urlWhatsApp('3001112233', mensajeAdopcionAdoptante('solicitado', 'Canela')),
    );
    expect(enlace).toHaveAttribute('href', expect.stringContaining('wa.me'));
    expect(screen.getByText(/Antes de coordinar un encuentro/i)).toBeInTheDocument();
  });

  // Mismo estado, dos personas mirando: el enlace no puede ser el mismo. Si lo
  // fuera, alguien estaría escribiéndose a sí mismo.
  it('el mismo detalle apunta a un lado distinto según quién lo mire', async () => {
    await montarCon(detalle());
    const desdeElPublicador = screen.getByRole('link', { name: /whatsapp/i }).getAttribute('href');

    cleanup();
    await montarCon(detalle(), ADOPTANTE);
    const desdeElAdoptante = screen.getByRole('link', { name: /whatsapp/i }).getAttribute('href');

    expect(desdeElAdoptante).not.toBe(desdeElPublicador);
  });

  // Sin teléfono no se pinta un botón que no lleva a ninguna parte (mismo
  // criterio que `MascotaDetalle`): se dice que no lo dejaron.
  it('sin teléfono del otro lado lo dice, y no hay botón de WhatsApp', async () => {
    await montarCon(detalle({ telefono_contacto: null }));

    expect(screen.queryByRole('link', { name: /whatsapp/i })).not.toBeInTheDocument();
    expect(screen.getByText(/no dejó un teléfono/i)).toBeInTheDocument();
  });
});

// El gate de cuenta, aparte porque es el caso de seguridad: la pantalla no
// compara autoría, *consulta* con el id activo, y sin cuenta ese id es el
// usuario demo (1) — una persona real en producción. La respuesta trae el
// mensaje, el teléfono y el cuestionario de hogar de quien le escribió.
describe('SolicitudDetalle sin cuenta', () => {
  it('redirige al registro con el volver de esta solicitud, sin pedir nada', async () => {
    vi.mocked(client.obtenerSolicitud).mockResolvedValue(detalle());

    renderDetalle();

    expect(
      await screen.findByText('registro /registro?volver=%2Fadoptar%2Fsolicitud%2F42'),
    ).toBeInTheDocument();
    expect(client.obtenerSolicitud).not.toHaveBeenCalled();
    expect(screen.queryByText('Canela')).not.toBeInTheDocument();
  });
});
