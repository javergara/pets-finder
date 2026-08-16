import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import {
  ApiError,
  desmarcarFavorita,
  eliminarMascota,
  marcarFavorita,
  obtenerMascota,
} from '../api/client';
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
import { getActiveUserId, hasActiveUser } from '../lib/session';
import { tiempoRelativo } from '../lib/tiempo';

// Ficha pública de una mascota en adopción (AD-01, acceptance A3).
//
// ⚠️ Casi todo lo que hace es leer. Lo que escribe —las acciones de quien la
// publicó (AD-02, paso 9) y el corazón de favoritos (AD-07, paso 7)— va SIEMPRE
// detrás de `hasActiveUser()`: `getActiveUserId()` cae al usuario demo (id 1) sin
// cuenta, así que sin ese guard un visitante vería "editar" y "despublicar" sobre
// las mascotas del usuario 1 —que en producción es una persona real— y guardaría
// mascotas en SU lista privada. Por lo mismo `adoptante_id` solo viaja con
// cuenta: es lo que llena `es_favorito`, y mandarlo inventado pintaría el corazón
// de otra persona como si fuera el propio.
//
// El corazón se pinta igual sin cuenta y lleva a `/registro?volver=` con la ruta
// de ESTA ficha (el mismo gate que "Me interesa" del deck): esconderlo ocultaría
// que los favoritos existen, y el `?volver=` con el id es lo que devuelve a la
// mascota que se estaba mirando en vez de al catálogo. Se pinta también sobre una
// mascota ya adoptada —a diferencia del contacto, que ahí desaparece—: la lista
// guardada no excluye adoptadas (guardaste esa mascota, tienes derecho a ver cómo
// terminó) y esta ficha es el único sitio donde quitarla desde su propia página.
//
// Esas acciones solo aparecen si publica un RESCATISTA y es quien está mirando.
// Para las mascotas de una organización no se pintan aunque las mire su autor:
// el publicador trae el id del LUGAR, no el de la persona que lo registró, así
// que compararlo con el usuario activo sería adivinar (y enseñarle los botones a
// quien tenga ese mismo número en `users`). El lugar las gestiona desde su panel.
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
const MENSAJE_ERROR_DESPUBLICAR = 'No pudimos despublicar la mascota. Intenta de nuevo.';

