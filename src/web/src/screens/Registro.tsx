import { type FormEvent, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ApiError, registrarUsuario } from '../api/client';
import { setActiveUserId } from '../lib/session';

// Solo rutas internas: un `?volver=` con URL absoluta externa se ignora.
function destinoSeguro(volver: string | null): string {
  return volver && volver.startsWith('/') ? volver : '/';
}

export function Registro() {
  const [nombre, setNombre] = useState('');
  const [email, setEmail] = useState('');
  const [ciudad, setCiudad] = useState('Armenia');
  const [barrio, setBarrio] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!nombre.trim() || !email.trim() || !ciudad.trim()) {
      setError('Nombre, correo y ciudad son obligatorios.');
      return;
    }

    setError(null);
    setEnviando(true);
    try {
      const perfil = await registrarUsuario({
        nombre: nombre.trim(),
        email: email.trim(),
        ciudad: ciudad.trim(),
        barrio: barrio.trim() || undefined,
      });
      setActiveUserId(perfil.id);
      navigate(destinoSeguro(searchParams.get('volver')));
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : 'No pudimos crear tu cuenta. Intenta de nuevo.',
      );
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="mx-auto mt-8 max-w-md p-6">
      <h1 className="mb-2 font-display text-2xl text-ink">Crea tu cuenta</h1>
      <p className="mb-6 text-sm text-muted">
        Solo necesitamos unos datos para poder ligar tus reportes a ti y que puedas marcarlos como
        reunidos cuando tu mascota vuelva a casa.
      </p>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div>
          <label htmlFor="registro-nombre" className="text-sm font-medium text-ink-soft">
            Nombre
          </label>
          <input
            id="registro-nombre"
            type="text"
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
          />
        </div>

        <div>
          <label htmlFor="registro-email" className="text-sm font-medium text-ink-soft">
            Correo
          </label>
          <input
            id="registro-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
          />
        </div>

        <div>
          <label htmlFor="registro-ciudad" className="text-sm font-medium text-ink-soft">
            Ciudad
          </label>
          <input
            id="registro-ciudad"
            type="text"
            value={ciudad}
            onChange={(e) => setCiudad(e.target.value)}
            className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
          />
        </div>

        <div>
          <label htmlFor="registro-barrio" className="text-sm font-medium text-ink-soft">
            Barrio (opcional)
          </label>
          <input
            id="registro-barrio"
            type="text"
            value={barrio}
            onChange={(e) => setBarrio(e.target.value)}
            className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
          />
        </div>

        {error && <p className="text-sm text-danger">{error}</p>}

        <button
          type="submit"
          disabled={enviando}
          className="mt-2 rounded-full bg-forest px-4 py-3 font-medium text-bg disabled:opacity-60"
        >
          {enviando ? 'Creando cuenta…' : 'Continuar'}
        </button>
      </form>
    </div>
  );
}
