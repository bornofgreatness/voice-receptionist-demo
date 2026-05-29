# Architecture

```
Caller (PSTN)
    → Twilio / provider SIP
        → Retell | Vapi | LiveKit (voice platform)
            → STT → LLM + tool calls → TTS
                → This API (FastAPI)
                    → Postgres (sessions, appointments, metrics, audit)
                    → Mock EHR / eligibility adapters
```

## This demo implements

- FastAPI tool layer (`book_appointment`, `check_availability`, `escalate`, `check_eligibility`)
- Multi-tenant practice config (`config/*.yaml`)
- Text simulator with latency fields (STT/TTS placeholders)
- Webhook stubs for voice providers (`/webhooks/voice/*`)

## Connect live voice (next step)

1. Create Retell or Vapi agent
2. Set tool webhook URL: `https://<your-host>/webhooks/voice/tool`
3. Header: `X-Webhook-Secret: <WEBHOOK_SECRET>`
4. Map tools to: `check_availability`, `book_appointment`, `escalate`, `check_eligibility`

## Latency budget (target production)

| Segment | Target |
|---------|--------|
| STT | ~150–250ms |
| LLM + tools | ~200–350ms |
| TTS | ~150–200ms |
| **Total** | **< 700ms** (Aispire target ~600ms) |

Simulator defaults: STT 120ms + TTS 180ms + LLM measured.
