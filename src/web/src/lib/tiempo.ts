// Recencia relativa (feature 34): en una emergencia "hace 2 horas" dice más
// que una fecha absoluta. Función pura para poder testearla con un "ahora" fijo.

export function tiempoRelativo(iso: string, ahora: Date = new Date()): string {
  // El backend serializa datetimes UTC sin sufijo de zona: anclarlo explícito
  // para que el navegador no lo interprete en hora local.
  const conZona = iso.endsWith('Z') || iso.includes('+') ? iso : `${iso}Z`;
  const ms = ahora.getTime() - new Date(conZona).getTime();
  const minutos = Math.floor(ms / 60_000);

  if (minutos < 1) return 'hace un momento';
  if (minutos < 60) return `hace ${minutos} min`;
  const horas = Math.floor(minutos / 60);
  if (horas < 24) return horas === 1 ? 'hace 1 hora' : `hace ${horas} horas`;
  const dias = Math.floor(horas / 24);
  if (dias === 1) return 'ayer';
  if (dias < 7) return `hace ${dias} días`;
  const semanas = Math.floor(dias / 7);
  return semanas === 1 ? 'hace 1 semana' : `hace ${semanas} semanas`;
}
