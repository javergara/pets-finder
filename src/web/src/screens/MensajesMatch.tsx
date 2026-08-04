import { useNavigate, useParams } from 'react-router-dom';
import { ChatHilo } from '../components/ChatHilo';
import { getActiveUserId } from '../lib/session';

export function MensajesMatch() {
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
        rol="adoptante"
        participantId={getActiveUserId()}
        mostrarRespuestasRapidas={true}
      />
    </div>
  );
}