export function MascotaDetalle() {
  const { id } = useParams<{ id: string }>();
  const [mascota, setMascota] = useState<Mascota | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [confirmandoDespublicar, setConfirmandoDespublicar] = useState(false);
  const [despublicando, setDespublicando] = useState(false);
  const [errorDespublicar, setErrorDespublicar] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (!id) return;
    setError(null);
    // El adoptante solo viaja si existe de verdad (ver la cabecera): es lo que
    // hace que `es_favorito` llegue lleno y el corazón se pinte como está.
    obtenerMascota(Number(id), hasActiveUser() ? getActiveUserId() : undefined)
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
  // Ver la cabecera: `hasActiveUser()` primero, y solo rescatistas. El backend
  // vuelve a verificar la autoría con un 403; esto es la mitad de UI del trato.
  const esDueno =
    hasActiveUser() && publicador?.tipo === 'rescatista' && publicador.id === getActiveUserId();

  async function despublicar() {
    if (!mascota) return;
    setErrorDespublicar(null);
    setDespublicando(true);
    try {
      await eliminarMascota(mascota.id, getActiveUserId());
      navigate('/adoptar');
    } catch (err) {
      // El backend responde en español ("Solo quien publicó la mascota puede
      // despublicarla"): copy de producto, se muestra tal cual.
      setErrorDespublicar(err instanceof ApiError ? err.message : MENSAJE_ERROR_DESPUBLICAR);
      setDespublicando(false);
    }
  }

  /** Guarda o quita la mascota de la lista, en optimista. */
  function alternarFavorita() {
    if (!mascota) return;
    // La cuenta se pide ANTES de tocar nada, como en el catálogo y el deck: sin
    // ella, `getActiveUserId()` escribiría en la lista del usuario 1.
    if (!hasActiveUser()) {
      navigate(`/registro?volver=${encodeURIComponent(`/adoptar/mascota/${mascota.id}`)}`);
      return;
    }

    const adoptanteId = getActiveUserId();
    const guardada = mascota.es_favorito;
    // El corazón cambia ya y la ficha NO se vuelve a pedir: recargarla entera
    // por un corazón haría parpadear la foto y perdería la miniatura elegida.
    setMascota((previa) => (previa ? { ...previa, es_favorito: !guardada } : previa));

    const peticion = guardada
      ? desmarcarFavorita(adoptanteId, mascota.id)
      : marcarFavorita(adoptanteId, mascota.id);
    peticion.catch(() => {
      // Vacío A PROPÓSITO, no por descuido (`docs/conventions.md` §3, mismo
      // criterio que el catálogo y el deck): un favorito no bloquea la ficha ni
      // merece un error rojo encima de la mascota. Tampoco se revierte el
      // corazón: lo que se pierde es una fila de una lista privada, y volver a
      // tocarlo lo reintenta.
    });
  }

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
        <div className="flex flex-col items-end gap-2">
          <span
            className={`rounded-md px-3 py-1 font-mono text-xs tracking-wide text-bg ${estado.color}`}
          >
            {estado.texto}
          </span>
          {/* Con texto y no solo el símbolo, al revés que en las tarjetas: aquí
              hay sitio de sobra y esta es la pantalla donde alguien decide con
              calma. El corazón va `aria-hidden` para que el nombre accesible del
              botón sea exactamente el mismo de las otras dos pantallas
              ("Guardar en favoritos" / "Quitar de favoritos") y no "♡ Guardar…". */}
          <button
            type="button"
            onClick={alternarFavorita}
            className={`flex items-center gap-1.5 rounded-full border px-4 py-2 text-sm font-medium ${
              mascota.es_favorito
                ? 'border-forest-tint-line bg-forest-tint text-forest'
                : 'border-line bg-surface text-ink-soft'
            }`}
          >
            <span aria-hidden className="text-lg leading-none">
              {mascota.es_favorito ? '♥' : '♡'}
            </span>
            {mascota.es_favorito ? 'Quitar de favoritos' : 'Guardar en favoritos'}
          </button>
        </div>
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

      {esDueno && (
        <section className="rounded-2xl border border-line bg-surface p-6">
          <h2 className="mb-2 font-display text-lg text-ink">Publicaste a {titulo}</h2>
          <p className="mb-4 text-sm text-muted">
            Corrige lo que haga falta, o despublícala cuando ya no la estés dando en adopción.
          </p>
          <div className="flex flex-wrap items-center gap-3">
            <Link
              to={`/adoptar/mascota/${mascota.id}/editar`}
              className="rounded-full border border-line px-5 py-2 font-medium text-ink-soft"
            >
              Editar la ficha
            </Link>
            {/* Confirmación en dos pasos DENTRO de la página (patrón de
                `ReporteDetalle`): un `window.confirm` no se puede leer con
                lector de pantalla ni probar, y esto no tiene deshacer. */}
            {!confirmandoDespublicar ? (
              <button
                type="button"
                onClick={() => setConfirmandoDespublicar(true)}
                className="text-sm font-medium text-ink-soft underline underline-offset-4"
              >
                Despublicar
              </button>
            ) : (
              <div>
                <p className="mb-3 text-sm text-ink-soft">
                  ¿Seguro que quieres despublicar a {titulo}? Sale del catálogo y esta acción no se
                  puede deshacer.
                </p>
                <div className="flex flex-wrap gap-3">
                  <button
                    type="button"
                    disabled={despublicando}
                    onClick={despublicar}
                    className="rounded-full bg-ochre px-5 py-2 font-medium text-bg disabled:opacity-60"
                  >
                    {despublicando ? 'Despublicando…' : 'Sí, despublicar'}
                  </button>
                  <button
                    type="button"
                    onClick={() => setConfirmandoDespublicar(false)}
                    className="rounded-full border border-line px-5 py-2 font-medium text-ink-soft"
                  >
                    Cancelar
                  </button>
                </div>
              </div>
            )}
          </div>
          {errorDespublicar && (
            <p
              role="alert"
              className="mt-4 rounded-2xl border border-line bg-surface p-4 text-sm text-ink-soft"
            >
              {errorDespublicar}
            </p>
          )}
        </section>
      )}
    </div>
  );
}
