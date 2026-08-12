import { Link } from 'react-router-dom';

// Landing de emergencia: dos caminos gigantes, decididos en dos segundos.
// La franja de reencuentros (contador + galería) llega con la feature 09.
export function LandingEmergencia() {
  return (
    <div className="mx-auto flex min-h-svh max-w-4xl flex-col items-center justify-center gap-8 p-6 text-center">
      <p className="font-mono text-sm uppercase tracking-wider text-muted">
        Eje Cafetero · Colombia · Sismo del 10 de agosto de 2026
      </p>
      <h1 className="max-w-2xl font-display text-5xl text-ink sm:text-6xl">
        Ayudemos a cada mascota a volver a casa.
      </h1>
      <p className="max-w-xl text-lg text-ink-soft">
        Reporta una mascota perdida o una que encontraste entre los escombros. La comunidad busca
        contigo: cada reporte con foto y ubicación acerca un reencuentro.
      </p>

      <div className="flex w-full max-w-2xl flex-col gap-4 sm:flex-row">
        <Link
          to="/reportar/perdido"
          className="flex-1 rounded-2xl bg-danger px-8 py-6 text-xl font-medium text-bg shadow-sm"
        >
          Perdí a mi mascota
        </Link>
        <Link
          to="/reportar/encontrado"
          className="flex-1 rounded-2xl bg-forest px-8 py-6 text-xl font-medium text-bg shadow-sm"
        >
          Encontré una mascota
        </Link>
      </div>

      <div className="flex flex-wrap items-center justify-center gap-6 text-sm">
        <Link to="/reportes" className="font-medium text-forest underline-offset-4 hover:underline">
          Ver todos los reportes
        </Link>
        <Link to="/mapa" className="font-medium text-forest underline-offset-4 hover:underline">
          Ver el mapa
        </Link>
      </div>

      <p className="max-w-md text-xs text-muted">
        Armenia · Pereira · Manizales · Cali · Quibdó · Bogotá — y cualquier lugar de Colombia. Sin
        costo, sin fricción: solo tu nombre y un teléfono de contacto.
      </p>
    </div>
  );
}
