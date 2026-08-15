import { type FormEvent, useEffect, useState } from 'react';
import { Navigate, useNavigate, useSearchParams } from 'react-router-dom';
import { ApiError, crearMascota, obtenerOrganizacion } from '../api/client';
import type { EnergiaMascota, EspecieAdopcion, SexoMascota, TamanoMascota } from '../api/types';
import { AvisoSeguridad } from '../components/AvisoSeguridad';
import { FotoUpload } from '../components/FotoUpload';
import { OpcionCard, OpcionesSiNo } from '../components/OpcionCard';
import { SelectorCiudad } from '../components/SelectorCiudad';
import {
  ETIQUETA_ENERGIA,
  ETIQUETA_ESPECIE_ADOPCION,
  ETIQUETA_SEXO,
  ETIQUETA_TAMANO_MASCOTA,
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
// en una organización ajena, un 403 que se muestra tal cual. El puente desde un
// reporte encontrado (`?reporte=`) es un paso aparte.
//
// Paleta `forest`/`ochre`: el rojo de emergencia está reservado a "perdido" y no
// aparece en este módulo, tampoco en el bloque de error.

const MENSAJE_ERROR_RED = 'No pudimos publicar la mascota. Intenta de nuevo.';
const MENSAJE_ERROR_LUGAR = 'No pudimos cargar los datos del lugar. Revísalos antes de publicar.';

// Tope de `PetIn.tags` en el backend: recortar aquí evita un 422 por una coma de más.
const MAX_TAGS = 8;

// Valores iniciales de los siete sí/no, los mismos de `PetIn`: salud
// conservadora (no) y convivencia optimista (sí), para no prometer lo que nadie
// verificó.
const FLAGS_INICIALES = {
  esterilizado: false,
  vacunas_al_dia: false,
  microchip: false,
  desparasitado: false,
  apto_ninos: true,
  apto_perros: true,
  apto_gatos: true,
};

type Flags = typeof FLAGS_INICIALES;

// Las dos secciones de sí/no se pintan con el mismo bloque: son idénticas salvo
// el título y las preguntas, y escribirlas dos veces en el JSX era la mitad del
// formulario.
const SECCIONES_SI_NO: { titulo: string; preguntas: { campo: keyof Flags; pregunta: string }[] }[] =
  [
    {
      titulo: 'Salud',
      preguntas: [
        { campo: 'esterilizado', pregunta: '¿Está esterilizada?' },
        { campo: 'vacunas_al_dia', pregunta: '¿Tiene las vacunas al día?' },
        { campo: 'microchip', pregunta: '¿Tiene microchip?' },
        { campo: 'desparasitado', pregunta: '¿Está desparasitada?' },
      ],
    },
    {
      titulo: 'Convivencia',
      preguntas: [
        { campo: 'apto_ninos', pregunta: '¿Convive bien con niños?' },
        { campo: 'apto_perros', pregunta: '¿Convive bien con otros perros?' },
        { campo: 'apto_gatos', pregunta: '¿Convive bien con gatos?' },
      ],
    },
  ];

const CLASE_INPUT = 'mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink';

/** Un catálogo cerrado (especie, sexo, tamaño, energía) como chips de opción
 * única. El grupo lleva el nombre accesible del catálogo para que "Perro" y
 * "Mediana" no floten sueltos entre los treinta botones del formulario. */
function GrupoOpciones<T extends string>({
  titulo,
  etiquetas,
  valor,
  onChange,
}: {
  titulo: string;
  etiquetas: Record<T, string>;
  valor: T | null;
  onChange: (valor: T) => void;
}) {
  return (
    <div>
      <h2 className="mb-2 font-display text-lg text-ink">{titulo}</h2>
      <div role="group" aria-label={titulo} className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {(Object.entries(etiquetas) as [T, string][]).map(([opcion, etiqueta]) => (
          <OpcionCard
            key={opcion}
            etiqueta={etiqueta}
            seleccionada={valor === opcion}
            onClick={() => onChange(opcion)}
          />
        ))}
      </div>
    </div>
  );
}

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
  const [flags, setFlags] = useState<Flags>(FLAGS_INICIALES);
  // La pantalla es dueña de las fotos: `FotoUpload` solo añade a esta lista.
  const [fotos, setFotos] = useState<string[]>([]);
  const [zona, setZona] = useState('');
  const [ciudadTexto, setCiudadTexto] = useState('');
  const [barrio, setBarrio] = useState('');
  const [telefono, setTelefono] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const navigate = useNavigate();
  // `?organizacion=7`: publica el lugar, no la persona. `Number(null)` es 0, así
  // que un parámetro ausente (o basura) cae en el camino de rescatista.
  const [busqueda] = useSearchParams();
  const organizacionId = Number(busqueda.get('organizacion')) || null;
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
        fotos,
        ...flags,
        zona,
        ...(zona === ZONA_OTRO ? { ciudad_texto: ciudadTexto.trim() } : {}),
        ...(barrio.trim() ? { barrio: barrio.trim() } : {}),
        telefono_contacto: telefono.trim(),
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
      </header>

      <form onSubmit={publicar} className="flex flex-col gap-5">
        <div>
          <label htmlFor="mascota-nombre" className="text-sm font-medium text-ink-soft">
            Nombre
          </label>
          <input
            id="mascota-nombre"
            type="text"
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            placeholder="Como le dices tú"
            className={CLASE_INPUT}
          />
        </div>

        <GrupoOpciones
          titulo="Especie"
          etiquetas={ETIQUETA_ESPECIE_ADOPCION}
          valor={especie}
          onChange={setEspecie}
        />
        <GrupoOpciones titulo="Sexo" etiquetas={ETIQUETA_SEXO} valor={sexo} onChange={setSexo} />

        <div>
          <label htmlFor="mascota-raza" className="text-sm font-medium text-ink-soft">
            Raza (opcional)
          </label>
          <input
            id="mascota-raza"
            type="text"
            value={raza}
            onChange={(e) => setRaza(e.target.value)}
            placeholder="Criolla, mestiza, labrador…"
            className={CLASE_INPUT}
          />
        </div>

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

        <div>
          <label htmlFor="mascota-etiquetas" className="text-sm font-medium text-ink-soft">
            Etiquetas (separadas por coma, opcional)
          </label>
          <input
            id="mascota-etiquetas"
            type="text"
            value={etiquetasTexto}
            onChange={(e) => setEtiquetasTexto(e.target.value)}
            placeholder="juguetona, tranquila, necesita experiencia"
            className={CLASE_INPUT}
          />
        </div>

        {SECCIONES_SI_NO.map(({ titulo, preguntas }) => (
          <div key={titulo}>
            <h2 className="mb-2 font-display text-lg text-ink">{titulo}</h2>
            <div className="flex flex-col gap-4">
              {preguntas.map(({ campo, pregunta }) => (
                <div key={campo}>
                  <p className="mb-2 text-sm text-ink-soft">{pregunta}</p>
                  <OpcionesSiNo
                    etiqueta={pregunta}
                    valor={flags[campo]}
                    onChange={(valor) => setFlags((previos) => ({ ...previos, [campo]: valor }))}
                  />
                </div>
              ))}
            </div>
          </div>
        ))}

        {/* Hasta 3 fotos, como un reporte: `FotoUpload` sube y comprime, y devuelve
            la lista completa en orden — la primera es la principal de la ficha. */}
        <FotoUpload maxFotos={3} onFotoSubida={() => {}} onFotosSubidas={setFotos} />

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
          <div>
            <label htmlFor="mascota-ciudad" className="text-sm font-medium text-ink-soft">
              ¿En qué ciudad o municipio?
            </label>
            <input
              id="mascota-ciudad"
              type="text"
              value={ciudadTexto}
              onChange={(e) => setCiudadTexto(e.target.value)}
              className={CLASE_INPUT}
            />
          </div>
        )}

        <div>
          <label htmlFor="mascota-barrio" className="text-sm font-medium text-ink-soft">
            Barrio o referencia (opcional)
          </label>
          <input
            id="mascota-barrio"
            type="text"
            value={barrio}
            onChange={(e) => setBarrio(e.target.value)}
            className={CLASE_INPUT}
          />
        </div>

        <div>
          <label htmlFor="mascota-telefono" className="text-sm font-medium text-ink-soft">
            Teléfono de contacto (WhatsApp)
          </label>
          <input
            id="mascota-telefono"
            type="tel"
            value={telefono}
            onChange={(e) => setTelefono(e.target.value)}
            placeholder="3001234567"
            className={CLASE_INPUT}
          />
          <p className="mt-1 text-xs text-muted">Por aquí te escribe quien quiera adoptarla.</p>
        </div>

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
