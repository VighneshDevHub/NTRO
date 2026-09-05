# Phase 5 — JWT Auth + Persistent Signing Keys

## What this phase delivers

Two fixes for the two highest-severity gaps flagged in an external code
review:

1. **Persistent signing keys** — a keypair is now auto-generated and
   saved to `backend/keys/` on first run, and reused on every subsequent
   start. Certificates signed before a restart now correctly still
   verify after one (this was explicitly broken before this phase).
2. **JWT authentication on operation submission** — `POST /api/v1/operations`
   now requires a logged-in operator. The `operator` field is no longer
   client-submitted free text; it is overridden server-side with the
   authenticated user's email, closing the "anyone can claim to be any
   operator" gap.

`GET /api/v1/operations/{id}` and `GET /api/v1/verify/{id}` remain
**public, deliberately** — independent verification without needing an
account is the core value proposition and must not be gated.

## Files added/changed

```
backend/
├── app/
│   ├── core/
│   │   ├── crypto.py              # CHANGED — persistent key resolution
│   │   └── security.py            # NEW — password hashing + JWT
│   ├── models/
│   │   └── user.py                # NEW
│   ├── schemas/
│   │   └── auth.py                # NEW
│   ├── api/
│   │   ├── deps.py                # CHANGED — added get_current_user
│   │   └── v1/
│   │       ├── auth.py            # NEW — register/login
│   │       └── operations.py      # CHANGED — POST now requires auth, overrides operator
│   └── main.py                    # CHANGED — wired in auth router
├── tests/
│   ├── test_key_persistence.py    # NEW
│   ├── test_auth.py               # NEW
│   └── test_api.py                # CHANGED — all POSTs now authenticate first
└── keys/                          # NEW (gitignored) — local persisted keypair

drive-eraser-agent/, file-folder-eraser/, recovery-engine/
├── src/
│   ├── api_client.py              # CHANGED — logs in (auto-registers), attaches JWT
│   └── main.py                    # CHANGED — --operator replaced by --email/--password
```

## Commands to run it yourself

```bash
cd backend
pip install -r requirements.txt
rm -rf keys/ *.db     # clean slate to see first-run key generation
pytest -v              # 25 passed
uvicorn app.main:app --reload --port 8000
```

Then any agent:
```bash
cd drive-eraser-agent
python -m src.main --target test.img --email investigator@example.com --password secret123 --api-url http://localhost:8000
```
The first run auto-registers that email; subsequent runs just log in.

## How to test the two fixes manually

**Persistent keys:**
1. Run the backend, submit one operation, note the certificate ID
2. Stop the server (Ctrl+C), start it again (`uvicorn app.main:app ...`)
3. `GET /api/v1/verify/{certificate_id}` — should still show `overall_verified: true`
4. Confirm `backend/keys/private.pem` and `public.pem` exist and are unchanged in content across the restart

**Auth:**
1. `POST /api/v1/operations` with **no** Authorization header — confirm `401`
2. Register + log in, get a token, retry with `Authorization: Bearer <token>` — confirm `201`
3. In the request body, set `"operator": "someone-else"` — confirm the response's `operator` field shows YOUR logged-in email, not what you typed

## What we tested

| Test file | What it proves |
|---|---|
| `test_key_persistence.py` (2 tests) | A keypair generated on "first run" is reused (not regenerated) on a simulated restart, and a certificate signed before the restart still verifies after it; env-var keys correctly take priority over a persisted file when both are present |
| `test_auth.py` (8 tests) | Registration, login, duplicate-email rejection; **critically**: submission without a token fails (401), with a garbage token fails (401), with a valid token succeeds; the operator field is overridden by the authenticated identity even when the client sends a different value in the request body; verify/get remain public |
| `test_api.py` (updated) | All pre-existing Phase 1 tests still pass, now going through the auth flow rather than testing against a bypassed backend |

**80 tests total pass across all 4 projects** (25 backend + 14 + 19 + 22
agents, unchanged). Also ran a full live demo: confirmed unauthenticated
submission is rejected, ran all three agents end-to-end with three
different operator accounts (each auto-registering on first use),
confirmed sequential ledger positions across modules, and — the key
proof — **restarted the backend as an entirely new process and
confirmed a certificate signed before the restart still verified true
after it.**

## An intentional simplification, disclosed

Full RBAC (Administrator / Investigator / Auditor roles with different
permissions, as recommended in the review) was **not** built in this
phase — every logged-in user currently has identical permissions. This
was a deliberate scope decision: basic auth closes the "anyone can call
the API" gap, which was the actual critical issue; a full role system is
real, well-understood additional work that's better scoped as an
explicit "Production Roadmap" item than rushed in alongside everything
else in this phase. State this plainly if asked — it's a scoping
decision, not an oversight.

## Known duplication, flagged not fixed

The updated `api_client.py` is now byte-identical across all three agent
folders. This was a pre-existing duplication (flagged in the earlier
review) that got slightly worse by adding auth logic to all three
copies rather than one shared location. Recommended before adding a 4th
module: extract into a small shared package. Not done now, to avoid
introducing a shared-dependency refactor risk this close to a working,
tested state across 4 projects.

## Next

Windows device detection for the Drive Eraser, then certificate PDFs +
the unified dashboard. Say "next" when ready.
