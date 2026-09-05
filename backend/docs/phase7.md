# Phase 7 — Certificate & Forensic Report PDFs

## What this phase delivers

`GET /api/v1/operations/{certificate_id}/pdf` — a single endpoint that
renders a different document depending on `operation_type`:

| Operation Type | Document Title |
|---|---|
| `DRIVE_ERASE` | Certificate of Secure Drive Erasure |
| `FILE_ERASE` | Certificate of Secure File & Folder Erasure |
| `RECOVERY` | Forensic File Recovery Report |

All three share the same trust footer: report hash, truncated
signature, and a QR code linking to live re-verification. As with
TrustWipe's Phase 3: **the PDF is a convenience, not the source of
trust** — the QR code always re-checks the live signed record.

## Files added/changed

```
backend/
├── app/
│   ├── services/
│   │   └── pdf_service.py          # NEW — routes by operation_type, renders type-specific fields
│   └── api/v1/
│       └── operations.py           # CHANGED — added GET /{id}/pdf (public)
└── tests/
    ├── test_pdf_service.py         # NEW
    └── test_api.py                 # CHANGED — added PDF endpoint tests
```

## Commands to run it yourself

```bash
cd backend
pip install -r requirements.txt   # now includes qrcode[pil], reportlab
pytest -v                          # 34 passed
uvicorn app.main:app --reload --port 8000
```

## How to test it manually

1. Register/login, submit a `DRIVE_ERASE` operation
2. `GET /api/v1/operations/{certificate_id}/pdf` — **no auth header
   needed**, this is deliberately public — opens a real certificate PDF
3. Submit a `RECOVERY` operation with a `details.files` list
4. Fetch its PDF — confirm it shows "Forensic File Recovery Report" as
   the title and includes the per-file recovered-files table

Two real sample PDFs (one drive-erase certificate, one recovery report)
are included alongside this delivery, generated from actual live API
calls.

## Design decisions worth explaining to judges

- **One shared PDF engine, three different documents.** Rather than
  three separate PDF generators (which would drift out of sync over
  time), `_type_specific_rows()` is the only per-type branch — the
  header, QR code, and trust footer are identical code paths for all
  three. This mirrors the same "shared trust layer, per-module details"
  pattern used throughout the whole project.
- **Graceful degradation on missing `details` keys.** Since `details`
  is a flexible JSON blob, a malformed or minimal submission must not
  crash PDF generation — every field falls back to `"N/A"` rather than
  raising. Tested directly (`test_pdf_handles_missing_details_keys_gracefully`).
- **The recovered-files table caps displayed rows (15 max) with a
  note pointing to the full JSON record.** A recovery run finding
  hundreds of files shouldn't produce an unreadable, page-sprawling PDF
  — tested with 50 synthetic files to confirm no crash.

## What we tested

| Test | What it proves |
|---|---|
| `test_drive_erase_pdf_is_valid` / `test_file_erase_pdf_is_valid` / `test_recovery_pdf_is_valid` | Each operation type renders a real, valid PDF |
| `test_recovery_pdf_handles_many_files_without_crashing` | The row-capping logic works under load (50 files) |
| `test_pdf_handles_missing_details_keys_gracefully` | An empty `details` dict doesn't crash generation |
| `test_unknown_operation_type_falls_back_to_generic_title` | A future 4th module's records (unknown type) still render something sensible rather than erroring |
| `test_get_operation_pdf_is_public_and_valid` / `test_get_operation_pdf_for_recovery_type` | Full HTTP round trip; **confirms the PDF endpoint is public**, consistent with `GET`/`verify` |
| `test_get_operation_pdf_404_for_unknown_id` | Clean 404, not a crash, for a bad certificate ID |

All 34 backend tests pass (25 from Phase 5 + 9 new PDF-specific ones).
Also generated two real sample PDFs from live API calls — a drive-erase
certificate and a recovery report — both valid, confirmed via `file`.

## Next

The unified dashboard (Next.js) tying all three modules + audit log
into one visual interface, styled in the direction of the reference
mockup where realistic (secure erase panel, verification/certificate
panel, audit log) — without the AI chatbot/risk-scoring parts that
aren't in current scope. Say "next" when ready.
