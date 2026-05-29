# ARIA Voice Receptionist Demo

Open-source demo of an **AI medical-practice receptionist**: scheduling, eligibility mock, safety escalation, multi-specialty config, and latency metrics.

Built to demonstrate production-style **voice agent orchestration** (FastAPI + tools + observability). **Not HIPAA certified** — fictional data only. See [docs/SECURITY.md](docs/SECURITY.md).

**Author:** Thomas Mo · [GitHub](https://github.com/bornofgreatness) · [LinkedIn](https://www.linkedin.com/in/thomas-mo-892b84411)

---

## Quick start (2 minutes)

```powershell
cd voice-receptionist-demo
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8080
```

Open **http://127.0.0.1:8080** — click **Start call**, try:

1. `I'd like to check availability tomorrow`
2. `My name is Jane Doe. Yes, book it.`
3. `I have chest pain` → escalation

API docs: **http://127.0.0.1:8080/docs**

Optional LLM: copy `.env.example` → `.env`, set `OPENAI_API_KEY` (otherwise rule-based replies work offline).

---

## Features

| Feature | Status |
|---------|--------|
| Multi-practice YAML config (spine + primary care) | Done |
| Tool calling: schedule / availability / escalate / eligibility | Done |
| Per-turn latency metrics (p50/p95) | Done |
| Audit event log (redacted) | Done |
| Web UI simulator | Done |
| Retell/Vapi webhook stubs | Done |
| Live PSTN + ElevenLabs | **You wire with provider keys** |

---

## Stack

- Python 3.11+, FastAPI, SQLAlchemy, SQLite (default)
- Optional: Postgres via `docker compose up -d`
- Voice providers: Retell / Vapi / LiveKit (webhook integration documented)

---

## Apply / interview talking points

> I built an ARIA-style receptionist demo: real tool orchestration, specialty configs, safety keyword escalation, mock FHIR/eligibility adapters, latency metrics, and HIPAA-oriented security design. Live telephony plugs in via Retell/Vapi webhooks—I can walk through the code and production trade-offs live.

**Demo URL (after deploy):** Railway/Fly/Render — add your public URL here.

**Loom:** Record 2 min: architecture + UI booking + metrics endpoint.

---

## License

MIT
