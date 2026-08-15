import { type FormEvent, useEffect, useState } from 'react';
import { Link, Navigate, useNavigate, useParams } from 'react-router-dom';
import { ApiError, editarMascota, obtenerMascota } from '../api/client';
import type {
  EnergiaMascota,
  EspecieAdopcion,
  EstadoMascota,
  Mascota,
  SexoMascota,
  TamanoMascota,
} from '../api/types';
import { CampoTexto } from '../components/CampoTexto';
import { FotosMascota } from '../components/FotosMascota';
import { GrupoOpciones } from '../components/GrupoOpciones';
import { SeccionesSiNo } from '../components/SeccionesSiNo';
import {
  ETIQUETA_ENERGIA,
  ETIQUETA_ESPECIE_ADOPCION,
  ETIQUETA_ESTADO_MASCOTA,
  ETIQUETA_SEXO,
  ETIQUETA_TAMANO_MASCOTA,
  type FlagsMascota,
  tituloMascota,
} from '../lib/adopcion';
import { getActiveUserId, hasActiveUser } from '../lib/session';

// Corregir lo que ya se publicó en adopción (AD-02, A1 y A2): el mismo
// formulario de `PublicarMascota`, precargado con lo que hay en la ficha.
//
// ⚠️ Escribe, así que lo primero es el gate de cuenta: `getActiveUserId()` cae al
// usuario demo (id 1) sin nada en localStorage y un visitante editaría mascotas
// de una persona real. La autoría de verdad la decide el backend (403 "Solo
// quien publicó la mascota puede editarla"), que es lo único en lo que se puede
// confiar: aquí no se sabe quién registró una organización.
//
// **Sin zona ni ciudad a propósito.** `MascotaUpdate` (espejo de `PetUpdate`) no
// las declara: mudar una mascota de zona cambiaría su encuadre en el mapa y en
// las búsquedas del catálogo, así que para eso se despublica y se vuelve a
// publicar. La pantalla lo dice en vez de dejar el hueco sin explicación.
//
// Contrato de las pantallas de detalle desde el fix de esqueletos (81d45ee):
// mientras carga hay `role="status"`, y si falla hay `role="alert"` con el copy
// del backend — un 404 nunca deja un esqueleto eterno.
//
// Paleta `forest`/`ochre`: el rojo de emergencia está reservado a "perdido" y no
// entra en este módulo, tampoco en el bloque de error.

const MENSAJE_ERROR_CARGA =
  'No pudimos cargar esta mascota. Revisa tu conexión e intenta de nuevo.';
const MENSAJE_ERROR_GUARDAR = 'No pudimos guardar los cambios. Intenta de nuevo.';

// Tope de `PetUpdate.tags` en el backend: recortar aquí evita un 422 por una coma de más.
const MAX_TAGS = 8;

const ESTADOS = Object.keys(ETIQUETA_ESTADO_MASCOTA) as EstadoMascota[];

const CLASE_INPUT = 'mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink';

