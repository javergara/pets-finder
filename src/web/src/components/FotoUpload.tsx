import { type ChangeEvent, useEffect, useState } from 'react';
import Cropper from 'react-easy-crop';
import { ApiError, subirFoto } from '../api/client';
import { type AreaRecorte, comprimirImagen, recortarImagen } from '../lib/imagen';

type Props = {
  // Se invoca con el foto_url definitivo (bajo /media/uploads/) al terminar la
  // subida. Con varias fotos (feature 41) recibe siempre la PRIMERA (la
  // principal) y onFotosSubidas la lista completa en orden.
  onFotoSubida: (fotoUrl: string) => void;
  maxFotos?: number;
  onFotosSubidas?: (fotoUrls: string[]) => void;
};

// Proporciones del encuadre: null = la de la foto original (el encuadre inicial
// es la foto completa, así que sin tocar nada se sube tal cual).
const PROPORCIONES = [
  { etiqueta: 'Original', valor: null },
  { etiqueta: 'Cuadrada', valor: 1 },
  { etiqueta: 'Horizontal', valor: 4 / 3 },
] as const;

export function FotoUpload({ onFotoSubida, maxFotos = 1, onFotosSubidas }: Props) {
  const [archivo, setArchivo] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [recortando, setRecortando] = useState(false);
  const [crop, setCrop] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [proporcion, setProporcion] = useState<number | null>(null);
  const [aspectoOriginal, setAspectoOriginal] = useState<number | null>(null);
  const [area, setArea] = useState<AreaRecorte | null>(null);
  const [subiendo, setSubiendo] = useState(false);
  const [subida, setSubida] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Fotos ya subidas (solo con maxFotos > 1): url del servidor + preview local.
  const [subidas, setSubidas] = useState<{ url: string; preview: string }[]>([]);

  // Los object URLs no se liberan solos: revocar el anterior al reemplazarlo o desmontar.
  useEffect(() => {
    return () => {
      if (preview) URL.revokeObjectURL(preview);
    };
  }, [preview]);

  function handleChange(e: ChangeEvent<HTMLInputElement>) {
    const elegido = e.target.files?.[0];
    if (!elegido) return;

    setArchivo(elegido);
    setPreview(URL.createObjectURL(elegido));
    setRecortando(true);
    setSubida(false);
    setError(null);
    setCrop({ x: 0, y: 0 });
    setZoom(1);
    setProporcion(null);
    setAspectoOriginal(null);
    setArea(null);
    // Permite volver a elegir el mismo archivo tras cancelar.
    e.target.value = '';
  }

  function cancelar() {
    setArchivo(null);
    setPreview(null);
    setRecortando(false);
    setError(null);
  }

  async function subir() {
    if (!archivo) return;
    setError(null);
    setSubiendo(true);
    try {
      // recortarImagen devuelve el original intacto si el encuadre cubre todo;
      // comprimirImagen reescala/recomprime (o pasa de largo si no aplica):
      // subir 3-5 MB de foto de celular castiga cada tarjeta del listado después.
      const recortada = area ? await recortarImagen(archivo, area) : archivo;
      const comprimida = await comprimirImagen(recortada);
      const { foto_url } = await subirFoto(comprimida);
      setRecortando(false);
      if (maxFotos > 1) {
        // Acumula y deja el picker listo para la siguiente (feature 41).
        const nuevas = [...subidas, { url: foto_url, preview: URL.createObjectURL(recortada) }];
        setSubidas(nuevas);
        setPreview(null);
        setArchivo(null);
        onFotosSubidas?.(nuevas.map((s) => s.url));
        onFotoSubida(nuevas[0].url);
      } else {
        if (recortada !== archivo) setPreview(URL.createObjectURL(recortada));
        onFotoSubida(foto_url);
      }
      setSubida(true);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : 'No pudimos subir la foto. Intenta de nuevo.',
      );
    } finally {
      setSubiendo(false);
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <label htmlFor="foto-upload" className="text-sm font-medium text-ink-soft">
        Foto de la mascota
      </label>

      {/* Paso de encuadre: arrastrar y hacer zoom recorta; sin tocar nada, el
          encuadre inicial es la foto completa y se sube el archivo original. */}
      {recortando && preview && (
        <div className="flex flex-col gap-3 rounded-xl border border-line bg-surface p-3">
          <div className="relative h-72 w-full overflow-hidden rounded-lg bg-ink">
            <Cropper
              image={preview}
              crop={crop}
              zoom={zoom}
              aspect={proporcion ?? aspectoOriginal ?? 4 / 3}
              onCropChange={setCrop}
              onZoomChange={setZoom}
              onCropComplete={(_, areaPixeles) => setArea(areaPixeles)}
              onMediaLoaded={(media) =>
                setAspectoOriginal(media.naturalWidth / media.naturalHeight)
              }
            />
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {PROPORCIONES.map(({ etiqueta, valor }) => (
              <button
                key={etiqueta}
                type="button"
                onClick={() => setProporcion(valor)}
                className={`rounded-full border px-3 py-1 text-xs font-medium ${
                  proporcion === valor
                    ? 'border-forest bg-forest text-bg'
                    : 'border-line bg-surface text-ink-soft'
                }`}
              >
                {etiqueta}
              </button>
            ))}
            <label className="ml-auto flex items-center gap-2 text-xs text-muted">
              Zoom
              <input
                type="range"
                min={1}
                max={4}
                step={0.05}
                value={zoom}
                onChange={(e) => setZoom(Number(e.target.value))}
              />
            </label>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={subir}
              disabled={subiendo}
              className="flex-1 rounded-full bg-forest px-4 py-2 text-sm font-medium text-bg disabled:opacity-60"
            >
              {subiendo ? 'Subiendo…' : 'Subir foto'}
            </button>
            <button
              type="button"
              onClick={cancelar}
              disabled={subiendo}
              className="rounded-full border border-line px-4 py-2 text-sm font-medium text-ink-soft"
            >
              Cancelar
            </button>
          </div>
        </div>
      )}

      {/* Miniaturas de lo ya subido (feature 41, solo multi-foto). */}
      {subidas.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {subidas.map((s, n) => (
            <div key={s.url} className="relative">
              <img
                src={s.preview}
                alt={`Foto ${n + 1} subida`}
                className="h-20 w-20 rounded-lg border border-line object-cover"
              />
              <button
                type="button"
                aria-label={`Quitar foto ${n + 1}`}
                onClick={() => {
                  const nuevas = subidas.filter((x) => x.url !== s.url);
                  setSubidas(nuevas);
                  onFotosSubidas?.(nuevas.map((x) => x.url));
                  if (nuevas.length > 0) onFotoSubida(nuevas[0].url);
                }}
                className="absolute -right-2 -top-2 h-6 w-6 rounded-full border border-line bg-surface text-xs text-ink-soft"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Preview final sin recorte extra (object-contain): debe verse tal cual
          quedará la foto en el detalle. */}
      {!recortando && preview && (
        <img
          src={preview}
          alt="Vista previa de la foto elegida"
          className="max-h-80 w-full rounded-xl border border-line bg-surface-alt object-contain"
        />
      )}

      {/* Dos caminos al mismo flujo (feature 40): la cámara directa en móvil
          (capture) y la galería. Ambos pasan por el recorte y la compresión.
          Con multi-foto (41) el picker vuelve hasta llegar al máximo. */}
      <div className={subidas.length >= maxFotos ? 'hidden' : 'flex flex-wrap gap-2'}>
        <label className="cursor-pointer rounded-full border border-line bg-surface px-4 py-2 text-sm font-medium text-ink">
          📷 {subidas.length > 0 ? 'Tomar otra' : 'Tomar foto'}
          <input
            type="file"
            accept="image/*"
            capture="environment"
            onChange={handleChange}
            disabled={subiendo}
            className="hidden"
          />
        </label>
        <label className="cursor-pointer rounded-full border border-line bg-surface px-4 py-2 text-sm font-medium text-ink">
          {subidas.length > 0 ? 'Añadir otra (galería)' : 'Elegir de galería'}
          <input
            id="foto-upload"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={handleChange}
            disabled={subiendo}
            className="hidden"
          />
        </label>
      </div>
      {maxFotos > 1 && (
        <p className="text-xs text-muted">
          {subidas.length}/{maxFotos} fotos — la primera es la principal.
        </p>
      )}
      {subiendo && <p className="text-sm text-muted">Subiendo la foto…</p>}
      {subida && !subiendo && <p className="text-sm text-forest">Foto lista.</p>}
      {error && <p className="text-sm text-danger">{error}</p>}
    </div>
  );
}
