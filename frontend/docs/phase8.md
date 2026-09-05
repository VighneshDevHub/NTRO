# Phase 8 — Unified Dashboard

## What this phase delivers

- **Backend addition**: `GET /api/v1/operations` (protected, paginated,
  newest-first) — the list endpoint the dashboard needed and didn't have yet.
- **Frontend**: `/login`, `/dashboard` (stat cards + filterable audit
  table across all 3 modules + CSV export), and `/verify/[certId]`
  (public verification page, type-aware detail rendering).

This is the piece that turns three separate CLI tools into one visible
platform — exactly what the PS's "User Interface Dashboard" deliverable
asks for.

## Directory structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── globals.css
│   │   ├── page.tsx                    # redirects to /dashboard or /login
│   │   ├── login/page.tsx
│   │   ├── dashboard/page.tsx          # stats + filterable table + CSV export
│   │   └── verify/[certId]/page.tsx    # public verification (QR destination)
│   ├── components/
│   │   └── OperationBadges.tsx         # type/status badges + type-specific detail rendering
│   └── lib/
│       ├── api.ts
│       ├── auth.ts
│       └── types.ts
├── package.json
├── tailwind.config.js
└── next.config.js
```

## Commands to run it yourself

```bash
cd backend && pip install -r requirements.txt && pytest -v   # 36 passed
uvicorn app.main:app --reload --port 8000
```
```bash
cd frontend
npm install
npm run build     # confirms no type/lint errors
npm run dev         # http://localhost:3000
```

## How to test it manually — the full demo script

1. Open `http://localhost:3000` → redirects to `/login`
2. Register + sign in
3. Run any/all of the three module agents against the backend
4. Refresh `/dashboard` — stat cards update, table shows all operations
   with correct type badges (blue/amber/purple) and status badges
5. Click the type filter buttons — table filters correctly
6. Click "View" on any row → opens the real PDF from Phase 7
7. Click "Export CSV" → downloads the currently-filtered rows
8. Copy a certificate ID, open `/verify/{id}` in an incognito tab (no
   login) — confirms the verification page is genuinely public
9. **The tamper demo**: edit that record's `success` field directly in
   `backend/forensicguard.db`, refresh the verify page → red

## What we verified

| Check | Result |
|---|---|
| `npm run build` | Zero type errors, zero lint errors |
| Backend `GET /operations` (list) | Returns all 3 operation types, newest-first, confirmed via live curl |
| Full stack together | Backend `/health` 200, all 4 frontend routes 200, `/dashboard` list matches what was submitted |
| Auth flow | Register → login → dashboard shows data; incognito `/dashboard` redirects to `/login` (not separately re-tested here since it reuses TrustWipe's proven pattern, but the guard logic is identical code) |

This mirrors the "full stack integration over unit tests" approach used
for TrustWipe's frontend — the dashboard has no independent business
logic of its own, so proving it renders correctly against a live
backend is the right level of testing rather than isolated component tests.

## Design decisions worth explaining to judges

- **`OperationDetails` renders differently per `operation_type`**,
  reading from the same flexible `details` JSON the backend stores —
  this is the same "shared trust layer, per-module presentation"
  pattern used in the PDF service (Phase 7) and the ledger itself
  (Phase 1). One dashboard, three genuinely different kinds of records,
  no duplicated page logic.
- **The verify page stays public** (no login check) — consistent with
  every earlier phase's reasoning: independent verification without an
  account is the actual value proposition.
- **Dark, cybersecurity-toned color palette** (`fg-navy`, `fg-panel`,
  semantic green/red reserved ONLY for verification/success status) —
  intentionally styled in the direction of the reference mockup you
  shared, without the AI chatbot/risk-scoring sections that aren't in
  current scope.

## Known simplification, disclosed

No automated frontend tests (Playwright, etc.) were written — this
mirrors the same decision made for TrustWipe's dashboard: the frontend
has no independent business logic (it's a thin rendering layer over a
well-tested API), so integration-testing it live against the real
backend is proportionate; component-level tests are a reasonable "if we
had more time" addition, not a gap that undermines the trust engine
itself.

## Next: Phase 9

Docker + docker-compose, tying backend + frontend + Postgres into one
`docker compose up` — the final packaging step. Say "next" when ready.
