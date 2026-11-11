"""Public (unauthenticated) endpoints — used by CSAT response links."""
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from fastapi import Depends

from app.core.database import get_db
from app.models.stage9_extras import CsatSurvey
from app.schemas.stage9_extras import CsatPublicRespond
from app.services.csat_service import record_response

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/csat/{token}")
async def get_csat(token: str, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(CsatSurvey).where(CsatSurvey.token == token))
    survey = result.scalar_one_or_none()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    return {
        "token": token,
        "already_responded": survey.responded_at is not None,
        "score": survey.score,
    }


@router.post("/csat/{token}")
async def respond_csat(token: str, body: CsatPublicRespond):
    survey = await record_response(token, body.score, body.feedback)
    if not survey:
        raise HTTPException(status_code=400, detail="Invalid token or already responded")
    return {"ok": True, "score": survey.score}
