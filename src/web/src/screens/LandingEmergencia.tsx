import { Link } from 'react-router-dom';

// Versión mínima de la landing de emergencia (feature 01). Los CTAs gigantes,
// los accesos al listado/mapa y la franja de reencuentros llegan en las
// features 04 y 09.
export function LandingEmergencia() {
  return (
    <div className="mx-auto flex min-h-svh max-w-3xl flex-col items-center justify-center gap-6 p-6 text-center">
      <p className="font-mono text-sm text-muted">
        Eje Cafetero · Colombia · Sismo del 10 de agosto
      </p>
      <h1 className="font-display text-5xl text-ink">
        Reencuentro: ayudemos a cada mascota a volver a casa.
      </h1>
      <p className="max-w-xl text-ink-soft">
        Reporta una mascota perdida o una que encontraste entre los escombros, y la comunidad te
        ayuda a reunirla con su familia.
      </p>
      <div className="flex flex-wrap justify-center gap-4">
        <Link
          to="/reportar/perdido"
          className="rounded-full bg-danger px-6 py-3 font-medium text-bg"
        >
          Perdí a mi mascota
        </Link>
        <Link
          to="/reportar/encontrado"
          className="rounded-full bg-forest px-6 py-3 font-medium text-bg"
        >
          Encontré una mascota
        </Link>
      </div>
    </div>
  );
}
