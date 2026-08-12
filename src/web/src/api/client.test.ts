import { describe, expect, it } from 'vitest';
import { mediaUrl } from './client';

describe('mediaUrl', () => {
  it('prefija las rutas relativas con la base de la API (fotos locales del seed/dev)', () => {
    expect(mediaUrl('/media/seed/report_1.jpg')).toBe(
      'http://127.0.0.1:8000/media/seed/report_1.jpg',
    );
  });

  it('devuelve las URLs absolutas tal cual (fotos en Supabase Storage, ADR 0006)', () => {
    const absoluta = 'https://abc123.supabase.co/storage/v1/object/public/fotos/x.jpg';
    expect(mediaUrl(absoluta)).toBe(absoluta);
  });
});
