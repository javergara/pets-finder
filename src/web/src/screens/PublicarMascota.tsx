import { type FormEvent, useEffect, useState } from 'react';
import { Navigate, useNavigate, useSearchParams } from 'react-router-dom';
import { ApiError, crearMascota, obtenerOrganizacion, obtenerReporte } from '../api/client';
import type { EnergiaMascota, EspecieAdopcion, SexoMascota, TamanoMascota } from '../api/types';
import { AvisoSeguridad } from '../components/AvisoSeguridad';
import { CampoTexto } from '../components/CampoTexto';
import { FotosMascota } from '../components/FotosMascota';
import { GrupoOpciones } from '../components/GrupoOpciones';
import { SeccionesSiNo } from '../components/SeccionesSiNo';
import { SelectorCiudad } from '../components/SelectorCiudad';
import {
  ETIQUETA_ENERGIA,
  ETIQUETA_ESPECIE_ADOPCION,
  ETIQUETA_SEXO,
  ETIQUETA_TAMANO_MASCOTA,
  FLAGS_MASCOTA_INICIALES,
  type FlagsMascota,
} from '../lib/adopcion';
import { ZONA_OTRO } from '../lib/ciudades';
import { getActiveUserId, hasActiveUser } from '../lib/session';

// Publicar una mascota en adopción, como rescatista individual (AD-02, A2) o a
// nombre de una organización (A1).
//
// ⚠️ Escribe en producción, así que lo primero de todo es el gate de cuenta:
// `getActiveUserId()` cae al usuario demo (id 1) cuando no hay nada en
// localStorage, y sin gate un visitante publicaría mascotas a nombre de una
// persona real. Mismo patrón que `PublicarAvisoAyuda` y `ReportarMascota`.
//
// Dos caminos, un solo formulario, y los distingue `?organizacion=7` en la URL:
// sin él se publica como rescatista (`rescatista_id`, el dueño es la persona) y
// con él a nombre del lugar (`organizacion_id`, y el autor vuelve a su ficha).
// El publicador es exclusivo: mandar los dos es un 422 del backend, y publicar
// en una organización ajena, un 403 que se muestra tal cual.
//
// Con `?reporte=12` se entra por el puente (A3), desde un encontrado propio que
// la persona tiene consigo: se precarga lo que ya escribió en el reporte y se
// manda `report_id` para que las dos filas queden enlazadas (el backend valida
// naturaleza, autoría y repetición). Las fotos se HEREDAN sin re-subirlas, ver
// `components/FotosMascota`.
//
// Paleta `forest`/`ochre`: el rojo de emergencia está reservado a "perdido" y no
// aparece en este módulo, tampoco en el bloque de error.

const MENSAJE_ERROR_RED = 'No pudimos publicar la mascota. Intenta de nuevo.';
const MENSAJE_ERROR_LUGAR = 'No pudimos cargar los datos del lugar. Revísalos antes de publicar.';
const MENSAJE_ERROR_REPORTE = 'No pudimos cargar el reporte. Llena los datos a mano.';

// Tope de `PetIn.tags` en el backend: recortar aquí evita un 422 por una coma de más.
const MAX_TAGS = 8;

const CLASE_INPUT = 'mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink';

