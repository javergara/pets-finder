import { useEffect, useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { ApiError, guardarPerfilHogar, obtenerPerfilHogar } from '../api/client';
import type { PerfilHogarIn } from '../api/types';
import { PasosHogar } from '../components/PasosHogar';
import { ESTADO_INICIAL, type EstadoWizard, TOTAL_PASOS, pasoValido } from '../lib/hogar';
import { getActiveUserId, hasActiveUser } from '../lib/session';

const VOLVER_A = '/adoptar/mi-hogar';

// Cuestionario de hogar (AD-04): seis pasos cortos que alimentan la afinidad del
// deck. Port del `Cuestionario` de la era Adopta con tres cambios de fondo.
//
// ⚠️ **Es una escritura, así que el gate de cuenta va antes de leer ningún id.**
// `getActiveUserId()` cae al `DEMO_USER_ID = 1` cuando no hay nada en
// localStorage: sin gate, un visitante anónimo sobrescribiría el cuestionario de
// una persona real y le cambiaría el deck. Mismo patrón que `PublicarMascota`,
// pero aquí el daño no es publicar de más sino pisar datos ajenos.
//
// **El presupuesto es opcional de verdad**: `adopta-v1` lo arrancaba en 300000 y
// quien no tocara el campo terminaba mandando un dato que nunca dio. Vacío se
// manda `null` y `services/afinidad.py` degrada a solo-experiencia.
//
// **La preferencia de especie ofrece las tres**, "Otro animal" incluida:
// excluirla condenaría a cero de afinidad a toda mascota que no sea perro ni
// gato, y el catálogo las acepta desde AD-01.
//
// Nada de este archivo bloquea el deck: el cuestionario es opcional (`afinidad:
// null` sin él, decisión de AD-03) y por eso no existe ningún `RequiereHogar`.

export function CuestionarioHogar() {
  const navigate = useNavigate();
  const [paso, setPaso] = useState(1);
  const [estado, setEstado] = useState<EstadoWizard>(ESTADO_INICIAL);
  const [error, setError] = useState<string | null>(null);
  const [guardando, setGuardando] = useState(false);
  const conCuenta = hasActiveUser();

  useEffect(() => {
    // Sin cuenta no se pide nada: el id sería el del usuario demo y estaríamos
    // leyendo (y luego pisando) el hogar de otra persona.
    if (!conCuenta) return;
    const userId = getActiveUserId();
    let vigente = true;
    obtenerPerfilHogar(userId, userId)
      .then((perfil) => {
        if (!vigente || perfil === null) return;
        setEstado({
          vivienda: perfil.vivienda,
          espacio_exterior: perfil.espacio_exterior,
          personas_en_casa: perfil.personas_en_casa,
          tiene_ninos: perfil.tiene_ninos,
          tiene_otros_perros: perfil.tiene_otros_perros,
          tiene_otros_gatos: perfil.tiene_otros_gatos,
          horas_fuera_dia: perfil.horas_fuera_dia,
          experiencia_previa: perfil.experiencia_previa,
          presupuesto_mensual_cop: perfil.presupuesto_mensual_cop,
          preferencia_especies: perfil.preferencia_especies,
          preferencia_tamanos: perfil.preferencia_tamanos,
          preferencia_energia: perfil.preferencia_energia,
        });
      })
      .catch(() => {
        // Un fallo al precargar no puede bloquear el cuestionario: se contesta
        // desde cero, que es el camino de la mayoría.
      });
    return () => {
      vigente = false;
    };
  }, [conCuenta]);

  if (!conCuenta) {
    return <Navigate to={`/registro?volver=${encodeURIComponent(VOLVER_A)}`} replace />;
  }

  async function guardar() {
    setError(null);
    setGuardando(true);
    try {
      const payload: PerfilHogarIn = {
        user_id: getActiveUserId(),
        vivienda: estado.vivienda!,
        espacio_exterior: estado.espacio_exterior!,
        personas_en_casa: estado.personas_en_casa,
        tiene_ninos: estado.tiene_ninos!,
        tiene_otros_perros: estado.tiene_otros_perros!,
        tiene_otros_gatos: estado.tiene_otros_gatos!,
        horas_fuera_dia: estado.horas_fuera_dia,
        experiencia_previa: estado.experiencia_previa!,
        presupuesto_mensual_cop: estado.presupuesto_mensual_cop,
        preferencia_especies: estado.preferencia_especies,
        preferencia_tamanos: estado.preferencia_tamanos,
        preferencia_energia: estado.preferencia_energia!,
      };
      await guardarPerfilHogar(getActiveUserId(), payload);
      navigate('/adoptar/descubrir');
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : 'No pudimos guardar tus respuestas. Intenta de nuevo.',
      );
    } finally {
      setGuardando(false);
    }
  }

  function avanzar() {
    if (paso < TOTAL_PASOS) setPaso((actual) => actual + 1);
    else void guardar();
  }

  return (
    <div className="mx-auto mt-6 w-full max-w-lg px-4 pb-16">
      <h1 className="font-display text-2xl text-ink">Cuéntanos de tu hogar</h1>
      <p className="mt-1 text-sm text-ink-soft">
        Son seis preguntas cortas. Con ellas calculamos qué tanto encaja cada mascota contigo — y te
        decimos por qué. Puedes cambiarlas cuando quieras.
      </p>

      <div className="mt-5">
        <div className="h-2 w-full overflow-hidden rounded-full bg-surface-alt">
          <div
            className="h-full rounded-full bg-forest transition-all"
            style={{ width: `${(paso / TOTAL_PASOS) * 100}%` }}
          />
        </div>
        <p className="mt-2 font-mono text-xs tracking-wide text-muted-2 uppercase">
          Paso {paso} de {TOTAL_PASOS}
        </p>
      </div>

      <PasosHogar paso={paso} estado={estado} setEstado={setEstado} />

      {error && (
        <p role="alert" className="mt-6 rounded-xl bg-surface-alt p-3 text-sm text-ink">
          {error}
        </p>
      )}

      <div className="mt-8 flex items-center justify-between gap-3">
        {paso > 1 ? (
          <button
            type="button"
            onClick={() => setPaso((actual) => actual - 1)}
            className="rounded-full border border-line px-5 py-3 font-medium text-ink-soft"
          >
            Atrás
          </button>
        ) : (
          <span />
        )}
        <button
          type="button"
          onClick={avanzar}
          disabled={!pasoValido(paso, estado) || guardando}
          className="rounded-full bg-forest px-6 py-3 font-medium text-bg disabled:opacity-60"
        >
          {paso === TOTAL_PASOS ? (guardando ? 'Guardando…' : 'Terminar') : 'Continuar'}
        </button>
      </div>
    </div>
  );
}
