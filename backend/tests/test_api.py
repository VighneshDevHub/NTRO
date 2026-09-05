import pytest
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.operation_record import OperationRecord

DRIVE_ERASE_REPORT = {
    "operation_type": "DRIVE_ERASE",
    "target_description": "SSD-WD2023-88451",
    "started_at": "2026-08-17T10:32:01Z",
    "completed_at": "2026-08-17T10:32:05Z",
    "success": True,
    "operator": "station-1",  # ignored server-side since Phase 5 — see test_auth.py
    "details": {"method": "NIST 800-88 Purge - Crypto Erase", "device_type": "NVMe SSD"},
}

FILE_ERASE_REPORT = {
    "operation_type": "FILE_ERASE",
    "target_description": "/cases/1234/evidence_notes/",
    "started_at": "2026-08-17T11:00:00Z",
    "completed_at": "2026-08-17T11:00:10Z",
    "success": True,
    "operator": "station-1",
    "details": {"file_count": 12, "metadata_scrubbed": True},
}

RECOVERY_REPORT = {
    "operation_type": "RECOVERY",
    "target_description": "seized_drive_image_001.dd",
    "started_at": "2026-08-17T12:00:00Z",
    "completed_at": "2026-08-17T12:15:00Z",
    "success": True,
    "operator": "investigator-7",
    "details": {"files_recovered": 8, "avg_confidence": 0.81},
}


async def _auth_headers(client, email="test-operator@forensicguard.example") -> dict:
    """Since Phase 5, submitting operations requires a login — all
    pre-existing API tests now authenticate first, consistent with the
    new requirement rather than testing against a bypassed backend."""
    await client.post("/api/v1/auth/register", json={"email": email, "password": "supersecret123"})
    login_resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "supersecret123"})
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_health_check(client):
    resp = await client.get("/health")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_submit_drive_erase_report(client):
    headers = await _auth_headers(client)
    resp = await client.post("/api/v1/operations", json=DRIVE_ERASE_REPORT, headers=headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["operation_type"] == "DRIVE_ERASE"
    assert body["details"]["method"] == "NIST 800-88 Purge - Crypto Erase"
    assert body["ledger_sequence_number"] == 1


@pytest.mark.asyncio
async def test_submit_file_erase_report(client):
    headers = await _auth_headers(client)
    resp = await client.post("/api/v1/operations", json=FILE_ERASE_REPORT, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["details"]["file_count"] == 12


@pytest.mark.asyncio
async def test_submit_recovery_report(client):
    headers = await _auth_headers(client)
    resp = await client.post("/api/v1/operations", json=RECOVERY_REPORT, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["details"]["avg_confidence"] == 0.81


@pytest.mark.asyncio
async def test_three_different_modules_share_one_chain(client):
    """End-to-end proof of the Phase 1 architecture claim, over real
    HTTP: submit one operation from each module (same authenticated
    operator, as would be the case for one investigator running all
    three tools) and confirm they land in sequential ledger positions."""
    headers = await _auth_headers(client)
    r1 = await client.post("/api/v1/operations", json=DRIVE_ERASE_REPORT, headers=headers)
    r2 = await client.post("/api/v1/operations", json=FILE_ERASE_REPORT, headers=headers)
    r3 = await client.post("/api/v1/operations", json=RECOVERY_REPORT, headers=headers)

    assert r1.json()["ledger_sequence_number"] == 1
    assert r2.json()["ledger_sequence_number"] == 2
    assert r3.json()["ledger_sequence_number"] == 3


@pytest.mark.asyncio
async def test_get_operation_by_certificate_id(client):
    headers = await _auth_headers(client)
    create_resp = await client.post("/api/v1/operations", json=DRIVE_ERASE_REPORT, headers=headers)
    cert_id = create_resp.json()["certificate_id"]

    # GET is public — no auth header needed here, by design
    get_resp = await client.get(f"/api/v1/operations/{cert_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["certificate_id"] == cert_id


@pytest.mark.asyncio
async def test_get_operation_not_found(client):
    resp = await client.get("/api/v1/operations/does-not-exist")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_verify_genuine_record_passes(client):
    headers = await _auth_headers(client)
    create_resp = await client.post("/api/v1/operations", json=RECOVERY_REPORT, headers=headers)
    cert_id = create_resp.json()["certificate_id"]

    verify_resp = await client.get(f"/api/v1/verify/{cert_id}")  # public, no auth
    body = verify_resp.json()
    assert body["signature_valid"] is True
    assert body["chain_intact"] is True
    assert body["overall_verified"] is True


@pytest.mark.asyncio
async def test_verify_detects_tampered_record(client):
    """The demo moment: create a valid record, verify green, tamper
    directly in the DB, verify again and confirm red — tested here
    against a RECOVERY record specifically, since forensic integrity
    matters most for that module."""
    headers = await _auth_headers(client)
    create_resp = await client.post("/api/v1/operations", json=RECOVERY_REPORT, headers=headers)
    cert_id = create_resp.json()["certificate_id"]

    verify_resp = await client.get(f"/api/v1/verify/{cert_id}")
    assert verify_resp.json()["overall_verified"] is True

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(OperationRecord).where(OperationRecord.certificate_id == cert_id)
        )
        record = result.scalar_one()
        record.success = False  # flip a fact after the fact
        await db.commit()

    verify_resp_after = await client.get(f"/api/v1/verify/{cert_id}")
    body = verify_resp_after.json()
    assert body["signature_valid"] is False
    assert body["overall_verified"] is False


@pytest.mark.asyncio
async def test_get_operation_pdf_is_public_and_valid(client):
    headers = await _auth_headers(client)
    create_resp = await client.post("/api/v1/operations", json=DRIVE_ERASE_REPORT, headers=headers)
    cert_id = create_resp.json()["certificate_id"]

    pdf_resp = await client.get(f"/api/v1/operations/{cert_id}/pdf")  # no auth header — public
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert pdf_resp.content.startswith(b"%PDF")


@pytest.mark.asyncio
async def test_get_operation_pdf_for_recovery_type(client):
    headers = await _auth_headers(client)
    create_resp = await client.post("/api/v1/operations", json=RECOVERY_REPORT, headers=headers)
    cert_id = create_resp.json()["certificate_id"]

    pdf_resp = await client.get(f"/api/v1/operations/{cert_id}/pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.content.startswith(b"%PDF")


@pytest.mark.asyncio
async def test_get_operation_pdf_404_for_unknown_id(client):
    resp = await client.get("/api/v1/operations/does-not-exist/pdf")
    assert resp.status_code == 404
