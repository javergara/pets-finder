import type { EstadoSolicitud } from '../api/types';

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

// URL del perfil de quien publicó un post crawleado (ADR 0010), derivada del
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

// Prefill para escribirle a quien publicó una mascota en adopción (AD-01).
// Quien recibe el WhatsApp puede ser una fundación con decenas de publicaciones
// o un rescatista con una sola: el mensaje nombra a la mascota y la app para que
// no tenga que preguntar de qué se trata, y abre con la única duda que siempre
// importa (si sigue disponible). "adoptarla" concuerda con "la mascota", no con
// el sexo del animal.
export function mensajeAdoptarMascota(nombre: string): string {
  return `Hola, vi a ${nombre} en Pet Finder Col y me interesa adoptarla. ¿Sigue disponible?`;
}

// La conversación de una solicitud de adopción, en las dos direcciones (AD-06,
// ADR 0013). No hay chat interno ni historial dentro del producto: estos dos
// mensajes son todo lo que quien recibe el WhatsApp tiene para entender de qué
// le hablan, así que nombran la mascota (quien publica puede tener decenas
// abiertas) y la app (el número le llega en frío).
//
// El texto cambia por estado porque el motivo de escribir cambia: presentarse,
// preguntar cómo va, confirmar la visita, coordinar la entrega. Los `Record`
// son exhaustivos sobre `EstadoSolicitud`: un sexto estado no compila sin
// decidir qué se dice en él, que es exactamente la revisión que hace falta.
//
// Nada de lenguaje de fracaso, tampoco en `cerrado`: una solicitud que se
// cierra no es una puerta que se azota, y quien la escribió sigue buscando (o
// sigue teniendo mascotas que dar en adopción).

/** Lo que escribe quien pidió la mascota a quien la publicó. */
export function mensajeAdopcionAdoptante(estado: EstadoSolicitud, nombre: string): string {
  const POR_ESTADO: Record<EstadoSolicitud, string> = {
    solicitado: `pedí a ${nombre} en adopción y me encantaría contarte cómo es mi hogar. ¿Cuándo podemos hablar?`,
    en_revision: `te escribo por mi solicitud de adopción de ${nombre}. ¿Cómo va? Quedo pendiente de lo que necesites saber de mí.`,
    visita_agendada: `me avisaron que puedo ir a conocer a ${nombre}. ¿Qué día y a qué hora te queda bien?`,
    adoptado: `¡gracias por confiarme a ${nombre}! Coordinemos la entrega: dime qué día te queda bien.`,
    cerrado: `te escribo por mi solicitud de ${nombre}. Sigo buscando una mascota a la que darle un hogar, así que si tienes otra en adopción cuenta conmigo.`,
  };
  return `Hola, te escribo desde Pet Finder Col: ${POR_ESTADO[estado]}`;
}

/** Lo que escribe quien publicó la mascota a quien la pidió.
 *
 * Lleva el nombre de quien la pidió porque el número que dejó al solicitarla
 * llega en frío y a esa persona le escribe alguien que no tiene agendado. */
export function mensajeAdopcionPublicador(
  estado: EstadoSolicitud,
  nombre: string,
  nombreAdoptante: string,
): string {
  const POR_ESTADO: Record<EstadoSolicitud, string> = {
    solicitado: `recibí tu solicitud para adoptar a ${nombre} y me encantaría conocerte. ¿Cuándo puedes hablar?`,
    en_revision: `estoy revisando tu solicitud para adoptar a ${nombre} y quiero preguntarte un par de cosas.`,
    visita_agendada: `ya puedes venir a conocer a ${nombre}. ¿Te sirve este fin de semana, o prefieres que busquemos otro día?`,
    adoptado: `${nombre} ya tiene hogar contigo. Coordinemos la entrega: dime qué día te queda bien.`,
    cerrado: `te escribo por tu solicitud para adoptar a ${nombre}. Esta vez no siguió adelante, pero me quedo con tus datos: en cuanto tengamos otra mascota buscando hogar te escribo.`,
  };
  return `Hola ${nombreAdoptante}, te escribo desde Pet Finder Col: ${POR_ESTADO[estado]}`;
}
