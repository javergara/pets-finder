import { describe, expect, it } from 'vitest';
import type { Reporte } from '../api/types';
import { textoCartel } from './cartel';

function reporte(overrides: Partial<Reporte> = {}): Reporte {
  return {
    id: 7,
    user_id: 1,
    tipo: 'perdido',
    especie: 'perro',
    nombre_mascota: 'Rocky',
    raza: null,
    color: null,
    tamano: null,
    descripcion: 'x',
    foto_url: null,
    zona: 'Cali',
    ciudad_texto: null,
    barrio: 'El Limonar',
    lat: 3.4,
    lng: -76.5,
    situacion: null,
    fecha_evento: '2026-08-10',
    telefono_contacto: '3001234567',
    instagram: null,
    facebook: null,
    fuente: 'manual',
    crawl_metadata: null,
    idempotency_id: null,
    estado: 'activo',
    creado_en: new Date().toISOString(),
    resuelto_en: null,
    ...overrides,
  };
}

describe('textoCartel', () => {
  it('un perdido con nombre, barrio y teléfono arma el cartel completo', () => {
    expect(textoCartel(reporte(), 'https://petfinder-col.com')).toEqual({
      encabezado: 'SE BUSCA',
      titulo: 'Rocky',
      lugar: 'El Limonar · Cali',
      contacto: 'WhatsApp: 3001234567',
      url: 'https://petfinder-col.com/reporte/7',
    });
  });

  it('un encontrado sin nombre usa el título compuesto y el encabezado ENCONTRADA', () => {
    const textos = textoCartel(
      reporte({
        tipo: 'encontrado',
        nombre_mascota: null,
        tamano: 'mediano',
        color: 'Café',
        situacion: 'conmigo',
      }),
    );

    expect(textos.encabezado).toBe('ENCONTRADA');
    expect(textos.titulo).toBe('Perro mediano café');
  });

  it('sin teléfono remite al QR y con zona Otro usa la ciudad', () => {
    const textos = textoCartel(
      reporte({ telefono_contacto: null, barrio: null, zona: 'Otro', ciudad_texto: 'Tuluá' }),
    );

    expect(textos.contacto).toBe('Contacto en el reporte (escanea el QR)');
    expect(textos.lugar).toBe('Tuluá');
  });
});
