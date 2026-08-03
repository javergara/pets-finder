// Sesión ligera sin backend (ver docs/architecture.md §6): el "usuario activo" es
// simplemente un id persistido en localStorage. Sin nada guardado (usuarios semilla,
// primera visita antes de /registro), cae al DEMO_USER_ID de siempre.
import { DEMO_USER_ID } from './constants';

const STORAGE_KEY = 'adopta_active_user_id';

export function getActiveUserId(): number {
  const raw = localStorage.getItem(STORAGE_KEY);
  const parsed = raw ? Number(raw) : NaN;
  return Number.isFinite(parsed) ? parsed : DEMO_USER_ID;
}

export function setActiveUserId(userId: number): void {
  localStorage.setItem(STORAGE_KEY, String(userId));
}
