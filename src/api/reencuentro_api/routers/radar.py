"""Radar de reencuentros (feature 43): la corrida diaria que avisa coincidencias.

Lo dispara Vercel Cron (GET con `Authorization: Bearer CRON_SECRET`, que Vercel
añade solo si la env var existe). Sin `CRON_SECRET` configurado el endpoint está
apagado (503): nunca un cron público abierto. El envío real de correos depende
de Resend (ADR 0011) — sin credenciales, la corrida registra igual las parejas
y los correos son no-op con log.
"""

import os

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.radar_aviso import RadarAviso
from ..models.report import Report
from ..models.suscripcion import Suscripcion
from ..models.user import User
from ..services.db import get_session
from ..services.notificaciones import notificar_coincidencia
from ..services.radar import parejas_a_avisar

router = APIRouter(prefix="/api/radar", tags=["radar"])


class ResumenRadar(BaseModel):
    perdidos_activos: int
    parejas_nuevas: int
    correos_enviados: int


def _autorizar(authorization: str | None) -> None:
    secreto = os.environ.get("CRON_SECRET", "").strip()
    if not secreto:
        raise HTTPException(503, "El radar está apagado: falta configurar CRON_SECRET")
    if authorization != f"Bearer {secreto}":
        raise HTTPException(401, "Token del radar inválido")


@router.get("", response_model=ResumenRadar)
@router.post("", response_model=ResumenRadar)
def correr_radar(
    authorization: str | None = Header(default=None),
    session: Session = Depends(get_session),
) -> ResumenRadar:
    _autorizar(authorization)

    activos = session.execute(select(Report).where(Report.estado == "activo")).scalars().all()
    perdidos = [r for r in activos if r.tipo == "perdido"]
    ya_avisadas = {
        (a.report_id, a.candidato_id) for a in session.execute(select(RadarAviso)).scalars()
    }

    parejas = parejas_a_avisar(perdidos, list(activos), ya_avisadas)

    correos = 0
    for perdido, candidato, _distancia, razones in parejas:
        # Autor + suscritos del reporte perdido, sin correos repetidos.
        destinatarios: list[str] = []
        autor = session.get(User, perdido.user_id)
        if autor is not None:
            destinatarios.append(autor.email.strip().lower())
        for s in session.execute(
            select(Suscripcion).where(Suscripcion.report_id == perdido.id)
        ).scalars():
            if s.email not in destinatarios:
                destinatarios.append(s.email)

        correos += notificar_coincidencia(perdido, candidato, razones, destinatarios)
        session.add(RadarAviso(report_id=perdido.id, candidato_id=candidato.id))

    session.commit()
    return ResumenRadar(
        perdidos_activos=len(perdidos),
        parejas_nuevas=len(parejas),
        correos_enviados=correos,
    )
