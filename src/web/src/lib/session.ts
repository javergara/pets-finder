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
