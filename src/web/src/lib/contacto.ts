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

// Mensaje precargado: menciona el reporte (nombre o especie) y la app, para
// que quien recibe el WhatsApp entienda de inmediato de qué se trata.
export function mensajeContacto(tipo: 'perdido' | 'encontrado', etiqueta: string): string {
  return tipo === 'perdido'
    ? `Hola, te escribo desde Pet Finder Col por tu reporte de ${etiqueta}. Creo que puedo ayudarte a encontrarla.`
    : `Hola, te escribo desde Pet Finder Col por la mascota que reportaste (${etiqueta}). Creo que puede ser la mía.`;
}
