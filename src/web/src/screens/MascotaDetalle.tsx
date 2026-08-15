import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { ApiError, obtenerMascota } from '../api/client';
import type { Mascota } from '../api/types';
import { AvisoSeguridad } from '../components/AvisoSeguridad';
import { GaleriaFotos } from '../components/GaleriaFotos';
import {
  ETIQUETA_CATEGORIA_EDAD,
  ETIQUETA_ENERGIA,
  ETIQUETA_ESPECIE_ADOPCION,
  ETIQUETA_ESTADO_MASCOTA,
  ETIQUETA_SEXO,
  ETIQUETA_TAMANO_MASCOTA,
  categoriaEdad,
  edadLegible,
  tituloMascota,
} from '../lib/adopcion';
import { mensajeAdoptarMascota, urlWhatsApp } from '../lib/contacto';
import { tiempoRelativo } from '../lib/tiempo';

// Ficha pública de una mascota en adopción (AD-01, acceptance A3).
//
// ⚠️ Pantalla de SOLO LECTURA, igual que el catálogo: no llama a
// `getActiveUserId()` porque esa función cae al usuario demo (id 1) cuando no hay
// cuenta, y aquí nada escribe. Favoritos y "me interesa" llegan con su propio gate
// en AD-03/AD-07; la versión de la era Adopta de esta pantalla sí los tenía y por
// eso no se portó tal cual.
//
// Paleta: el rojo de emergencia está reservado en toda la app a "perdido" y no
// entra en este módulo — ni siquiera en el error, que se pinta con el borde
// neutro de las tarjetas. Aquí solo hay `forest` y `ochre` (la regla, con el
// nombre del token, está en `ETIQUETA_ESTADO_MASCOTA` de lib/adopcion.ts).
//
// El estado de error es explícito a propósito: la pantalla hermana
// (`ReporteDetalle`) hace `obtenerReporte(...).then(setReporte)` sin `.catch`, así
// que un id inexistente se queda en el esqueleto para siempre. Aquí un 404 muestra
// el mensaje del backend y la salida al catálogo.

const MENSAJE_ERROR_RED = 'No pudimos cargar esta mascota. Revisa tu conexión e intenta de nuevo.';

