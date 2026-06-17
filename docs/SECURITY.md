# Security

MailGuard AI Ultra takes a defense-in-depth approach.

## Authentication

- **JWT (HS256)** with 24-hour expiry by default. Algorithm pinned.
- Passwords hashed with **bcrypt** via passlib.
- Role-based access control (`admin`, `user`, `auditor`) — see `core/security.py`.

## Encryption

- **TLS** in transit (terminated at nginx with modern ciphers).
- **AES-GCM** field-level encryption for OAuth refresh tokens (see
  `app/core/crypto.py`). Nonce stored alongside ciphertext.
- `AES_SECRET` validated at startup; rejects anything not 16/24/32 bytes after
  base64 decode.

## Rate limiting

- Per-user **token-bucket** in Redis: 120 burst, refills at 2 rps. Backed by
  `app/core/rate_limit.py`. Tune via env if needed.

## Audit logging

- Every API request logged with user_id, IP, UA, action, resource.
- Persisted to `audit_logs` table (immutable).

## Webhook verification

- Gmail Pub/Sub messages validated against JWT signed by Google (production).
- Outlook webhook `clientState` validated against expected value.

## Headers

- `Strict-Transport-Security`, `X-Frame-Options`, `X-Content-Type-Options`,
  `Referrer-Policy` set by nginx.

## OWASP mitigations

- SQL injection: SQLAlchemy parameterized queries throughout.
- XSS: React auto-escapes; no `dangerouslySetInnerHTML` outside controlled
  components.
- CSRF: API is bearer-token only; cookie usage intentionally avoided.
- SSRF: outbound HTTP only to whitelisted domains (`graph.microsoft.com`,
  `gmail.googleapis.com`, `graph.facebook.com`).
- Secrets: never logged. `.env` gitignored.

## Reporting vulnerabilities

Email `security@mailguard.ai` with details. We respond within 48 hours.
