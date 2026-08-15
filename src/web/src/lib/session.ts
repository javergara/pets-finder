// Sesión ligera sin backend (ver docs/architecture.md §6): el "usuario activo" es
// simplemente un id persistido en localStorage. Sin nada guardado (usuarios semilla,
// primera visita antes de /registro), cae al DEMO_USER_ID de siempre.
import { DEMO_USER_ID } from './constants';

const STORAGE_KEY = 'reencuentro_active_user_id';

export function getActiveUserId(): number {
  const raw = localStorage.getItem(STORAGE_KEY);
  const parsed = raw ? Number(raw) : NaN;
  return Number.isFinite(parsed) ? parsed : DEMO_USER_ID;
}

export function setActiveUserId(userId: number): void {
  localStorage.setItem(STORAGE_KEY, String(userId));
}

// Distingue "nunca se registró" (clave ausente) del fallback DEMO_USER_ID que
// devuelve getActiveUserId(): el formulario de reporte usa esto para mandar al
// registro antes de reportar.
export function hasActiveUser(): boolean {
  return localStorage.getItem(STORAGE_KEY) !== null;
}

/**
 * ¿Este `userId` es el de la persona que está usando la app ahora mismo?
 *
 * ⚠️ Es la única forma correcta de calcular autoría en la UI. Comparar a mano
 * contra `getActiveUserId()` es un agujero de seguridad: sin cuenta esa función
 * cae al `DEMO_USER_ID` (1), así que un visitante anónimo se hace pasar por el
 * usuario 1 y ve —y puede usar— los controles de escritura de todo lo que le
 * pertenezca. El `hasActiveUser()` de delante es lo que lo impide.
 */
export function esUsuarioActivo(userId: number | null | undefined): boolean {
  return hasActiveUser() && userId === getActiveUserId();
}
