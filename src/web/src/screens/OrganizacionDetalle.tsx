import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { ApiError, listarNecesidades, mediaUrl, obtenerOrganizacion } from '../api/client';
import type { Necesidad, Organizacion } from '../api/types';
import { MapaLienzo } from '../components/MapaLienzo';
import { mensajeAyudaOrganizacion, urlTelefono, urlWhatsApp } from '../lib/contacto';
import { ETIQUETA_TIPO_ORGANIZACION } from '../lib/organizaciones';
import { esUsuarioActivo } from '../lib/session';
import { AdministrarOrganizacion } from '../components/AdministrarOrganizacion';
import { AvisoSeguridad } from '../components/AvisoSeguridad';
import { PanelAdopcionOrganizacion } from '../components/PanelAdopcionOrganizacion';
import { SeccionNecesidades } from '../components/SeccionNecesidades';

// Fix 2026-08-15: la carga iba sin `.catch` (mismo bug que en `ReporteDetalle`),
// así que una organización inexistente o eliminada dejaba el esqueleto para siempre.
const MENSAJE_ERROR_CARGA = 'No pudimos cargar este lugar. Revisa tu conexión e intenta de nuevo.';

export function OrganizacionDetalle() {
  const { id } = useParams<{ id: string }>();
  const [organizacion, setOrganizacion] = useState<Organizacion | null>(null);
  const [necesidades, setNecesidades] = useState<Necesidad[]>([]);
  const [errorCarga, setErrorCarga] = useState<string | null>(null);
  // Pestañas (AD-02): `?tab=adopcion` abre directo el panel de mascotas, que es
  // adonde vuelve quien acaba de publicar una desde este lugar. Patrón de `RedDeApoyo`.
  const [busqueda] = useSearchParams();
  const [pestana, setPestana] = useState<'lugar' | 'adopcion'>(
    busqueda.get('tab') === 'adopcion' ? 'adopcion' : 'lugar',
  );
  const navigate = useNavigate();

  useEffect(() => {
    if (!id) return;
    setErrorCarga(null);
    obtenerOrganizacion(Number(id))
      .then(setOrganizacion)
      // El backend responde en español ("La organización 7 no existe"): copy de
      // producto, se muestra tal cual.
      .catch((err) => setErrorCarga(err instanceof ApiError ? err.message : MENSAJE_ERROR_CARGA));
    // Las necesidades son una sección complementaria: si fallan (con un id
    // inexistente el backend responde 404 también aquí) la pantalla sigue en pie,
    // pero la promesa hay que atenderla o queda un rechazo sin manejar en consola.
    listarNecesidades(Number(id))
      .then(setNecesidades)
      .catch(() => setNecesidades([]));
  }, [id]);

  if (errorCarga) {
    return (
      <div className="mx-auto max-w-2xl space-y-4 p-6 text-center">
        <h1 className="font-display text-2xl text-ink">No pudimos mostrar este lugar</h1>
        <p
          role="alert"
          className="rounded-2xl border border-line bg-surface p-4 text-sm text-ink-soft"
        >
          {errorCarga}
        </p>
        <Link
          to="/ayudar"
          className="inline-block rounded-full bg-forest px-5 py-2 font-medium text-bg"
        >
          Ver los centros de ayuda
        </Link>
      </div>
    );
  }

  if (!organizacion) {
    return (
      <div
        role="status"
        aria-label="Cargando la información del lugar"
        className="mx-auto mt-8 h-96 max-w-2xl animate-pulse rounded-2xl bg-surface-alt"
      />
    );
  }

  const etiqueta = ETIQUETA_TIPO_ORGANIZACION[organizacion.tipo];
  const lugar =
    organizacion.zona === 'Otro' ? organizacion.ciudad_texto ?? 'Colombia' : organizacion.zona;
  const esAutor = esUsuarioActivo(organizacion.user_id);

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-6 pb-24">
      <button type="button" onClick={() => navigate(-1)} className="text-sm text-muted">
        ← Volver
      </button>

      {organizacion.foto_url && (
        <img
          src={mediaUrl(organizacion.foto_url)}
          alt={`Foto de ${organizacion.nombre}`}
          className="max-h-[50vh] w-full rounded-[22px] border border-line bg-surface-alt object-contain"
        />
      )}

      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl text-ink">{organizacion.nombre}</h1>
          <p className="mt-1 text-sm text-muted">
            {lugar}
            {organizacion.barrio ? ` · ${organizacion.barrio}` : ''} · {organizacion.direccion}
          </p>
        </div>
        <span
          className={`rounded-md px-3 py-1 font-mono text-xs tracking-wide text-bg ${etiqueta.color}`}
        >
          {etiqueta.texto}
        </span>
      </header>

      {organizacion.estado === 'cerrado' && (
        <p className="rounded-2xl border border-line bg-surface-alt p-4 text-sm text-muted">
          Este lugar está marcado como cerrado.
        </p>
      )}

      <div className="flex gap-2 border-b border-line">
        {(
          [
            ['lugar', 'El lugar'],
            ['adopcion', 'En adopción'],
          ] as const
        ).map(([clave, texto]) => (
          <button
            key={clave}
            type="button"
            onClick={() => setPestana(clave)}
            className={`-mb-px border-b-2 px-4 py-2 font-medium ${
              pestana === clave ? 'border-forest text-forest' : 'border-transparent text-muted'
            }`}
          >
            {texto}
          </button>
        ))}
      </div>

      {pestana === 'adopcion' && (
        <PanelAdopcionOrganizacion
          organizacionId={organizacion.id}
          nombreOrganizacion={organizacion.nombre}
          telefonoContacto={organizacion.telefono_contacto}
          zona={lugar}
          esAutor={esAutor}
        />
      )}

      {pestana === 'lugar' && (
        <>
          <section className="rounded-2xl border border-line bg-surface p-6">
            <h2 className="mb-2 font-display text-lg text-ink">Qué hacen</h2>
            <p className="text-ink-soft">{organizacion.descripcion}</p>
            {organizacion.horario && (
              <p className="mt-3 text-sm text-muted">Horario: {organizacion.horario}</p>
            )}
          </section>

          <section className="rounded-2xl border border-line bg-surface p-6">
            <h2 className="mb-2 font-display text-lg text-ink">Dónde están</h2>
            <MapaLienzo
              zona={organizacion.zona}
              pines={[
                {
                  id: organizacion.id,
                  lat: organizacion.lat,
                  lng: organizacion.lng,
                  colorClass: etiqueta.color,
                  etiqueta: `Ubicación de ${organizacion.nombre}`,
                },
              ]}
            />
          </section>

          {organizacion.como_donar && (
            <section className="rounded-2xl border border-forest-tint-line bg-forest-tint p-6">
              <h2 className="mb-2 font-display text-lg text-ink">Cómo donar</h2>
              <p className="text-ink-soft">{organizacion.como_donar}</p>
            </section>
          )}

          <SeccionNecesidades
            organizacion={organizacion}
            necesidades={necesidades}
            onNecesidades={setNecesidades}
            esAutor={esAutor}
          />

          {organizacion.estado === 'activo' && (
            <section className="rounded-2xl border border-line bg-surface p-6">
              <h2 className="mb-2 font-display text-lg text-ink">Contacto</h2>
              <div className="flex flex-wrap gap-3">
                <a
                  href={urlWhatsApp(
                    organizacion.telefono_contacto,
                    mensajeAyudaOrganizacion(organizacion.nombre),
                  )}
                  target="_blank"
                  rel="noreferrer"
                  className="rounded-full bg-forest px-5 py-3 font-medium text-bg"
                >
                  Escribir por WhatsApp
                </a>
                <a
                  href={urlTelefono(organizacion.telefono_contacto)}
                  className="rounded-full border border-line px-5 py-3 font-medium text-ink"
                >
                  Llamar
                </a>
              </div>
              <AvisoSeguridad contexto="contactar" />
            </section>
          )}

          <AdministrarOrganizacion
            organizacion={organizacion}
            esAutor={esAutor}
            onActualizada={setOrganizacion}
          />
        </>
      )}
    </div>
  );
}
