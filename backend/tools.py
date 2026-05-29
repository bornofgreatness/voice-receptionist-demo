import json
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from backend.models import Appointment, AuditEvent


def check_safety_keywords(text: str, keywords: list[str]) -> bool:
    lower = text.lower()
    return any(k in lower for k in keywords)


def get_availability(practice_id: str, date_hint: str | None = None) -> dict:
    base = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
    if date_hint and "tomorrow" in date_hint.lower():
        base += timedelta(days=1)
    slots = [(base + timedelta(days=0, hours=h)).isoformat() for h in (0, 2, 4)]
    return {"practice_id": practice_id, "available_slots": slots}


def book_appointment(
    db: Session,
    *,
    call_id: str,
    practice_id: str,
    patient_name: str,
    phone: str,
    service: str,
    slot_iso: str,
) -> dict:
    existing = (
        db.query(Appointment)
        .filter(Appointment.call_id == call_id, Appointment.slot_iso == slot_iso)
        .first()
    )
    if existing:
        return {"status": "already_booked", "appointment_id": existing.id, "slot_iso": slot_iso}

    row = Appointment(
        call_id=call_id,
        practice_id=practice_id,
        patient_name=patient_name,
        phone=phone[-4:].rjust(len(phone), "*") if len(phone) > 4 else "****",
        service=service,
        slot_iso=slot_iso,
    )
    db.add(row)
    db.add(
        AuditEvent(
            call_id=call_id,
            event_type="appointment_booked",
            detail_redacted=json.dumps({"service": service, "slot": slot_iso}),
        )
    )
    db.commit()
    db.refresh(row)
    return {"status": "booked", "appointment_id": row.id, "slot_iso": slot_iso}


def escalate(db: Session, *, call_id: str, reason: str) -> dict:
    db.add(
        AuditEvent(
            call_id=call_id,
            event_type="escalated",
            detail_redacted=reason[:200],
        )
    )
    db.commit()
    return {"status": "escalated", "reason": reason}


def mock_eligibility(payer: str = "self-pay") -> dict:
    return {"eligible": True, "payer": payer, "copay_usd": 40, "note": "mock Availity response"}


def mock_patient_lookup(phone: str) -> dict:
    return {
        "resourceType": "Patient",
        "id": "demo-001",
        "telecom": [{"value": phone[-4:]}],
        "name": [{"text": "Demo Patient"}],
    }
