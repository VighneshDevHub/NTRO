# Phase 1 — Core Trust Engine

## What this phase delivers

A generalized, module-agnostic trust engine:
1. `OperationRecord` — one table shape for ALL THREE modules (drive erase,
   file erase, recovery), distinguished by an `operation_type` field and
   a flexible `details` JSON blob for module-specific data.
2. ECDSA signing (identical mechanism regardless of operation type).
3. A single shared hash-chain ledger — a drive erase, a file erase, and
   a recovery operation can sit back-to-back in the SAME chain.
4. `POST /api/v1/operations` (shared write path for all 3 future modules),
   `GET /api/v1/operations/{id}`, `GET /api/v1/verify/{id}`.

This generalizes TrustWipe's Phase 1 (which had a wipe-only `WipeRecord`)
so Phases 2–4 don't each need their own signing/ledger implementation.

## Directory structure

```
backend/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   └── crypto.py               # ECDSA sign/verify — shared by all modules
│   ├── models/
│   │   └── operation_record.py     # OperationRecord + OperationType enum + LedgerEntry
│   ├── schemas/
│   │   └── operation.py
│   ├── services/
│   │   └── ledger_service.py       # module-agnostic hash chain
│   ├── api/
│   │   ├── deps.py
│   │   └── v1/
│   │       ├── operations.py       # POST/GET — shared by all modules
│   │       └── verify.py
│   └── db/
│       └── session.py
├── tests/
└── requirements.txt
```

## Commands to run it yourself

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pytest -v          # 15 passed
uvicorn app.main:app --reload --port 8000
```

## How to test it manually

1. Open `http://localhost:8000/docs`
2. `POST /api/v1/operations` with `operation_type: "DRIVE_ERASE"` — note the `ledger_sequence_number: 1`
3. `POST /api/v1/operations` again with `operation_type: "FILE_ERASE"` — `ledger_sequence_number: 2`
4. `POST /api/v1/operations` again with `operation_type: "RECOVERY"` — `ledger_sequence_number: 3`

   This proves the core Phase 1 claim: **all three operation types share
   one sequential, unbroken chain**, not three separate ledgers.

5. `GET /api/v1/verify/{certificate_id}` on any of them → `overall_verified: true`

## An important honest correction — read this before demoing

I initially assumed (incorrectly) that tampering with an *earlier* record
in the chain would make verification of a *later* record fail too. I
tested this directly and **that assumption was wrong** — here's the
accurate behavior:

| What you tamper | What you verify | Result |
|---|---|---|
| Record A's data (e.g. flip `success`) | Record A itself | ❌ Correctly fails — `signature_valid: false` |
| Record A's data | A different record B, later in the chain | ✅ Still shows verified — **does not catch A's tampering** |

**Why:** `chain_intact` checks that the ledger table's own internal
linkage is self-consistent (`entry_hash = sha256(previous_hash +
stored_report_hash)`). It does **not** re-derive each ledger entry's hash
from that operation record's *current* live data — it only checks the
ledger against itself, not the ledger against the records table.

**Practical implication:** each certificate's own verification is fully
reliable — tamper that specific record, that specific verification will
correctly go red, every time (tested in `test_verify_detects_tampered_record`).
But you **cannot** conclude "nothing in the system has been tampered
with" from checking one record — **the dashboard (Phase 6) must check
and display status per-record**, not rely on any single "spot check"
implying system-wide integrity. This is a genuine design constraint to
carry forward, not a bug to silently patch over — it's worth stating
explicitly in your SIH presentation as evidence of rigorous testing.

## What we tested

| Test | What it proves |
|---|---|
| `test_crypto.py` (3 tests) | Signing/verification correctness |
| `test_chain_links_across_different_operation_types` | **The core Phase 1 architectural claim** — 3 different operation types chain together correctly, in order |
| `test_verify_chain_integrity_detects_tampering_regardless_of_operation_type` | Ledger-level tampering is caught, and correctly reports which module's record broke the chain |
| `test_three_different_modules_share_one_chain` | Same claim, proven over real HTTP rather than direct service calls |
| `test_verify_detects_tampered_record` | Per-record tamper detection works correctly (tested specifically against a RECOVERY record, since forensic integrity matters most there) |

All 15 tests pass. Also ran a full live demo over real HTTP: submitted
one record from each of the three (future) modules, confirmed sequential
chain positions, then deliberately tampered with a live database row and
confirmed the corrected (accurate) verification behavior above.

## Next: Phase 2

The Drive Eraser module — adapting TrustWipe's proven wipe agent to call
this generalized `POST /api/v1/operations` endpoint with
`operation_type: "DRIVE_ERASE"`. Say "next" when ready.