export function MascotaDetalle() {
  const { id } = useParams<{ id: string }>();
  const [mascota, setMascota] = useState<Mascota | null>(null);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (!id) return;
    setError(null);
    obtenerMascota(Number(id))
      .then(setMascota)
      // El backend ya responde en español ("La mascota 7 no existe"): ese texto es
      // copy de producto, no un detalle técnico, así que se muestra tal cual.
      .catch((err) => setError(err instanceof ApiError ? err.message : MENSAJE_ERROR_RED));
  }, [id]);

  if (error) {
    return (
      <div className="mx-auto max-w-2xl space-y-4 p-6 text-center">
        <h1 className="font-display text-2xl text-ink">No pudimos mostrar esta mascota</h1>
        <p
          role="alert"
          className="rounded-2xl border border-line bg-surface p-4 text-sm text-ink-soft"
        >
          {error}
        </p>
        <Link
          to="/adoptar"
          className="inline-block rounded-full bg-forest px-5 py-2 font-medium text-bg"
        >
          Ver las mascotas en adopción
        </Link>
      </div>
    );
  }

  if (!mascota) {
    return (
      <div
        role="status"
        aria-label="Cargando la ficha de la mascota"
        className="mx-auto mt-8 h-96 max-w-2xl animate-pulse rounded-2xl bg-surface-alt"
      />
    );
  }

  const titulo = tituloMascota(mascota);
  const estado = ETIQUETA_ESTADO_MASCOTA[mascota.estado];
  const lugar = mascota.zona === 'Otro' ? mascota.ciudad_texto ?? 'Colombia' : mascota.zona;
  const publicador = mascota.publicador;
  // El teléfono sale siempre del publicador: el router ya resolvió lo asimétrico
  // (el rescatista lo trae en la mascota, la organización tiene el suyo).
  const telefono = publicador?.telefono_contacto ?? null;

  // Ficha en chips, como las señas de `ReporteDetalle`: a 360px una tabla de
  // etiqueta-valor obliga a hacer scroll y aquí cada dato se lee solo.
  const datos = [
    ETIQUETA_ESPECIE_ADOPCION[mascota.especie],
    mascota.raza,
    ETIQUETA_SEXO[mascota.sexo],
    edadLegible(mascota.edad_meses),
    ETIQUETA_CATEGORIA_EDAD[categoriaEdad(mascota.edad_meses)],
    ETIQUETA_TAMANO_MASCOTA[mascota.tamano],
    ETIQUETA_ENERGIA[mascota.energia],
  ].filter((dato): dato is string => Boolean(dato));

  // Aptitudes: un "no" nunca se dice como carencia de la mascota, sino como el
  // hogar que le queda mejor. Es la misma regla de tono del resto de la app.
  const aptitudes = [
    mascota.apto_ninos
      ? { ok: true, texto: 'Le va bien con niños' }
      : { ok: false, texto: 'Mejor en un hogar sin niños' },
    mascota.apto_perros
      ? { ok: true, texto: 'Convive con otros perros' }
      : { ok: false, texto: 'Prefiere ser la única mascota perruna' },
    mascota.apto_gatos
      ? { ok: true, texto: 'Convive con gatos' }
      : { ok: false, texto: 'Mejor en un hogar sin gatos' },
  ];

  // Los cuatro flags del acceptance A3, en ese orden.
  const salud = [
    { texto: 'Esterilización', ok: mascota.esterilizado },
    { texto: 'Vacunas al día', ok: mascota.vacunas_al_dia },
    { texto: 'Microchip', ok: mascota.microchip },
    { texto: 'Desparasitación', ok: mascota.desparasitado },
  ];

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-6 pb-24">
      <button type="button" onClick={() => navigate(-1)} className="text-sm text-muted">
        ← Volver
      </button>

      <GaleriaFotos fotos={mascota.fotos} alt={`Foto de ${titulo}, en adopción`} />

      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl text-ink">{titulo}</h1>
          <p className="mt-1 text-sm text-muted">
            {lugar}
            {mascota.barrio ? ` · ${mascota.barrio}` : ''} · Publicada{' '}
            {tiempoRelativo(mascota.publicado_en)}
          </p>
        </div>
        <span
          className={`rounded-md px-3 py-1 font-mono text-xs tracking-wide text-bg ${estado.color}`}
        >
          {estado.texto}
        </span>
      </header>

      {mascota.estado === 'adoptado' && (
        <p className="rounded-2xl border border-forest-tint-line bg-forest-tint p-4 text-sm text-forest">
          {titulo} ya encontró familia. 💚
        </p>
      )}

      <section className="rounded-2xl border border-line bg-surface p-6">
        <h2 className="mb-3 font-display text-lg text-ink">Sus datos</h2>
        <div className="flex flex-wrap gap-1.5">
          {datos.map((dato) => (
            <span
              key={dato}
              className="rounded-full bg-surface-alt px-2.5 py-1 text-xs text-ink-soft"
            >
              {dato}
            </span>
          ))}
        </div>
        {mascota.tags.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {mascota.tags.map((tag) => (
              <span
                key={tag}
                className="rounded-full bg-forest-tint px-2.5 py-1 text-xs text-forest"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
      </section>

      <section className="rounded-2xl border border-line bg-surface p-6">
        <h2 className="mb-2 font-display text-lg text-ink">Su historia</h2>
        <p className="whitespace-pre-line text-ink-soft">{mascota.historia}</p>
      </section>

      <section className="rounded-2xl border border-line bg-surface p-6">
        <h2 className="mb-3 font-display text-lg text-ink">Con quién convive bien</h2>
        <div className="flex flex-wrap gap-1.5">
          {aptitudes.map((aptitud) => (
            <span
              key={aptitud.texto}
              className={`rounded-full px-2.5 py-1 text-xs ${
                aptitud.ok
                  ? 'bg-forest-tint text-forest'
                  : 'border border-ochre/40 bg-ochre/10 text-ink-soft'
              }`}
            >
              {aptitud.texto}
            </span>
          ))}
        </div>
      </section>

      <section className="rounded-2xl border border-line bg-surface p-6">
        <h2 className="mb-3 font-display text-lg text-ink">Salud y cuidados</h2>
        <ul className="grid grid-cols-1 gap-2 text-sm sm:grid-cols-2">
          {salud.map((item) => (
            <li key={item.texto} className={item.ok ? 'text-ink-soft' : 'text-muted'}>
              {item.ok ? '✓' : '—'} {item.texto}
            </li>
          ))}
        </ul>
        <p className="mt-3 text-xs text-muted">
          El — quiere decir que quien la publica no lo confirmó todavía: pregúntale al escribirle.
        </p>
      </section>

      {publicador && (
        <section className="rounded-2xl border border-line bg-surface p-6">
          <h2 className="mb-2 font-display text-lg text-ink">Quién la publica</h2>
          {/* Solo la organización tiene perfil propio. El `id` de un rescatista es
              de la tabla `users`: enlazarlo a /organizacion/{id} llevaría a una
              entidad distinta (o a un 404), así que su nombre va sin link. */}
          {publicador.tipo === 'organizacion' ? (
            <Link
              to={`/organizacion/${publicador.id}`}
              className="font-medium text-forest underline-offset-4 hover:underline"
            >
              {publicador.nombre}
            </Link>
          ) : (
            <p className="font-medium text-ink">{publicador.nombre}</p>
          )}
          <p className="mt-1 text-sm text-muted">
            {publicador.tipo === 'organizacion'
              ? 'Organización de la red de apoyo'
              : 'Rescatista de la comunidad'}
            {publicador.zona ? ` · ${publicador.zona}` : ''}
          </p>
        </section>
      )}

      {/* Una mascota adoptada ya no se contacta: la ficha queda como memoria del
          final feliz (mismo criterio que un reporte reunido). */}
      {mascota.estado !== 'adoptado' && (
        <section className="rounded-2xl border border-line bg-surface p-6">
          <h2 className="mb-2 font-display text-lg text-ink">¿Quieres darle un hogar?</h2>
          {telefono ? (
            <div className="flex flex-col gap-3">
              <p className="text-sm text-ink-soft">
                Escríbele a {publicador?.nombre ?? 'quien la publica'} para conocerla y preguntar
                por el proceso de adopción.
              </p>
              <a
                href={urlWhatsApp(telefono, mensajeAdoptarMascota(titulo))}
                target="_blank"
                rel="noreferrer"
                className="inline-block self-start rounded-full bg-forest px-5 py-3 font-medium text-bg"
              >
                Escribir por WhatsApp
              </a>
              <AvisoSeguridad contexto="contactar" />
            </div>
          ) : (
            // Sin teléfono no se pinta un botón que no lleva a ninguna parte.
            <p className="text-sm text-ink-soft">
              Quien publicó a {titulo} no dejó un teléfono de contacto todavía.
            </p>
          )}
        </section>
      )}
    </div>
  );
}