export function EditarMascota() {
  const { id } = useParams<{ id: string }>();
  const [mascota, setMascota] = useState<Mascota | null>(null);
  const [nombre, setNombre] = useState('');
  const [especie, setEspecie] = useState<EspecieAdopcion | null>(null);
  const [sexo, setSexo] = useState<SexoMascota | null>(null);
  const [tamano, setTamano] = useState<TamanoMascota | null>(null);
  const [energia, setEnergia] = useState<EnergiaMascota | null>(null);
  const [raza, setRaza] = useState('');
  const [edadMeses, setEdadMeses] = useState(0);
  const [historia, setHistoria] = useState('');
  const [etiquetasTexto, setEtiquetasTexto] = useState('');
  const [flags, setFlags] = useState<FlagsMascota | null>(null);
  // Las fotos ya publicadas están en Storage: se conservan tal cual (o se
  // quitan), y las nuevas se suben aparte. Al guardar viajan juntas como lista
  // completa, nunca como una mutación parcial.
  const [fotosPublicadas, setFotosPublicadas] = useState<string[]>([]);
  const [fotosSubidas, setFotosSubidas] = useState<string[]>([]);
  const [barrio, setBarrio] = useState('');
  const [telefono, setTelefono] = useState('');
  const [estado, setEstado] = useState<EstadoMascota>('disponible');
  const [error, setError] = useState<string | null>(null);
  const [errorCarga, setErrorCarga] = useState<string | null>(null);
  const [guardando, setGuardando] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    // Sin cuenta la pantalla redirige abajo: pedir la mascota sería una consulta
    // tirada a la basura (y los efectos corren aunque el render devuelva Navigate).
    if (!id || !hasActiveUser()) return;
    setErrorCarga(null);
    obtenerMascota(Number(id))
      .then((m) => {
        setMascota(m);
        setNombre(m.nombre);
        setEspecie(m.especie);
        setSexo(m.sexo);
        setTamano(m.tamano);
        setEnergia(m.energia);
        setRaza(m.raza ?? '');
        setEdadMeses(m.edad_meses);
        setHistoria(m.historia);
        setEtiquetasTexto(m.tags.join(', '));
        setFlags({
          esterilizado: m.esterilizado,
          vacunas_al_dia: m.vacunas_al_dia,
          microchip: m.microchip,
          desparasitado: m.desparasitado,
          apto_ninos: m.apto_ninos,
          apto_perros: m.apto_perros,
          apto_gatos: m.apto_gatos,
        });
        setFotosPublicadas(m.fotos);
        setBarrio(m.barrio ?? '');
        setTelefono(m.telefono_contacto ?? '');
        setEstado(m.estado);
      })
      // El backend responde en español ("La mascota 31 no existe"): copy de
      // producto, se muestra tal cual.
      .catch((err) => setErrorCarga(err instanceof ApiError ? err.message : MENSAJE_ERROR_CARGA));
  }, [id]);

  // ⚠️ Antes de leer ningún id de sesión: ver la cabecera del archivo.
  if (!hasActiveUser()) {
    const volver = `/adoptar/mascota/${id}/editar`;
    return <Navigate to={`/registro?volver=${encodeURIComponent(volver)}`} replace />;
  }

  if (errorCarga) {
    return (
      <div className="mx-auto max-w-2xl space-y-4 p-6 text-center">
        <h1 className="font-display text-2xl text-ink">No pudimos abrir esta ficha</h1>
        <p
          role="alert"
          className="rounded-2xl border border-line bg-surface p-4 text-sm text-ink-soft"
        >
          {errorCarga}
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

  if (!mascota || !flags) {
    return (
      <div
        role="status"
        aria-label="Cargando la ficha de la mascota"
        className="mx-auto mt-8 h-96 max-w-2xl animate-pulse rounded-2xl bg-surface-alt"
      />
    );
  }

  // Mismas reglas que al publicar y en el mismo bloque `role="alert"` que los
  // errores del backend: `PetUpdate` rechaza con 422 un nombre o una historia
  // vacíos, y sin teléfono nadie puede escribir para adoptarla.
  function revisar(): string | null {
    if (!nombre.trim()) return 'Ponle un nombre: es lo primero que ve quien busca a quién adoptar.';
    if (!especie || !sexo || !tamano || !energia) return 'Elige especie, sexo, tamaño y energía.';
    if (!historia.trim()) return 'Cuéntanos su historia: es lo que más ayuda a que la adopten.';
    if (!telefono.trim())
      return 'Deja un teléfono de contacto: sin él nadie puede escribirte para adoptarla.';
    return null;
  }

  async function guardar(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!mascota || !flags) return;
    const problema = revisar();
    if (problema) {
      setError(problema);
      return;
    }
    setError(null);
    setGuardando(true);
    try {
      await editarMascota(mascota.id, {
        // Quien pide el cambio. El dueño no se toca: `PetUpdate` no deja mover
        // una mascota de publicador (ni de zona).
        user_id: getActiveUserId(),
        nombre: nombre.trim(),
        especie: especie as EspecieAdopcion,
        sexo: sexo as SexoMascota,
        tamano: tamano as TamanoMascota,
        energia: energia as EnergiaMascota,
        // Los opcionales viajan aunque estén vacíos: el backend ignora los
        // nulos (`exclude_none=True`), así que la cadena vacía es la única
        // forma de borrar una raza o un barrio que estaban mal.
        raza: raza.trim(),
        edad_meses: edadMeses,
        historia: historia.trim(),
        tags: etiquetasTexto
          .split(',')
          .map((tag) => tag.trim())
          .filter(Boolean)
          .slice(0, MAX_TAGS),
        fotos: [...fotosPublicadas, ...fotosSubidas],
        ...flags,
        barrio: barrio.trim(),
        telefono_contacto: telefono.trim(),
        estado,
      });
      navigate(`/adoptar/mascota/${mascota.id}`);
    } catch (err) {
      // El 403 del backend ("Solo quien publicó la mascota puede editarla") ya
      // viene en español: es copy de producto y se muestra tal cual.
      setError(err instanceof ApiError ? err.message : MENSAJE_ERROR_GUARDAR);
    } finally {
      setGuardando(false);
    }
  }

  const lugar = mascota.zona === 'Otro' ? mascota.ciudad_texto ?? 'Colombia' : mascota.zona;

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-6 pb-24">
      <header>
        <h1 className="font-display text-3xl text-ink">
          Editar la ficha de {tituloMascota(mascota)}
        </h1>
        <p className="mt-1 text-sm text-muted">
          Corrige lo que quedó mal o cuenta lo que ha cambiado: quien la vea en el catálogo verá
          esto mismo.
        </p>
        <p className="mt-2 text-sm text-ink-soft">
          Está publicada en {lugar}, y la zona no se cambia desde aquí: si se mudó, despublícala y
          publícala de nuevo desde donde esté.
        </p>
      </header>

      <form onSubmit={guardar} className="flex flex-col gap-5">
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
          onChange={(campo, valor) =>
            setFlags((previos) => (previos === null ? previos : { ...previos, [campo]: valor }))
          }
        />

        {/* Las publicadas llenan cupo sin volver a subirse; hasta 3 en total. */}
        <FotosMascota
          origen="mascota"
          heredadas={fotosPublicadas}
          onQuitarHeredada={(url) =>
            setFotosPublicadas((previas) => previas.filter((foto) => foto !== url))
          }
          onSubidas={setFotosSubidas}
        />

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

        {/* Quien publica como rescatista no tiene panel: este es su único sitio
            para decir que ya encontró familia (el lugar lo hace desde el suyo). */}
        <div>
          <label htmlFor="mascota-estado" className="text-sm font-medium text-ink-soft">
            Estado de la publicación
          </label>
          <select
            id="mascota-estado"
            value={estado}
            onChange={(e) => setEstado(e.target.value as EstadoMascota)}
            className={CLASE_INPUT}
          >
            {ESTADOS.map((opcion) => (
              <option key={opcion} value={opcion}>
                {ETIQUETA_ESTADO_MASCOTA[opcion].texto}
              </option>
            ))}
          </select>
        </div>

        {error && (
          <p
            role="alert"
            className="rounded-2xl border border-line bg-surface p-4 text-sm text-ink-soft"
          >
            {error}
          </p>
        )}

        <div className="flex flex-wrap gap-3">
          <button
            type="submit"
            disabled={guardando}
            className="rounded-full bg-forest px-5 py-3 font-medium text-bg disabled:opacity-60"
          >
            {guardando ? 'Guardando…' : 'Guardar cambios'}
          </button>
          <button
            type="button"
            onClick={() => navigate(`/adoptar/mascota/${mascota.id}`)}
            className="rounded-full border border-line px-5 py-3 font-medium text-ink-soft"
          >
            Cancelar
          </button>
        </div>
      </form>
    </div>
  );
}
