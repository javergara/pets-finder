import { Link } from 'react-router-dom';
import { mediaUrl } from '../api/client';
import type { Mascota } from '../api/types';
import {
  ETIQUETA_ESTADO_MASCOTA,
  ETIQUETA_SEXO,
  ETIQUETA_TAMANO_MASCOTA,
  edadLegible,
  tituloMascota,
} from '../lib/adopcion';

// Tarjeta de una mascota en adopción para la rejilla de /adoptar.
//
// Es un componente aparte de `ReporteCard` a propósito: aquella está soldada al
// dominio de emergencia (perdido/encontrado, situación, fecha del evento,
// "Reunida 💚") y la usan cinco pantallas en producción; generalizarla pedía un
// tipo unión con narrowing o una docena de props opcionales. Lo que sí se
// comparte —copiado clase por clase— es el esqueleto visual, para que las dos
// rejillas se lean como un mismo sistema: mismo radio y borde, foto 4:3 con
// `loading="lazy"` y `object-contain` (feature 35: la mascota completa, sin
// recortes, para reconocerla sin entrar), título display, historia a dos
// líneas, chips redondos y pie separado por una línea suave.
//
// Paleta: el rojo de emergencia está reservado en toda la app a "perdido" y no
// entra en este módulo; aquí solo hay `forest` y `ochre` (la regla, con el
// nombre del token, está en `ETIQUETA_ESTADO_MASCOTA` de lib/adopcion.ts).

// Tope de chips visibles. Con más de tres, la fila salta a dos líneas y a 360px
// desplaza el pie de la tarjeta; el resto de los tags se ven en la ficha.
const MAX_TAGS = 3;

export function MascotaCard({ mascota }: { mascota: Mascota }) {
  const titulo = tituloMascota(mascota);
  const estado = ETIQUETA_ESTADO_MASCOTA[mascota.estado];
  const foto = mascota.fotos[0];
  const lugar = mascota.zona === 'Otro' ? mascota.ciudad_texto ?? 'Colombia' : mascota.zona;
  const edadYRaza = [edadLegible(mascota.edad_meses), mascota.raza].filter(Boolean).join(' · ');

  return (
    <Link
      to={`/adoptar/mascota/${mascota.id}`}
      className="flex flex-col overflow-hidden rounded-[22px] border border-line bg-surface transition-shadow hover:shadow-[0_18px_40px_-28px_rgba(27,26,23,.5)]"
    >
      <div className="relative aspect-4/3 bg-surface-alt">
        {foto ? (
          <img
            src={mediaUrl(foto)}
            alt={`Foto de ${titulo}, en adopción`}
            loading="lazy"
            className="absolute inset-0 h-full w-full object-contain"
          />
        ) : (
          // Sin foto la tarjeta conserva su alto (el 4:3 lo fija el contenedor):
          // la rejilla no se descuadra y el hueco se explica en vez de quedar en
          // blanco. Publicar sin foto es raro pero posible desde la API.
          <span className="absolute inset-0 flex items-center justify-center text-sm text-muted">
            Sin foto todavía
          </span>
        )}
        <div className="relative flex items-start gap-2 p-3">
          <span
            className={`rounded-md px-3 py-1 font-mono text-xs tracking-wide text-bg ${estado.color}`}
          >
            {estado.texto}
          </span>
          {/* En AD-01 `afinidad` siempre viaja en null: la calcula AD-03 y solo
              para quien ya tiene perfil de hogar. */}
          {mascota.afinidad && (
            <span className="ml-auto rounded-full bg-forest px-3 py-1 font-mono text-xs text-bg">
              {mascota.afinidad.score}% afín
            </span>
          )}
        </div>
      </div>

      <div className="border-t border-line p-4">
        <h3 className="font-display text-xl text-ink">{titulo}</h3>
        <p className="text-sm text-forest">{edadYRaza}</p>
        <p className="mt-1 line-clamp-2 text-sm text-muted">{mascota.historia}</p>
        {mascota.tags.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {mascota.tags.slice(0, MAX_TAGS).map((tag) => (
              <span
                key={tag}
                className="rounded-full bg-forest-tint px-2.5 py-1 text-xs text-forest"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
        <div className="mt-3 flex items-center justify-between gap-2 border-t border-line-soft pt-3 text-xs text-muted">
          <span>{lugar}</span>
          <span>
            {ETIQUETA_SEXO[mascota.sexo]} · {ETIQUETA_TAMANO_MASCOTA[mascota.tamano]}
          </span>
        </div>
      </div>
    </Link>
  );
}
