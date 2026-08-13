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
/** Área de recorte en píxeles de la imagen original (contrato de react-easy-crop). */
export type AreaRecorte = { x: number; y: number; width: number; height: number };

/** Devuelve el recorte `area` del archivo como JPEG, o el archivo original tal
 * cual si el área cubre la imagen completa (subir "sin recortar" no debe
 * re-codificar) o si el navegador no puede decodificar/recortar. La compresión
 * a tamaño de subida la hace después `comprimirImagen`, por eso aquí la calidad
 * es alta: recortar no debe degradar dos veces. */
export async function recortarImagen(archivo: File, area: AreaRecorte): Promise<File> {
  try {
    const bitmap = await createImageBitmap(archivo);
    const cubreTodo =
      area.x <= 0 && area.y <= 0 && area.width >= bitmap.width && area.height >= bitmap.height;
    if (cubreTodo || area.width < 1 || area.height < 1) {
      bitmap.close();
      return archivo;
    }

    const canvas = document.createElement('canvas');
    canvas.width = Math.round(area.width);
    canvas.height = Math.round(area.height);
    const contexto = canvas.getContext('2d');
    if (!contexto) return archivo;
    contexto.drawImage(
      bitmap,
      area.x,
      area.y,
      area.width,
      area.height,
      0,
      0,
      canvas.width,
      canvas.height,
    );
    bitmap.close();

    const blob = await new Promise<Blob | null>((resolve) =>
      canvas.toBlob(resolve, 'image/jpeg', 0.92),
    );
    if (!blob) return archivo;

    const nombre = archivo.name.replace(/\.[^.]+$/, '') + '.jpg';
    return new File([blob], nombre, { type: 'image/jpeg' });
  } catch {
    return archivo;
  }
}

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