export function PublicarMascota() {
  const [nombre, setNombre] = useState('');
  const [especie, setEspecie] = useState<EspecieAdopcion | null>(null);
  const [sexo, setSexo] = useState<SexoMascota | null>(null);
  const [tamano, setTamano] = useState<TamanoMascota | null>(null);
  const [energia, setEnergia] = useState<EnergiaMascota | null>(null);
  const [raza, setRaza] = useState('');
  const [edadMeses, setEdadMeses] = useState(0);
  const [historia, setHistoria] = useState('');
  const [etiquetasTexto, setEtiquetasTexto] = useState('');
  const [flags, setFlags] = useState<FlagsMascota>(FLAGS_MASCOTA_INICIALES);
  // La pantalla es dueña de las fotos, en dos listas: las que vienen del reporte
  // (ya en Storage) y las que se suben aquí. Al publicar viajan juntas, las
  // heredadas primero, porque la primera es la principal de la ficha.
  const [fotosHeredadas, setFotosHeredadas] = useState<string[]>([]);
  const [fotosSubidas, setFotosSubidas] = useState<string[]>([]);
  const [zona, setZona] = useState('');
  const [ciudadTexto, setCiudadTexto] = useState('');
  const [barrio, setBarrio] = useState('');
  // Sin campo propio: el formulario no pide pin (la zona basta para el mapa),
  // pero si venimos de un reporte ya hay un punto exacto y sería una pena tirarlo.
  const [punto, setPunto] = useState<{ lat: number; lng: number } | null>(null);
  const [telefono, setTelefono] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const navigate = useNavigate();
  // `?organizacion=7` / `?reporte=12`: `Number(null)` es 0, así que un parámetro
  // ausente (o basura) cae en el camino de rescatista sin reporte enlazado.
  const [busqueda] = useSearchParams();
  const organizacionId = Number(busqueda.get('organizacion')) || null;
  const reporteId = Number(busqueda.get('reporte')) || null;
  const [nombreOrganizacion, setNombreOrganizacion] = useState<string | null>(null);

  // Precarga: quien publica desde un lugar no debería reescribir la zona ni el
  // teléfono que ya registró. Quedan editables (la mascota puede estar en otra
  // parte) y el teléfono ya escrito a mano no se pisa.
  useEffect(() => {
    // Sin cuenta la pantalla redirige abajo: pedir el lugar sería una consulta
    // tirada a la basura.
    if (organizacionId === null || !hasActiveUser()) return;
    obtenerOrganizacion(organizacionId)
      .then((organizacion) => {
        setNombreOrganizacion(organizacion.nombre);
        setZona(organizacion.zona);
        setCiudadTexto(organizacion.ciudad_texto ?? '');
        setTelefono((previo) => previo || organizacion.telefono_contacto);
      })
      // El backend responde en español ("La organización 7 no existe"): copy de
      // producto, se muestra tal cual en el mismo bloque de error del formulario.
      .catch((err) => setError(err instanceof ApiError ? err.message : MENSAJE_ERROR_LUGAR));
  }, [organizacionId]);

  // Precarga del puente: la mascota ya está descrita en el reporte y el sitio y
  // el teléfono son los mismos. Volver a teclearlo todo sería el peor momento
  // para pedirle esfuerzo a alguien que lleva días con un animal ajeno en casa,
  // y cada campo retecleado es una oportunidad de que la ficha contradiga al
  // reporte. Todo queda editable: esto es un borrador, no un calco.
  useEffect(() => {
    if (reporteId === null || !hasActiveUser()) return;
    obtenerReporte(reporteId)
      .then((reporte) => {
        if (reporte.nombre_mascota) setNombre(reporte.nombre_mascota);
        setEspecie(reporte.especie);
        setTamano(reporte.tamano);
        setRaza(reporte.raza ?? '');
        setHistoria(reporte.descripcion);
        setZona(reporte.zona);
        setCiudadTexto(reporte.ciudad_texto ?? '');
        setBarrio(reporte.barrio ?? '');
        setPunto({ lat: reporte.lat, lng: reporte.lng });
        setTelefono((previo) => previo || reporte.telefono_contacto || '');
        // Las fotos NO se re-suben: son URLs que ya están en Storage.
        setFotosHeredadas(
          reporte.fotos?.length ? reporte.fotos : reporte.foto_url ? [reporte.foto_url] : [],
        );
      })
      // Mismo criterio que el lugar: el 404/403 del backend viene en español.
      .catch((err) => setError(err instanceof ApiError ? err.message : MENSAJE_ERROR_REPORTE));
  }, [reporteId]);

  // ⚠️ Antes de leer ningún id: ver la cabecera del archivo. El `volver` conserva
  // la query: sin ella, quien se registra vuelve al camino de rescatista.
  if (!hasActiveUser()) {
    const query = busqueda.toString();
    const volver = `/adoptar/publicar${query ? `?${query}` : ''}`;
    return <Navigate to={`/registro?volver=${encodeURIComponent(volver)}`} replace />;
  }

  // Los mensajes son de producto y en español, y salen por el mismo bloque
  // `role="alert"` que los del backend: quien publica ve un solo sitio de error.
  function revisar(): string | null {
    if (!nombre.trim()) return 'Ponle un nombre: es lo primero que ve quien busca a quién adoptar.';
    if (!especie || !sexo || !tamano || !energia) return 'Elige especie, sexo, tamaño y energía.';
    if (!historia.trim()) return 'Cuéntanos su historia: es lo que más ayuda a que la adopten.';
    if (!zona) return 'Selecciona la zona donde está la mascota.';
    if (zona === ZONA_OTRO && !ciudadTexto.trim())
      return 'Con "Otro lugar" cuéntanos en qué ciudad o municipio está.';
    if (!telefono.trim())
      return 'Deja un teléfono de contacto: sin él nadie puede escribirte para adoptarla.';
    return null;
  }

  async function publicar(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const problema = revisar();
    if (problema) {
      setError(problema);
      return;
    }
    setError(null);
    setEnviando(true);
    try {
      const mascota = await crearMascota({
        // `user_id` es siempre quien hace el request; el dueño va aparte y es
        // exclusivo. Como rescatista son la misma persona (el backend rechaza con
        // 422 que alguien publique a nombre de otro); a nombre de un lugar, el
        // dueño es la organización y quien pide debe ser quien la registró (403).
        user_id: getActiveUserId(),
        ...(organizacionId === null
          ? { rescatista_id: getActiveUserId() }
          : { organizacion_id: organizacionId }),
        nombre: nombre.trim(),
        especie: especie as EspecieAdopcion,
        sexo: sexo as SexoMascota,
        tamano: tamano as TamanoMascota,
        energia: energia as EnergiaMascota,
        ...(raza.trim() ? { raza: raza.trim() } : {}),
        edad_meses: edadMeses,
        historia: historia.trim(),
        tags: etiquetasTexto
          .split(',')
          .map((tag) => tag.trim())
          .filter(Boolean)
          .slice(0, MAX_TAGS),
        fotos: [...fotosHeredadas, ...fotosSubidas],
        ...flags,
        zona,
        ...(zona === ZONA_OTRO ? { ciudad_texto: ciudadTexto.trim() } : {}),
        ...(barrio.trim() ? { barrio: barrio.trim() } : {}),
        ...(punto ?? {}),
        telefono_contacto: telefono.trim(),
        // Enlaza las dos filas: el reporte muestra la franja y el backend impide
        // publicarlo dos veces (409) o eliminarlo dejando la ficha huérfana.
        ...(reporteId === null ? {} : { report_id: reporteId }),
      });
      // Desde un lugar se vuelve a su panel (donde está el resto de su camada y
      // el selector de estado); como rescatista, a la ficha recién publicada.
      navigate(
        organizacionId === null
          ? `/adoptar/mascota/${mascota.id}`
          : `/organizacion/${organizacionId}?tab=adopcion`,
      );
    } catch (err) {
      // El backend responde en español ("Solo quien registró la organización…"):
      // ese texto es copy de producto y se muestra tal cual.
      setError(err instanceof ApiError ? err.message : MENSAJE_ERROR_RED);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-6 pb-24">
      <header>
        <h1 className="font-display text-3xl text-ink">Dar una mascota en adopción</h1>
        <p className="mt-1 text-sm text-muted">
          {nombreOrganizacion
            ? `Publicas a nombre de ${nombreOrganizacion}: quien quiera adoptarla escribirá al teléfono del lugar.`
            : 'Rescataste un animal que nadie reclamó y buscas familia para él. Cuéntanos cómo es: entre más sepan de él, más fácil es que alguien se decida.'}
        </p>
        {reporteId !== null && (
          <p className="mt-2 text-sm text-ink-soft">
            Copiamos lo que ya contaste en tu reporte: revísalo y completa lo que falte.
          </p>
        )}
      </header>

      <form onSubmit={publicar} className="flex flex-col gap-5">
        <CampoTexto
          id="mascota-nombre"
          etiqueta="Nombre"
          valor={nombre}
          onChange={setNombre}
          placeholder="Como le dices tú"
        />

        <GrupoOpciones
          titulo="Especie"
          etiquetas={ETIQUETA_ESPECIE_ADOPCION}
          valor={especie}
          onChange={setEspecie}
        />
        <GrupoOpciones titulo="Sexo" etiquetas={ETIQUETA_SEXO} valor={sexo} onChange={setSexo} />

        <CampoTexto
          id="mascota-raza"
          etiqueta="Raza (opcional)"
          valor={raza}
          onChange={setRaza}
          placeholder="Criolla, mestiza, labrador…"
        />

        <div>
          <label htmlFor="mascota-edad" className="text-sm font-medium text-ink-soft">
            Edad (en meses)
          </label>
          <input
            id="mascota-edad"
            type="number"
            min={0}
            max={360}
            value={edadMeses}
            onChange={(e) => setEdadMeses(Number(e.target.value))}
            className={CLASE_INPUT}
          />
          <p className="mt-1 text-xs text-muted">Aproximada está bien: 6 meses, 24 meses…</p>
        </div>

        <GrupoOpciones
          titulo="Tamaño"
          etiquetas={ETIQUETA_TAMANO_MASCOTA}
          valor={tamano}
          onChange={setTamano}
        />
        <GrupoOpciones
          titulo="Energía"
          etiquetas={ETIQUETA_ENERGIA}
          valor={energia}
          onChange={setEnergia}
        />

        <div>
          <label htmlFor="mascota-historia" className="text-sm font-medium text-ink-soft">
            Historia
          </label>
          <textarea
            id="mascota-historia"
            rows={4}
            value={historia}
            onChange={(e) => setHistoria(e.target.value)}
            placeholder="Cómo llegó a ti, cómo es su carácter, qué necesita…"
            className={CLASE_INPUT}
          />
        </div>

        <CampoTexto
          id="mascota-etiquetas"
          etiqueta="Etiquetas (separadas por coma, opcional)"
          valor={etiquetasTexto}
          onChange={setEtiquetasTexto}
          placeholder="juguetona, tranquila, necesita experiencia"
        />

        <SeccionesSiNo
          flags={flags}
          onChange={(campo, valor) => setFlags((previos) => ({ ...previos, [campo]: valor }))}
        />

        {/* Hasta 3 fotos, como un reporte, y la primera es la principal de la
            ficha. Las heredadas del reporte llenan cupo sin volver a subirse. */}
        <FotosMascota
          heredadas={fotosHeredadas}
          onQuitarHeredada={(url) =>
            setFotosHeredadas((previas) => previas.filter((foto) => foto !== url))
          }
          onSubidas={setFotosSubidas}
        />

        <div>
          <label htmlFor="selector-zona" className="text-sm font-medium text-ink-soft">
            ¿En qué zona está?
          </label>
          <div className="mt-1">
            <SelectorCiudad
              value={zona}
              onChange={setZona}
              incluirOtro
              placeholder="Selecciona la zona"
            />
          </div>
        </div>

        {zona === ZONA_OTRO && (
          <CampoTexto
            id="mascota-ciudad"
            etiqueta="¿En qué ciudad o municipio?"
            valor={ciudadTexto}
            onChange={setCiudadTexto}
          />
        )}

        <CampoTexto
          id="mascota-barrio"
          etiqueta="Barrio o referencia (opcional)"
          valor={barrio}
          onChange={setBarrio}
        />

        <CampoTexto
          id="mascota-telefono"
          etiqueta="Teléfono de contacto (WhatsApp)"
          tipo="tel"
          valor={telefono}
          onChange={setTelefono}
          placeholder="3001234567"
          ayuda="Por aquí te escribe quien quiera adoptarla."
        />

        <AvisoSeguridad contexto="publicar" />

        {error && (
          <p
            role="alert"
            className="rounded-2xl border border-line bg-surface p-4 text-sm text-ink-soft"
          >
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={enviando}
          className="mt-2 rounded-full bg-forest px-4 py-3 font-medium text-bg disabled:opacity-60"
        >
          {enviando ? 'Publicando…' : 'Publicar en adopción'}
        </button>
      </form>
    </div>
  );
}
