import { useEffect, useState } from 'react';
import { ApiError, crearApadrinamiento, listarNecesitanApoyo, mediaUrl } from '../api/client';
import type { MascotaNecesitaApoyo } from '../api/types';
import { getActiveUserId } from '../lib/session';

// Mismo patrón visual de chips de opción única que src/web/src/screens/PublicarMascota.tsx
// (feature 03/06), reutilizado aquí sin extraer un componente compartido.

type NivelDonacion = 30000 | 70000 | 'libre';

const NIVELES: { valor: NivelDonacion; titulo: string; detalle: string }[] = [
  { valor: 30000, titulo: '$30.000', detalle: 'Alimento' },
  { valor: 70000, titulo: '$70.000', detalle: 'Alimento + veterinario' },
  { valor: 'libre', titulo: 'Monto libre', detalle: 'Tú eliges cuánto' },
];

const PERIODICIDAD_OPCIONES: { valor: 'mensual' | 'unico'; etiqueta: string }[] = [
  { valor: 'mensual', etiqueta: 'Mensual' },
  { valor: 'unico', etiqueta: 'Pago único' },
];

function formatoCop(valor: number): string {
  return `$${valor.toLocaleString('es-CO')}`;
}

function extractoHistoria(historia: string): string {
  const limite = 140;
  return historia.length > limite ? `${historia.slice(0, limite).trim()}…` : historia;
}

interface NivelCardProps {
  titulo: string;
  detalle: string;
  seleccionada: boolean;
  destacada: boolean;
  onClick: () => void;
}

function NivelCard({ titulo, detalle, seleccionada, destacada, onClick }: NivelCardProps) {
  const clases = seleccionada
    ? 'border-forest bg-forest-tint text-ink'
    : destacada
      ? 'border-ochre bg-surface text-ink hover:border-forest-tint-line'
      : 'border-line bg-surface text-ink-soft hover:border-forest-tint-line';

  return (
    <button
      type="button"
      aria-pressed={seleccionada}
      onClick={onClick}
      className={`relative min-h-[88px] rounded-2xl border p-4 text-left transition ${clases}`}
    >
      {destacada && (
        <span className="absolute -top-2 right-3 rounded-full bg-ochre px-2 py-0.5 font-mono text-[10px] tracking-wide text-bg uppercase">
          Recomendado
        </span>
      )}
      <p className="font-display text-lg">{titulo}</p>
      <p className="text-xs text-muted">{detalle}</p>
    </button>
  );
}

