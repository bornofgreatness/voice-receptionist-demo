"""Webhook adapters for Retell / Vapi-style voice providers.

Point provider tool URLs to:
  POST /webhooks/voice/tool   — execute scheduling tools
  POST /webhooks/voice/event  — log call events + latency fields
"""

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.agent import process_turn, start_session
from backend.database import SessionLocal
from backend.practice_config import load_practice
from backend.settings import settings
from backend.tools import book_appointment, escalate, get_availability, mock_eligibility

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _verify_secret(x_webhook_secret: str | None) -> None:
    if x_webhook_secret != settings.webhook_secret:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")


class ToolRequest(BaseModel):
    call_id: str
    practice_id: str = "spine_demo"
    tool_name: str
    arguments: dict = {}


class VoiceEvent(BaseModel):
    call_id: str
    event: str
    transcript: str | None = None
    stt_ms: float = 0
    tts_ms: float = 0


@router.post("/voice/tool")
def voice_tool(
    body: ToolRequest,
    db: Session = Depends(get_db),
    x_webhook_secret: str | None = Header(default=None),
):
    _verify_secret(x_webhook_secret)
    practice = load_practice(body.practice_id)
    args = body.arguments

    if body.tool_name == "check_availability":
        return get_availability(body.practice_id, args.get("date_hint"))
    if body.tool_name == "book_appointment":
        return book_appointment(db, call_id=body.call_id, practice_id=body.practice_id, **args)
    if body.tool_name == "escalate":
        return escalate(db, call_id=body.call_id, reason=args.get("reason", "user_request"))
    if body.tool_name == "check_eligibility":
        return mock_eligibility(args.get("payer", "self-pay"))
    raise HTTPException(status_code=400, detail=f"Unknown tool: {body.tool_name}")


@router.post("/voice/event")
def voice_event(
    body: VoiceEvent,
    db: Session = Depends(get_db),
    x_webhook_secret: str | None = Header(default=None),
):
    _verify_secret(x_webhook_secret)
    if body.event == "user_turn" and body.transcript:
        session = start_session(db, settings.default_practice_id, channel="voice")
        session.id = body.call_id
        db.commit()
        return process_turn(
            db,
            session,
            body.transcript,
            stt_ms=body.stt_ms,
            tts_ms=body.tts_ms,
        )
    return {"ok": True, "event": body.event}
