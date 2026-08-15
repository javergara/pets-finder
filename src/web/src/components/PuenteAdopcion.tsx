import { Link } from 'react-router-dom';
import type { Reporte } from '../api/types';
import { getActiveUserId, hasActiveUser } from '../lib/session';

// El puente entre los dos dominios (AD-02, A3): un encontrado que nadie reclamó
// puede pasar a adopción, y el reporte queda enseñando adónde fue.
//
// Devuelve `null` en el caso común —la inmensa mayoría de los reportes no son
// candidatos— y decide todo aquí dentro para que `ReporteDetalle`, que ya son
// 681 líneas, crezca solo tres. Las dos caras del puente tienen público
// distinto a propósito:
//
// - La franja de "ya está en adopción" la ve **cualquiera**, también quien llega
//   por un link compartido: es información pública y sin ella el rastro se corta.
// - El CTA lo ve **solo el autor**, y solo mientras el reporte sigue activo. Con
//   la mascota ya reunida con su familia, ofrecer darla en adopción sería una
//   invitación al desastre; y si solo la vieron (`situacion: 'vista'`), no la
//   tiene nadie, así que el backend responde 422.
//
// ⚠️ `hasActiveUser()` no es decorativo: `getActiveUserId()` cae al DEMO_USER_ID
// (1) sin cuenta, así que sin ese guard cualquier visitante vería el CTA sobre
// los reportes del usuario 1 en producción.
//
// Paleta: `forest` para lo que ya pasó, `ochre` para la invitación. `danger`
// está reservado a "perdido" y no entra en el módulo de adopción.

const CLASE_BOTON = 'inline-block rounded-full bg-forest px-5 py-2 font-medium text-bg';

export function PuenteAdopcion({ reporte }: { reporte: Reporte }) {
  if (reporte.adopcion_pet_id) {
    return (
      <section className="rounded-2xl border border-forest-tint-line bg-forest-tint p-4">
        <p className="mb-3 text-sm text-ink-soft">
          <span className="font-medium text-ink">Ahora en adopción.</span> Nadie la reclamó, así que
          busca una familia nueva.
        </p>
        <Link to={`/adoptar/mascota/${reporte.adopcion_pet_id}`} className={CLASE_BOTON}>
          Ver su ficha de adopción
        </Link>
      </section>
    );
  }

  const esAutor = hasActiveUser() && reporte.user_id === getActiveUserId();
  if (
    reporte.tipo !== 'encontrado' ||
    reporte.situacion !== 'conmigo' ||
    reporte.estado !== 'activo' ||
    !esAutor
  ) {
    return null;
  }

  return (
    <section className="rounded-2xl border border-ochre/40 bg-ochre/10 p-4">
      <p className="mb-3 text-sm text-ink-soft">
        ¿Nadie la reclamó? Puedes darla en adopción para que encuentre una familia. Seguimos
        buscando a la suya: el reporte no se borra.
      </p>
      <Link to={`/adoptar/publicar?reporte=${reporte.id}`} className={CLASE_BOTON}>
        Darla en adopción
      </Link>
    </section>
  );
}
