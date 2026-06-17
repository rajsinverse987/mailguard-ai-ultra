# Architecture

MailGuard AI Ultra is built as a small set of cooperating services that scale
independently. This document explains how they fit together.

---

## High-level

```
                ┌────────────────────────┐
                │  Gmail / Outlook APIs  │
                └──────────┬─────────────┘
                           │ Push / Poll
                           ▼
        ┌──────────────────────────────────────┐
        │   API (FastAPI) — connects accounts  │
        │   • OAuth, webhooks, ingestion       │
        └──────┬───────────────────────────────┘
               │ enqueue process_raw_email
               ▼
        ┌──────────────────────────────────────┐
        │      Celery workers (Redis)          │
        │  • AI analysis   (GPT-4o + LangChain)│
        │  • Fraud detect  (heuristic + LLM)   │
        │  • Embeddings    (OpenAI/SBERT)      │
        │  • TTS           (OpenAI / gTTS)     │
        │  • WhatsApp      (Meta / Twilio)     │
        └──────┬───────────────────────────────┘
               │ persist
               ▼
   ┌─────────────────────────────────────────────┐
   │  Postgres (durable)   ChromaDB (semantic)  │
   │  Redis (cache+broker)  Object storage       │
   └─────────────────────────────────────────────┘
               ▲
               │ API queries
   ┌─────────────────────────────────────────────┐
   │  Next.js dashboard (Tailwind, SWR, Recharts)│
   └─────────────────────────────────────────────┘
```

## Core flow

1. **Connect**: User clicks *Connect Gmail* / *Connect Outlook* and completes
   OAuth. Tokens are stored AES-GCM encrypted.
2. **Ingest**: Gmail Pub/Sub pushes to `/api/v1/webhooks/gmail`; Outlook Graph
   pushes to `/api/v1/webhooks/outlook`. For accounts without webhook support,
   `poll_all_accounts` runs every 5 minutes.
3. **Analyze**: `process_raw_email` runs AI analysis (sender, category, priority,
   summary, action items, dates, etc.) and fraud detection.
4. **Embed**: An embedding of `subject + body` is upserted into ChromaDB with
   metadata so users can search semantically.
5. **Notify**: For high/critical emails, `send_notifications_for_email` is
   enqueued. The worker composes a Hindi voice script, calls TTS, and sends
   both text + audio via the configured WhatsApp provider.
6. **Brief**: Celery Beat triggers morning + evening briefings. Each user gets
   a personalized Hindi voice report.

## Modularity

| Layer | Folder | Purpose |
| --- | --- | --- |
| API | `app/api/v1` | HTTP routers. |
| Domain services | `app/services/*` | AI, voice, messaging, connectors, vector. |
| Workers | `app/workers` | Celery tasks + beat schedule. |
| Persistence | `app/models`, `app/db` | SQLAlchemy + Alembic. |
| Core | `app/core` | Auth, crypto, logging, rate limit. |

## Scaling

- **Stateless API**: 4+ uvicorn replicas behind nginx / ingress.
- **Workers**: Independent horizontal scaling; queue per concern (`mailguard.email`,
  `mailguard.voice`, `mailguard.whatsapp`, `mailguard.briefings`).
- **Postgres**: Single primary + read replicas for analytics queries.
- **Redis**: Sentinel/Cluster for HA; workers share via `CELERY_BROKER_URL`.
- **ChromaDB**: Persistent volume; sharding by tenant in large deployments.

## Security boundaries

- All secrets loaded from env / k8s secret. Never logged.
- AES-GCM field encryption for OAuth tokens (`refresh_token`).
- JWT with HS256; algorithm pinned.
- Rate limit middleware in front of every protected route.
- TLS termination at nginx; HSTS headers set.
