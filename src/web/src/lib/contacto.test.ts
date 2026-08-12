import { describe, expect, it } from 'vitest';
import { mensajeContacto, urlPerfilPlataforma, urlTelefono, urlWhatsApp } from './contacto';

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
