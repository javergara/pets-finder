// Cartel imprimible por reporte (feature 44, plan de impacto Cali C1): el
// flyer que la comunidad ya pega en postes y manda por WhatsApp, generado en
// el navegador con canvas (mismo enfoque local de comprimirImagen) y con un
// QR que trae a la gente al reporte — el puente físico→digital.

import QRCode from 'qrcode';
import { mediaUrl } from '../api/client';
import type { Reporte } from '../api/types';
import { tituloReporte } from './titulo';

const ANCHO = 1080;
const ALTO = 1350;

const COLORES = {
  fondo: '#f7f3ea',
  tinta: '#1b1a17',
  suave: '#6b665c',
  perdido: '#9b3b2e',
  encontrado: '#1f4d3a',
};

export type TextoCartel = {
  encabezado: string;
  titulo: string;
  lugar: string;
  contacto: string;
  url: string;
};

/** Los textos del cartel — puro y testeable, separado del dibujo. */
export function textoCartel(
  reporte: Reporte,
  origen: string = 'https://petfinder-col.com',
): TextoCartel {
  const lugarBase = reporte.zona === 'Otro' ? reporte.ciudad_texto ?? 'Colombia' : reporte.zona;
  return {
    encabezado: reporte.tipo === 'perdido' ? 'SE BUSCA' : 'ENCONTRADA',
    titulo: tituloReporte(reporte),
    lugar: reporte.barrio ? `${reporte.barrio} · ${lugarBase}` : lugarBase,
    contacto: reporte.telefono_contacto
      ? `WhatsApp: ${reporte.telefono_contacto}`
      : 'Contacto en el reporte (escanea el QR)',
    url: `${origen}/reporte/${reporte.id}`,
  };
}

function cargarFoto(fotoUrl: string): Promise<HTMLImageElement | null> {
  return new Promise((resolve) => {
    const imagen = new Image();
    imagen.crossOrigin = 'anonymous';
    imagen.onload = () => resolve(imagen);
    imagen.onerror = () => resolve(null);
    // Cache-bust deliberado: el <img> del detalle ya cacheó esta foto SIN
    // header CORS (petición sin Origin) y Chrome reusa esa entrada para la
    // petición con crossOrigin, bloqueándola. Un query param fuerza una
    // respuesta fresca con Access-Control-Allow-Origin.
    const base = mediaUrl(fotoUrl);
    imagen.src = `${base}${base.includes('?') ? '&' : '?'}cartel=1`;
  });
}

/** Dibuja el cartel y dispara la descarga del PNG. */
export async function descargarCartel(reporte: Reporte): Promise<void> {
  const textos = textoCartel(reporte, window.location.origin);
  const color = reporte.tipo === 'perdido' ? COLORES.perdido : COLORES.encontrado;

  const canvas = document.createElement('canvas');
  canvas.width = ANCHO;
  canvas.height = ALTO;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  // Fondo y banda superior con el encabezado.
  ctx.fillStyle = COLORES.fondo;
  ctx.fillRect(0, 0, ANCHO, ALTO);
  ctx.fillStyle = color;
  ctx.fillRect(0, 0, ANCHO, 150);
  ctx.fillStyle = '#f7f3ea';
  ctx.font = 'bold 92px Georgia, serif';
  ctx.textAlign = 'center';
  ctx.fillText(textos.encabezado, ANCHO / 2, 110);

  // Foto (contain, centrada) — el cartel funciona igual sin ella.
  const foto = reporte.foto_url ? await cargarFoto(reporte.foto_url) : null;
  const fotoAlto = 620;
  if (foto) {
    const escala = Math.min((ANCHO - 80) / foto.width, fotoAlto / foto.height);
    const w = foto.width * escala;
    const h = foto.height * escala;
    ctx.drawImage(foto, (ANCHO - w) / 2, 180 + (fotoAlto - h) / 2, w, h);
  } else {
    ctx.fillStyle = '#e4ddce';
    ctx.fillRect(40, 180, ANCHO - 80, fotoAlto);
    ctx.fillStyle = COLORES.suave;
    ctx.font = '44px Georgia, serif';
    ctx.fillText('Foto en el reporte (escanea el QR)', ANCHO / 2, 180 + fotoAlto / 2);
  }

  // Título, lugar y contacto.
  ctx.fillStyle = COLORES.tinta;
  ctx.font = 'bold 64px Georgia, serif';
  ctx.fillText(textos.titulo, ANCHO / 2, 890);
  ctx.fillStyle = COLORES.suave;
  ctx.font = '42px Helvetica, Arial, sans-serif';
  ctx.fillText(textos.lugar, ANCHO / 2, 950);
  ctx.fillStyle = color;
  ctx.font = 'bold 58px Helvetica, Arial, sans-serif';
  ctx.fillText(textos.contacto, ANCHO / 2, 1040);

  // QR + marca.
  const qr = document.createElement('canvas');
  await QRCode.toCanvas(qr, textos.url, { width: 220, margin: 1 });
  ctx.drawImage(qr, ANCHO - 270, ALTO - 270);
  ctx.fillStyle = COLORES.tinta;
  ctx.textAlign = 'left';
  ctx.font = 'bold 44px Georgia, serif';
  ctx.fillText('Pet Finder Col', 50, ALTO - 150);
  ctx.fillStyle = COLORES.suave;
  ctx.font = '34px Helvetica, Arial, sans-serif';
  ctx.fillText('Más señas, fotos y contacto directo:', 50, ALTO - 95);
  ctx.fillText('petfinder-col.com', 50, ALTO - 50);

  const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, 'image/png'));
  if (!blob) return;
  const enlace = document.createElement('a');
  enlace.href = URL.createObjectURL(blob);
  enlace.download = `cartel-${textos.titulo.toLowerCase().replace(/[^a-z0-9]+/g, '-')}.png`;
  enlace.click();
  URL.revokeObjectURL(enlace.href);
}
