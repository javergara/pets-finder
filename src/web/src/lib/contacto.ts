// Contacto directo dueño↔rescatista por WhatsApp/teléfono (ADR 0005 §3):
// sin chat interno, el canal es el que todo el mundo ya tiene abierto.

// Normaliza un teléfono colombiano al formato E.164 sin '+': solo dígitos y,
// si es un celular nacional de 10 dígitos (3XXXXXXXXX), se antepone el 57.
function normalizar(telefono: string): string {
  const digitos = telefono.replace(/\D/g, '');
  if (digitos.length === 10) return `57${digitos}`;
  return digitos;
}

export function urlWhatsApp(telefono: string, mensaje: string): string {
  return `https://wa.me/${normalizar(telefono)}?text=${encodeURIComponent(mensaje)}`;
}

export function urlTelefono(telefono: string): string {
  return `tel:+${normalizar(telefono)}`;
}

// URL del perfil de quien publicó un post crawleado (ADR 0009), derivada del
// handle cuando el pantallazo no dejó leer la URL del post. Para WhatsApp el
// "handle" visible suele ser el número de quien publicó → wa.me si es un
// teléfono plausible. 'desconocida' no tiene forma canónica de perfil → null.
export function urlPerfilPlataforma(
  plataforma: 'instagram' | 'facebook' | 'whatsapp' | 'x' | 'tiktok' | 'desconocida',
  handle: string,
): string | null {
  const limpio = handle.trim().replace(/^@/, '');
  if (!limpio) return null;
  switch (plataforma) {
    case 'instagram':
      return `https://www.instagram.com/${limpio}/`;
    case 'facebook':
      return `https://www.facebook.com/${limpio}`;
    case 'x':
      return `https://x.com/${limpio}`;
    case 'tiktok':
      return `https://www.tiktok.com/@${limpio}`;
    case 'whatsapp': {
      const digitos = limpio.replace(/\D/g, '');
      return digitos.length >= 7
        ? `https://wa.me/${digitos.length === 10 ? `57${digitos}` : digitos}`
        : null;
    }
    default:
      return null;
  }
}

// Mensaje precargado: menciona el reporte (nombre o especie) y la app, para
// que quien recibe el WhatsApp entienda de inmediato de qué se trata.
export function mensajeContacto(tipo: 'perdido' | 'encontrado', etiqueta: string): string {
  return tipo === 'perdido'
    ? `Hola, te escribo desde Pet Finder Col por tu reporte de ${etiqueta}. Creo que puedo ayudarte a encontrarla.`
    : `Hola, te escribo desde Pet Finder Col por la mascota que reportaste (${etiqueta}). Creo que puede ser la mía.`;
}

// Mensaje para escribirle a una organización de la red de apoyo (feature 32).
export function mensajeAyudaOrganizacion(nombre: string): string {
  return `Hola, los encontré en Pet Finder Col (${nombre}). Quiero ayudar / necesito información.`;
}

// Prefill del botón "Quiero ayudar" de una necesidad concreta (feature 33).
export function mensajeQuieroAyudar(descripcion: string): string {
  return `Hola, vi en Pet Finder Col que necesitan ${descripcion}. Quiero ayudar.`;
}
