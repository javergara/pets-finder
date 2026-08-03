import { useEffect, useState } from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { obtenerPerfil } from '../api/client';
import { getActiveUserId } from '../lib/session';

type Estado =
  | { tipo: 'cargando' }
  | { tipo: 'sin-cuestionario' }
  | { tipo: 'listo' }
  | { tipo: 'error'; mensaje: string };

// Gate de rutas: sin HomeProfile no hay afinidad que calcular, así que /descubrir,
// /matches y /mascota/:id no tienen sentido todavía (ver progress/current.md, paso 6).
// /registro y /cuestionario quedan fuera de este guard a propósito.
export function RequiereHomeProfile() {
  const [estado, setEstado] = useState<Estado>({ tipo: 'cargando' });

  useEffect(() => {
    let cancelado = false;
    obtenerPerfil(getActiveUserId())
      .then((perfil) => {
        if (cancelado) return;
        setEstado(perfil.home_profile === null ? { tipo: 'sin-cuestionario' } : { tipo: 'listo' });
      })
      .catch((error: unknown) => {
        if (cancelado) return;
        const mensaje = error instanceof Error ? error.message : 'No se pudo verificar tu perfil.';
        setEstado({ tipo: 'error', mensaje });
      });
    return () => {
      cancelado = true;
    };
  }, []);

  if (estado.tipo === 'cargando') {
    return (
      <div className="mx-auto mt-8 max-w-2xl space-y-4 p-6">
        <div className="h-24 animate-pulse rounded-2xl bg-surface-alt" />
        <div className="h-40 animate-pulse rounded-2xl bg-surface-alt" />
      </div>
    );
  }

  if (estado.tipo === 'error') {
    return (
      <div className="mx-auto mt-8 max-w-2xl p-6">
        <div className="rounded-2xl border border-line bg-surface-alt p-6 text-center text-ink-soft">
          No pudimos cargar tu perfil. Intenta de nuevo en unos minutos.
          <p className="mt-2 text-xs text-muted">{estado.mensaje}</p>
        </div>
      </div>
    );
  }

  if (estado.tipo === 'sin-cuestionario') {
    return <Navigate to="/cuestionario" replace />;
  }

  return <Outlet />;
}
