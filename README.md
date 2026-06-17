# MailGuard AI Ultra

> AI Email Intelligence + WhatsApp Voice Assistant for Gmail & Outlook.

MailGuard AI Ultra continuously monitors inboxes, deeply understands every email with
LLM-powered analysis, detects fraud and phishing, and pushes rich WhatsApp alerts
plus natural Hindi / English / Hinglish AI voice notes — in real time.

---

## ✨ Highlights

- 🔌 **Gmail + Outlook** OAuth2 ingestion with real-time push (`Pub/Sub`, webhooks, polling)
- 🧠 **AI Email Intelligence** — GPT-4o + LangChain extracts sender, intent, priority,
  deadlines, invoices, OTPs, interview calls, action items, and a 0-100 confidence score
- 🛡️ **Phishing & Fraud Detection** — threat scoring + reasoning, link & domain analysis
- 🔊 **Hindi AI Voice Assistant** — OpenAI TTS with male / female / news-reader /
  personal-assistant personas, auto-selected per email priority
- 💬 **WhatsApp Business API + Twilio fallback** — rich text summary + MP3 voice note
- 🔍 **RAG + Vector Search** — ChromaDB-backed semantic search across your entire inbox
- 📊 **Enterprise Dashboard** — Next.js + Tailwind analytics, fraud center, voice logs
- 🌅 **Daily Morning Briefing + Evening Summary** — automatic Hindi voice reports
- 🔮 **Predictive AI** — missed deadlines, upcoming payments, interview probability
- 🧪 **Production Grade** — FastAPI, PostgreSQL, Redis, Celery, Docker, Kubernetes, JWT,
  AES encryption, audit logs, RBAC, rate limiting

---

## 🏗 Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                       Gmail / Outlook APIs                       │
└────────────────┬────────────────────────────────┬────────────────┘
                 │ Pub/Sub / Webhooks / Polling   │
                 ▼                                ▼
       ┌─────────────────────┐        ┌─────────────────────┐
       │  Connectors (async) │        │   Celery Workers    │
       └──────────┬──────────┘        └──────────▲──────────┘
                  │ raw email                   │ tasks
                  ▼                             │
       ┌─────────────────────┐                  │
       │  AI Analyzer (LLM)  │ ─── embeddings ─┘
       │  + Fraud Detector   │
       └──────────┬──────────┘
                  │ structured result
                  ▼
       ┌─────────────────────┐    ┌─────────────────────┐
       │  ChromaDB / Postgres│    │  TTS Service (OpenAI)│
       └──────────┬──────────┘    └──────────┬──────────┘
                  │                          │ MP3 / OGG
                  ▼                          ▼
       ┌─────────────────────────────────────────────────┐
       │      WhatsApp Business API + Twilio fallback    │
       └─────────────────────────────────────────────────┘
```

---

## 📦 Repository Layout

```
mailguard-ai-ultra/
├── backend/             FastAPI service, workers, AI, TTS, WhatsApp
├── frontend/            Next.js dashboard
├── infrastructure/      Docker, Kubernetes, Nginx
├── .github/workflows/   CI/CD pipelines
├── docs/                API, architecture, security, deployment
└── scripts/             Operational scripts
```

---

## 🚀 Quick Start (Local Dev)

```bash
# 1. Copy env template
cp .env.example .env

# 2. Start everything (Postgres, Redis, API, worker, frontend)
docker compose up --build

# 3. Open the dashboard
open http://localhost:3000

# 4. Trigger API docs
open http://localhost:8000/docs
```

Without Docker:

```bash
# Backend
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
celery -A app.workers.celery_app worker -l info   # in another shell

# Frontend
cd frontend && npm install && npm run dev
```

---

## 🔐 Environment Variables

See [.env.example](.env.example). Critical keys:

| Key | Purpose |
| --- | --- |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis broker + cache |
| `OPENAI_API_KEY` | LLM + embeddings + TTS |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Gmail OAuth |
| `MS_CLIENT_ID` / `MS_CLIENT_SECRET` | Outlook OAuth |
| `WHATSAPP_TOKEN` / `WHATSAPP_PHONE_ID` | WhatsApp Business API |
| `TWILIO_*` | Twilio WhatsApp fallback |
| `JWT_SECRET` | Token signing |
| `AES_SECRET` | Field-level encryption |

---

## 🧪 Tests

```bash
cd backend && pytest -q                       # backend
cd frontend && npm test                       # frontend
```

---

## 📚 Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [API Reference](docs/API.md)
- [Security](docs/SECURITY.md)
- [Production Deployment](docs/DEPLOYMENT.md)
- URL LINK- http://localhost:3000/inbox

---

## 📜 License

Proprietary — © 2026 MailGuard AI Ultra. All rights reserved.
