import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { listarApadrinamientos, mediaUrl, obtenerPerfil } from '../api/client';
import type { Sponsorship, UserProfile } from '../api/types';
import { HogarResumen } from '../components/HogarResumen';
import { getActiveUserId } from '../lib/session';

function formatoCop(valor: number): string {
  return `$${valor.toLocaleString('es-CO')}`;
}

function etiquetaPeriodicidad(periodicidad: Sponsorship['periodicidad']): string {
  return periodicidad === 'mensual' ? 'Mensual' : 'Pago único';
}

function iniciales(nombre: string): string {
  return nombre
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((parte) => parte[0]?.toUpperCase())
    .join('');
}

function miembroDesde(creadoEn: string): string {
  const fecha = new Date(creadoEn);
  if (Number.isNaN(fecha.getTime())) return creadoEn;
  return fecha.toLocaleDateString('es-CO', { year: 'numeric', month: 'long' });
}

export function MiPerfil() {
  const [perfil, setPerfil] = useState<UserProfile | null>(null);
  const [apadrinamientos, setApadrinamientos] = useState<Sponsorship[] | null>(null);

  useEffect(() => {
    obtenerPerfil(getActiveUserId()).then(setPerfil);
    listarApadrinamientos(getActiveUserId()).then(setApadrinamientos);
  }, []);

  if (perfil === null) {
    return (
      <div className="mx-auto mt-8 max-w-2xl space-y-4 p-6">
        <div className="h-24 animate-pulse rounded-2xl bg-surface-alt" />
        <div className="grid grid-cols-3 gap-4">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-20 animate-pulse rounded-2xl bg-surface-alt" />
          ))}
        </div>
        <div className="h-40 animate-pulse rounded-2xl bg-surface-alt" />
      </div>
    );
  }

  const metricas = perfil.metricas;
  const ubicacion = [perfil.ciudad, perfil.barrio].filter(Boolean).join(' · ');

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-6">
      <header className="flex items-center gap-4 rounded-2xl border border-line bg-surface p-6">
        {perfil.avatar_url ? (
          <img
            src={mediaUrl(perfil.avatar_url)}
            alt={`Foto de ${perfil.nombre}`}
            className="h-[82px] w-[82px] rounded-full object-cover"
          />
        ) : (
          <div className="flex h-[82px] w-[82px] items-center justify-center rounded-full bg-forest-tint font-display text-2xl text-forest">
            {iniciales(perfil.nombre)}
          </div>
        )}
        <div>
          <h1 className="font-display text-2xl text-ink">{perfil.nombre}</h1>
          <p className="text-sm text-muted">
            {ubicacion} · miembro desde {miembroDesde(perfil.creado_en)}
          </p>
        </div>
      </header>

      <div className="grid grid-cols-3 gap-4">
        <div className="rounded-2xl border border-line bg-surface p-4 text-center">
          <p className="font-display text-2xl text-forest">{metricas?.matches_activos ?? 0}</p>
          <p className="text-xs text-muted">Matches activos</p>
        </div>
        <div className="rounded-2xl border border-line bg-surface p-4 text-center">
          <p className="font-display text-2xl text-forest">{metricas?.visitas_agendadas ?? 0}</p>
          <p className="text-xs text-muted">Visitas agendadas</p>
        </div>
        <div className="rounded-2xl border border-line bg-surface p-4 text-center">
          <p className="font-display text-2xl text-forest">{metricas?.apadrinamientos ?? 0}</p>
          <p className="text-xs text-muted">Apadrinamientos</p>
        </div>
      </div>

      <section className="rounded-2xl border border-line bg-surface p-6">
        <div className="mb-4 flex items-center justify-between gap-3">
          <h2 className="font-display text-lg text-ink">Mi hogar</h2>
          <Link
            to="/cuestionario"
            className="font-mono text-xs tracking-wide text-forest uppercase hover:underline"
          >
            {perfil.home_profile ? 'Editar cuestionario' : 'Completar cuestionario'}
          </Link>
        </div>
        {perfil.home_profile ? (
          <HogarResumen home={perfil.home_profile} />
        ) : (
          <p className="text-sm text-muted">
            Aún no completaste el cuestionario de hogar. Cuando lo hagas, aquí verás un resumen.
          </p>
        )}
      </section>

      <section className="rounded-2xl border border-line bg-surface p-6">
        <h2 className="mb-2 font-display text-lg text-ink">Sobre mí</h2>
        <p className="text-ink-soft">
          {perfil.bio && perfil.bio.trim().length > 0
            ? perfil.bio
            : 'Todavía no escribiste nada sobre ti. Esto lo ven los refugios al recibir tu solicitud.'}
        </p>
      </section>

      <section className="rounded-2xl border border-line bg-surface p-6">
        <h2 className="mb-4 font-display text-lg text-ink">Mis apadrinamientos</h2>
        {apadrinamientos === null ? (
          <div className="space-y-3">
            {[0, 1].map((i) => (
              <div key={i} className="h-20 animate-pulse rounded-2xl bg-surface-alt" />
            ))}
          </div>
        ) : apadrinamientos.length === 0 ? (
          <p className="text-sm text-muted">
            Todavía no apadrinas ninguna mascota.{' '}
            <Link to="/apadrinar" className="text-forest hover:underline">
              Apadrina una ahora
            </Link>
            .
          </p>
        ) : (
          <ul className="space-y-4">
            {apadrinamientos.map((apadrinamiento) => (
              <li
                key={apadrinamiento.id}
                className="flex gap-4 rounded-2xl border border-line bg-surface-alt p-4"
              >
                {apadrinamiento.pet.fotos[0] && (
                  <img
                    src={mediaUrl(apadrinamiento.pet.fotos[0])}
                    alt={`Foto de ${apadrinamiento.pet.nombre}`}
                    className="h-16 w-16 shrink-0 rounded-xl object-cover"
                  />
                )}
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <p className="font-display text-lg text-ink">{apadrinamiento.pet.nombre}</p>
                    {!apadrinamiento.activo && (
                      <span className="rounded-full bg-surface px-2 py-0.5 font-mono text-[10px] tracking-wide text-muted uppercase">
                        Inactivo
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-ink-soft">
                    {formatoCop(apadrinamiento.monto_cop)} ·{' '}
                    {etiquetaPeriodicidad(apadrinamiento.periodicidad)}
                  </p>
                  {apadrinamiento.novedad && (
                    <p className="mt-2 rounded-xl bg-forest-tint p-3 text-sm text-ink">
                      {apadrinamiento.novedad}
                    </p>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
