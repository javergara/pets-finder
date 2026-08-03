import { useEffect, useState } from 'react';
import { mediaUrl, obtenerPerfil } from '../api/client';
import type { HomeProfile, UserProfile } from '../api/types';
import { DEMO_USER_ID } from '../lib/constants';

const VIVIENDA_LABEL: Record<string, string> = {
  apartamento: 'Apartamento',
  casa: 'Casa',
};

const ESPACIO_EXTERIOR_LABEL: Record<string, string> = {
  ninguno: 'Sin espacio exterior',
  patio: 'Patio',
  jardin: 'Jardín',
};

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

function HogarResumen({ home }: { home: HomeProfile }) {
  const filas: Array<[string, string]> = [
    ['Vivienda', VIVIENDA_LABEL[home.vivienda] ?? home.vivienda],
    ['Espacio exterior', ESPACIO_EXTERIOR_LABEL[home.espacio_exterior] ?? home.espacio_exterior],
    ['Personas en casa', String(home.personas_en_casa)],
    ['Niños en casa', home.tiene_ninos ? 'Sí' : 'No'],
    ['Otros perros', home.tiene_otros_perros ? 'Sí' : 'No'],
    ['Otros gatos', home.tiene_otros_gatos ? 'Sí' : 'No'],
    ['Horas fuera al día', `${home.horas_fuera_dia}h`],
  ];

  return (
    <dl className="grid grid-cols-2 gap-x-4 gap-y-3">
      {filas.map(([etiqueta, valor]) => (
        <div key={etiqueta}>
          <dt className="font-mono text-xs tracking-wide text-muted-2 uppercase">{etiqueta}</dt>
          <dd className="text-ink-soft">{valor}</dd>
        </div>
      ))}
    </dl>
  );
}

export function MiPerfil() {
  const [perfil, setPerfil] = useState<UserProfile | null>(null);

  useEffect(() => {
    obtenerPerfil(DEMO_USER_ID).then(setPerfil);
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
        <h2 className="mb-4 font-display text-lg text-ink">Mi hogar</h2>
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
    </div>
  );
}
