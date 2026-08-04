import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { listarRefugiosMapa, mediaUrl, obtenerPerfil } from '../api/client';
import type { ShelterMap } from '../api/types';
import { posicionEnMapa } from '../lib/mapa';
import { getActiveUserId } from '../lib/session';

export function Mapa() {
  const [shelters, setShelters] = useState<ShelterMap[] | null>(null);
  const [miPosicion, setMiPosicion] = useState<{ lat: number; lng: number } | null | undefined>(
    undefined,
  );
  const [seleccionado, setSeleccionado] = useState<ShelterMap | null>(null);

  useEffect(() => {
    const userId = getActiveUserId();
    listarRefugiosMapa(userId).then(setShelters);
    obtenerPerfil(userId).then((perfil) => {
      setMiPosicion(
        perfil.lat !== null && perfil.lng !== null ? { lat: perfil.lat, lng: perfil.lng } : null,
      );
    });
  }, []);

  const cargando = shelters === null || miPosicion === undefined;

  if (cargando) {
    return (
      <div className="mx-auto max-w-4xl p-6">
        <div className="aspect-4/3 w-full animate-pulse rounded-2xl bg-surface-alt" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      <div>
        <h1 className="mb-2 font-display text-2xl text-ink">Mapa de refugios</h1>
        <p className="text-sm text-muted">
          Ubicación aproximada de los refugios aliados y las mascotas que tienen disponibles.
        </p>
      </div>

      <div className="relative aspect-4/3 w-full rounded-2xl border border-line bg-surface-alt">
        {shelters.map((shelter) => {
          if (shelter.lat === null || shelter.lng === null) return null;
          const { left, top } = posicionEnMapa(shelter.lat, shelter.lng);
          return (
            <button
              key={shelter.id}
              type="button"
              data-testid={`pin-refugio-${shelter.id}`}
              title={shelter.nombre}
              onClick={() => setSeleccionado(shelter)}
              className="absolute flex h-3.5 w-3.5 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full bg-forest"
              style={{ left, top }}
            >
              {shelter.verificado && (
                <span className="h-1.5 w-1.5 rounded-full bg-bg" aria-hidden="true" />
              )}
            </button>
          );
        })}

        {miPosicion && (
          <div
            title="Tú estás aquí"
            className="absolute h-3 w-3 -translate-x-1/2 -translate-y-1/2 rotate-45 bg-ochre"
            style={posicionEnMapa(miPosicion.lat, miPosicion.lng)}
          />
        )}
      </div>

      {seleccionado === null ? (
        <p className="text-sm text-muted">
          Selecciona un refugio en el mapa para ver sus mascotas.
        </p>
      ) : (
        <div className="rounded-2xl border border-line bg-surface p-4">
          <div className="flex items-center gap-2">
            <p className="font-display text-lg text-ink">{seleccionado.nombre}</p>
            {seleccionado.verificado && (
              <span className="rounded-full bg-forest-tint px-2 py-0.5 font-mono text-[10px] tracking-wide text-forest uppercase">
                Verificado
              </span>
            )}
            {seleccionado.distancia_km !== null && (
              <span className="font-mono text-[11px] text-muted-2">
                {seleccionado.distancia_km.toFixed(1)} km
              </span>
            )}
          </div>

          {seleccionado.mascotas.length === 0 ? (
            <p className="mt-3 text-sm text-muted">Sin mascotas disponibles ahora mismo.</p>
          ) : (
            <div className="mt-3 space-y-2">
              {seleccionado.mascotas.map((pet) => (
                <Link
                  key={pet.id}
                  to={`/mascota/${pet.id}`}
                  className="flex items-center gap-3 rounded-xl border border-line bg-surface-alt p-2"
                >
                  {pet.fotos[0] && (
                    <img
                      src={mediaUrl(pet.fotos[0])}
                      alt={`Foto de ${pet.nombre}`}
                      className="h-12 w-12 shrink-0 rounded-lg object-cover"
                    />
                  )}
                  <p className="text-sm font-medium text-ink">{pet.nombre}</p>
                </Link>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
