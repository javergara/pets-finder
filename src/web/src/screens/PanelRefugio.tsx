import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { listarSolicitudes, obtenerRefugio } from '../api/client';
import type { Solicitud, ShelterProfile } from '../api/types';
import { DEMO_SHELTER_ID } from '../lib/constants';

function formatoCop(valor: number): string {
  return `$${valor.toLocaleString('es-CO')}`;
}

function claseEtiqueta(etiqueta: string): string {
  if (etiqueta.startsWith('Sin responder')) return 'text-ochre';
  if (etiqueta === 'Visita agendada') return 'text-forest';
  return 'text-muted';
}

export function PanelRefugio() {
  const [perfil, setPerfil] = useState<ShelterProfile | null>(null);
  const [solicitudes, setSolicitudes] = useState<Solicitud[] | null>(null);

  useEffect(() => {
    obtenerRefugio(DEMO_SHELTER_ID).then(setPerfil);
    listarSolicitudes(DEMO_SHELTER_ID).then(setSolicitudes);
  }, []);

  if (perfil === null || solicitudes === null) {
    return (
      <div className="mx-auto mt-8 max-w-4xl space-y-4 p-6">
        <div className="h-24 animate-pulse rounded-2xl bg-surface-alt" />
        <div className="grid grid-cols-4 gap-4">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="h-20 animate-pulse rounded-2xl bg-surface-alt" />
          ))}
        </div>
        <div className="h-56 animate-pulse rounded-2xl bg-surface-alt" />
      </div>
    );
  }

  const metricas = perfil.metricas;

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      <header className="flex items-center justify-between gap-4 rounded-2xl border border-line bg-surface p-6">
        <div>
          <h1 className="font-display text-2xl text-ink">{perfil.nombre}</h1>
          <p className="text-sm text-muted">{metricas.mascotas_publicadas} mascotas publicadas</p>
        </div>
        <Link
          to="/refugio/publicar"
          className="rounded-full bg-forest px-4 py-2 text-sm font-medium text-bg"
        >
          Publicar mascota
        </Link>
      </header>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div className="rounded-2xl border border-line bg-surface p-4 text-center">
          <p className="font-display text-2xl text-forest">{metricas.interesados_este_mes}</p>
          <p className="text-xs text-muted">Interesados este mes</p>
        </div>
        <div className="rounded-2xl border border-line bg-surface p-4 text-center">
          <p className="font-display text-2xl text-forest">{metricas.visitas_agendadas}</p>
          <p className="text-xs text-muted">Visitas agendadas</p>
        </div>
        <div className="rounded-2xl border border-line bg-surface p-4 text-center">
          <p className="font-display text-2xl text-forest">{metricas.adopciones_cerradas}</p>
          <p className="text-xs text-muted">Adopciones cerradas</p>
        </div>
        <div className="rounded-2xl border border-line bg-surface p-4 text-center">
          <p className="font-display text-2xl text-forest">
            {formatoCop(metricas.apadrinamientos_recaudados_cop)}
          </p>
          <p className="text-xs text-muted">Apadrinamientos recaudados</p>
        </div>
      </div>

      <section className="rounded-2xl border border-line bg-surface p-6">
        <h2 className="mb-4 font-display text-lg text-ink">Solicitudes por revisar</h2>
        {solicitudes.length === 0 ? (
          <p className="text-sm text-muted">
            Todavía no llegan solicitudes de adopción para tus mascotas publicadas.
          </p>
        ) : (
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-line text-xs text-muted-2 uppercase">
                <th className="py-2 font-mono font-normal">Adoptante</th>
                <th className="py-2 font-mono font-normal">Mascota</th>
                <th className="py-2 font-mono font-normal">Afinidad</th>
                <th className="py-2 font-mono font-normal">Estado</th>
                <th className="py-2 font-mono font-normal" />
              </tr>
            </thead>
            <tbody>
              {solicitudes.map((solicitud) => (
                <tr key={solicitud.id} className="border-b border-line last:border-0">
                  <td className="py-3 text-ink-soft">{solicitud.adoptante.nombre}</td>
                  <td className="py-3 text-ink-soft">{solicitud.pet.nombre}</td>
                  <td className="py-3">
                    <span className="rounded-full bg-forest px-2 py-0.5 font-mono text-xs text-bg">
                      {solicitud.afinidad.score}%
                    </span>
                  </td>
                  <td className={`py-3 ${claseEtiqueta(solicitud.etiqueta)}`}>
                    {solicitud.etiqueta}
                  </td>
                  <td className="py-3 text-right">
                    <Link
                      to={`/refugio/solicitudes/${solicitud.id}`}
                      className="font-mono text-xs tracking-wide text-forest uppercase hover:underline"
                    >
                      Revisar
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
