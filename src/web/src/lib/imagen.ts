// Compresión de fotos en el navegador antes de subirlas (feature 19): una foto
// de celular moderno pesa 3-5 MB y el listado la descarga completa en cada
// tarjeta — reescalar a un lado máximo razonable y recomprimir a JPEG recorta
// eso a ~100-300 KB sin pérdida visible a los tamaños en que se muestra.

export const LADO_MAXIMO = 1280;
export const CALIDAD_JPEG = 0.8;

/** Devuelve una versión reescalada (máx `LADO_MAXIMO` px) y recomprimida a JPEG
 * del archivo, o el archivo original tal cual si la compresión no aplica: el
 * navegador no soporta canvas/createImageBitmap, el formato no se puede
 * decodificar, o el resultado no queda más pequeño que el original. El backend
 * valida tipo y tamaño igual en ambos casos. */
export async function comprimirImagen(archivo: File): Promise<File> {
  try {
    const bitmap = await createImageBitmap(archivo);
    const escala = Math.min(1, LADO_MAXIMO / Math.max(bitmap.width, bitmap.height));
    const canvas = document.createElement('canvas');
    canvas.width = Math.round(bitmap.width * escala);
    canvas.height = Math.round(bitmap.height * escala);

    const contexto = canvas.getContext('2d');
    if (!contexto) return archivo;
    contexto.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    bitmap.close();

    const blob = await new Promise<Blob | null>((resolve) =>
      canvas.toBlob(resolve, 'image/jpeg', CALIDAD_JPEG),
    );
    if (!blob || blob.size >= archivo.size) return archivo;

    const nombre = archivo.name.replace(/\.[^.]+$/, '') + '.jpg';
    return new File([blob], nombre, { type: 'image/jpeg' });
  } catch {
    return archivo;
  }
}
