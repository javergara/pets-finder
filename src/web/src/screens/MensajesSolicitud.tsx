import { useNavigate, useParams } from 'react-router-dom';
import { ChatHilo } from '../components/ChatHilo';
import { DEMO_SHELTER_ID } from '../lib/constants';

export function MensajesSolicitud() {
  const { matchId } = useParams<{ matchId: string }>();
  const navigate = useNavigate();

  if (!matchId) return null;

  return (
    <div className="pb-6">
      <div className="mx-auto max-w-2xl px-6 pt-6">
        <button type="button" onClick={() => navigate(-1)} className="text-sm text-muted">
          ← Volver
        </button>
      </div>
      <ChatHilo
        matchId={Number(matchId)}
        rol="refugio"
        participantId={DEMO_SHELTER_ID}
        mostrarRespuestasRapidas={false}
      />
    </div>
  );
}
