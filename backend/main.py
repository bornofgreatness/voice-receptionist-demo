from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.agent import process_turn, start_session
from backend.database import SessionLocal, init_db
from backend.models import Appointment, TurnMetric
from backend.practice_config import list_practices, load_practice
from backend.settings import settings
from backend.webhooks import router as webhooks_router

app = FastAPI(
    title="ARIA Voice Receptionist Demo",
    description="HIPAA-oriented design demo — fictional patients only",
    version="0.1.0",
)

STATIC = Path(__file__).resolve().parents[1] / "static"
app.mount("/static", StaticFiles(directory=STATIC), name="static")
app.include_router(webhooks_router)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/health")
def health():
    return {"status": "ok", "practices": list_practices()}


class StartBody(BaseModel):
    practice_id: str = "spine_demo"


class MessageBody(BaseModel):
    session_id: str
    text: str


@app.post("/api/simulate/start")
def simulate_start(body: StartBody, db: Session = Depends(get_db)):
    try:
        load_practice(body.practice_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    session = start_session(db, body.practice_id, channel="simulate")
    practice = load_practice(body.practice_id)
    greeting = (
        f"Thank you for calling {practice['practice_name']}. "
        f"I'm the AI receptionist. How can I help you today?"
    )
    return {"session_id": session.id, "practice_id": body.practice_id, "reply": greeting}


@app.post("/api/simulate/message")
def simulate_message(body: MessageBody, db: Session = Depends(get_db)):
    from backend.models import CallSession

    session = db.get(CallSession, body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return process_turn(db, session, body.text)


@app.get("/api/metrics")
def metrics(db: Session = Depends(get_db)):
    rows = db.query(TurnMetric).all()
    if not rows:
        return {"turns": 0, "p50_total_ms": 0, "p95_total_ms": 0}
    totals = sorted(r.total_ms for r in rows)
    n = len(totals)
    p50 = totals[n // 2]
    p95 = totals[int(n * 0.95) - 1] if n > 1 else totals[-1]
    return {
        "turns": n,
        "p50_total_ms": round(p50, 1),
        "p95_total_ms": round(p95, 1),
        "avg_llm_ms": round(sum(r.llm_ms for r in rows) / n, 1),
        "note": "Simulated STT/TTS latency included; plug Retell/Vapi for live voice",
    }


@app.get("/api/appointments")
def appointments(db: Session = Depends(get_db)):
    rows = db.query(Appointment).order_by(Appointment.id.desc()).limit(20).all()
    return [
        {
            "id": r.id,
            "practice_id": r.practice_id,
            "patient_name": r.patient_name,
            "phone_redacted": r.phone,
            "service": r.service,
            "slot_iso": r.slot_iso,
        }
        for r in rows
    ]


@app.get("/api/practices/{practice_id}")
def practice_detail(practice_id: str):
    return load_practice(practice_id)
