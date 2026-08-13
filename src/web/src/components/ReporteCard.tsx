import { Link } from 'react-router-dom';
import { mediaUrl } from '../api/client';
import type { Reporte } from '../api/types';
import { tiempoRelativo } from '../lib/tiempo';
import { tituloReporte } from '../lib/titulo';

const ETIQUETA_TIPO = {
  perdido: { texto: 'Se perdió', color: 'bg-danger' },
  encontrado: { texto: 'Encontrada', color: 'bg-forest' },
} as const;

const ETIQUETA_ESPECIE = { perro: 'Perro', gato: 'Gato', otro: 'Otro animal' } as const;

function formatearFecha(iso: string): string {
  const [y, m, d] = iso.split('-');
  return `${d}/${m}/${y}`;
}

// Tarjeta de reporte: adaptación del estilo visual de las tarjetas de mascota
// de la era Adopta (git show adopta-v1:src/web/src/components/SwipeCard.tsx) —
// foto grande arriba con badge, bloque de texto abajo con chips y pie.
export function ReporteCard({ reporte }: { reporte: Reporte }) {
  const tipo = ETIQUETA_TIPO[reporte.tipo];
  const titulo = tituloReporte(reporte);
  const lugar = reporte.zona === 'Otro' ? reporte.ciudad_texto ?? 'Colombia' : reporte.zona;

  return (
    <Link
      to={`/reporte/${reporte.id}`}
      className="flex flex-col overflow-hidden rounded-[22px] border border-line bg-surface transition-shadow hover:shadow-[0_18px_40px_-28px_rgba(27,26,23,.5)]"
    >
      {/* <img loading="lazy"> en vez de background-image: el navegador solo
          descarga las fotos de las tarjetas que se acercan al viewport.
          object-contain (no cover): la mascota completa también en la tarjeta,
          para reconocerla rápido sin entrar al detalle. */}
      <div className="relative aspect-4/3 bg-surface-alt">
        {reporte.foto_url && (
          <img
            src={mediaUrl(reporte.foto_url)}
            alt={`Foto del reporte de ${titulo}`}
            loading="lazy"
            className="absolute inset-0 h-full w-full object-contain"
          />
        )}
        <div className="relative flex items-start p-3">
          {/* Un reencuentro se celebra por encima del tipo (feature 27). */}
          {reporte.estado === 'reunido' ? (
            <span className="rounded-md bg-forest px-3 py-1 font-mono text-xs tracking-wide text-bg">
              Reunida 💚
            </span>
          ) : (
            <span
              className={`rounded-md px-3 py-1 font-mono text-xs tracking-wide text-bg ${tipo.color}`}
            >
              {tipo.texto}
            </span>
          )}
        </div>
      </div>

      <div className="border-t border-line p-4">
        <h3 className="font-display text-xl text-ink">{titulo}</h3>
        <p className="mt-1 line-clamp-2 text-sm text-muted">{reporte.descripcion}</p>
        <div className="mt-2 flex flex-wrap gap-1.5">
          <span className="rounded-full bg-forest-tint px-2.5 py-1 text-xs text-forest">
            {ETIQUETA_ESPECIE[reporte.especie]}
          </span>
          {reporte.raza && (
            <span className="rounded-full bg-surface-alt px-2.5 py-1 text-xs text-ink-soft">
              {reporte.raza}
            </span>
          )}
          {reporte.color && (
            <span className="rounded-full bg-surface-alt px-2.5 py-1 text-xs text-ink-soft">
              {reporte.color}
            </span>
          )}
          {reporte.tamano && (
            <span className="rounded-full bg-surface-alt px-2.5 py-1 text-xs text-ink-soft">
              {reporte.tamano.charAt(0).toUpperCase() + reporte.tamano.slice(1)}
            </span>
          )}
          {reporte.situacion === 'conmigo' && (
            <span className="rounded-full bg-forest-tint px-2.5 py-1 text-xs text-forest">
              Resguardada
            </span>
          )}
          {reporte.situacion === 'vista' && (
            <span className="rounded-full bg-surface-alt px-2.5 py-1 text-xs text-muted">
              Vista, sin atrapar
            </span>
          )}
        </div>
        <div className="mt-3 flex items-center justify-between border-t border-line-soft pt-3 text-xs text-muted">
          <span>{lugar}</span>
          <span>
            {formatearFecha(reporte.fecha_evento)} · {tiempoRelativo(reporte.creado_en)}
          </span>
        </div>
      </div>
    </Link>
  );
}
