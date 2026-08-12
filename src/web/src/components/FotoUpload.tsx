import { type ChangeEvent, useEffect, useState } from 'react';
import { ApiError, subirFoto } from '../api/client';
import { comprimirImagen } from '../lib/imagen';

type Props = {
  // Se invoca con el foto_url definitivo (bajo /media/uploads/) al terminar la subida.
  onFotoSubida: (fotoUrl: string) => void;
};

export function FotoUpload({ onFotoSubida }: Props) {
  const [preview, setPreview] = useState<string | null>(null);
  const [subiendo, setSubiendo] = useState(false);
  const [subida, setSubida] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Los object URLs no se liberan solos: revocar el anterior al reemplazarlo o desmontar.
  useEffect(() => {
    return () => {
      if (preview) URL.revokeObjectURL(preview);
    };
  }, [preview]);

  async function handleChange(e: ChangeEvent<HTMLInputElement>) {
    const archivo = e.target.files?.[0];
    if (!archivo) return;

    setPreview(URL.createObjectURL(archivo));
    setSubida(false);
    setError(null);
    setSubiendo(true);
    try {
      // Reescala/recomprime en el navegador (o devuelve el original si no aplica):
      // subir 3-5 MB de foto de celular castiga cada tarjeta del listado después.
      const comprimida = await comprimirImagen(archivo);
      const { foto_url } = await subirFoto(comprimida);
      setSubida(true);
      onFotoSubida(foto_url);
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
      {/* Preview sin recorte (object-contain): debe verse tal cual quedará la
          foto en el detalle, no una versión 4:3 que engaña sobre el encuadre. */}
      {preview && (
        <img
          src={preview}
          alt="Vista previa de la foto elegida"
          className="max-h-80 w-full rounded-xl border border-line bg-surface-alt object-contain"
        />
      )}
      <input
        id="foto-upload"
        type="file"
        accept="image/jpeg,image/png,image/webp"
        onChange={handleChange}
        disabled={subiendo}
        className="text-sm text-muted file:mr-3 file:rounded-full file:border file:border-line file:bg-surface file:px-4 file:py-2 file:font-medium file:text-ink"
      />
      {subiendo && <p className="text-sm text-muted">Subiendo la foto…</p>}
      {subida && !subiendo && <p className="text-sm text-forest">Foto lista.</p>}
      {error && <p className="text-sm text-danger">{error}</p>}
    </div>
  );
}
