import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { Reporte } from '../api/types';
import { ZONAS } from '../lib/ciudades';
import { ReporteDetalle } from './ReporteDetalle';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return {
    ...actual,
    obtenerReporte: vi.fn(),
    listarCoincidencias: vi.fn(),
    marcarReunido: vi.fn(),
    eliminarReporte: vi.fn(),
    listarAvistamientos: vi.fn(),
    crearAvistamiento: vi.fn(),
    suscribirseANovedades: vi.fn(),
  };
});

beforeEach(() => {
  // La mayoría de los casos no ejercita coincidencias ni avistamientos: vacías.
  vi.mocked(client.listarCoincidencias).mockResolvedValue([]);
  vi.mocked(client.listarAvistamientos).mockResolvedValue([]);
});

afterEach(() => {
  vi.resetAllMocks();
});

function crearReporte(overrides: Partial<Reporte> = {}): Reporte {
  return {
    id: 1,
    user_id: 1,
    tipo: 'perdido',
    especie: 'perro',
    nombre_mascota: 'Rocky',
    raza: null,
    color: null,
    tamano: null,
    descripcion: 'Criollo color miel con collar rojo',
    foto_url: '/media/seed/report_1.jpg',
    zona: 'Armenia',
    ciudad_texto: null,
    barrio: 'La Castellana',
    lat: ZONAS.Armenia.centroLat,
    lng: ZONAS.Armenia.centroLng,
    situacion: null,
    fecha_evento: '2026-08-10',
    telefono_contacto: '3001234561',
    fuente: 'manual',
    crawl_metadata: null,
    idempotency_id: null,
    estado: 'activo',
    creado_en: '2026-08-12T08:00:00',
    resuelto_en: null,
    ...overrides,
  };
}

