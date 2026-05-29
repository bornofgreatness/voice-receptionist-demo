import json
import re
import time
import uuid
from typing import Any

import httpx
from sqlalchemy.orm import Session

from backend.models import CallSession, TurnMetric
from backend.practice_config import load_practice
from backend.settings import settings
from backend.tools import (
    book_appointment,
    check_safety_keywords,
    escalate,
    get_availability,
    mock_eligibility,
)


def _session_state(raw: str) -> dict:
    try:
        return json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {}


def start_session(db: Session, practice_id: str, channel: str = "simulate") -> CallSession:
    sid = str(uuid.uuid4())[:12]
    row = CallSession(id=sid, practice_id=practice_id, channel=channel, state_json="{}")
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _rule_based_turn(
    db: Session, practice: dict, state: dict, user_text: str, session: CallSession
) -> tuple[str, str | None, dict]:
    lower = user_text.lower()
    if check_safety_keywords(user_text, practice["safety_keywords"]):
        escalate(db, call_id=session.id, reason="safety_keyword")
        session.escalated = 1
        return practice["escalation_message"], "escalate", {"reason": "safety_keyword"}

    if "availability" in lower or "slot" in lower or "when" in lower:
        avail = get_availability(practice["practice_id"], lower)
        state["last_slots"] = avail["available_slots"]
        slot = avail["available_slots"][0]
        return (
            f"I have {slot} available for {practice['services'][0]}. Should I book that for you?",
            "check_availability",
            avail,
        )

    name_match = re.search(r"my name is (\w+(?:\s+\w+)?)", lower)
    if name_match:
        state["patient_name"] = name_match.group(1).title()

    phone_match = re.search(r"(\d{10,})", user_text.replace("-", ""))
    if phone_match:
        state["phone"] = phone_match.group(1)

    if any(w in lower for w in ("book", "schedule", "appointment", "yes")) and state.get("last_slots"):
        slot = state["last_slots"][0]
        result = book_appointment(
            db,
            call_id=session.id,
            practice_id=practice["practice_id"],
            patient_name=state.get("patient_name", "Guest Caller"),
            phone=state.get("phone", "5550000000"),
            service=practice["services"][0],
            slot_iso=slot,
        )
        return (
            f"You're booked for {practice['services'][0]} on {slot}. Anything else?",
            "book_appointment",
            result,
        )

    if "insurance" in lower or "eligibility" in lower:
        el = mock_eligibility()
        return (
            f"Eligibility check: {el['payer']}, copay about {el['copay_usd']} USD.",
            "check_eligibility",
            el,
        )

    return (
        "I can help schedule or check availability. May I have your name and preferred day?",
        None,
        {},
    )


def _openai_turn(practice: dict, user_text: str) -> tuple[str, str | None, dict]:
    system = (
        f"You are ARIA-demo receptionist for {practice['practice_name']} ({practice['specialty']}). "
        "Be brief. No medical advice. Offer scheduling."
    )
    t0 = time.perf_counter()
    with httpx.Client(timeout=30) as client:
        r = client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_text},
                ],
                "temperature": 0.3,
            },
        )
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
    return content, None, {"llm_ms": (time.perf_counter() - t0) * 1000}


def process_turn(
    db: Session,
    session: CallSession,
    user_text: str,
    *,
    stt_ms: float = 120,
    tts_ms: float = 180,
) -> dict[str, Any]:
    practice = load_practice(session.practice_id)
    state = _session_state(session.state_json)
    state["call_id"] = session.id

    t0 = time.perf_counter()
    if settings.openai_api_key and not check_safety_keywords(user_text, practice["safety_keywords"]):
        reply, tool, extra = _openai_turn(practice, user_text)
    else:
        reply, tool, extra = _rule_based_turn(db, practice, state, user_text, session)

    session.state_json = json.dumps(state)
    db.add(session)

    llm_ms = extra.get("llm_ms", (time.perf_counter() - t0) * 1000)
    total_ms = stt_ms + llm_ms + tts_ms

    db.add(
        TurnMetric(
            call_id=session.id,
            stt_ms=stt_ms,
            llm_ms=llm_ms,
            tts_ms=tts_ms,
            total_ms=total_ms,
            tool_name=tool,
        )
    )
    db.commit()

    return {
        "call_id": session.id,
        "reply": reply,
        "tool": tool,
        "latency_ms": {"stt": stt_ms, "llm": round(llm_ms, 1), "tts": tts_ms, "total": round(total_ms, 1)},
        "state": state,
        "escalated": bool(session.escalated),
    }
