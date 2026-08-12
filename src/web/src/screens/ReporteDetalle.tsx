import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { mediaUrl, obtenerReporte } from '../api/client';
import type { Reporte } from '../api/types';
import { ContactoBotones } from '../components/ContactoBotones';
import { MapaLienzo } from '../components/MapaLienzo';

const ETIQUETA_TIPO = {
  perdido: { texto: 'Se perdió', color: 'bg-danger' },
  encontrado: { texto: 'Encontrada', color: 'bg-forest' },
} as const;

const ETIQUETA_ESPECIE = { perro: 'Perro', gato: 'Gato', otro: 'Otro animal' } as const;

const ETIQUETA_SITUACION = {
  conmigo: 'La tiene resguardada quien la reportó',
  vista: 'Fue vista, pero no la pudieron atrapar',
} as const;

function formatearFecha(iso: string): string {
  const [y, m, d] = iso.split('-');
  return `${d}/${m}/${y}`;
}

export function ReporteDetalle() {
  const { id } = useParams<{ id: string }>();
  const [reporte, setReporte] = useState<Reporte | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (!id) return;
    obtenerReporte(Number(id)).then(setReporte);
  }, [id]);

  if (!reporte) {
    return <div className="mx-auto mt-8 h-96 max-w-2xl animate-pulse rounded-2xl bg-surface-alt" />;
  }

  const tipo = ETIQUETA_TIPO[reporte.tipo];
  const titulo = reporte.nombre_mascota ?? ETIQUETA_ESPECIE[reporte.especie];
  const lugar = reporte.zona === 'Otro' ? reporte.ciudad_texto ?? 'Colombia' : reporte.zona;

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-6 pb-24">
      <button type="button" onClick={() => navigate(-1)} className="text-sm text-muted">
        ← Volver
      </button>

      {reporte.foto_url && (
        <img
          src={mediaUrl(reporte.foto_url)}
          alt={`Foto del reporte de ${titulo}`}
          className="aspect-4/3 w-full rounded-[22px] border border-line object-cover"
        />
      )}

      <header className="flex items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl text-ink">{titulo}</h1>
          <p className="mt-1 text-sm text-muted">
            {ETIQUETA_ESPECIE[reporte.especie]} · {lugar}
            {reporte.barrio ? ` · ${reporte.barrio}` : ''} · {formatearFecha(reporte.fecha_evento)}
          </p>
        </div>
        <span
          className={`rounded-md px-3 py-1 font-mono text-xs tracking-wide text-bg ${tipo.color}`}
        >
          {tipo.texto}
        </span>
      </header>

      {reporte.estado === 'reunido' && (
        <p className="rounded-2xl border border-forest-tint-line bg-forest-tint p-4 text-sm text-forest">
          Esta mascota ya se reencontró con su familia. 💚
        </p>
      )}

      <section className="rounded-2xl border border-line bg-surface p-6">
        <h2 className="mb-2 font-display text-lg text-ink">Descripción y señas</h2>
        <p className="text-ink-soft">{reporte.descripcion}</p>
        {reporte.situacion && (
          <p className="mt-3 text-sm text-muted">{ETIQUETA_SITUACION[reporte.situacion]}</p>
        )}
      </section>

      <section className="rounded-2xl border border-line bg-surface p-6">
        <h2 className="mb-2 font-display text-lg text-ink">
          {reporte.tipo === 'perdido' ? 'Dónde se perdió' : 'Dónde la vieron o encontraron'}
        </h2>
        <MapaLienzo
          zona={reporte.zona}
          pines={[
            {
              id: reporte.id,
              lat: reporte.lat,
              lng: reporte.lng,
              colorClass: tipo.color,
              etiqueta: `Ubicación del reporte de ${titulo}`,
            },
          ]}
        />
      </section>

      {reporte.estado === 'activo' && (
        <section className="rounded-2xl border border-line bg-surface p-6">
          <h2 className="mb-2 font-display text-lg text-ink">
            {reporte.tipo === 'perdido' ? '¿La viste? Avísale a su familia' : '¿Es tuya? Escríbele'}
          </h2>
          <ContactoBotones
            tipo={reporte.tipo}
            etiqueta={titulo}
            telefono={reporte.telefono_contacto}
          />
        </section>
      )}
    </div>
  );
}
