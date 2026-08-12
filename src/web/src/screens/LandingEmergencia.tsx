import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { mediaUrl, obtenerReunidos } from '../api/client';
import type { ReunidosResumen } from '../api/types';

// Landing de emergencia: dos caminos gigantes, decididos en dos segundos,
// y la franja de reencuentros como métrica de esperanza.
export function LandingEmergencia() {
  const [reunidos, setReunidos] = useState<ReunidosResumen | null>(null);

  useEffect(() => {
    // La landing nunca se bloquea por esta llamada: sin datos, la franja no aparece.
    obtenerReunidos()
      .then(setReunidos)
      .catch(() => setReunidos(null));
  }, []);

  return (
    <div className="mx-auto flex min-h-svh max-w-4xl flex-col items-center justify-center gap-8 p-6 text-center">
      <p className="font-mono text-sm uppercase tracking-wider text-muted">
        Colombia · Sismo del 10 de agosto de 2026
      </p>
      <h1 className="max-w-2xl font-display text-5xl text-ink sm:text-6xl">
        Ayudemos a cada mascota a volver a casa.
      </h1>
      <p className="max-w-xl text-lg text-ink-soft">
        Reporta una mascota perdida o una que encontraste entre los escombros. La comunidad busca
        contigo: cada reporte con foto y ubicación acerca un reencuentro.
      </p>

      <div className="flex w-full max-w-2xl flex-col gap-4 sm:flex-row">
        <Link
          to="/reportar/perdido"
          className="flex-1 rounded-2xl bg-danger px-8 py-6 text-xl font-medium text-bg shadow-sm"
        >
          Perdí a mi mascota
        </Link>
        <Link
          to="/reportar/encontrado"
          className="flex-1 rounded-2xl bg-forest px-8 py-6 text-xl font-medium text-bg shadow-sm"
        >
          Encontré una mascota
        </Link>
      </div>

      <div className="flex flex-wrap items-center justify-center gap-6 text-sm">
        <Link to="/reportes" className="font-medium text-forest underline-offset-4 hover:underline">
          Ver todos los reportes
        </Link>
        <Link to="/mapa" className="font-medium text-forest underline-offset-4 hover:underline">
          Ver el mapa
        </Link>
        <Link to="/ayudar" className="font-medium text-forest underline-offset-4 hover:underline">
          ¿Quieres ayudar? Centros de acopio y fundaciones
        </Link>
      </div>

      {reunidos !== null && reunidos.total > 0 && (
        <section className="w-full max-w-2xl rounded-2xl border border-forest-tint-line bg-forest-tint p-6">
          <p className="font-display text-3xl text-forest">{reunidos.total}</p>
          <p className="text-sm text-ink-soft">
            {reunidos.total === 1 ? 'reencuentro logrado' : 'reencuentros logrados'} gracias a la
            comunidad
          </p>
          <div className="mt-4 flex justify-center gap-3">
            {reunidos.recientes.slice(0, 4).map((reporte) => (
              <Link
                key={reporte.id}
                to={`/reporte/${reporte.id}`}
                aria-label={`Reencuentro de ${reporte.nombre_mascota ?? reporte.especie}`}
                className="h-14 w-14 rounded-xl border border-forest-tint-line bg-surface-alt bg-cover bg-center"
                style={{
                  backgroundImage: reporte.foto_url
                    ? `url(${mediaUrl(reporte.foto_url)})`
                    : undefined,
                }}
              />
            ))}
          </div>
        </section>
      )}

      <p className="max-w-md text-xs text-muted">
        Armenia · Pereira · Manizales · Cali · Quibdó · Bogotá — y cualquier lugar de Colombia. Sin
        costo, sin fricción: solo tu nombre y un teléfono de contacto.
      </p>
    </div>
  );
}