function renderDetalle(id = 1) {
  return render(
    <MemoryRouter initialEntries={[`/reporte/${id}`]}>
      <Routes>
        <Route path="/reporte/:id" element={<ReporteDetalle />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('ReporteDetalle', () => {
  it('muestra los datos del reporte y los hrefs exactos de WhatsApp y llamada', async () => {
    vi.mocked(client.obtenerReporte).mockResolvedValue(crearReporte());

    renderDetalle();

    expect(await screen.findByRole('heading', { name: 'Rocky' })).toBeInTheDocument();
    expect(screen.getByText('Criollo color miel con collar rojo')).toBeInTheDocument();

    const whatsapp = screen.getByRole('link', { name: 'Contactar por WhatsApp' });
    const href = whatsapp.getAttribute('href') ?? '';
    expect(href.startsWith('https://wa.me/573001234561?text=')).toBe(true);
    // El mensaje precargado menciona el reporte y la app.
    const texto = decodeURIComponent(href.split('?text=')[1]);
    expect(texto).toContain('Rocky');
    expect(texto).toContain('Pet Finder Col');

    expect(screen.getByRole('link', { name: 'Llamar' })).toHaveAttribute(
      'href',
      'tel:+573001234561',
    );
  });

  it('el mini-mapa incluye el pin del reporte con su color por tipo', async () => {
    // Los tiles y la posición real los pinta Leaflet en el navegador (no corre
    // en jsdom); el contrato testeable es el equivalente accesible del pin.
    vi.mocked(client.obtenerReporte).mockResolvedValue(crearReporte());

    renderDetalle();

    const pin = await screen.findByRole('button', {
      name: 'Ubicación del reporte de Rocky',
    });
    expect(pin.className).toContain('bg-danger');
  });

  it('un encontrado usa la especie como título, el badge forest y su situación', async () => {
    vi.mocked(client.obtenerReporte).mockResolvedValue(
      crearReporte({
        tipo: 'encontrado',
        nombre_mascota: null,
        especie: 'gato',
        situacion: 'conmigo',
      }),
    );

    renderDetalle();

    expect(await screen.findByRole('heading', { name: 'Gato' })).toBeInTheDocument();
    expect(screen.getByText('Encontrada')).toBeInTheDocument();
    expect(screen.getByText('La tiene resguardada quien la reportó')).toBeInTheDocument();
  });

  it('la caja de novedades suscribe el correo y confirma (feature 39)', async () => {
    vi.mocked(client.obtenerReporte).mockResolvedValue(crearReporte());
    vi.mocked(client.suscribirseANovedades).mockResolvedValue({});

    renderDetalle();
    await screen.findByText('🔔 Avísame si hay novedades');

    fireEvent.change(screen.getByLabelText('Tu correo'), {
      target: { value: 'vecina@example.co' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Avísame' }));

    await waitFor(() =>
      expect(client.suscribirseANovedades).toHaveBeenCalledWith(1, 'vecina@example.co'),
    );
    expect(await screen.findByText(/Listo: te avisaremos a vecina@example.co/)).toBeInTheDocument();
  });

  it('un reporte reunido no ofrece la caja de novedades', async () => {
    vi.mocked(client.obtenerReporte).mockResolvedValue(crearReporte({ estado: 'reunido' }));

    renderDetalle();
    await screen.findByText('Rocky');

    expect(screen.queryByText('🔔 Avísame si hay novedades')).not.toBeInTheDocument();
  });

  it('muestra las posibles coincidencias con su distancia y link al detalle', async () => {
    vi.mocked(client.obtenerReporte).mockResolvedValue(crearReporte());
    vi.mocked(client.listarCoincidencias).mockResolvedValue([
      {
        ...crearReporte({
          id: 2,
          tipo: 'encontrado',
          nombre_mascota: null,
          situacion: 'conmigo',
          descripcion: 'Perro color miel resguardado',
        }),
        distancia_km: 0.6,
        razones: ['mismo perro', 'misma zona (Armenia)', 'a 0.6 km', '1 día de diferencia'],
      },
    ]);

    renderDetalle();

    expect(await screen.findByText('Posibles coincidencias')).toBeInTheDocument();
    // Las razones del backend se muestran como chips (feature 37).
    expect(screen.getByText('a 0.6 km')).toBeInTheDocument();
    expect(screen.getByText('mismo perro')).toBeInTheDocument();
    expect(screen.getByText('1 día de diferencia')).toBeInTheDocument();
    const links = screen.getAllByRole('link');
    expect(links.some((l) => l.getAttribute('href') === '/reporte/2')).toBe(true);
  });

  it('sin coincidencias no muestra la sección', async () => {
    vi.mocked(client.obtenerReporte).mockResolvedValue(crearReporte());

    renderDetalle();

    await screen.findByRole('heading', { name: 'Rocky' });
    expect(screen.queryByText('Posibles coincidencias')).not.toBeInTheDocument();
  });

  it('un reporte reunido celebra el reencuentro y no muestra botones de contacto', async () => {
    vi.mocked(client.obtenerReporte).mockResolvedValue(
      crearReporte({ estado: 'reunido', resuelto_en: '2026-08-12T15:00:00' }),
    );

    renderDetalle();

    expect(
      await screen.findByText('Esta mascota ya se reencontró con su familia. 💚'),
    ).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'Contactar por WhatsApp' })).not.toBeInTheDocument();
    // Búsqueda terminada: tampoco se piden avistamientos.
    expect(screen.queryByText('Avistamientos')).not.toBeInTheDocument();
  });

  it('el botón de marcar reunida solo aparece para el autor, y al usarlo celebra', async () => {
    // Sin nada en localStorage getActiveUserId() cae a DEMO_USER_ID=1 == user_id del reporte.
    vi.mocked(client.obtenerReporte).mockResolvedValue(crearReporte({ user_id: 1 }));
    vi.mocked(client.marcarReunido).mockResolvedValue(
      crearReporte({ estado: 'reunido', resuelto_en: '2026-08-12T15:00:00' }),
    );

    renderDetalle();

    const boton = await screen.findByRole('button', { name: 'Marcar como reunida' });
    boton.click();

    expect(
      await screen.findByText('Esta mascota ya se reencontró con su familia. 💚'),
    ).toBeInTheDocument();
    expect(client.marcarReunido).toHaveBeenCalledWith(1, 1);
  });

  it('el botón de marcar reunida NO aparece para quien no es el autor', async () => {
    vi.mocked(client.obtenerReporte).mockResolvedValue(crearReporte({ user_id: 2 }));

    renderDetalle();

    await screen.findByRole('heading', { name: 'Rocky' });
    expect(screen.queryByRole('button', { name: 'Marcar como reunida' })).not.toBeInTheDocument();
  });

  it('eliminar exige confirmar en dos pasos, llama al API y navega al listado', async () => {
    // getActiveUserId() cae a DEMO_USER_ID=1 == user_id del reporte: es el autor.
    vi.mocked(client.obtenerReporte).mockResolvedValue(crearReporte({ user_id: 1 }));
    vi.mocked(client.eliminarReporte).mockResolvedValue(undefined);

    render(
      <MemoryRouter initialEntries={['/reporte/1']}>
        <Routes>
          <Route path="/reporte/:id" element={<ReporteDetalle />} />
          <Route path="/reportes" element={<div>Listado stub</div>} />
        </Routes>
      </MemoryRouter>,
    );

    // Primer paso: el botón no borra nada, abre la confirmación.
    (await screen.findByRole('button', { name: 'Eliminar este reporte' })).click();
    expect(
      await screen.findByText(
        '¿Seguro que quieres eliminar este reporte? Esta acción no se puede deshacer.',
      ),
    ).toBeInTheDocument();
    expect(client.eliminarReporte).not.toHaveBeenCalled();

    // Cancelar vuelve atrás sin llamar al API.
    screen.getByRole('button', { name: 'Cancelar' }).click();
    expect(
      await screen.findByRole('button', { name: 'Eliminar este reporte' }),
    ).toBeInTheDocument();
    expect(client.eliminarReporte).not.toHaveBeenCalled();

    // Confirmar de verdad: borra y navega al listado.
    (await screen.findByRole('button', { name: 'Eliminar este reporte' })).click();
    (await screen.findByRole('button', { name: 'Sí, eliminar' })).click();

    await screen.findByText('Listado stub');
    expect(client.eliminarReporte).toHaveBeenCalledWith(1, 1);
  });

  it('el botón de eliminar NO aparece para quien no es el autor', async () => {
    vi.mocked(client.obtenerReporte).mockResolvedValue(crearReporte({ user_id: 2 }));

    renderDetalle();

    await screen.findByRole('heading', { name: 'Rocky' });
    expect(screen.queryByRole('button', { name: 'Eliminar este reporte' })).not.toBeInTheDocument();
  });

  it('compartir usa navigator.share cuando existe', async () => {
    vi.mocked(client.obtenerReporte).mockResolvedValue(crearReporte());
    const share = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal('navigator', { ...navigator, share });

    renderDetalle();

    (await screen.findByRole('button', { name: 'Compartir este reporte' })).click();

    await waitFor(() =>
      expect(share).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Pet Finder Col',
          text: 'Rocky — Se perdió en Armenia. Ayuda a difundir:',
          url: window.location.href,
        }),
      ),
    );
    vi.unstubAllGlobals();
  });

  it('sin navigator.share copia el link y lo confirma', async () => {
    vi.mocked(client.obtenerReporte).mockResolvedValue(crearReporte());
    const writeText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal('navigator', { ...navigator, share: undefined, clipboard: { writeText } });

    renderDetalle();

    (await screen.findByRole('button', { name: 'Compartir este reporte' })).click();

    expect(await screen.findByText('Link copiado — pégalo donde quieras.')).toBeInTheDocument();
    expect(writeText).toHaveBeenCalledWith(window.location.href);
    vi.unstubAllGlobals();
  });

  it('muestra los avistamientos como lista y como pins ochre en el mapa', async () => {
    vi.mocked(client.obtenerReporte).mockResolvedValue(crearReporte());
    vi.mocked(client.listarAvistamientos).mockResolvedValue([
      {
        id: 5,
        report_id: 1,
        lat: 4.55,
        lng: -75.67,
        fecha: '2026-08-13',
        comentario: 'Corría hacia el parque',
        nombre: 'Carlos',
        creado_en: '2026-08-13T10:00:00',
      },
    ]);

    renderDetalle();

    expect(await screen.findByText('Vista el 13/08/2026')).toBeInTheDocument();
    expect(screen.getByText(/Corría hacia el parque/)).toBeInTheDocument();
    expect(screen.getByText(/\(Carlos\)/)).toBeInTheDocument();
    const pin = screen.getByRole('button', { name: 'Avistamiento del 13/08/2026' });
    expect(pin.className).toContain('bg-ochre');
  });

  it('guardar un avistamiento llama al API con el pin y lo añade a la lista', async () => {
    vi.mocked(client.obtenerReporte).mockResolvedValue(crearReporte());
    vi.mocked(client.crearAvistamiento).mockResolvedValue({
      id: 9,
      report_id: 1,
      lat: ZONAS.Armenia.centroLat,
      lng: ZONAS.Armenia.centroLng,
      fecha: '2026-08-12',
      comentario: 'La vi en la ciclovía',
      nombre: null,
      creado_en: '2026-08-12T09:00:00',
    });

    renderDetalle();

    (await screen.findByRole('button', { name: 'La vi — marcar avistamiento' })).click();
    fireEvent.change(await screen.findByLabelText('¿Qué viste?'), {
      target: { value: 'La vi en la ciclovía' },
    });
    screen.getByRole('button', { name: 'Guardar avistamiento' }).click();

    expect(await screen.findByText(/La vi en la ciclovía/)).toBeInTheDocument();
    expect(client.crearAvistamiento).toHaveBeenCalledWith(
      1,
      expect.objectContaining({
        // Sin click en el mapa (jsdom), el pin queda en las coords del reporte.
        lat: ZONAS.Armenia.centroLat,
        lng: ZONAS.Armenia.centroLng,
        comentario: 'La vi en la ciclovía',
      }),
    );
  });

  it('la sección de avistamientos NO aparece en reportes encontrados', async () => {
    vi.mocked(client.obtenerReporte).mockResolvedValue(
      crearReporte({ tipo: 'encontrado', nombre_mascota: null, situacion: 'conmigo' }),
    );

    renderDetalle();

    await screen.findByRole('heading', { name: 'Perro' });
    expect(screen.queryByText('Avistamientos')).not.toBeInTheDocument();
  });

  // --- Reportes del crawler (ADR 0010) ---

  it('un reporte crawleado sin teléfono ofrece la publicación original en vez de WhatsApp', async () => {
    vi.mocked(client.obtenerReporte).mockResolvedValue(
      crearReporte({
        user_id: 2,
        telefono_contacto: null,
        fuente: 'crawl',
        crawl_metadata: {
          plataforma: 'instagram',
          url_post: 'https://www.instagram.com/p/ABC123/',
          autor_handle: 'rescate.cali',
          fecha_post: '2026-08-11',
          texto_original: null,
          modelo_extraccion: 'llamaextract',
          confianza: 0.87,
          indice_mascota: 0,
          total_mascotas: 1,
        },
      }),
    );

    renderDetalle();

    const original = await screen.findByRole('link', { name: 'Ver publicación original' });
    expect(original.getAttribute('href')).toBe('https://www.instagram.com/p/ABC123/');
    expect(screen.queryByRole('link', { name: 'Contactar por WhatsApp' })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'Llamar' })).not.toBeInTheDocument();
    expect(
      screen.getByText(
        /Encontrado en Instagram, publicado por @rescate\.cali\. La información fue extraída automáticamente/,
      ),
    ).toBeInTheDocument();
  });

  it('un reporte crawleado solo con handle ofrece el perfil de quien publicó', async () => {
    vi.mocked(client.obtenerReporte).mockResolvedValue(
      crearReporte({
        user_id: 2,
        telefono_contacto: null,
        fuente: 'crawl',
        crawl_metadata: {
          plataforma: 'instagram',
          url_post: null,
          autor_handle: 'rescate.cali',
          fecha_post: null,
          texto_original: null,
          modelo_extraccion: 'llamaextract',
          confianza: 0.7,
          indice_mascota: 0,
          total_mascotas: 1,
        },
      }),
    );

    renderDetalle();

    const perfil = await screen.findByRole('link', { name: 'Ver perfil de quien publicó' });
    expect(perfil.getAttribute('href')).toBe('https://www.instagram.com/rescate.cali/');
    expect(screen.queryByRole('link', { name: 'Contactar por WhatsApp' })).not.toBeInTheDocument();
  });

  it('un reporte crawleado CON teléfono mantiene los botones de contacto de siempre', async () => {
    vi.mocked(client.obtenerReporte).mockResolvedValue(
      crearReporte({
        user_id: 2,
        fuente: 'crawl',
        crawl_metadata: {
          plataforma: 'facebook',
          grupo: 'Mascotas Perdidas Armenia',
          url_post: null,
          autor_handle: 'rescates.armenia',
          fecha_post: null,
          texto_original: null,
          modelo_extraccion: 'llamaextract',
          confianza: 0.9,
          indice_mascota: 0,
          total_mascotas: 1,
        },
      }),
    );

    renderDetalle();

    expect(await screen.findByRole('link', { name: 'Contactar por WhatsApp' })).toBeInTheDocument();
    expect(
      screen.queryByRole('link', { name: 'Ver publicación original' }),
    ).not.toBeInTheDocument();
    // La variante de Facebook muestra también el grupo donde se publicó.
    expect(
      screen.getByText(/Encontrado en Facebook \(grupo Mascotas Perdidas Armenia\)/),
    ).toBeInTheDocument();
  });
});