export function Apadrinar() {
  const [nivel, setNivel] = useState<NivelDonacion>(30000);
  const [montoLibre, setMontoLibre] = useState('');
  const [periodicidad, setPeriodicidad] = useState<'mensual' | 'unico'>('mensual');
  const [mascotas, setMascotas] = useState<MascotaNecesitaApoyo[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [enviandoId, setEnviandoId] = useState<number | null>(null);
  const [mensajeExitoId, setMensajeExitoId] = useState<number | null>(null);

  useEffect(() => {
    listarNecesitanApoyo().then(setMascotas);
  }, []);

  const montoLibreNumero = Number(montoLibre);
  const montoValido = nivel !== 'libre' || (montoLibre.trim().length > 0 && montoLibreNumero > 0);
  const montoActual = nivel === 'libre' ? montoLibreNumero : nivel;

  async function handleApadrinar(mascota: MascotaNecesitaApoyo) {
    setError(null);
    setMensajeExitoId(null);
    setEnviandoId(mascota.id);
    try {
      await crearApadrinamiento({
        user_id: getActiveUserId(),
        pet_id: mascota.id,
        monto_cop: montoActual,
        periodicidad,
      });
      setMensajeExitoId(mascota.id);
      const actualizadas = await listarNecesitanApoyo();
      setMascotas(actualizadas);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : 'No pudimos registrar el apadrinamiento. Intenta de nuevo.',
      );
    } finally {
      setEnviandoId(null);
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-6">
      <div>
        <h1 className="mb-2 font-display text-2xl text-ink">Apadrinar</h1>
        <p className="text-sm text-muted">
          Tu aporte ayuda a mascotas que llevan más tiempo esperando un hogar. Es un compromiso de
          apoyo, no reemplaza el proceso de adopción.
        </p>
      </div>

      <section>
        <h2 className="mb-3 font-display text-lg text-ink">Elige un monto</h2>
        <div className="grid grid-cols-3 gap-3">
          {NIVELES.map((opcion) => (
            <NivelCard
              key={opcion.valor}
              titulo={opcion.titulo}
              detalle={opcion.detalle}
              seleccionada={nivel === opcion.valor}
              destacada={opcion.valor === 70000}
              onClick={() => setNivel(opcion.valor)}
            />
          ))}
        </div>
        {nivel === 'libre' && (
          <div className="mt-3">
            <label htmlFor="monto-libre" className="text-sm font-medium text-ink-soft">
              ¿Cuánto quieres aportar? (COP)
            </label>
            <input
              id="monto-libre"
              type="number"
              min={1}
              value={montoLibre}
              onChange={(e) => setMontoLibre(e.target.value)}
              placeholder="Ej. 50000"
              className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
            />
          </div>
        )}
      </section>

      <section>
        <h2 className="mb-3 font-display text-lg text-ink">Periodicidad</h2>
        <div className="grid grid-cols-2 gap-3">
          {PERIODICIDAD_OPCIONES.map((opcion) => (
            <button
              key={opcion.valor}
              type="button"
              aria-pressed={periodicidad === opcion.valor}
              onClick={() => setPeriodicidad(opcion.valor)}
              className={`min-h-[48px] rounded-2xl border px-4 py-3 text-left font-medium transition ${
                periodicidad === opcion.valor
                  ? 'border-forest bg-forest-tint text-ink'
                  : 'border-line bg-surface text-ink-soft hover:border-forest-tint-line'
              }`}
            >
              {opcion.etiqueta}
            </button>
          ))}
        </div>
      </section>

      {error && <p className="text-sm text-danger">{error}</p>}

      <section>
        <h2 className="mb-3 font-display text-lg text-ink">Necesitan apoyo ahora</h2>
        {mascotas === null ? (
          <div className="space-y-3">
            {[0, 1, 2].map((i) => (
              <div key={i} className="h-32 animate-pulse rounded-2xl bg-surface-alt" />
            ))}
          </div>
        ) : mascotas.length === 0 ? (
          <p className="text-sm text-muted">
            Por ahora ninguna mascota necesita apoyo adicional. Vuelve pronto.
          </p>
        ) : (
          <div className="space-y-4">
            {mascotas.map((mascota) => (
              <div
                key={mascota.id}
                className="flex gap-4 rounded-2xl border border-line bg-surface p-4"
              >
                {mascota.fotos[0] && (
                  <img
                    src={mediaUrl(mascota.fotos[0])}
                    alt={`Foto de ${mascota.nombre}`}
                    className="h-20 w-20 shrink-0 rounded-xl object-cover"
                  />
                )}
                <div className="flex-1">
                  <p className="font-display text-lg text-ink">{mascota.nombre}</p>
                  <p className="mt-1 text-sm text-ink-soft">{extractoHistoria(mascota.historia)}</p>
                  <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-surface-alt">
                    <div
                      className="h-full rounded-full bg-forest transition-all"
                      style={{ width: `${mascota.porcentaje_cubierto}%` }}
                    />
                  </div>
                  <div className="mt-1 flex items-center justify-between">
                    <p className="text-xs text-muted">
                      {mascota.porcentaje_cubierto}% cubierto ·{' '}
                      {formatoCop(mascota.monto_recaudado_cop)} recaudados
                    </p>
                  </div>
                  {mensajeExitoId === mascota.id && (
                    <p className="mt-2 text-sm text-forest">
                      ¡Gracias por apadrinar a {mascota.nombre}!
                    </p>
                  )}
                  <button
                    type="button"
                    disabled={!montoValido || enviandoId === mascota.id}
                    onClick={() => handleApadrinar(mascota)}
                    className="mt-3 rounded-full bg-forest px-4 py-2 text-sm font-medium text-bg disabled:opacity-60"
                  >
                    {enviandoId === mascota.id ? 'Apadrinando…' : 'Apadrinar'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
