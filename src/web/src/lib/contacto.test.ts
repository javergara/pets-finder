import { describe, expect, it } from 'vitest';
import type { EstadoSolicitud } from '../api/types';
import {
  mensajeAdopcionAdoptante,
  mensajeAdopcionPublicador,
  mensajeContacto,
  urlPerfilPlataforma,
  urlTelefono,
  urlWhatsApp,
} from './contacto';

describe('urlWhatsApp', () => {
  it('un celular nacional de 10 dígitos queda con el 57 antepuesto', () => {
    expect(urlWhatsApp('3001234567', 'Hola')).toBe('https://wa.me/573001234567?text=Hola');
  });

  it('un número ya con indicativo no se duplica', () => {
    expect(urlWhatsApp('573001234567', 'Hola')).toBe('https://wa.me/573001234567?text=Hola');
  });

  it('espacios, guiones y el + se descartan', () => {
    expect(urlWhatsApp('+57 300 123-4567', 'Hola')).toBe('https://wa.me/573001234567?text=Hola');
  });

  it('el mensaje va URL-encoded', () => {
    expect(urlWhatsApp('3001234567', 'Hola, ¿cómo estás?')).toBe(
      'https://wa.me/573001234567?text=Hola%2C%20%C2%BFc%C3%B3mo%20est%C3%A1s%3F',
    );
  });
});

describe('urlTelefono', () => {
  it('genera tel: en formato internacional', () => {
    expect(urlTelefono('3001234567')).toBe('tel:+573001234567');
    expect(urlTelefono('+57 300 123 4567')).toBe('tel:+573001234567');
  });
});

describe('mensajeContacto', () => {
  it('para un perdido menciona el reporte y la app', () => {
    const mensaje = mensajeContacto('perdido', 'Rocky');
    expect(mensaje).toContain('Pet Finder Col');
    expect(mensaje).toContain('Rocky');
  });

  it('para un encontrado menciona la mascota reportada y la app', () => {
    const mensaje = mensajeContacto('encontrado', 'Perro');
    expect(mensaje).toContain('Pet Finder Col');
    expect(mensaje).toContain('Perro');
  });
});

// La comunicación de una solicitud de adopción (AD-06, ADR 0013): no hay chat
// interno, así que estos dos mensajes son TODO lo que quien recibe el WhatsApp
// tiene para entender de qué le hablan. De ahí las tres aserciones de cada caso:
// nombra la mascota (quien publica puede tener decenas), nombra la app (el
// número le llega en frío) y arma una url de wa.me con el texto URL-encoded.
const ESTADOS: EstadoSolicitud[] = [
  'solicitado',
  'en_revision',
  'visita_agendada',
  'adoptado',
  'cerrado',
];

const TELEFONO = '3001112233';

describe('mensajeAdopcionAdoptante (quien pidió la mascota escribe a quien la publicó)', () => {
  it.each(ESTADOS)('en estado "%s" nombra la mascota, la marca, y va a wa.me', (estado) => {
    const mensaje = mensajeAdopcionAdoptante(estado, 'Canela');

    expect(mensaje).toContain('Canela');
    expect(mensaje).toContain('Pet Finder Col');
    expect(urlWhatsApp(TELEFONO, mensaje)).toBe(
      `https://wa.me/573001112233?text=${encodeURIComponent(mensaje)}`,
    );
  });

  // El motivo de escribir cambia con el estado (presentarse, preguntar cómo va,
  // confirmar la visita, coordinar la entrega): un mensaje único para los cinco
  // sería el mismo "hola" genérico de siempre.
  it('los cinco estados dicen cosas distintas', () => {
    const mensajes = ESTADOS.map((estado) => mensajeAdopcionAdoptante(estado, 'Canela'));

    expect(new Set(mensajes).size).toBe(ESTADOS.length);
  });
});

describe('mensajeAdopcionPublicador (quien publicó escribe a quien pidió la mascota)', () => {
  it.each(ESTADOS)('en estado "%s" nombra la mascota, la marca, y va a wa.me', (estado) => {
    const mensaje = mensajeAdopcionPublicador(estado, 'Canela', 'Carlos');

    expect(mensaje).toContain('Canela');
    expect(mensaje).toContain('Pet Finder Col');
    expect(urlWhatsApp(TELEFONO, mensaje)).toBe(
      `https://wa.me/573001112233?text=${encodeURIComponent(mensaje)}`,
    );
  });

  // Quien pidió la mascota dejó su número al solicitarla y puede no reconocerlo:
  // el mensaje lo saluda por su nombre.
  it.each(ESTADOS)('en estado "%s" saluda por su nombre a quien pidió la mascota', (estado) => {
    expect(mensajeAdopcionPublicador(estado, 'Canela', 'Carlos')).toContain('Carlos');
  });

  it('los cinco estados dicen cosas distintas', () => {
    const mensajes = ESTADOS.map((estado) => mensajeAdopcionPublicador(estado, 'Canela', 'Carlos'));

    expect(new Set(mensajes).size).toBe(ESTADOS.length);
  });
});

// Las dos direcciones no son la misma frase con el nombre cambiado: quien pide
// se presenta y pregunta, quien publica responde y propone. Reusar una función
// para las dos dejaría a alguien escribiéndose a sí mismo en tercera persona.
it('cada dirección tiene su propio texto en todos los estados', () => {
  for (const estado of ESTADOS) {
    expect(mensajeAdopcionPublicador(estado, 'Canela', 'Carlos')).not.toBe(
      mensajeAdopcionAdoptante(estado, 'Canela'),
    );
  }
});

describe('urlPerfilPlataforma', () => {
  it('deriva el perfil por plataforma quitando el @ inicial', () => {
    expect(urlPerfilPlataforma('instagram', '@rescate.cali')).toBe(
      'https://www.instagram.com/rescate.cali/',
    );
    expect(urlPerfilPlataforma('facebook', 'rescates.armenia')).toBe(
      'https://www.facebook.com/rescates.armenia',
    );
    expect(urlPerfilPlataforma('x', 'rescates')).toBe('https://x.com/rescates');
    expect(urlPerfilPlataforma('tiktok', 'rescates')).toBe('https://www.tiktok.com/@rescates');
  });

  it('en whatsapp el handle visible es un teléfono: wa.me con prefijo 57 si es celular nacional', () => {
    expect(urlPerfilPlataforma('whatsapp', '300 123 4567')).toBe('https://wa.me/573001234567');
    expect(urlPerfilPlataforma('whatsapp', '+573001234567')).toBe('https://wa.me/573001234567');
  });

  it("sin forma canónica de perfil devuelve null ('desconocida', handle vacío, whatsapp no numérico)", () => {
    expect(urlPerfilPlataforma('desconocida', 'alguien')).toBeNull();
    expect(urlPerfilPlataforma('instagram', '  @ ')).toBeNull();
    expect(urlPerfilPlataforma('whatsapp', 'Cadena Mascotas')).toBeNull();
  });
});
