# Phase 2 — Drive Eraser Module

## What this phase delivers

The Drive Eraser CLI agent — functionally identical to TrustWipe's proven
wipe agent (same detectors, same NIST 800-88 method selection, same
wipers, same read-back verification), adapted at exactly one boundary:
the report it submits now matches ForensicGuard's **generalized**
`OperationReportIn` schema instead of a wipe-specific one.

## What changed vs. TrustWipe's wipe agent (and what didn't)

| Component | Status |
|---|---|
| `detectors/` | Unchanged — same file-target + Linux block-device detection |
| `wipers/` (Clear, Purge, Crypto Erase) | Unchanged — same NIST 800-88 logic |
| `method_selector.py` | Unchanged |
| `verifier.py` | Unchanged |
| `report_builder.py` | **Changed** — now emits `{operation_type: "DRIVE_ERASE", target_description, details: {...}}` instead of a flat wipe-only shape |
| `api_client.py` | **Changed** — posts to `/api/v1/operations` instead of `/api/v1/wipes` |

This is exactly the "reuse what's proven, adapt the boundary" approach
promised in the roadmap — the actual wiping logic didn't need to change
at all.

## Directory structure

```
drive-eraser-agent/
├── src/
│   ├── main.py                    # CLI entrypoint
│   ├── method_selector.py
│   ├── verifier.py
│   ├── report_builder.py          # CHANGED — generalized report shape
│   ├── api_client.py              # CHANGED — posts to /api/v1/operations
│   ├── detectors/
│   │   ├── base.py
│   │   ├── file_target.py         # safe demo mode
│   │   └── linux_block_device.py  # real hardware, gated behind --real-device
│   └── wipers/
│       ├── base.py
│       ├── clear.py
│       ├── purge.py
│       └── crypto_erase.py
└── tests/
```

## Commands to run it yourself

```bash
cd drive-eraser-agent
pip install -r requirements.txt
pytest -v      # 14 passed

# Make sure the Phase 1 backend is running first:
#   cd ../backend && uvicorn app.main:app --port 8000

python3 -c "open('test_volume.img','wb').write(b'CASE-1234-EVIDENCE-'*3000)"
python -m src.main --target test_volume.img --operator "forensics-station-1" --api-url http://localhost:8000
```

Expected output ends with a `Certificate issued: <uuid>` and
`Ledger sequence number: 1` — confirming it landed correctly in the
shared, module-agnostic ledger from Phase 1.

## How to test it manually / for your demo

1. `head -c 60 test_volume.img` before running — shows readable evidence text
2. Run the agent (command above)
3. `head -c 60 test_volume.img | od -A x -t x1z` after — pure random bytes
4. `GET /api/v1/operations/{certificate_id}` — confirm `operation_type: "DRIVE_ERASE"` and that `details` contains the device model/type/method nested correctly
5. `GET /api/v1/verify/{certificate_id}` — `overall_verified: true`

## What we tested

| Test file | What it proves |
|---|---|
| `test_wipers.py` (3 tests) | Each wiper actually overwrites content correctly (reused, unchanged from TrustWipe) |
| `test_detectors.py` (7 tests) | Detection + method selection logic (reused, unchanged) |
| `test_verifier.py` (2 tests) | Read-back verification catches both real wipes and no-op wipes correctly (reused, unchanged) |
| `test_report_builder.py` (2 tests) | **New** — confirms the report's top-level keys exactly match the backend's generalized `OperationReportIn` schema, and that `success` tracks verification result (not just "the wipe ran") |

All 14 tests pass. Also ran a full live integration: wiped a real test
file end-to-end against the actual Phase 1 backend (not mocked),
confirmed the `details` JSON nested correctly, and confirmed
`GET /verify/{id}` returned `overall_verified: true`.

## Production notes

Identical to TrustWipe Phase 2's production notes — real ATA Secure
Erase / NVMe Sanitize hardware commands, Windows detector support, and
bootable-USB packaging remain documented extensions rather than built,
since the file-target demo mode proves the same logic path.

## Next: Phase 3

The Secure File & Folder Eraser module — genuinely new work: selective
deletion inside a live filesystem, metadata scrubbing, and free-space
overwriting, reporting through the same `operation_type: "FILE_ERASE"`
path. Say "next" when ready.
